# Running SmartTIA on Any Laptop

A 5-minute setup. The **demo needs no GitHub login and no `.env`** — it works out of the box.

## Prerequisites
- **Python 3.9+**  (`python --version`)
- **Node.js 18+ and npm**  (`node --version`)
- **Git**

---

## 1. Backend (FastAPI · port 8000)

From the project root (`4pm-chai-lovers/`):

```bash
cd backend

# create + activate a virtual environment
python -m venv venv
venv\Scripts\activate            # Windows (PowerShell/CMD)
# source venv/bin/activate       # macOS / Linux

# install dependencies
pip install -r requirements.txt

# start the API
python -m uvicorn app.main:app --reload --port 8000
```

Leave this running. Verify in a browser: <http://localhost:8000/api/health> → `{"status":"ok",...}`

> The bundled demo repository **builds itself automatically** the first time you
> open a demo scenario — there is no extra build step to remember.

---

## 2. Frontend (React + Vite · port 5173)

In a **second terminal**, from the project root:

```bash
cd frontend
npm install
npm run dev
```

Open the URL it prints (usually <http://localhost:5173>).

---

## 3. Use it

1. On the login screen, click **“Continue in demo mode →”** (no GitHub needed).
2. Click any demo button: **Safe Refactor · Inject Regression · Hidden Bug · Safety Net**.
3. The dashboard shows the selected tests, time saved, and requirements traceability.

---

## Notes & troubleshooting

| Situation | What to do |
|---|---|
| **“Failed to fetch” / blank dashboard** | The backend isn’t running. Make sure step 1 is up at <http://localhost:8000/api/health>. |
| **Frontend opened on port 5174 instead of 5173** | Fine — the backend accepts any `localhost` port. (Port 5173 was just busy.) |
| **`ModuleNotFoundError: No module named 'app'`** | Run backend commands from inside the `backend/` folder with the venv activated. |
| **GitHub login** (optional, only for private repos) | Create `backend/.env` with `GITHUB_CLIENT_ID` and `GITHUB_CLIENT_SECRET`, and set the OAuth callback URL to `http://localhost:5173/auth/callback`. Not needed for the demo. |
| **Reset the demo to a clean state** | `cd backend` → `python -m app.demo.setup_demo` |

---

### TL;DR (two terminals)

```bash
# Terminal 1 — backend
cd backend && python -m venv venv && venv\Scripts\activate && pip install -r requirements.txt && python -m uvicorn app.main:app --reload

# Terminal 2 — frontend
cd frontend && npm install && npm run dev
```

Then open the frontend URL → **Continue in demo mode** → click a demo button.
