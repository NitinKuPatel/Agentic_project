from app.infrastructure.db.mongo import db
import asyncio

async def inspect():
    db.connect()
    
    print("\n--- CHUNKS IN MONGO ---")
    async for chunk in db.get_db()["chunks"].find():
        print(f"ID: {chunk['_id']}, EmbedID: {chunk.get('embedding_id')}, Vis: {chunk.get('visibility')}, Text: {chunk.get('text')[:30]}...")

if __name__ == "__main__":
    asyncio.run(inspect())
