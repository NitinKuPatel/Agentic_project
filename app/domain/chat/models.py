from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
import uuid

class ChatMessage(BaseModel):
    id: str = Field(default_factory=lambda: uuid.uuid4().hex, alias="_id")
    user_id: str
    user_role: List[str]
    query: str
    answer: str
    sources: List[str]
    confidence: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
