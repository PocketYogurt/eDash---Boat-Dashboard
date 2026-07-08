import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from database import init_db, get_db
from auth import hash_password
from routers import auth, users, routes, trips, admin, tides

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialise DB schema
    init_db()
    # Create default admin account if no users exist
    with get_db() as conn:
        count = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
        if count == 0:
            admin_user = os.environ.get("ADMIN_USERNAME", "admin")
            admin_pass = os.environ.get("ADMIN_PASSWORD", "changeme123")
            conn.execute(
                "INSERT INTO users (username, password_hash, role) VALUES (?,?,?)",
                (admin_user, hash_password(admin_pass), "admin")
            )
            conn.commit()
            print(f"[eBoat] Created default admin: username={admin_user}")
    yield

app = FastAPI(lifespan=lifespan, docs_url=None, redoc_url=None)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router,   prefix="/api/auth")
app.include_router(users.router,  prefix="/api")
app.include_router(routes.router, prefix="/api")
app.include_router(trips.router,  prefix="/api")
app.include_router(admin.router,  prefix="/api/admin")
app.include_router(tides.router,  prefix="/api/tides")

@app.get("/api/health")
def health():
    """Unauthenticated health check — useful for debugging startup issues."""
    return {"status": "ok"}
