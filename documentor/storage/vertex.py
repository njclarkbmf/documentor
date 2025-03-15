"""
Vertex AI Matching Engine vector store implementation.
"""

import os
import json
import uuid
import tempfile
from typing import List, Dict, Any, Optional

from google.cloud import storage
from google.cloud import aiplatform
from google.cloud.aiplatform.matching_engine import MatchingEngineIndex
from google.cloud.aiplatform.matching_engine import MatchingEngineIndexEndpoint

from documetor.config import logger, DEFAULT_LOCATION
from documetor.storage.base import VectorStore


class VertexMatchingEngineStore(VectorStore):
    """Vector store using Google Vertex AI Matching Engine"""
    
    def __init__(
        self,
        project_id: str,
        location: str = DEFAULT_LOCATION,
        index_name: str = "document_embeddings",
        dimensions: int = 768,  # Depends on your embedding model
        display_name: str = "Document Embeddings Index",
        description: str = "Vector index for document embeddings",
        create_if_not_exists: bool = True
    ):
        """
        Initialize the Vertex AI Matching Engine store
        
        Args:
            project_id: Google Cloud project ID
            location: Google Cloud region
            index_name: Name of the index
            dimensions: Dimensions of the embedding vectors
            display_name: Display name for the index
            description: Description of the index
            create_if_not_exists: Whether to create the index if it doesn't exist
        """
        self.project_id = project_id
        self.location = location
        self.index_name = index_name
        self.dimensions = dimensions
        
        # Initialize Vertex AI
        aiplatform.init(project=project_id, location=location)
        
        if create_if_not_exists:
            # Check if index exists or create it
            self.index = self._get_or_create_index(
                display_name=display_name,
                description=description
            )
            
            # Check or create endpoint
            self.endpoint = self._get_or_create_endpoint()
        else:
            # Just get existing resources
            self.index = self._get_index()
            self.endpoint = self._get_endpoint()
    
    def _get_index(self) -> MatchingEngineIndex:
        """
        Get existing index
        
        Returns:
            MatchingEngineIndex: The index
            
        Raises:
            ValueError: If index not found
        """
        indexes = aiplatform.MatchingEngineIndex.list(
            filter=f'display_name="{self.index_name}"'
        )
        
        if not indexes:
            raise ValueError(f"Matching Engine index '{self.index_name}' not found")
        
        return indexes[0]
    
    def _get_or_create_index(
        self, 
        display_name: str, 
        description: str
    ) -> MatchingEngineIndex:
        """
        Get existing index or create a new one
        
        Args:
            display_name: Display name for the index
            description: Description of the index
            
        Returns:
            MatchingEngineIndex: The index
            
        Raises:
            Exception: If index creation fails
        """
        try:
            # Try to get existing index
            indexes = aiplatform.MatchingEngineIndex.list(
                filter=f'display_name="{self.index_name}"'
            )
            
            if indexes:
                logger.info(f"Using existing Matching Engine index: {self.index_name}")
                return indexes[0]
            
            # Create new index
            logger.info(f"Creating new Matching Engine index: {self.index_name}")
            return aiplatform.MatchingEngineIndex.create(
                display_name=display_name,
                description=description,
                dimensions=self.dimensions,
                approximate_neighbors_count=150,
                distance_measure_type="DOT_PRODUCT_DISTANCE",
                shard_size="SHARD_SIZE_MEDIUM"
            )
        except Exception as e:
            logger.error(f"Error creating/getting Matching Engine index: {str(e)}")
            raise
    
    def _get_endpoint(self) -> MatchingEngineIndexEndpoint:
        """
        Get existing endpoint
        
        Returns:
            MatchingEngineIndexEndpoint: The endpoint
            
        Raises:
            ValueError: If endpoint not found
        """
        endpoints = aiplatform.MatchingEngineIndexEndpoint.list(
            filter=f'display_name="{self.index_name}_endpoint"'
        )
        
        if not endpoints:
            raise ValueError(f"Matching Engine endpoint for '{self.index_name}' not found")
        
        return endpoints[0]
    
    def _get_or_create_endpoint(self) -> MatchingEngineIndexEndpoint:
        """
        Get existing endpoint or create a new one
        
        Returns:
            MatchingEngineIndexEndpoint: The endpoint
            
        Raises:
            Exception: If endpoint creation fails
        """
        try:
            # Try to get existing endpoint
            endpoints = aiplatform.MatchingEngineIndexEndpoint.list(
                filter=f'display_name="{self.index_name}_endpoint"'
            )
            
            if endpoints:
                endpoint = endpoints[0]
                logger.info(f"Using existing Matching Engine endpoint: {self.index_name}_endpoint")
            else:
                # Create new endpoint
                logger.info(f"Creating new Matching Engine endpoint: {self.index_name}_endpoint")
                endpoint = aiplatform.MatchingEngineIndexEndpoint.create(
                    display_name=f"{self.index_name}_endpoint",
                    description=f"Endpoint for {self.index_name}",
                    network=f"projects/{self.project_id}/global/networks/default"
                )
            
            # Check if our index is deployed to this endpoint
            deployed = False
            for deployed_index in endpoint.deployed_indexes:
                if deployed_index.index == self.index.resource_name:
                    deployed = True
                    break
            
            # Deploy index if not already deployed
            if not deployed:
                logger.info(f"Deploying index {self.index_name} to endpoint")
                endpoint.deploy_index(
                    index=self.index,
                    deployed_index_id=self.index_name
                )
            else:
                logger.info(f"Index {self.index_name} already deployed to endpoint")
            
            return endpoint
        except Exception as e:
            logger.error(f"Error creating/getting Matching Engine endpoint: {str(e)}")
            raise
    
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
            Exception: If adding embeddings fails
        """
        if not embeddings:
            logger.warning("No embeddings to add")
            return
            
        try:
            # Create a temporary jsonl file to upload
            with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
                temp_file = f.name
                for i, (emb, meta) in enumerate(zip(embeddings, metadata)):
                    # Create ID for the vector
                    vector_id = meta.get("id", str(uuid.uuid4()))
                    
                    # Extract restricts (filter fields) if any
                    restricts = {}
                    if "source" in meta:
                        restricts["source"] = meta["source"]
                    
                    # Prepare the entry
                    entry = {
                        "id": vector_id,
                        "embedding": emb,
                        "restricts": restricts,
                        "metadata": json.dumps(meta)  # Metadata must be string
                    }
                    
                    # Write to jsonl file
                    f.write(json.dumps(entry) + "\n")
            
            # Upload to GCS
            logger.info(f"Uploading {len(embeddings)} embeddings to GCS")
            bucket_name = f"{self.project_id}-matching-engine"
            self._ensure_bucket_exists(bucket_name)
            
            blob_name = f"uploads/{self.index_name}/{uuid.uuid4()}.jsonl"
            self._upload_to_gcs(temp_file, bucket_name, blob_name)
            
            # Update the index with new vectors
            logger.info("Updating Matching Engine index with new embeddings")
            self.index.update_embeddings(
                contents_delta_uri=f"gs://{bucket_name}/{blob_name}"
            )
            
            # Clean up
            os.unlink(temp_file)
            logger.info("Successfully added embeddings to Matching Engine")
        except Exception as e:
            logger.error(f"Error adding embeddings to Matching Engine: {str(e)}")
            raise
    
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
            Exception: If search fails
        """
        try:
            # Prepare filters if any
            filter_dict = {}
            if filters:
                for key, value in filters.items():
                    filter_dict[key] = value
            
            # Search the index
            response = self.endpoint.find_neighbors(
                deployed_index_id=self.index_name,
                queries=[query_embedding],
                num_neighbors=top_k,
                filter=filter_dict if filter_dict else None
            )
            
            # Process results
            results = []
            for neighbor in response[0]:
                try:
                    # Parse the metadata JSON
                    result = json.loads(neighbor.metadata)
                    result["similarity"] = float(neighbor.distance)
                    results.append(result)
                except json.JSONDecodeError:
                    logger.warning(f"Could not parse metadata for result: {neighbor.metadata}")
                    # Include minimal result
                    results.append({
                        "id": neighbor.id,
                        "similarity": float(neighbor.distance),
                        "metadata_raw": neighbor.metadata
                    })
                    
            return results
        except Exception as e:
            logger.error(f"Error searching Matching Engine: {str(e)}")
            raise
    
    def _ensure_bucket_exists(self, bucket_name: str) -> None:
        """
        Ensure GCS bucket exists
        
        Args:
            bucket_name: Name of the bucket
        """
        storage_client = storage.Client(project=self.project_id)
        
        try:
            storage_client.get_bucket(bucket_name)
            logger.debug(f"Using existing GCS bucket: {bucket_name}")
        except Exception:
            logger.info(f"Creating GCS bucket: {bucket_name}")
            storage_client.create_bucket(bucket_name, location=self.location)
    
    def _upload_to_gcs(
        self, 
        local_file: str, 
        bucket_name: str, 
        blob_name: str
    ) -> None:
        """
        Upload file to GCS
        
        Args:
            local_file: Path to local file
            bucket_name: Name of the bucket
            blob_name: Name of the blob
        """
        storage_client = storage.Client(project=self.project_id)
        bucket = storage_client.bucket(bucket_name)
        blob = bucket.blob(blob_name)
        blob.upload_from_filename(local_file)
        logger.debug(f"Uploaded {local_file} to gs://{bucket_name}/{blob_name}")
