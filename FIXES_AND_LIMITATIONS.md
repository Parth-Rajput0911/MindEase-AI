# MindEase-AI — Fixes and Review Notes

## Fixes applied in this review

1. **Backend starts without an AI key.** The Groq SDK/client is optional at startup. If the SDK or `GROQ_API_KEY` is missing, the rest of the API remains available and the chat endpoint returns a safe fallback response.
2. **AI failures no longer leak provider exceptions.** The chat endpoint does not return raw exception details to users.
3. **CORS is restricted to configured frontend origins.** Configure `CORS_ORIGINS` as a comma-separated list. The development default allows localhost Vite origins instead of every origin.
4. **Debug mode defaults to off.** Set `DEBUG=True` explicitly for local debugging.
5. **Added the missing `POST /api/v1/users` endpoint.** It validates the user payload, rejects duplicate email/username with HTTP 409, and returns the created profile. This fixed the failing API test.
6. **Added AI/CORS configuration notes to `.env.example`.** AI remains optional for the software prototype.

## Validation performed

- Backend test suite: **27 passed**.
- Tests use an isolated SQLite database.

## Important remaining production work

- The user endpoints are prototype endpoints, not a complete authentication system. Add authentication/authorization before exposing user data outside a local demo.
- Password handling in the existing repository should be reviewed and changed to a vetted password-hashing implementation before real accounts are accepted.
- The notification delivery confirmation route currently trusts a client-supplied confirmation payload. Do not expose it publicly or treat it as proof of delivery until it is protected by authenticated provider webhooks/signature verification.
- The project is not a medical diagnostic device. Sensor thresholds and generated values are illustrative and require validation before any real-world health use.
- Real SMS/email/push delivery, actual BLE hardware input, a production GenAI service, and a clinically validated detector are not implemented by this patch.

## Run the backend

From the repository root:

```bash
pip install -r Backend/requirements.txt
cp Backend/.env.example Backend/.env
uvicorn Backend.main:app --reload --port 8000
```

Open `http://localhost:8000/docs` for interactive API documentation.

Run tests:

```bash
pytest -v Backend/tests
```
