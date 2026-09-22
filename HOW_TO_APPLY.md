# How to apply this to your SanRaksha repo

This is an overlay, not a replacement — it adds files and changes exactly
3 lines in one existing file.

1. Copy `app/mental_health/` into your repo's `app/` folder (new package).
2. Copy `docs/*.md` into your repo's `docs/` folder (new).
3. Copy `tests/*.py` into your repo's `tests/` folder (new).
4. In your existing `app/main.py`, right after the line `app = FastAPI()`,
   add exactly this (nothing else in the file changes):

   ```python
   from app.mental_health.router import router as mental_health_router
   app.include_router(mental_health_router)
   ```

5. Append the two lines at the bottom of `requirements.txt`
   (`pytest`, `httpx`) — needed for the test suite only, not runtime.

6. Run `pytest tests/ -v` from the repo root. You should see 27 passed
   (verified in this environment; TensorFlow isn't installed here so the
   two regression tests stub it out — they'll run against the real model
   once you run them in your actual environment with TF installed).

Everything else (Android UI, dashboard chart) is a written plan in
`docs/android_integration_plan.md`, not implemented — see that file and
`docs/mental_health_architecture.md` §9 for why, and what's left to do.
