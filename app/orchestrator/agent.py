from typing import List, Optional, Dict, Any
from app.core.config import settings
from app.domain.knowledge.models import Document
from app.observability.logging import logger

# Services
from app.domain.retrieval.embedding_service import get_embedding_service
from app.domain.response.llm_client import get_llm_client, LLMClient
from app.infrastructure.vector.faiss_service import faiss_service
from app.infrastructure.db.mongo import db
from app.core.auth import auth_handler

class AgentOrchestrator:
    """
    The central brain of the Agentic AI.
    """

    def __init__(self):
        self.embedding_service = get_embedding_service()
        self.llm_client = get_llm_client()
        self.vector_service = faiss_service

    @property
    def chunk_collection(self):
        return db.get_db()["chunks"]

    async def process_query(self, query: str, user_roles: List[str], user_id: str, kb_snapshot_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Main entry point for processing a user query.
        """
        logger.info("Processing query", extra={"query": query, "roles": user_roles, "user": user_id})
        
        # 1. Embed Query
        # ---------------------------------------------------------
        query_vector = await self.embedding_service.generate_embedding(query)
        
        # 2. Retrieve (Vector Search)
        # ---------------------------------------------------------
        # Retrieve top K candidates (e.g., 10)
        distances, indices = await self.vector_service.search(query_vector, k=10)
        
        # indices[0] is the list of IDs (if flat) or indices
        # Since we used simple add(), indices are 0-based integers matching insertion order.
        # Capability limitation: FAISS flat index doesn't give us the external 'chunk_id' back easily 
        # unless we used IndexIDMap. 
        # WORKAROUND for MVP: We assume we can fetch by embedding_id stored in Mongo.
        
        found_indices = indices[0]
        valid_indices = [int(i) for i in found_indices if i >= 0]
        
        if not valid_indices:
            return await self._finalize_response(query, "No relevant documents found.", [], "Low", user_id, user_roles)

        # 3. Fetch Metadata & Enforce RBAC
        # ---------------------------------------------------------
        # We need to query Mongo for chunks where `embedding_id` IN valid_indices
        # AND user has permission.
        
        cursor = self.chunk_collection.find({
            "embedding_id": {"$in": valid_indices}
        })
        
        retrieved_chunks = await cursor.to_list(length=len(valid_indices))
        
        # Filter based on RBAC logic
        # A chunk is visible if user_roles intersects with chunk.visibility
        # OR if chunk.visibility contains "PUBLIC"
        # OR if user is ADMIN
        
        allowed_chunks = []
        for chunk in retrieved_chunks:
            chunk_vis = chunk.get("visibility", ["INTERNAL"])
            
            # Check permissions
            if "PUBLIC" in chunk_vis:
                allowed_chunks.append(chunk)
                continue
            
            if "ADMIN" in user_roles:
                allowed_chunks.append(chunk)
                continue
                
            # Intersect
            # Note: In real app, roles often need mapping (e.g. user has group_id, doc has group_id)
            # Here we assume direct string match.
            if set(user_roles) & set(chunk_vis):
                allowed_chunks.append(chunk)
        
        if not allowed_chunks:
            logger.warning("Documents found but filtered by RBAC", extra={"user_roles": user_roles})
            return await self._finalize_response(
                query,
                "Relevant information exists, but you do not have permission to view it.", 
                [], 
                "High",
                user_id,
                user_roles
            )

        # 4. Context Assembly
        # ---------------------------------------------------------
        # Deduplicate by text content (simple)
        unique_texts = set()
        final_context = []
        sources = []
        
        for c in allowed_chunks:
            if c["text"] not in unique_texts:
                unique_texts.add(c["text"])
                final_context.append(c["text"])
                sources.append(c.get("doc_id", "unknown"))
            if len(final_context) >= 3: # Limit to Top 3 for context window
                break
        
        # 5. Generate Response
        # ---------------------------------------------------------
        answer = await self.llm_client.generate_answer(query, final_context)
        
        return await self._finalize_response(query, answer, list(set(sources)), "Medium", user_id, user_roles)

    async def _finalize_response(self, query: str, answer: str, sources: List[str], confidence: str, user_id: str, user_roles: List[str]) -> Dict[str, Any]:
        """
        Helper to construct response + Save History
        """
        # Save to History
        try:
            from app.infrastructure.db.chat_repo import chat_repo
            from app.domain.chat.models import ChatMessage
            
            msg = ChatMessage(
                user_id=user_id,
                user_role=user_roles,
                query=query,
                answer=answer,
                sources=sources,
                confidence=confidence
            )
            await chat_repo.save_message(msg)
        except Exception as e:
            logger.error(f"Failed to save chat history: {e}")

        return {
            "answer": answer,
            "sources": sources,
            "confidence": confidence,
            "backend_used": self.llm_client.__class__.__name__
        }

# Singleton
agent_orchestrator = AgentOrchestrator()
