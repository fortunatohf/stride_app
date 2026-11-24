# STRYDE architecture

## Big picture

```
 iPhone / Android app (Expo)                         Watches & platforms
 ├─ Native GPS recorder (Swift/Kotlin)               ├─ Apple Watch ──► Apple Health ──┐
 ├─ SQLite buffer (points saved first)               ├─ Wear OS, Samsung, Pixel ──► Health Connect ──┤ read by the app
 ├─ Health import (HealthKit / Health Connect) ◄─────┘   (Garmin/COROS/Polar can also sync into these)
 └─ uploads Track JSON ──────────────┐
                                     ▼
                         Django API (DRF, JWT)  ◄── Garmin / COROS / Polar / Suunto webhooks (server-to-server)
                                     │          ◄── FIT / GPX / TCX file upload (any watch)
                                     ▼
                     importers → Track (one format for every source)
                                     ▼
                Celery worker: validate against nearby routes (stryde_core.validator)
                                     ▼
            Attempt saved → title change? → points ledger → push notification (Expo Push)
                                     ▼
                       PostgreSQL + PostGIS   ·   Redis (queue)
```

## Core domain (`backend/stryde_core`)

| Module | Job |
| --- | --- |
| `track.py` | `TrackPoint` / `Track` dataclasses; the single format every source becomes |
| `geo.py` | Haversine, local metric projection, point-to-segment math |
| `filtering.py` | Drops bad GPS: low accuracy, duplicates, out-of-order times, teleports |
| `route_builder.py` | Turns a recorded run into a route: simplify, length check, loop detection, checkpoints, duplicate and privacy checks |
| `validator.py` | Decides if an attempt on a route is valid and how long it took |
| `importers/` | FIT, GPX, TCX, Apple Health payload, Health Connect payload → `Track` |
| `providers/` | Garmin, COROS, Polar, Suunto adapters: webhook parsing + file download → importer |

## How an attempt is validated

1. Clean the track (`filtering.clean`).
2. Find every pass through the **start gate** (25 m). For each:
3. Hit every **checkpoint in order** (30 m), then reach the **finish gate**.
4. Times are interpolated at the closest approach to each gate, so sparse watch data (1 point per
   few seconds) still times fairly.
5. Reject if: distance between gates is under 95% or over 115% of the route; under 90% of points are
   inside the 40 m corridor around the route; sustained speed over 7 m/s (vehicle); a GPS gap over 60 s;
   too many teleport jumps.
6. Keep the fastest valid pass in the activity. Return splits per km.

## Title logic (server, in a DB transaction)

- Lock the route row (`select_for_update`), compare with the champion's time.
- Strictly faster takes the title. A tie keeps the current champion.
- Write a `TitleChange`, award points through the ledger (weekly cap), push-notify the dethroned runner.

## Data model (Django apps)

- `accounts`: User, PrivacyZone, PushToken
- `routes`: Route (LineString, start/finish Points, checkpoints, status), TitleChange
- `activities`: Activity (source, device, simplified geometry, raw points), Attempt
- `leagues`: Season, Division, Membership, PointsLedger
- `training`: TrainingPlan, TrainingSession (comeback plan generator)
- `integrations`: DeviceConnection (encrypted tokens), WebhookEvent

## Why this stack

Expo/React Native for one app on both phones; GPS recording in native Swift/Kotlin for accuracy and
battery; Django + PostGIS because the validator, anti-cheat and leagues are easiest to write and test in
Python, and PostGIS is the best tool for route geometry.
