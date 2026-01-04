from app.infrastructure.db.mongo import db

if __name__ == "__main__":
    db.connect()
    print("Dropping database...")
    db.client.drop_database("agentic_ai_kb")
    print("Database dropped.")
    
    # Also clear FAISS index file
    import os
    if os.path.exists("./data/vector/index.faiss"):
        os.remove("./data/vector/index.faiss")
        print("FAISS index file deleted.")
