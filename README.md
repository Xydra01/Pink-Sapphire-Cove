# Pink Sapphire Cove — The Gem Cove

Phase 1 (Foundation) focuses on setting up the async Python backend environment and dependencies.

## Backend environment (Git Bash)

From the repo root:

```bash
python -m venv .venv
source .venv/Scripts/activate
python -m pip install --upgrade pip
pip install -r backend/requirements.txt
```

Quick sanity check:

```bash
python -c "import fastapi, uvicorn, beanie, motor, httpx; print('deps ok')"
```
