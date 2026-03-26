import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from backend.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    yield
    # Shutdown
    from backend.database import engine
    await engine.dispose()


app = FastAPI(
    title="Home Hub",
    description="Bonifacic Home Management API",
    version="2.0.0",
    lifespan=lifespan,
    docs_url="/api/docs",
    openapi_url="/api/openapi.json",
)

# CORS — allow Vite dev server in development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
from backend.routers import auth, health, chores, dashboard, recipes, meals, grocery, outdoor, calendar, pantry, home, chat

app.include_router(auth.router)
app.include_router(health.router)
app.include_router(chores.router)
app.include_router(dashboard.router)
app.include_router(recipes.router)
app.include_router(meals.router)
app.include_router(grocery.router)
app.include_router(outdoor.router)
app.include_router(calendar.router)
app.include_router(pantry.router)
app.include_router(home.router)
app.include_router(chat.router)

# Serve frontend build in production
frontend_dist = Path(__file__).parent.parent / "frontend" / "dist"
if frontend_dist.exists():
    # Serve static assets (JS, CSS, images)
    app.mount("/assets", StaticFiles(directory=frontend_dist / "assets"), name="static-assets")

    # Catch-all: serve index.html for SPA routing
    from fastapi.responses import FileResponse

    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        # Don't intercept /api routes (they're already registered above)
        file_path = frontend_dist / full_path
        if file_path.exists() and file_path.is_file():
            return FileResponse(file_path)
        return FileResponse(frontend_dist / "index.html")
