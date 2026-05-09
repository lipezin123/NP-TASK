from fastapi import APIRouter, Depends, HTTPException, Request, status

from app.core.database import get_db
from app.core.rate_limiter import enforce_rate_limit
from app.core.security import create_access_token
from app.schemas.user import LoginRequest, TokenResponse, UserCreate, UserResponse
from app.services import user_service

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(enforce_rate_limit)],
)
async def register(payload: UserCreate, request: Request):
    ip = request.client.host
    db = get_db()

    if await user_service.ip_already_registered(db, ip):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Este IP já possui uma conta registrada.",
        )

    if await user_service.get_by_username(db, payload.username):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username já está em uso.",
        )
    if await user_service.get_by_email(db, payload.email):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="E-mail já está em uso.",
        )

    user = await user_service.create(db, payload)
    await user_service.register_ip(db, ip)

    return UserResponse(
        id=user.id,
        username=user.username,
        email=user.email,
        created_at=user.created_at,
    )


@router.post(
    "/login",
    response_model=TokenResponse,
    dependencies=[Depends(enforce_rate_limit)],
)
async def login(payload: LoginRequest):
    db = get_db()
    user = await user_service.authenticate(db, payload.username, payload.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciais inválidas.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token = create_access_token(subject=user.username)
    return TokenResponse(access_token=token)
