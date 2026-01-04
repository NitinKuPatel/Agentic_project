from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from app.orchestrator.agent import agent_orchestrator
from app.api.dependencies import get_current_user, UserPrincipal

router = APIRouter()

class QueryRequest(BaseModel):
    query: str
    kb_snapshot_id: Optional[str] = None

class QueryResponse(BaseModel):
    answer: str
    sources: List[str]
    confidence: str
    backend_used: str

@router.post("/query", response_model=QueryResponse)
async def submit_query(
    request: QueryRequest,
    current_user: UserPrincipal = Depends(get_current_user)
):
    """
    Submit a query to the Agentic Knowledge Base.
    """
    try:
        response = await agent_orchestrator.process_query(
            query=request.query,
            user_roles=current_user.roles,
            user_id=current_user.user_id,
            kb_snapshot_id=request.kb_snapshot_id
        )
        return QueryResponse(**response)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
