from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, Request, status

from app.core.config import settings
from app.core.database import get_db


async def enforce_rate_limit(request: Request) -> None:
    ip = request.client.host
    db = get_db()
    now = datetime.now(timezone.utc)
    window_start = now - timedelta(seconds=settings.RATE_LIMIT_WINDOW_SECONDS)

    count = await db.rate_limits.count_documents(
        {"ip": ip, "timestamp": {"$gte": window_start}}
    )

    if count >= settings.RATE_LIMIT_REQUESTS:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Muitas requisições. Tente novamente mais tarde.",
            headers={"Retry-After": str(settings.RATE_LIMIT_WINDOW_SECONDS)},
        )

    await db.rate_limits.insert_one(
        {
            "ip": ip,
            "timestamp": now,
            "expires_at": now + timedelta(seconds=settings.RATE_LIMIT_WINDOW_SECONDS),
        }
    )
