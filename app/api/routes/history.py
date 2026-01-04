from fastapi import APIRouter, Depends, Query, HTTPException
from typing import List, Optional
from app.api.dependencies import get_current_user, UserPrincipal
from app.infrastructure.db.chat_repo import chat_repo
from app.domain.chat.models import ChatMessage

router = APIRouter()

@router.get("/history", response_model=List[ChatMessage])
async def get_chat_history(
    current_user: UserPrincipal = Depends(get_current_user),
    limit: int = Query(50, ge=1, le=100)
):
    """
    Retrieve chat history.
    - **Admins**: Can see ALL history (from everyone).
    - **Others**: Can see ONLY their own history.
    """
    if "ADMIN" in current_user.roles:
        # Admin View: See everything
        history = await chat_repo.get_all_history(limit=limit)
    else:
        # User View: See own
        history = await chat_repo.get_history_by_user(current_user.user_id, limit=limit)
        
    return history
