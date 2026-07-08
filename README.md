# eBoat

A self-hosted electric boat dashboard, route planner and navigation tool with multi-user accounts. Runs as two Docker containers (API + nginx) behind your existing reverse proxy.

## Features

### Dashboard (`/`)
- Live GPS position with rotating heading marker (course-up or north-up)
- Follow mode — map centres on vessel, drag to explore freely
- Speed, heading, wind, weather and tidal data panels
- Tap any instrument tile for a full-screen detail view with compass rose, tide times, Beaufort scale etc.
- GPS coordinates overlay, OpenSeaMap nautical chart overlay
- AIS vessel tracking (aisstream.io, toggle on/off)
- Trip recorder — tap REC to log your voyage; saved to your account when stopped

### Route Planner (`/planner.html`)
- Plot, save and load routes stored server-side per user
- Distance, ETA and range calculations based on your battery and motor
- Location search, OpenSeaMap overlay, persistent boat settings

### My Trips (`/trips.html`)
- Browse all your recorded voyages with distance and duration
- Download as GPX, compatible with Google Maps, Strava, OS Maps etc.

### Profile & Settings (`/profile.html`)
- Change your password
- Use server default API keys or configure your own
- Keys are tested before saving — can't save until all pass

### Admin Panel (`/admin.html`)
- Create and delete user accounts (admin only)
- Usage statistics and recent activity log

## Requirements

- Docker + Docker Compose
- A Google Cloud project with **Maps JavaScript API** and **Places API (New)** enabled
- A UKHO Admiralty Developer Portal account subscribed to **UK Tidal API - Discovery** (free)
- An aisstream.io API key (optional — AIS button is hidden if not set)

## Quick Start

```bash
git clone https://github.com/PocketYogurt/eDash---Boat-Dashboard.git
cd eDash---Boat-Dashboard
cp .env.example .env
# Edit .env with your values
docker compose up -d --build
```

Point your reverse proxy at port `8080`. On first boot the admin account is created automatically from your `.env` credentials.

**First thing after logging in:** change the admin password on the Profile page.

## Environment Variables

| Variable | Required | Description |
|---|---|---|
| `GOOGLE_MAPS_API_KEY` | Yes | Google Cloud Console — Maps JS API + Places API (New) |
| `ADMIRALTY_API_KEY` | Yes | [developer.admiralty.co.uk](https://developer.admiralty.co.uk) — UK Tidal API Discovery (free) |
| `AISSTREAM_API_KEY` | No | [aisstream.io](https://aisstream.io) — AIS vessel tracking (free) |
| `ADMIN_USERNAME` | No | Default admin username (default: `admin`) |
| `ADMIN_PASSWORD` | No | Default admin password — **change this** (default: `changeme123`) |

## Deploying Updates

```bash
git pull
docker compose down
docker compose up -d --build
```

> If you see password/bcrypt errors after an update, delete `data/eboat.db` before restarting so the admin account is recreated cleanly.

## Architecture

```
docker compose:
  api  — Python FastAPI  (auth, routes, trips, tides proxy, admin API)
  web  — nginx           (serves static HTML, proxies /api/* to the API)

data/
  eboat.db  — SQLite database (users, sessions, routes, trips, usage log)
```

API keys are served at runtime via `/api/me/config` — never baked into static files. Each user can use the server defaults or configure their own on the Profile page.

## Attribution

Contains ADMIRALTY® tidal data: © Crown Copyright and database right.
AIS data provided by [aisstream.io](https://aisstream.io).
