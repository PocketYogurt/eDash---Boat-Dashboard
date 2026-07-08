import json
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from database import get_db, log_action
from deps import get_current_user

router = APIRouter()

class RouteCreate(BaseModel):
    name: str
    coords: list  # [{lat, lng}, ...]

class RouteUpdate(BaseModel):
    name: str | None = None
    coords: list | None = None

@router.get("/routes")
def list_routes(user=Depends(get_current_user)):
    with get_db() as conn:
        rows = conn.execute(
            "SELECT id, name, created_at, updated_at FROM boat_routes WHERE user_id=? ORDER BY updated_at DESC",
            (user["id"],)
        ).fetchall()
    return [dict(r) for r in rows]

@router.post("/routes")
def create_route(body: RouteCreate, user=Depends(get_current_user)):
    with get_db() as conn:
        cur = conn.execute(
            "INSERT INTO boat_routes (user_id, name, coords_json) VALUES (?,?,?)",
            (user["id"], body.name, json.dumps(body.coords))
        )
        conn.commit()
        route_id = cur.lastrowid
    log_action(user["id"], "route_save", json.dumps({"name": body.name}))
    return {"id": route_id, "name": body.name}

@router.get("/routes/{route_id}")
def get_route(route_id: int, user=Depends(get_current_user)):
    with get_db() as conn:
        row = conn.execute(
            "SELECT * FROM boat_routes WHERE id=? AND user_id=?",
            (route_id, user["id"])
        ).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Route not found")
    d = dict(row)
    d["coords"] = json.loads(d["coords_json"])
    del d["coords_json"]
    return d

@router.put("/routes/{route_id}")
def update_route(route_id: int, body: RouteUpdate, user=Depends(get_current_user)):
    with get_db() as conn:
        row = conn.execute(
            "SELECT * FROM boat_routes WHERE id=? AND user_id=?",
            (route_id, user["id"])
        ).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Route not found")
        name = body.name or row["name"]
        coords = json.dumps(body.coords) if body.coords is not None else row["coords_json"]
        conn.execute(
            "UPDATE boat_routes SET name=?, coords_json=?, updated_at=CURRENT_TIMESTAMP WHERE id=?",
            (name, coords, route_id)
        )
        conn.commit()
    return {"ok": True}

@router.delete("/routes/{route_id}")
def delete_route(route_id: int, user=Depends(get_current_user)):
    with get_db() as conn:
        conn.execute(
            "DELETE FROM boat_routes WHERE id=? AND user_id=?",
            (route_id, user["id"])
        )
        conn.commit()
    return {"ok": True}
