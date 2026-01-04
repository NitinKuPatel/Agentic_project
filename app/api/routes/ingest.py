from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException
from typing import List
from app.domain.knowledge.service import knowledge_service
from app.api.dependencies import get_current_user, UserPrincipal, RoleChecker
from app.observability.logging import logger

router = APIRouter()

@router.post("/ingest", status_code=201)
async def ingest_document(
    file: UploadFile = File(...),
    visibility: str = Form("INTERNAL"), # Comma separated
    current_user: UserPrincipal = Depends(RoleChecker(["ADMIN", "MANAGER"]))
):
    """
    Upload and ingest a document into the Knowledge Base.
    Requires ADMIN or MANAGER role.
    """
    visibility_list = [v.strip() for v in visibility.split(",")]
    
    try:
        result = await knowledge_service.ingest_document(
            file=file, 
            user_id=current_user.user_id, 
            visibility=visibility_list
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Ingestion failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Ingestion error: {str(e)}")

@router.get("/documents", response_model=List[dict])
async def list_documents(
    visibility: str = None,
    current_user: UserPrincipal = Depends(RoleChecker(["ADMIN", "MANAGER"]))
):
    """
    List documents in the Knowledge Base.
    Optional 'visibility' query param to filter by role (GUEST, CUSTOMER, INTERNAL).
    """
    try:
        docs = await knowledge_service.list_documents(visibility)
        return docs
    except Exception as e:
        logger.error(f"Failed to list docs: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

