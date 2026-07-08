from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
from database import get_db
from auth import hash_password
from deps import require_admin

router = APIRouter()

class CreateUser(BaseModel):
    username: str
    email: Optional[str] = None
    password: str
    role: str = "user"

class UpdateUser(BaseModel):
    role: Optional[str] = None
    email: Optional[str] = None

@router.get("/users")
def list_users(admin=Depends(require_admin)):
    with get_db() as conn:
        rows = conn.execute(
            """SELECT u.id, u.username, u.email, u.role,
                      u.use_default_keys, u.created_at, u.last_seen,
                      COUNT(DISTINCT r.id) AS route_count,
                      COUNT(DISTINCT t.id) AS trip_count
               FROM users u
               LEFT JOIN boat_routes r ON r.user_id = u.id
               LEFT JOIN trips t ON t.user_id = u.id
               GROUP BY u.id
               ORDER BY u.created_at DESC"""
        ).fetchall()
    return [dict(r) for r in rows]

@router.post("/users")
def create_user(body: CreateUser, admin=Depends(require_admin)):
    if len(body.password) < 8:
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters")
    if body.role not in ("user", "admin"):
        raise HTTPException(status_code=400, detail="Role must be 'user' or 'admin'")
    try:
        with get_db() as conn:
            cur = conn.execute(
                "INSERT INTO users (username, email, password_hash, role) VALUES (?,?,?,?)",
                (body.username, body.email, hash_password(body.password), body.role)
            )
            conn.commit()
            return {"id": cur.lastrowid, "username": body.username}
    except Exception as e:
        if "UNIQUE" in str(e):
            raise HTTPException(status_code=409, detail="Username already exists")
        raise

@router.put("/users/{user_id}")
def update_user(user_id: int, body: UpdateUser, admin=Depends(require_admin)):
    with get_db() as conn:
        if body.role:
            if body.role not in ("user", "admin"):
                raise HTTPException(status_code=400, detail="Role must be 'user' or 'admin'")
            conn.execute("UPDATE users SET role=? WHERE id=?", (body.role, user_id))
        if body.email is not None:
            conn.execute("UPDATE users SET email=? WHERE id=?", (body.email, user_id))
        conn.commit()
    return {"ok": True}

@router.delete("/users/{user_id}")
def delete_user(user_id: int, admin=Depends(require_admin)):
    with get_db() as conn:
        user = conn.execute("SELECT * FROM users WHERE id=?", (user_id,)).fetchone()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        if user["role"] == "admin":
            # Count admins — don't allow deleting the last admin
            count = conn.execute("SELECT COUNT(*) FROM users WHERE role='admin'").fetchone()[0]
            if count <= 1:
                raise HTTPException(status_code=400, detail="Cannot delete the only admin account")
        conn.execute("DELETE FROM users WHERE id=?", (user_id,))
        conn.commit()
    return {"ok": True}

@router.get("/stats")
def get_stats(admin=Depends(require_admin)):
    with get_db() as conn:
        total_users   = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
        total_routes  = conn.execute("SELECT COUNT(*) FROM boat_routes").fetchone()[0]
        total_trips   = conn.execute("SELECT COUNT(*) FROM trips").fetchone()[0]
        active_today  = conn.execute(
            "SELECT COUNT(DISTINCT user_id) FROM sessions WHERE created_at > DATE('now','-1 day')"
        ).fetchone()[0]
        active_week   = conn.execute(
            "SELECT COUNT(DISTINCT user_id) FROM sessions WHERE created_at > DATE('now','-7 days')"
        ).fetchone()[0]
        recent_actions = conn.execute(
            """SELECT u.username, l.action, l.created_at
               FROM usage_log l
               LEFT JOIN users u ON u.id = l.user_id
               ORDER BY l.created_at DESC LIMIT 50"""
        ).fetchall()
    return {
        "total_users":     total_users,
        "total_routes":    total_routes,
        "total_trips":     total_trips,
        "active_today":    active_today,
        "active_week":     active_week,
        "recent_actions":  [dict(r) for r in recent_actions]
    }
