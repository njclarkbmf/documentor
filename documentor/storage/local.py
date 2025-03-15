"""
Local vector store implementation.
"""

import os
import pickle
import numpy as np
from typing import List, Dict, Any, Optional

from documetor.config import logger
from documetor.storage.base import VectorStore


class LocalVectorStore(VectorStore):
    """Simple local vector store using numpy"""
    
    def __init__(self, store_path: Optional[str] = None):
        """
        Initialize the local vector store
        
        Args:
            store_path: Path to save/load the store (None for in-memory only)
        """
        self.store_path = store_path
        self.embeddings = []
        self.metadata = []
        
        if store_path and os.path.exists(store_path):
            self._load()
    
    def add_embeddings(
        self, 
        embeddings: List[List[float]], 
        metadata: List[Dict[str, Any]]
    ) -> None:
        """
        Add embeddings to the store
        
        Args:
            embeddings: List of embedding vectors
            metadata: List of metadata dictionaries (one per embedding)
        """
        self.embeddings.extend(embeddings)
        self.metadata.extend(metadata)
        
        if self.store_path:
            self._save()
    
    def search(
        self, 
        query_embedding: List[float], 
        top_k: int = 5,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for similar vectors
        
        Args:
            query_embedding: Query embedding vector
            top_k: Number of results to return
            filters: Dictionary of metadata fields to filter on
            
        Returns:
            List of metadata dictionaries for the most similar vectors
        """
        if not self.embeddings:
            return []
        
        # Convert to numpy for faster computation
        query_np = np.array(query_embedding)
        embeddings_np = np.array(self.embeddings)
        
        # Compute cosine similarity
        dot_product = np.dot(embeddings_np, query_np)
        norm_query = np.linalg.norm(query_np)
        norm_embeddings = np.linalg.norm(embeddings_np, axis=1)
        
        similarity = dot_product / (norm_query * norm_embeddings)
        
        # Apply filters if provided
        if filters:
            mask = np.ones(len(self.metadata), dtype=bool)
            for key, value in filters.items():
                for i, meta in enumerate(self.metadata):
                    if key not in meta or meta[key] != value:
                        mask[i] = False
            
            # Apply mask to similarity scores
            filtered_similarity = np.where(mask, similarity, -np.inf)
        else:
            filtered_similarity = similarity
        
        # Get top-k indices (ignoring -inf values from filtering)
        valid_indices = np.where(filtered_similarity != -np.inf)[0]
        if len(valid_indices) == 0:
            return []
            
        top_indices = valid_indices[np.argsort(filtered_similarity[valid_indices])[-top_k:][::-1]]
        
        # Return metadata with similarity scores
        results = []
        for idx in top_indices:
            # Skip results with -inf similarity (filtered out)
            if filtered_similarity[idx] == -np.inf:
                continue
                
            result = self.metadata[idx].copy()
            result["similarity"] = float(similarity[idx])
            results.append(result)
            
        return results
    
    def _save(self) -> None:
        """Save the store to disk"""
        try:
            with open(self.store_path, 'wb') as f:
                pickle.dump((self.embeddings, self.metadata), f)
            logger.debug(f"Vector store saved to {self.store_path}")
        except Exception as e:
            logger.error(f"Error saving vector store: {str(e)}")
    
    def _load(self) -> None:
        """Load the store from disk"""
        try:
            with open(self.store_path, 'rb') as f:
                self.embeddings, self.metadata = pickle.load(f)
            logger.debug(f"Vector store loaded from {self.store_path} with {len(self.embeddings)} embeddings")
        except Exception as e:
            logger.error(f"Error loading vector store: {str(e)}")
            # Initialize empty store on error
            self.embeddings = []
            self.metadata = []
