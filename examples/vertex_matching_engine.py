"""
Example of using Documetor with Vertex AI Matching Engine for production-scale deployments.
"""

import os
import sys
import time

# Add the parent directory to the path so we can import documetor
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from documetor import DocumentEmbedder, VertexMatchingEngineStore


def main():
    # Get Google Cloud project ID from environment variable or specify directly
    project_id = os.environ.get("GOOGLE_CLOUD_PROJECT")
    
    if not project_id:
        print("Error: GOOGLE_CLOUD_PROJECT environment variable not set.")
        print("Please set it or specify the project ID directly in the script.")
        sys.exit(1)
    
    # Directory containing documents to process
    documents_dir = "path/to/your/documents"
    
    # Initialize the embedder with Vertex AI Matching Engine storage
    print("Initializing Vertex AI Matching Engine...")
    embedder = DocumentEmbedder(
        project_id=project_id,
        location="us-central1",  # Adjust to your preferred region
        store_type="vertex",
        index_name="documetor-demo",  # Custom name for your index
        embedding_model="textembedding-gecko@latest",
        verbose=True
    )
    
    # Process all documents in the directory
    print(f"Processing documents in {documents_dir}...")
    start_time = time.time()
    embedder.process_directory(documents_dir)
    processing_time = time.time() - start_time
    print(f"Processing completed in {processing_time:.2f} seconds")
    
    # Wait for embeddings to be indexed (Matching Engine has some delay)
    print("Waiting for embeddings to be indexed (10 seconds)...")
    time.sleep(10)
    
    # Search for relevant documents
    while True:
        query = input("\nEnter search query (or 'q' to quit): ")
        if query.lower() == 'q':
            break
        
        # Measure search performance
        start_time = time.time()
        results = embedder.search(query, top_k=5)
        search_time = time.time() - start_time
        
        # Display results
        print(f"Search completed in {search_time:.4f} seconds")
        print(f"Found {len(results)} results:\n")
        
        for i, result in enumerate(results):
            print(f"Result {i+1} - Score: {result['similarity']:.4f}")
            print(f"Source: {result['source']}")
            print(f"Text: {result['text'][:200]}...")
            print("-" * 80)
    
    print("Search demo completed.")


if __name__ == "__main__":
    main()
