"""
Base vector store class.
"""

from typing import List, Dict, Any, Optional


class VectorStore:
    """Base class for vector stores"""
    
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
            
        Raises:
            NotImplementedError: If not implemented by subclass
        """
        raise NotImplementedError("Subclasses must implement add_embeddings")
    
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
            
        Raises:
            NotImplementedError: If not implemented by subclass
        """
        raise NotImplementedError("Subclasses must implement search")
