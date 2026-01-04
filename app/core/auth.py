from datetime import datetime, timedelta
from typing import Optional, List, Union, Any
from jose import jwt
from passlib.context import CryptContext
from app.core.config import settings

# Password hashing configuration
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

ALGORITHM = "HS256"

class AuthHandler:
    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        return pwd_context.verify(plain_password, hashed_password)

    @staticmethod
    def get_password_hash(password: str) -> str:
        return pwd_context.hash(password)

    @staticmethod
    def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt

    @staticmethod
    def decode_token(token: str) -> dict:
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
            return payload
        except jwt.JWTError:
            return None

    @staticmethod
    def check_permissions(user_roles: List[str], required_roles: List[str]) -> bool:
        """
        Returns True if the user has AT LEAST one of the required roles.
        If required_roles is empty, access is implied to be public/open to auth users.
        """
        if not required_roles:
            return True
        # Check intersection
        return bool(set(user_roles) & set(required_roles))

auth_handler = AuthHandler()
