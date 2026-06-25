# Setup & Deployment Guide

## Prerequisites

- Python 3.x
- Node.js 18+ and npm
- Git

## Backend Setup

### 1. Clone and Configure

```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Environment Variables

Create `backend/.env`:

```
GITHUB_CLIENT_ID=your_github_oauth_client_id
GITHUB_CLIENT_SECRET=your_github_oauth_client_secret
```

**To get GitHub OAuth credentials:**
1. Go to GitHub Settings → Developer Settings → OAuth Apps → New OAuth App
2. Set `Authorization callback URL` to `http://localhost:5173/auth/callback`
3. Copy `Client ID` and `Client Secret`

### 3. Build the Demo Repository (First Run)

```bash
cd backend
python -m app.demo.setup_demo
```

This creates the `.demo_repo/` directory with all 4 scenario branches. Run this anytime you want to reset the demo.

### 4. Start the Backend Server

```bash
cd backend
uvicorn app.main:app --reload --port 8000
```

The API will be available at `http://localhost:8000`.

### 5. Verify

```bash
curl http://localhost:8000/api/health
# {"status":"ok","service":"SmartTIA Engine"}
```

## Frontend Setup

### 1. Install Dependencies

```bash
cd frontend
npm install
```

### 2. Environment Variables (Optional)

Create `frontend/.env` if you need a custom API base URL:

```
VITE_API_BASE=http://localhost:8000
VITE_GITHUB_CLIENT_ID=your_github_oauth_client_id
```

- `VITE_API_BASE`: Backend URL (defaults to `http://localhost:8000`)
- `VITE_GITHUB_CLIENT_ID`: Must match the backend's `GITHUB_CLIENT_ID`

### 3. Start the Dev Server

```bash
cd frontend
npm run dev
```

The dashboard will be available at `http://localhost:5173`.

## Running the Full Stack

### Option A: Two Terminals

```bash
# Terminal 1
cd backend && source venv/bin/activate && uvicorn app.main:app --reload

# Terminal 2
cd frontend && npm run dev
```

### Option B: Single Terminal (background)

```bash
cd backend && source venv/bin/activate && uvicorn app.main:app --reload &
cd frontend && npm run dev
```

## Demo Day Quick Start

```bash
# 1. Reset demo (clean build)
cd backend && python -m app.demo.setup_demo

# 2. Start backend
uvicorn app.main:app --reload &

# 3. Start frontend
cd ../frontend && npm run dev

# 4. Open http://localhost:5173
# 5. Click "Continue in demo mode"
# 6. Click any demo button (safe / regression / transitive / safety-net)
```

## Configuration Reference

### Backend Configuration

| Setting | File | Default | Description |
|---------|------|---------|-------------|
| `GITHUB_CLIENT_ID` | `backend/.env` | — | GitHub OAuth App client ID |
| `GITHUB_CLIENT_SECRET` | `backend/.env` | — | GitHub OAuth App secret |
| Server port | CLI argument | `8000` | `uvicorn app.main:app --port XXXX` |
| CORS origins | `backend/app/main.py` | `http://localhost:5173` | Frontend dev server URL |

### Frontend Configuration

| Setting | Variable | Default | Description |
|---------|----------|---------|-------------|
| API base URL | `VITE_API_BASE` | `http://localhost:8000` | Backend server URL |
| GitHub Client ID | `VITE_GITHUB_CLIENT_ID` | `YOUR_CLIENT_ID` | Must match backend OAuth app |

### Project Configuration Files

| File | Purpose |
|------|---------|
| `backend/requirements.txt` | Python dependencies |
| `frontend/package.json` | Node.js dependencies and scripts |
| `frontend/vite.config.js` | Vite build configuration |
| `frontend/.oxlintrc.json` | Linter configuration |

## Troubleshooting

### "ModuleNotFoundError: No module named 'app'"

Run commands from the `backend/` directory with the virtual environment activated:

```bash
cd backend
source venv/bin/activate
python -m app.demo.setup_demo
```

### "CORS error" in browser

Ensure the backend is running on port 8000 and the frontend on port 5173. CORS is configured to allow `http://localhost:5173`.

### "Failed to clone repository"

- For private repos: ensure GitHub OAuth is set up and the user has authorized the app
- For public repos: no authentication needed
- Check network connectivity to GitHub

### "No tests selected" with C++/non-Python repo

- The system will fall back to AST static mapping
- Ensure test files are under the configured `tests_dir`
- Check that test file extensions are in the supported list (`.cpp`, `.c`, `.h`, `.hpp`, etc.)
- Add a `test_timings.json` for time-saved metrics

### "Coverage map is empty"

- Python-only feature: requires `pytest-cov` and `coverage.py`
- Ensure the repo has Python test files with `pytest` markers
- For non-Python repos, this is expected behavior — the system falls through to AST mapping

### Coverage Cache Issues

Delete the cache directory and retry:

```bash
rm -rf backend/.tia_cache
```

## Production Deployment Considerations

### Backend

- Use a production ASGI server (e.g., `uvicorn --workers 4` or `gunicorn -k uvicorn.workers.UvicornWorker`)
- Set up proper secret management for GitHub OAuth credentials
- Configure CORS for your production frontend domain
- Consider rate limiting for the analysis endpoints
- Set up monitoring for temp directory cleanup (analysis creates temp repos)

### Frontend

- Build for production: `npm run build` → outputs to `frontend/dist/`
- Serve via Nginx, Cloudflare Pages, Vercel, or similar
- Set `VITE_API_BASE` to your production backend URL
- Enable HTTPS for OAuth redirect security

### Security Notes

- GitHub tokens are stored in `localStorage` (client-side only)
- Tokens are passed in request bodies (not headers) to avoid CORS preflight issues
- Temp directories are cleaned up after each analysis in `finally` blocks
- Cache files are limited to coverage maps (no sensitive data)
