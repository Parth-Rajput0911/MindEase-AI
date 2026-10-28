# MindEase AI — Redesigned Frontend

A responsive browser-based frontend for the MindEase AI wellness-support prototype. It runs without hardware and remains usable when the backend is offline.

## Run the frontend

The frontend is plain HTML, CSS and JavaScript, so no Node build step is required.

1. Open a terminal in the project root.
2. Start the backend (optional, for the health check and AI chat integration):

   ```bash
   pip install -r Backend/requirements.txt
   uvicorn Backend.main:app --reload --port 8000
   ```

3. Open `frontend/index.html` using VS Code Live Server, or another static HTTP server. Live Server commonly uses `http://127.0.0.1:5500`.
4. Open **Settings & safety** and confirm the backend URL is `http://localhost:8000`.
5. Select **Save & test connection** to check `/health`.

You can also open `index.html` directly in a browser. Some browsers restrict API requests from `file://`; use Live Server if the backend connection does not work.

## Included features

- Responsive dashboard with synthetic heart rate, HRV, EDA and movement readings
- Live-updating chart drawn with Canvas
- Normal, elevated physiological pattern, and movement-context scenarios
- Guided breathing and grounding exercise
- Mood check-ins and local episode history
- JSON export and clear-history controls
- Trusted-contact placeholders and demo notification preferences
- Reflection assistant that calls `POST /api/v1/chat` when the backend is available and falls back to local supportive text when offline
- Backend health status via `GET /health`
- Settings for the backend URL
- Local browser persistence for demo history, contacts and preferences

## Current limitations

- Sensor readings are synthetic; no Bluetooth or physical wearable is connected.
- The UI does not yet persist sensor readings, episodes, contacts or interventions through the backend database. Demo activity is stored in browser local storage.
- AI chat uses the backend endpoint if reachable; otherwise it uses preset local responses.
- Contact and help workflows are simulations. No SMS, email, phone call or emergency notification is sent.
- This is a wellness-support prototype, not a diagnostic or emergency-monitoring device.

## Later integration

1. Create or select an authenticated user profile.
2. Send validated sensor readings to `POST /api/v1/sensors/readings` and fetch readings using `GET /api/v1/sensors/readings/{user_id}`.
3. Persist episodes/interventions using the corresponding backend endpoints.
4. Add a sensor adapter for BLE hardware without coupling hardware details to the UI.
5. Implement authenticated, consent-based notification delivery and verify provider callbacks.
