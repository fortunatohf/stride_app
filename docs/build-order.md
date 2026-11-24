# Build order

Each milestone ends with something you can run on a phone. Check items off as they land.

## Milestone 0 — foundation (done)
- [x] Repo, CLAUDE.md, architecture docs
- [x] `stryde_core`: Track, filtering, validator, route builder, importers (FIT/GPX/TCX/HealthKit/Health Connect)
- [x] Provider adapters: Garmin (webhook + FIT download), COROS/Polar/Suunto scaffolds
- [x] Django models, API, Celery tasks, docker-compose (PostGIS + Redis)
- [x] Expo app foundation: theme, navigation, core screens wired to the API, run recorder, native GPS module, health import

## Milestone 1 — record a run on a real iPhone
- [ ] Apple Developer account, `eas build --profile development --platform ios`
- [ ] Field test the native recorder: locked screen, 60 min, compare distance with a watch
- [ ] Upload a run, see it in Activities

## Milestone 2 — create and conquer (flows 1 and 2)
- [ ] Publish a route from a run; admin approves in Django admin
- [ ] Map screen lists nearby routes; route card with leaderboard
- [ ] Attempt mode (checkpoints + live gap); server validates; title changes

## Milestone 3 — defend and train (flows 3 and 4)
- [ ] Push notification on title lost (Expo Push)
- [ ] Rivalry screen with split comparison
- [ ] Comeback plan generated and shown in Train

## Milestone 4 — watches
- [ ] Apple Health import on device (Apple Watch run → attempt)
- [ ] Health Connect import on Android
- [ ] File upload screen (FIT/GPX/TCX)
- [ ] Garmin: apply, add keys, build the OAuth callback (code → tokens into DeviceConnection), test webhook on staging

## Milestone 5 — pilot readiness
- [ ] Leagues: season job, divisions, points cap
- [ ] Privacy zones UI, report a route/attempt, admin review queue
- [ ] Sentry, TestFlight, Google Play closed test (12 testers × 14 days)
