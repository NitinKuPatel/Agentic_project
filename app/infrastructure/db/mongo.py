from motor.motor_asyncio import AsyncIOMotorClient
from app.core.config import settings

from app.observability.logging import logger

class MongoDB:
    client: AsyncIOMotorClient = None
    db_name: str = settings.MONGODB_DB_NAME

    def connect(self):
        try:
            self.client = AsyncIOMotorClient(settings.MONGODB_URI)
            # Ping implementation to verify connection
            # self.client.admin.command('ping') 
            logger.info("Connected to MongoDB", extra={"uri": settings.MONGODB_URI})
        except Exception as e:
            logger.critical("Failed to connect to MongoDB", exc_info=True)
            raise

    def close(self):
        if self.client:
            self.client.close()
            logger.info("MongoDB connection closed")

    def get_db(self):
        return self.client[self.db_name]

db = MongoDB()

# Dependency for FastAPI
async def get_database():
    return db.get_db()
