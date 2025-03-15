"""
Example of basic usage of the Documetor library.
"""

import os
import sys
from pprint import pprint

# Add the parent directory to the path so we can import documetor
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from documetor import DocumentEmbedder


def main():
    # Get Google Cloud project ID from environment variable or specify directly
    project_id = os.environ.get("GOOGLE_CLOUD_PROJECT")
    
    if not project_id:
        print("Error: GOOGLE_CLOUD_PROJECT environment variable not set.")
        print("Please set it or specify the project ID directly in the script.")
        sys.exit(1)
    
    # Directory containing documents to process
    documents_dir = "path/to/your/documents"
    
    # Initialize the embedder with local storage
    embedder = DocumentEmbedder(
        project_id=project_id,
        store_type="local",  # Use local storage for simplicity
        store_path="documents.pkl",  # Save embeddings to disk
        verbose=True  # Show detailed progress
    )
    
    # Process all documents in the directory
    print(f"Processing documents in {documents_dir}...")
    embedder.process_directory(documents_dir)
    
    # Search for relevant documents
    query = "What is the procedure for customer onboarding?"
    print(f"\nSearching for: {query}")
    
    results = embedder.search(query, top_k=3)
    
    # Display results
    print("\nSearch results:")
    for i, result in enumerate(results):
        print(f"\n--- Result {i+1} ---")
        print(f"Source: {result['source']}")
        print(f"Similarity: {result['similarity']:.4f}")
        print(f"Text snippet: {result['text'][:200]}...")


if __name__ == "__main__":
    main()
