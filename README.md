# STRYDE

Running routes become titles. Publish a route, hold the record, defend it, train to win it back.

```
backend/   Django + PostGIS API, attempt validator, watch importers (36 tests)
mobile/    Expo app (iPhone + Android) with a native GPS recorder and Apple Health / Health Connect sync
docs/      Architecture, watch integrations, build order
```

Start with `CLAUDE.md` (rules for Claude Code) and `docs/build-order.md` (what's done, what's next).

## Run the backend

```bash
cd backend
cp .env.example .env
docker compose up -d db redis
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser          # for the route review queue at /admin
python manage.py seed_demo                # Zilker Loop + runners ana / luis / sofia (password stryde-demo-123)
python manage.py runserver 0.0.0.0:8000
pytest                                    # 36 tests: validator, cheats, watch formats, full API flows
```

## Run the app on your iPhone

The app needs a **development build** (Expo Go can't record GPS with the screen locked or load the native recorder).

1. Apple Developer account ($99/yr). Install Xcode on a Mac, or use EAS cloud builds (no Mac needed).
2. `cd mobile && cp .env.example .env` and set:
   - `EXPO_PUBLIC_API_URL` to your laptop's LAN IP (`http://192.168.x.x:8000`) or a deployed API
   - `EXPO_PUBLIC_MAPBOX_TOKEN` (free Mapbox account)
3. `npm install`
4. Build and install:
   - with a Mac: `npx expo run:ios --device`
   - without: `npx eas-cli build --profile development --platform ios`, then scan the QR to install
5. `npx expo start` and open the app. Sign in as `ana` after running `seed_demo`.
6. First real run: start a free run, lock the phone, run a loop, finish, publish it as a route, approve it in `/admin`.

## Watches

| Watch | How it reaches STRYDE |
| --- | --- |
| Apple Watch | Apple Health sync in the app (Watches screen) |
| Garmin, COROS, Polar, Suunto, Wahoo | Turn on the brand app's Apple Health / Health Connect sync, **or** upload the .FIT/.GPX/.TCX, **or** connect directly once each developer program approves STRYDE |
| Wear OS, Galaxy Watch, Pixel Watch | Health Connect sync in the app |

Details and approval steps: `docs/watch-integrations.md`.

## Status

Built and tested here: backend, validator, importers, Garmin/Polar adapters, API flows, app screens
(typechecked and bundled for iOS and Android), native project generation.

Not yet tested on real hardware: the native Swift/Kotlin GPS recorder, Apple Health and Health Connect reads,
Mapbox rendering, push notifications. Those need a physical phone — see Milestone 1 in `docs/build-order.md`.
