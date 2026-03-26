# home-hub

## Project Overview
FastAPI home management system with async PostgreSQL backend and Vue 3 frontend. Integrates CalDAV for calendar sync, authentication via bcrypt, rate limiting, and Claude AI capabilities.

## Tech Stack
- **Backend**: Python 3.11+, FastAPI, uvicorn, SQLAlchemy 2.0 (async), asyncpg
- **Frontend**: Vue 3, TypeScript, Vite
- **Database**: PostgreSQL with Alembic migrations
- **Auth**: bcrypt password hashing
- **Other**: CalDAV, Claude AI integration, slowapi rate limiting

## Architecture
- backend/main.py — FastAPI app entry point, route registration
- backend/routers/ — API endpoints (separate modules per resource)
- backend/services/ — Business logic layer
- backend/models/ — SQLAlchemy ORM models
- backend/schemas/ — Pydantic request/response schemas
- backend/database.py — async PostgreSQL connection
- backend/deps.py — FastAPI dependency injection
- alembic/ — Database migration scripts
- frontend/src/ — Vue 3 components, stores, views
- Data flows: Frontend → FastAPI routes → services → SQLAlchemy → Postgres

## Build & Test Commands
Install Python deps: pip install -e .
Run dev server (FastAPI on :8400): uv run dev
Run migrations: alembic upgrade head
Run backend tests: pytest
Build frontend: cd frontend && npm run build
Serve frontend dev: cd frontend && npm run dev

## Coding Rules
- ALWAYS use full file replacements, never incremental edits
- Security-first: no credentials in code, use .env files (see .env.example)
- All API endpoints require authentication (FastAPI Depends + JWT or session)
- Use SQLAlchemy async patterns (Session, select(), await)
- Run tests after every change
- Vue components use composition API, TypeScript strict mode
- CORS configured in main.py

## Known Pitfalls
- asyncpg connection pool must be closed on shutdown
- Alembic migrations must be applied before schema changes
- CalDAV queries can hang—use timeouts
- Frontend dist/ must be rebuilt before deployment

## Deployment
- Dev: Mac Studio (localhost:8400 backend, :5173 frontend via Vite dev server)
- Prod: Mac Mini via git pull + uvicorn systemd service
- Launchd plist at com.bonifacic.homehub.plist for auto-restart
- Never push directly to main

## References
@/Users/qbot/.openclaw/workspace/LESSONS-LEARNED.md
