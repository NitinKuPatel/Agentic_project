from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

class Document(BaseModel):
    id: str = Field(..., alias="_id")
    title: str
    status: str  # ACTIVE, ARCHIVED, DRAFT
    visibility: List[str]
    current_version: int
    created_at: datetime

class DocumentVersion(BaseModel):
    id: str = Field(..., alias="_id")
    doc_id: str
    version: int
    content_hash: str
    approved_by: Optional[str]
    approved_at: Optional[datetime]
    activated_at: Optional[datetime]
    chunk_ids: List[str]
    snapshot_ids: List[str]

class Chunk(BaseModel):
    id: str = Field(..., alias="_id")
    doc_id: str
    version: int
    text: str
    visibility: List[str]
    embedding_id: str
