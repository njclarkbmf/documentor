"""
Main DocumentEmbedder class that coordinates document processing, chunking, 
embedding generation, and vector storage.
"""

import os
import time
import concurrent.futures
from typing import List, Dict, Any, Optional

from rich.progress import Progress, TextColumn, BarColumn, TimeElapsedColumn, TimeRemainingColumn

from documetor.config import (
    logger, DEFAULT_CHUNK_SIZE, DEFAULT_CHUNK_OVERLAP, DEFAULT_LOCATION,
    DEFAULT_EMBEDDING_MODEL, DEFAULT_BATCH_SIZE, DEFAULT_MAX_WORKERS,
    DEFAULT_CHUNK_STRATEGY, NullContext
)
from documetor.processors import get_processor_for_file
from documetor.processors.pdf import PDFProcessor
from documetor.text.chunker import TextChunker
from documetor.embedding.vertex import VertexEmbeddings
from documetor.storage.base import VectorStore
from documetor.storage.local import LocalVectorStore
from documetor.storage.vertex import VertexMatchingEngineStore


class DocumentEmbedder:
    """Main class to process documents and create embeddings"""
    
    def __init__(
        self,
        project_id: str,
        location: str = DEFAULT_LOCATION,
        chunk_size: int = DEFAULT_CHUNK_SIZE,
        chunk_overlap: int = DEFAULT_CHUNK_OVERLAP,
        chunk_strategy: str = DEFAULT_CHUNK_STRATEGY,
        embedding_model: str = DEFAULT_EMBEDDING_MODEL,
        store_type: str = "local",
        store_path: Optional[str] = None,
        index_name: Optional[str] = None,
        vector_store: Optional[VectorStore] = None,
        batch_size: int = DEFAULT_BATCH_SIZE,
        max_workers: int = DEFAULT_MAX_WORKERS,
        use_ocr: bool = False,
        verbose: bool = False,
        silent: bool = False,
        log_level: str = "INFO"
    ):
        """
        Initialize the document embedder
        
        Args:
            project_id: Google Cloud project ID
            location: Google Cloud region
            chunk_size: Maximum size of text chunks
            chunk_overlap: Overlap between consecutive chunks
            chunk_strategy: Strategy for chunking text (hybrid, sentence, fixed)
            embedding_model: Vertex AI model name for embeddings
            store_type: Type of vector store (local, vertex)
            store_path: Path to save/load local vector store
            index_name: Name for Vertex Matching Engine index
            vector_store: Custom vector store instance
            batch_size: Number of documents to process in batch
            max_workers: Maximum number of concurrent workers
            use_ocr: Whether to use OCR for PDF text extraction
            verbose: Whether to show detailed output
            silent: Whether to suppress all output
            log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
        """
        # Set up logging based on verbosity
        if silent:
            logger.setLevel("ERROR")
        elif verbose:
            logger.setLevel("DEBUG")
        else:
            logger.setLevel(log_level)
        
        logger.debug("Initializing DocumentEmbedder")
        
        self.project_id = project_id
        self.location = location
        self.use_ocr = use_ocr
        self.batch_size = batch_size
        self.max_workers = max_workers
        self.verbose = verbose
        self.silent = silent
        
        # Set up chunker
        self.chunker = TextChunker(
            chunk_size=chunk_size, 
            chunk_overlap=chunk_overlap,
            strategy=chunk_strategy
        )
        
        # Set up embeddings generator
        self.embeddings_generator = VertexEmbeddings(
            project_id=project_id,
            location=location,
            model_name=embedding_model,
            batch_size=batch_size
        )
        
        # Set up vector store
        if vector_store:
            self.vector_store = vector_store
        elif store_type == "vertex":
            self.vector_store = VertexMatchingEngineStore(
                project_id=project_id,
                location=location,
                index_name=index_name or "documetor_embeddings"
            )
        else:  # default to local
            self.vector_store = LocalVectorStore(store_path=store_path)
        
        logger.info(f"DocumentEmbedder initialized with {store_type} vector store")
    
    def process_directory(self, directory_path: str, recursive: bool = True) -> None:
        """
        Process all supported documents in a directory
        
        Args:
            directory_path: Path to directory containing documents
            recursive: Whether to recursively process subdirectories
        """
        from documetor.processors import get_supported_extensions
        
        # Get list of supported files
        supported_extensions = get_supported_extensions()
        files = []
        
        # Walk directory
        walk_fn = os.walk if recursive else lambda d: [(d, [], [f for f in os.listdir(d) if os.path.isfile(os.path.join(d, f))])]
        
        for root, _, filenames in walk_fn(directory_path):
            for filename in filenames:
                ext = os.path.splitext(filename)[1].lower()
                if ext in supported_extensions:
                    files.append(os.path.join(root, filename))
        
        if not files:
            logger.warning(f"No supported documents found in {directory_path}")
            return
        
        logger.info(f"Found {len(files)} documents to process")
        
        # Process files in parallel
        if self.max_workers > 1 and len(files) > 1:
            self._process_files_parallel(files)
        else:
            self._process_files_sequential(files)
    
    def _process_files_sequential(self, files: List[str]) -> None:
        """Process files sequentially with progress bar"""
        with Progress(
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TimeElapsedColumn(),
            TimeRemainingColumn(),
            disable=self.silent
        ) as progress:
            task_id = progress.add_task("Processing documents", total=len(files))
            
            for file_path in files:
                try:
                    self.process_file(file_path, show_progress=False)
                    progress.update(task_id, advance=1)
                except Exception as e:
                    logger.error(f"Error processing {file_path}: {str(e)}")
    
    def _process_files_parallel(self, files: List[str]) -> None:
        """Process files in parallel with progress bar"""
        with Progress(
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TimeElapsedColumn(),
            TimeRemainingColumn(),
            disable=self.silent
        ) as progress:
            task_id = progress.add_task("Processing documents", total=len(files))
            
            # Process in batches to avoid memory issues
            for i in range(0, len(files), self.batch_size):
                batch = files[i:i+self.batch_size]
                
                with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                    futures = {executor.submit(self.process_file, file_path, False): file_path for file_path in batch}
                    
                    for future in concurrent.futures.as_completed(futures):
                        file_path = futures[future]
                        try:
                            future.result()
                        except Exception as e:
                            logger.error(f"Error processing {file_path}: {str(e)}")
                        
                        progress.update(task_id, advance=1)
    
    def process_file(self, file_path: str, show_progress: bool = True) -> bool:
        """
        Process a single document file
        
        Args:
            file_path: Path to document file
            show_progress: Whether to show progress bars
            
        Returns:
            True if processing was successful, False otherwise
        """
        logger.info(f"Processing {file_path}")
        
        try:
            # Get appropriate processor
            processor = get_processor_for_file(file_path)
            
            # If we need OCR for PDFs, initialize with OCR flag
            if self.use_ocr and isinstance(processor, PDFProcessor):
                processor.use_ocr = True
            
            # Extract text
            text = processor.extract_text(file_path)
            
            # Check if we got any text
            if not text or not text.strip():
                logger.warning(f"No text extracted from {file_path}")
                return False
            
            # Chunk text
            chunks = self.chunker.chunk_text(text)
            
            # Skip if no chunks
            if not chunks:
                logger.warning(f"No chunks created from {file_path}")
                return False
            
            logger.info(f"Created {len(chunks)} chunks from {file_path}")
            
            # Generate embeddings
            embeddings = self.embeddings_generator.get_embeddings(chunks, show_progress=show_progress and self.verbose)
            
            # Create metadata
            metadata = []
            for i, chunk in enumerate(chunks):
                metadata.append({
                    "id": f"{os.path.basename(file_path)}_{i}",
                    "source": file_path,
                    "chunk_index": i,
                    "text": chunk,
                    "total_chunks": len(chunks),
                    "extraction_time": time.time()
                })
            
            # Add to vector store
            self.vector_store.add_embeddings(embeddings, metadata)
            
            logger.info(f"Successfully processed {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error processing {file_path}: {str(e)}")
            return False
    
    def search(
        self, 
        query: str, 
        top_k: int = 5,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for documents similar to query
        
        Args:
            query: Query text
            top_k: Number of results to return
            filters: Dictionary of metadata fields to filter on
            
        Returns:
            List of search results with metadata
        """
        logger.info(f"Searching for: {query}")
        
        # Generate embedding for query
        query_embedding = self.embeddings_generator.get_embeddings([query])[0]
        
        # Search vector store
        results = self.vector_store.search(
            query_embedding, 
            top_k=top_k,
            filters=filters
        )
        
        logger.info(f"Found {len(results)} results")
        return results
