from fastapi import APIRouter, Request, Response, HTTPException, Depends
from pydantic import BaseModel
from database import get_db, log_action
from auth import verify_password, create_session, delete_session

router = APIRouter()

class LoginRequest(BaseModel):
    username: str
    password: str

@router.post("/login")
def login(body: LoginRequest, response: Response):
    with get_db() as conn:
        user = conn.execute(
            "SELECT * FROM users WHERE username=?", (body.username,)
        ).fetchone()
    if not user or not verify_password(body.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid username or password")
    token = create_session(user["id"])
    response.set_cookie(
        key="session", value=token,
        httponly=True, samesite="lax", max_age=86400*30
    )
    log_action(user["id"], "login")
    return {"ok": True, "username": user["username"], "role": user["role"]}

@router.post("/logout")
def logout(request: Request, response: Response):
    token = request.cookies.get("session")
    if token:
        delete_session(token)
    response.delete_cookie("session")
    return {"ok": True}
