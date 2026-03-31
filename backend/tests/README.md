# Backend tests

These tests cover the Phase 1 backend: settings loading, the Dragon Cave wrapper (mocked), and the `/api/dragons/*` routes.

## Requirements

- Python venv activated
- `MONGODB_URI` set (Atlas recommended)
- Use a dedicated test DB name via `MONGODB_DB` (to keep cleanup safe)

## Run (Git Bash)

From repo root:

```bash
source .venv/Scripts/activate
pip install -r backend/requirements.txt

export MONGODB_DB=pink_sapphire_cove_test
pytest -q
```

## Run (PowerShell)

From repo root:

```powershell
.\.venv\Scripts\Activate.ps1
pip install -r backend\requirements.txt

$env:MONGODB_DB = "pink_sapphire_cove_test"
pytest -q
```

## Notes

- Tests **delete all documents** from the `dragons` and `user_sessions` collections in the configured test database.
- Dragon Cave API calls are mocked; you do not need `DC_API_KEY` for the route tests.

