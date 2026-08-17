from fastapi import APIRouter

router = APIRouter(tags=["login"])

@router.get("/health-check")
async def health_check() -> None:
    """
    Check if the booking service is healthy.
    """
    return None
