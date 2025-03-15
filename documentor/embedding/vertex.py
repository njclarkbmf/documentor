"""
Vertex AI embeddings implementation.
"""

import time
from typing import List

from google.cloud import aiplatform
from rich.progress import Progress, TextColumn, BarColumn, TimeElapsedColumn, TimeRemainingColumn

from documentor.config import logger, DEFAULT_LOCATION, DEFAULT_BATCH_SIZE, NullContext


class VertexEmbeddings:
    """Class to create embeddings using Google Vertex AI"""
    
    def __init__(
        self, 
        project_id: str, 
        location: str = DEFAULT_LOCATION, 
        model_name: str = "textembedding-gecko@latest",
        batch_size: int = DEFAULT_BATCH_SIZE,
        max_retries: int = 3,
        retry_delay: int = 2
    ):
        """
        Initialize the embeddings generator
        
        Args:
            project_id: Google Cloud project ID
            location: Google Cloud region
            model_name: Vertex AI model name for embeddings
            batch_size: Number of texts to embed in a single API call
            max_retries: Maximum number of retries for API calls
            retry_delay: Delay between retries in seconds
        """
        self.project_id = project_id
        self.location = location
        self.model_name = model_name
        self.batch_size = batch_size
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        
        # Initialize Vertex AI
        aiplatform.init(project=project_id, location=location)
        
        # Model will be lazily initialized when needed
        self._model = None
    
    @property
    def model(self):
        """Lazy initialization of the model"""
        if self._model is None:
            self._model = aiplatform.TextEmbeddingModel.from_pretrained(self.model_name)
        return self._model
    
    def get_embeddings(
        self, 
        texts: List[str], 
        show_progress: bool = False
    ) -> List[List[float]]:
        """
        Generate embeddings for a list of texts
        
        Args:
            texts: List of text chunks to embed
            show_progress: Whether to show a progress bar
            
        Returns:
            List of embedding vectors
        """
        all_embeddings = []
        total_batches = (len(texts) + self.batch_size - 1) // self.batch_size
        
        # Create progress bar if requested
        progress_context = Progress(
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TimeElapsedColumn(),
            TimeRemainingColumn(),
        ) if show_progress else NullContext()
        
        try:
            with progress_context as progress:
                if show_progress:
                    task_id = progress.add_task("Generating embeddings", total=len(texts))
                
                for i in range(0, len(texts), self.batch_size):
                    batch_texts = texts[i:i+self.batch_size]
                    
                    # Retry logic for API calls
                    for retry in range(self.max_retries):
                        try:
                            embeddings = self.model.get_embeddings(batch_texts)
                            # Extract the embedding values
                            embedding_values = [emb.values for emb in embeddings]
                            all_embeddings.extend(embedding_values)
                            
                            if show_progress:
                                progress.update(task_id, advance=len(batch_texts))
                            
                            break  # Success, exit retry loop
                        except Exception as e:
                            if retry < self.max_retries - 1:
                                logger.warning(f"Embedding API error (retry {retry+1}/{self.max_retries}): {str(e)}")
                                time.sleep(self.retry_delay)
                            else:
                                logger.error(f"Failed to generate embeddings after {self.max_retries} retries: {str(e)}")
                                raise
        except Exception as e:
            logger.error(f"Error generating embeddings: {str(e)}")
            raise
            
        return all_embeddings
