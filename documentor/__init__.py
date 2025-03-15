"""
Documetor: A library for creating vector embeddings from documents using Google Vertex AI.

This package provides tools to extract text from various document formats,
chunk text intelligently, generate embeddings using Vertex AI,
and create a searchable vector database.
"""

__version__ = "0.1.0"

# Import main classes for convenient access
from documetor.core.embedder import DocumentEmbedder
from documetor.processors.base import DocumentProcessor
from documetor.text.chunker import TextChunker
from documetor.storage.base import VectorStore
from documetor.storage.local import LocalVectorStore
from documetor.storage.vertex import VertexMatchingEngineStore
