# STRYDE — guide for Claude Code

STRYDE is a running app where public routes become titles. A runner publishes a route and is its first
champion; others run the same course faster to take the title; leagues and training plans bring them back.
Read `docs/architecture.md` before changing anything structural.

## Repo layout

```
backend/            Django + GeoDjango API, Celery jobs
  stryde_core/      Pure-Python domain logic. NO Django imports. Validator, route builder, importers.
  apps/             Django apps: accounts, routes, activities, leagues, training, integrations
  config/           settings, urls, celery
  tests/            pytest (core tests need no DB; api tests need PostGIS)
mobile/             Expo (React Native, TypeScript, Expo Router)
  src/app/          Expo Router screens (tabs: Home, Routes, Run, League, Train; route/[slug], run/[activityId], devices)
  src/recorder/     Run recording: engine (native or expo-location), SQLite buffer, upload with retry
  src/health/       Apple Health + Health Connect sync (watch runs)
  modules/stryde-location/   Native GPS recorder (Swift + Kotlin, Expo Modules API)
docs/               Architecture, watch integrations, build order, product walkthrough
```

## Non-negotiable rules

1. **The server decides if an attempt is valid.** The phone only records and uploads points. Never trust a
   time, distance or "valid" flag sent by a client.
2. **Every activity source becomes the same `Track`** (`stryde_core/track.py`) before validation. Phone GPS,
   Apple Health, Health Connect, Garmin, COROS, Polar, Suunto and uploaded FIT/GPX/TCX files all go
   through an importer to a `Track`. Do not add source-specific logic to the validator.
3. **Strava data is never shown to other users** (Strava API terms). Strava is export/share only.
4. **No pay-to-win.** Premium never changes points, ranks, attempts or titles.
5. **Privacy:** never expose a user's raw track near their privacy zones; never return other users'
   raw GPS points from the API, only route geometry and results.
6. `stryde_core` must stay free of Django so it can be tested fast and reused (e.g. in a worker).
7. Any change to `stryde_core/validator.py` or `filtering.py` must keep `tests/core` green and should add a
   fixture for the case it handles.

## Commands

```bash
# backend (from backend/)
docker compose up -d db redis          # PostGIS + Redis
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
celery -A config worker -l info
pytest tests/core                      # fast, no database
pytest                                 # everything (needs PostGIS)

# mobile (from mobile/)
npm install
npx expo install <pkg>                 # always use this to add packages (SDK-compatible versions)
npx expo prebuild                      # generates ios/ and android/ (native module needs this)
npx expo run:ios --device              # development build on a real iPhone
npx tsc --noEmit                       # typecheck
```

## Conventions

- Python 3.12+, type hints, `ruff` formatting. Times are timezone-aware UTC everywhere.
- Distances in meters, durations in seconds (float), coordinates as (lat, lon) in WGS84 in Python
  and `{latitude, longitude}` in TypeScript.
- API is DRF under `/api/`, JWT auth. Keep responses small: lists paginate, tracks are simplified.
- Mobile: functional components, TanStack Query for server state, no global store unless needed.
  Theme tokens live in `mobile/src/theme.ts` (match the mockups in docs).
