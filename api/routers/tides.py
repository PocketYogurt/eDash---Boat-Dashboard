import os
import httpx
from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.responses import JSONResponse
from deps import get_current_user

router = APIRouter()

ADMIRALTY_BASE = "https://admiraltyapi.azure-api.net/uktidalapi/api/V1"

def get_admiralty_key(user) -> str:
    """Return the Admiralty API key for this user — their own or the server default."""
    if user["use_default_keys"] or not user["admiralty_key"]:
        key = os.environ.get("DEFAULT_ADMIRALTY_KEY", "")
    else:
        key = user["admiralty_key"]
    if not key:
        raise HTTPException(status_code=503, detail="Admiralty API key not configured")
    return key

@router.get("/Stations")
async def get_stations(user=Depends(get_current_user)):
    key = get_admiralty_key(user)
    async with httpx.AsyncClient(timeout=15) as client:
        r = await client.get(
            f"{ADMIRALTY_BASE}/Stations",
            headers={"Ocp-Apim-Subscription-Key": key}
        )
    return JSONResponse(content=r.json(), status_code=r.status_code)

@router.get("/Stations/{station_id}/TidalEvents")
async def get_tidal_events(station_id: str, request: Request, user=Depends(get_current_user)):
    key = get_admiralty_key(user)
    params = dict(request.query_params)
    async with httpx.AsyncClient(timeout=15) as client:
        r = await client.get(
            f"{ADMIRALTY_BASE}/Stations/{station_id}/TidalEvents",
            headers={"Ocp-Apim-Subscription-Key": key},
            params=params
        )
    return JSONResponse(content=r.json(), status_code=r.status_code)
