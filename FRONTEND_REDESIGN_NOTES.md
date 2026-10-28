# Frontend redesign notes

The frontend was redesigned as a responsive, single-page browser experience while preserving the existing FastAPI backend.

## What changed
- Replaced the previous visual system with a responsive sidebar, top navigation, metric cards, chart panel, state panel, support tools, history, reflections, contacts and safety settings.
- Added a synthetic sensor stream and three demo contexts: normal, elevated physiological pattern, and movement/activity.
- Added an interactive canvas heart-rate chart, chart range control, breathing timer, grounding exercise, mood check-ins and local history.
- Added local JSON export and a clear-history action.
- Added a backend health check (`GET /health`) and optional chat integration (`POST /api/v1/chat`). The app falls back to local supportive responses when the backend is unavailable.
- Added responsive mobile navigation and accessible labels for important controls.
- Made the simulation boundary explicit: no real sensors or emergency notifications are used.

## Data and integration boundaries
The browser stores demo history, contacts and preferences in local storage. The backend is currently used for health status and optional chat only. Sensor/episode database integration is intentionally left for the next implementation phase because it requires a user identity and careful mapping to the existing Pydantic schemas.

## Verification
- JavaScript syntax checked with `node --check`.
- Manual browser QA is still recommended in the target browser, including responsive layouts, Live Server CORS configuration and backend availability.
