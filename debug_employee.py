import asyncio
from app.infrastructure.db.mongo import db

async def inspect():
    db.connect()
    print("\n--- CHUNKS FOR EMPLOYEE DOC ---")
    async for chunk in db.get_db()["chunks"].find({"visibility": "EMPLOYEE"}):
        print(f"ID: {chunk['_id']}, Vis: {chunk.get('visibility')}, Text: {chunk.get('text')}")
        
    print("\n--- ALL CHUNKS ---")
    async for chunk in db.get_db()["chunks"].find():
         print(f"ID: {chunk['_id']}, Vis: {chunk.get('visibility')}, Text: {chunk.get('text')[:30]}...")

if __name__ == "__main__":
    asyncio.run(inspect())
