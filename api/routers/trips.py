from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel
from typing import Optional
from database import get_db, log_action
from deps import get_current_user

router = APIRouter()

class TripCreate(BaseModel):
    name: str
    gpx_data: str
    point_count: Optional[int] = 0
    distance_nm: Optional[float] = 0
    duration_seconds: Optional[int] = 0
    started_at: Optional[str] = None

@router.get("/trips")
def list_trips(user=Depends(get_current_user)):
    with get_db() as conn:
        rows = conn.execute(
            """SELECT id, name, point_count, distance_nm, duration_seconds,
                      started_at, created_at
               FROM trips WHERE user_id=? ORDER BY created_at DESC""",
            (user["id"],)
        ).fetchall()
    return [dict(r) for r in rows]

@router.post("/trips")
def save_trip(body: TripCreate, user=Depends(get_current_user)):
    with get_db() as conn:
        cur = conn.execute(
            """INSERT INTO trips
               (user_id, name, gpx_data, point_count, distance_nm, duration_seconds, started_at)
               VALUES (?,?,?,?,?,?,?)""",
            (user["id"], body.name, body.gpx_data, body.point_count,
             body.distance_nm, body.duration_seconds, body.started_at)
        )
        conn.commit()
        trip_id = cur.lastrowid
    log_action(user["id"], "trip_upload", f'{{"name":"{body.name}","points":{body.point_count}}}')
    return {"id": trip_id, "name": body.name}

@router.get("/trips/{trip_id}/download")
def download_trip(trip_id: int, user=Depends(get_current_user)):
    with get_db() as conn:
        row = conn.execute(
            "SELECT name, gpx_data FROM trips WHERE id=? AND user_id=?",
            (trip_id, user["id"])
        ).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Trip not found")
    filename = row["name"].replace(" ", "_") + ".gpx"
    return Response(
        content=row["gpx_data"],
        media_type="application/gpx+xml",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )

@router.delete("/trips/{trip_id}")
def delete_trip(trip_id: int, user=Depends(get_current_user)):
    with get_db() as conn:
        conn.execute(
            "DELETE FROM trips WHERE id=? AND user_id=?",
            (trip_id, user["id"])
        )
        conn.commit()
    return {"ok": True}
