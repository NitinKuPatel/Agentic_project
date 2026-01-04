import faiss
import numpy as np
import os
import asyncio
from app.core.config import settings

class FaissService:
    def __init__(self, dimension: int = 384):
        self.dimension = dimension
        self.index_path = settings.FAISS_INDEX_PATH
        self.index = None
        self._load_or_create_index()

    def _load_or_create_index(self):
        if os.path.exists(self.index_path):
            try:
                self.index = faiss.read_index(self.index_path)
                print(f"Loaded FAISS index from {self.index_path}")
            except Exception as e:
                print(f"Error loading index: {e}. Creating new one.")
                self.index = faiss.IndexFlatL2(self.dimension)
        else:
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(self.index_path), exist_ok=True)
            self.index = faiss.IndexFlatL2(self.dimension)
            print("Created new FAISS index.")

    def add_vectors(self, vectors: np.ndarray):
        """
        Add vectors to the index. 
        Note: FAISS IndexFlatL2 doesn't support IDs by default in the simplest Add. 
        For a real ID mapping, we usually use IndexIDMap.
        """
        # Convert to float32 as FAISS expects
        vectors = vectors.astype('float32')
        self.index.add(vectors)
        self.save_index()

    async def search(self, query_vector: np.ndarray, k: int = 5):
        query_vector = query_vector.astype('float32')
        # Reshape if 1D
        if len(query_vector.shape) == 1:
            query_vector = query_vector.reshape(1, -1)
            
        distances, indices = await asyncio.to_thread(self.index.search, query_vector, k)
        return distances, indices

    def save_index(self):
        faiss.write_index(self.index, self.index_path)
        print(f"Saved FAISS index to {self.index_path}")

    @property
    def total_count(self) -> int:
        if self.index:
            return self.index.ntotal
        return 0

# Singleton instance (initialized with default dimension, can be adjusted)
# In a real app, dimension should match the embedding model used.
faiss_service = FaissService(dimension=384)
