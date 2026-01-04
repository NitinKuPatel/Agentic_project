import uuid
from datetime import datetime
from typing import List, BinaryIO
from fastapi import UploadFile

from app.core.config import settings
from app.domain.knowledge.models import Document, DocumentVersion, Chunk
from app.domain.retrieval.embedding_service import get_embedding_service
from app.infrastructure.db.mongo import db
from app.infrastructure.vector.faiss_service import faiss_service
from app.infrastructure.storage.blob_storage import get_storage_client
from app.observability.logging import logger

class KnowledgeService:
    def __init__(self):
        self.embedding_service = get_embedding_service()
        self.storage_client = get_storage_client()
    
    @property
    def collection_docs(self):
        return db.get_db()["documents"]

    @property
    def collection_versions(self):
        return db.get_db()["document_versions"]

    @property
    def collection_chunks(self):
        return db.get_db()["chunks"]

    async def ingest_document(self, file: UploadFile, user_id: str, visibility: List[str]):
        """
        Full ingestion pipeline:
        1. Upload raw file to storage
        2. Extract text (Simplified for TXT/MD)
        3. Chunk text
        4. Generate Embeddings
        5. Store in FAISS & MongoDB
        """
        logger.info(f"Starting ingestion for file: {file.filename}")
        
        doc_id = f"doc_{uuid.uuid4().hex}"
        version_id = f"{doc_id}_v1"
        
        # 1. Upload to Storage
        file_path = await self.storage_client.upload_file(file, f"{doc_id}_{file.filename}")
        
        # 2. Extract Text (Simplistic loader for now)
        # In a real enterprise app, we'd use Unstructured.io or LlamaParse here
        content = ""
        # Rewind file to read content
        await file.seek(0)
        content_bytes = await file.read()
        try:
            content = content_bytes.decode('utf-8')
        except UnicodeDecodeError:
            logger.error("Failed to decode file. Only UTF-8 text files supported currently.")
            raise ValueError("Only UTF-8 text files are currently supported.")

        # 3. Chunking
        chunks = self._chunk_text(content, chunk_size=500, overlap=50)
        logger.info(f"Generated {len(chunks)} chunks")

        # 4. Embeddings & Vector Store
        chunk_ids = []
        vectors = []
        
        mongo_chunks = []
        
        # Generate embeddings in batch for efficiency
        text_chunks = [c['text'] for c in chunks]
        embeddings = await self.embedding_service.generate_embeddings(text_chunks)
        
        # Get starting index from FAISS (Global Offset)
        start_index = faiss_service.total_count

        for i, chunk_data in enumerate(chunks):
            chunk_id = f"chk_{uuid.uuid4().hex}"
            chunk_ids.append(chunk_id)
            
            # Prepare Mongo Entry
            mongo_chunks.append({
                "_id": chunk_id,
                "doc_id": doc_id,
                "version": 1,
                "text": chunk_data['text'],
                "start_char": chunk_data['start'],
                "end_char": chunk_data['end'],
                "visibility": visibility,
                "embedding_id": start_index + i  # Sync with FAISS global index
            })
            
            vectors.append(embeddings[i])

        # Add to FAISS
        # Note: IndexFlatL2 doesn't store IDs. We must maintain sync or use IndexIDMap.
        # For this MVP, we assume the FAISS index matches the order of 'active' chunks or use a more complex ID mapping.
        # To make it robust, we should really use an ID Map, but sticking to the faiss_service simple implementation for now.
        import numpy as np
        vector_array = np.array(vectors)
        faiss_service.add_vectors(vector_array)

        # 5. Store Metadata in MongoDB
        
        # Save chunks
        if mongo_chunks:
            await self.collection_chunks.insert_many(mongo_chunks)

        # Save Document
        doc_model = Document(
            _id=doc_id,
            title=file.filename,
            status="ACTIVE",
            visibility=visibility,
            current_version=1,
            created_at=datetime.utcnow()
        )
        await self.collection_docs.insert_one(doc_model.model_dump(by_alias=True))

        # Save Version
        version_model = DocumentVersion(
            _id=version_id,
            doc_id=doc_id,
            version=1,
            content_hash=str(uuid.uuid4()), # Placeholder for SHA256
            approved_by=user_id,
            approved_at=datetime.utcnow(),
            activated_at=datetime.utcnow(),
            chunk_ids=chunk_ids,
            snapshot_ids=[]
        )
        await self.collection_versions.insert_one(version_model.model_dump(by_alias=True))
        
        logger.info("Ingestion complete")
        return {"doc_id": doc_id, "chunks": len(chunks)}

    def _chunk_text(self, text: str, chunk_size: int, overlap: int) -> List[dict]:
        """
        Simple character-based sliding window chunker.
        In production, use token-based chunking (tiktoken).
        """
        chunks = []
        start = 0
        text_len = len(text)
        
        while start < text_len:
            end = min(start + chunk_size, text_len)
            chunk_text = text[start:end]
            
            chunks.append({
                "text": chunk_text,
                "start": start,
                "end": end
            })
            
            if end == text_len:
                break
                
            start += (chunk_size - overlap)
            
        return chunks

    async def list_documents(self, visibility: str = None) -> List[dict]:
        """
        List documents, optionally filtered by visibility.
        """
        query = {}
        if visibility:
            query["visibility"] = visibility
            
        cursor = self.collection_docs.find(query).sort("created_at", -1)
        docs = await cursor.to_list(length=100)
        return docs

knowledge_service = KnowledgeService()
