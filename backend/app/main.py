from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import analyze, auth

app = FastAPI(title="SmartTIA Engine API")

# Configure CORS for the Vite frontend. Vite auto-increments the port
# (5173 -> 5174 -> ...) when one is taken, so allow any localhost port
# instead of pinning a single one (avoids "Failed to fetch" CORS errors).
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"http://(localhost|127\.0\.0\.1):\d+",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
async def health():
    return {"status": "ok", "service": "SmartTIA Engine"}


# Include Routers
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(analyze.router, prefix="/api/analyze", tags=["Analysis"])
