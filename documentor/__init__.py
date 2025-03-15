"""
Documetor: A library for creating vector embeddings from documents using Google Vertex AI.

This package provides tools to extract text from various document formats,
chunk text intelligently, generate embeddings using Vertex AI,
and create a searchable vector database.
"""

__version__ = "0.1.0"

# Import main classes for convenient access
from documentor.core.embedder import DocumentEmbedder
from documentor.processors.base import DocumentProcessor
from documentor.text.chunker import TextChunker
from documentor.storage.base import VectorStore
from documentor.storage.local import LocalVectorStore
from documentor.storage.vertex import VertexMatchingEngineStore
