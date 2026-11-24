# Connecting watches

Goal: a run recorded on **any** watch can count as a STRYDE attempt. Every source ends up as the same
`Track` and goes through the same validator, so a Garmin run and a phone run are judged identically.

## The four doors

| Door | Covers | How | Status in this repo |
| --- | --- | --- | --- |
| 1. Apple Health (HealthKit) | Apple Watch, plus Garmin, COROS, Polar, Suunto, Wahoo, Amazfit when the user turns on their app's Apple Health sync | The STRYDE iPhone app asks permission, reads running workouts and their GPS route, uploads to `/api/activities/health/` | Mobile service + backend importer built |
| 2. Health Connect (Android) | Wear OS (Pixel, Samsung Galaxy Watch), plus brands that sync into Health Connect | Same as above with the Android permissions for exercise and exercise routes | Mobile service + backend importer built |
| 3. Direct cloud APIs | Garmin (Activity API), COROS, Polar (AccessLink), Suunto | User connects their account once (OAuth). The brand calls our webhook after each workout; we download the FIT file | Garmin adapter + webhook built; COROS/Polar/Suunto adapters scaffolded. Each needs developer approval and keys |
| 4. File upload | Every watch that can export a file | User uploads a .FIT, .GPX or .TCX from the brand's app or website | Built (`/api/activities/import-file/`) |

Doors 1, 2 and 4 work at launch with no partner approval. Door 3 removes the need for the phone (the run
syncs straight from the brand's cloud) and is added brand by brand as approvals come in.

## Applying for direct access

- **Garmin Connect Developer Program**: apply with the public website and privacy policy. New apps start
  on a Starter tier that may limit user connections until Garmin reviews them.
- **Polar AccessLink**: open developer registration; supports webhooks and FIT/GPX/TCX downloads.
- **COROS** and **Suunto**: partner application required.
- **Strava**: NOT a data source (its terms forbid showing a user's Strava data to other users). Use only
  to let runners share STRYDE results.

## Option: a wearables aggregator

Services such as Terra or ROOK expose many brands through one API for a monthly fee. They would plug in
as one more provider in `stryde_core/providers/`. Check each brand's terms, because some brands do not
allow their data to pass through intermediaries.

## Anti-cheat for imported runs

- Imported runs go through the same checks as phone runs (gates, checkpoints, corridor, speed, gaps).
- An activity is processed once per (source, external_id); re-imports are ignored.
- Manually created or edited activities (flagged in FIT/HealthKit metadata) are not eligible for titles.
- Watch runs are only posted to leaderboards after the runner agrees (one-time setting).
