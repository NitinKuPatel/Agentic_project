from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel
from typing import List
from app.core.auth import auth_handler
from app.observability.logging import logger

router = APIRouter()

class Token(BaseModel):
    access_token: str
    token_type: str

@router.post("/login", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    """
    Simulated Login for MVP.
    
    Hardcoded Users for testing:
    - User: 'admin', Password: 'password' -> Roles: ['ADMIN', 'MANAGER']
    - User: 'employee', Password: 'password' -> Roles: ['EMPLOYEE']
    """
    logger.info(f"Login attempt for user: {form_data.username}")
    
    # In a real system, you would fetch user from DB and verify hash
    # user = await user_service.get_user(form_data.username)
    # if not user or not auth_handler.verify_password(form_data.password, user.hashed_password):
    
    # Mock Validation
    valid_users = {
        "admin": ["ADMIN", "MANAGER"],
        "employee": ["EMPLOYEE"],
        "manager": ["MANAGER"],
        "guest": ["GUEST"],
        "customer": ["CUSTOMER"]
    }
    
    if form_data.username not in valid_users:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    if form_data.password != "password": # Simple hardcoded password for dev
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    roles = valid_users[form_data.username]
    
    access_token = auth_handler.create_access_token(
        data={"sub": form_data.username, "email": f"{form_data.username}@example.com", "roles": roles}
    )
    
    logger.info(f"Login successful for {form_data.username}")
    return {"access_token": access_token, "token_type": "bearer"}
