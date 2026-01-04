from fastapi import Depends, HTTPException, status, Header
from fastapi.security import OAuth2PasswordBearer
from typing import Optional, List
from app.core.auth import auth_handler
from app.observability.logging import logger

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"/api/v1/auth/login", auto_error=False)

class UserPrincipal:
    def __init__(self, user_id: str, email: str, roles: List[str]):
        self.user_id = user_id
        self.email = email
        self.roles = roles

async def get_current_user(token: Optional[str] = Depends(oauth2_scheme)) -> UserPrincipal:
    """
    Validates JWT if present. If NOT present, returns a GUEST user.
    """
    # 1. Anonymous / Guest Handling
    if not token:
        # Generate a temporary guest session ID (or just use 'anonymous_guest')
        # In a real app, you might want to fingerprint the IP or generate a random session ID
        return UserPrincipal(
            user_id="anonymous_guest", 
            email="guest@public.web", 
            roles=["GUEST"]
        )

    # 2. Authenticated User Handling
    payload = auth_handler.decode_token(token)
    if not payload:
        logger.warning("Invalid token provided")
        # If token was provided but is invalid, we REJECT (Security choice).
        # Alternatively, we could downgrade to Guest, but that hides auth errors.
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user_id: str = payload.get("sub")
    email: str = payload.get("email")
    roles: List[str] = payload.get("roles", [])
    
    if user_id is None:
        raise HTTPException(status_code=401, detail="Invalid token payload")
        
    return UserPrincipal(user_id=user_id, email=email, roles=roles)

class RoleChecker:
    def __init__(self, allowed_roles: List[str]):
        self.allowed_roles = allowed_roles

    def __call__(self, user: UserPrincipal = Depends(get_current_user)):
        if not auth_handler.check_permissions(user.roles, self.allowed_roles):
            logger.warning(f"Access denied for user {user.email} with roles {user.roles}. Required: {self.allowed_roles}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, 
                detail="Not authorized to perform this action"
            )
        return user
