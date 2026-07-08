import bcrypt
import uuid
import os
from datetime import datetime, timedelta
from database import get_db

SESSION_DAYS = int(os.environ.get("SESSION_DAYS", 30))

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))

def create_session(user_id: int) -> str:
    token = str(uuid.uuid4())
    expires = datetime.utcnow() + timedelta(days=SESSION_DAYS)
    with get_db() as conn:
        conn.execute(
            "DELETE FROM sessions WHERE user_id=? AND expires_at < CURRENT_TIMESTAMP",
            (user_id,)
        )
        conn.execute(
            "INSERT INTO sessions (user_id, token, expires_at) VALUES (?,?,?)",
            (user_id, token, expires.isoformat())
        )
        conn.execute(
            "UPDATE users SET last_seen=CURRENT_TIMESTAMP WHERE id=?",
            (user_id,)
        )
        conn.commit()
    return token

def get_user_from_token(token: str):
    if not token:
        return None
    with get_db() as conn:
        row = conn.execute(
            """SELECT u.* FROM users u
               JOIN sessions s ON s.user_id = u.id
               WHERE s.token=? AND s.expires_at > CURRENT_TIMESTAMP""",
            (token,)
        ).fetchone()
    return row

def delete_session(token: str):
    with get_db() as conn:
        conn.execute("DELETE FROM sessions WHERE token=?", (token,))
        conn.commit()
