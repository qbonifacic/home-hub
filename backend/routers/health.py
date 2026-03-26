from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get("/api/health")
async def health():
    return {"status": "ok", "app": "home-hub", "version": "2.0.0"}
