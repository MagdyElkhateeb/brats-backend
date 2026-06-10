from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.routes import auth, cases, patients, results, uploads
from app.core.config import settings

app = FastAPI(
    title="BraTS Brain Tumor Segmentation Backend",
    description="Integration backend for a React Native BraTS mobile app and an external AI model endpoint.",
    version="0.1.0",
)

# CORS configuration for frontend integration during development.
# We use Bearer tokens, not cookies, so allow_credentials=False works safely with allow_origins=["*"].
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

Path(settings.STORAGE_ROOT).mkdir(parents=True, exist_ok=True)
app.mount("/storage", StaticFiles(directory=settings.STORAGE_ROOT), name="storage")

app.include_router(auth.router)
app.include_router(patients.router)
app.include_router(cases.router)
app.include_router(uploads.router)
app.include_router(results.router)


@app.get("/health", tags=["health"])
def health_check() -> dict[str, str]:
    return {"status": "ok"}