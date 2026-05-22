from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AuthException, NotFoundException, ValidationException
from app.core.logging import get_logger
from app.core.security import create_access_token, get_password_hash, verify_password
from app.models.models import User
from app.schemas.auth import Token, UserRegister, UserLogin, UserResponse

logger = get_logger(__name__)


class AuthService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def register(self, data: UserRegister) -> User:
        # Check existing username
        result = await self.db.execute(select(User).where(User.username == data.username))
        if result.scalar_one_or_none():
            raise ValidationException("Username already taken")

        # Check existing email
        result = await self.db.execute(select(User).where(User.email == data.email))
        if result.scalar_one_or_none():
            raise ValidationException("Email already registered")

        user = User(
            username=data.username,
            email=data.email,
            hashed_password=get_password_hash(data.password),
            full_name=data.full_name,
        )
        self.db.add(user)
        await self.db.flush()
        await self.db.refresh(user)
        logger.info(f"New user registered: {user.email}")
        return user

    async def login(self, data: UserLogin) -> Token:
        result = await self.db.execute(select(User).where(User.email == data.email))
        user = result.scalar_one_or_none()

        if not user or not verify_password(data.password, user.hashed_password):
            raise AuthException("Incorrect email or password")

        if not user.is_active:
            raise AuthException("Account is deactivated")

        # Update last login
        user.last_login = datetime.now(timezone.utc)
        await self.db.flush()

        token = create_access_token({"sub": str(user.id)})
        logger.info(f"User logged in: {user.email}")
        return Token(access_token=token)

    async def get_user_by_id(self, user_id: int) -> User:
        result = await self.db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if not user:
            raise NotFoundException("User")
        return user
