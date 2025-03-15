"""
Example of extending Documetor with custom document processors.
"""

import os
import sys
import csv
import json
from typing import Dict, List, Any

# Add the parent directory to the path so we can import documetor
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from documetor import DocumentEmbedder, DocumentProcessor
from documetor.processors import register_processor


# Custom CSV Processor
class CSVProcessor(DocumentProcessor):
    """Processor for CSV files"""
    
    def extract_text(self, file_path: str) -> str:
        """
        Extract text from a CSV file
        
        Args:
            file_path: Path to the CSV file
            
        Returns:
            Extracted text from the CSV
        """
        try:
            lines = []
            with open(file_path, 'r', newline='', encoding='utf-8') as csvfile:
                reader = csv.reader(csvfile)
                headers = next(reader)  # Get headers
                
                # Add headers as first line
                lines.append(' | '.join(headers))
                
                # Process rows
                for row in reader:
                    # Create a line with header:value pairs
                    row_text = []
                    for i, value in enumerate(row):
                        if i < len(headers) and value:
                            row_text.append(f"{headers[i]}: {value}")
                    
                    lines.append('. '.join(row_text))
            
            return '\n'.join(lines)
        except Exception as e:
            print(f"Error extracting text from CSV {file_path}: {str(e)}")
            return ""


# Custom JSON Processor
class JSONProcessor(DocumentProcessor):
    """Processor for JSON files"""
    
    def extract_text(self, file_path: str) -> str:
        """
        Extract text from a JSON file
        
        Args:
            file_path: Path to the JSON file
            
        Returns:
            Extracted text from the JSON
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                data = json.load(file)
            
            # Convert JSON to text
            return self._json_to_text(data)
        except Exception as e:
            print(f"Error extracting text from JSON {file_path}: {str(e)}")
            return ""
    
    def _json_to_text(self, data: Any, prefix: str = "") -> str:
        """
        Recursively convert JSON to text
        
        Args:
            data: JSON data
            prefix: Prefix for nested fields
            
        Returns:
            Text representation of JSON
        """
        if isinstance(data, dict):
            lines = []
            for key, value in data.items():
                field_name = f"{prefix}{key}" if prefix else key
                if isinstance(value, (dict, list)):
                    lines.append(self._json_to_text(value, f"{field_name}."))
                else:
                    lines.append(f"{field_name}: {value}")
            return "\n".join(lines)
        elif isinstance(data, list):
            if not data:
                return ""
                
            # If list contains dictionaries, process each item
            if all(isinstance(item, dict) for item in data):
                return "\n\n".join(self._json_to_text(item, prefix) for item in data)
            
            # For simple lists, join items
            return f"{prefix.rstrip('.')}: " + ", ".join(str(item) for item in data)
        else:
            return str(data)


def main():
    # Register custom processors
    register_processor('.csv', CSVProcessor)
    register_processor('.json', JSONProcessor)
    
    # Get Google Cloud project ID
    project_id = os.environ.get("GOOGLE_CLOUD_PROJECT")
    
    if not project_id:
        print("Error: GOOGLE_CLOUD_PROJECT environment variable not set.")
        print("Please set it or specify the project ID directly in the script.")
        sys.exit(1)
    
    # Directory containing documents to process
    documents_dir = "path/to/your/documents"
    
    # Initialize the embedder
    embedder = DocumentEmbedder(
        project_id=project_id,
        store_type="local",
        store_path="custom_processors.pkl",
        verbose=True
    )
    
    # Process all documents in the directory, including CSV and JSON files
    print(f"Processing documents in {documents_dir}...")
    embedder.process_directory(documents_dir)
    
    # Search for relevant documents
    query = "Enter your search query here"
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
