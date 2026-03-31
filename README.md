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

## Dev servers (avoid stale reload processes)

On Windows, `uvicorn --reload` can leave multiple old processes bound to ports. If requests start behaving inconsistently, do a hard restart.

Hard kill (dev only):

```bash
powershell -NoProfile -Command "Get-Process python, node -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue"
```

Start backend (repo root):

```bash
./.venv/Scripts/python.exe -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000
```

Start frontend:

```bash
cd frontend
npm run dev -- --host 127.0.0.1 --port 5173
```
