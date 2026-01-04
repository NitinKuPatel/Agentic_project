from app.infrastructure.db.mongo import db
from app.domain.chat.models import ChatMessage
from app.core.config import settings
from typing import List

class ChatRepository:
    def __init__(self):
        self.collection_name = "chat_history"

    @property
    def collection(self):
        return db.get_db()[self.collection_name]

    async def save_message(self, message: ChatMessage):
        if not settings.ENABLE_CHAT_HISTORY:
            return
        await self.collection.insert_one(message.model_dump(by_alias=True))

    async def get_history_by_user(self, user_id: str, limit: int = 50) -> List[dict]:
        cursor = self.collection.find({"user_id": user_id}).sort("timestamp", -1).limit(limit)
        return await cursor.to_list(length=limit)

    async def get_all_history(self, limit: int = 100) -> List[dict]:
        """
        Admin only: View interactions from ALL users.
        """
        cursor = self.collection.find({}).sort("timestamp", -1).limit(limit)
        return await cursor.to_list(length=limit)

chat_repo = ChatRepository()
