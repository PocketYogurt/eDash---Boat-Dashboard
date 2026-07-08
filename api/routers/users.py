import os
import httpx
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
from database import get_db, log_action
from auth import verify_password, hash_password
from deps import get_current_user

router = APIRouter()

@router.get("/me")
def me(user=Depends(get_current_user)):
    return {
        "id": user["id"],
        "username": user["username"],
        "email": user["email"],
        "role": user["role"],
        "use_default_keys": bool(user["use_default_keys"]),
        "created_at": user["created_at"],
        "last_seen": user["last_seen"]
    }

@router.get("/me/config")
def get_config(user=Depends(get_current_user)):
    """Return the effective API keys for this session."""
    use_defaults = bool(user["use_default_keys"])
    return {
        "google_maps_key": os.environ.get("DEFAULT_GOOGLE_MAPS_KEY", "") if use_defaults else (user["google_maps_key"] or ""),
        "admiralty_key":   os.environ.get("DEFAULT_ADMIRALTY_KEY", "")   if use_defaults else (user["admiralty_key"]   or ""),
        "aisstream_key":   os.environ.get("DEFAULT_AISSTREAM_KEY", "")   if use_defaults else (user["aisstream_key"]   or ""),
        "use_default_keys": use_defaults
    }

class PasswordChange(BaseModel):
    current_password: str
    new_password: str

class SettingsUpdate(BaseModel):
    use_default_keys: bool
    google_maps_key: Optional[str] = None
    admiralty_key: Optional[str] = None
    aisstream_key: Optional[str] = None

class TestKeys(BaseModel):
    google_maps_key: Optional[str] = None
    admiralty_key: Optional[str] = None
    aisstream_key: Optional[str] = None

@router.put("/me/password")
def change_password(body: PasswordChange, user=Depends(get_current_user)):
    if not verify_password(body.current_password, user["password_hash"]):
        raise HTTPException(status_code=400, detail="Current password is incorrect")
    if len(body.new_password) < 8:
        raise HTTPException(status_code=400, detail="New password must be at least 8 characters")
    with get_db() as conn:
        conn.execute(
            "UPDATE users SET password_hash=? WHERE id=?",
            (hash_password(body.new_password), user["id"])
        )
        conn.commit()
    log_action(user["id"], "password_change")
    return {"ok": True}

@router.put("/me/settings")
def update_settings(body: SettingsUpdate, user=Depends(get_current_user)):
    if not body.use_default_keys:
        # Require all three keys when not using defaults
        missing = []
        if not body.google_maps_key: missing.append("Google Maps")
        if not body.admiralty_key:   missing.append("Admiralty")
        if not body.aisstream_key:   missing.append("AIS Stream")
        if missing:
            raise HTTPException(
                status_code=400,
                detail=f"Missing API keys: {', '.join(missing)}"
            )
    with get_db() as conn:
        conn.execute(
            """UPDATE users SET
               use_default_keys=?, google_maps_key=?, admiralty_key=?, aisstream_key=?
               WHERE id=?""",
            (
                1 if body.use_default_keys else 0,
                body.google_maps_key,
                body.admiralty_key,
                body.aisstream_key,
                user["id"]
            )
        )
        conn.commit()
    log_action(user["id"], "settings_update")
    return {"ok": True}

@router.post("/me/test-keys")
async def test_keys(body: TestKeys, user=Depends(get_current_user)):
    """Test user-provided API keys before saving."""
    results = {}

    # Test Admiralty key — try to fetch stations list
    if body.admiralty_key:
        try:
            async with httpx.AsyncClient(timeout=8) as client:
                r = await client.get(
                    "https://admiraltyapi.azure-api.net/uktidalapi/api/V1/Stations",
                    headers={"Ocp-Apim-Subscription-Key": body.admiralty_key}
                )
                results["admiralty"] = r.status_code == 200
        except Exception:
            results["admiralty"] = False
    else:
        results["admiralty"] = None

    # Test AIS key — just validate it's non-empty for now
    # (WebSocket connections can't be tested server-side easily)
    results["aisstream"] = bool(body.aisstream_key and len(body.aisstream_key) > 10)

    # Test Google Maps key — try a minimal geocode request
    if body.google_maps_key:
        try:
            async with httpx.AsyncClient(timeout=8) as client:
                r = await client.get(
                    "https://maps.googleapis.com/maps/api/geocode/json",
                    params={"address": "London", "key": body.google_maps_key}
                )
                data = r.json()
                results["google_maps"] = data.get("status") not in ("REQUEST_DENIED", "INVALID_REQUEST")
        except Exception:
            results["google_maps"] = False
    else:
        results["google_maps"] = None

    return results
