# Documetor

A powerful document embedding and semantic search library that converts PDF, Word, and other document formats into vector embeddings using Google's Vertex AI.

## Features

- **Multi-format Support**: Process PDF, Word documents, and more
- **Smart Text Chunking**: Intelligent text splitting with configurable chunk size and overlap
- **Vertex AI Integration**: High-quality embeddings using Google's Vertex AI models
- **Flexible Storage Options**: 
  - Local vector store for development/testing
  - Vertex Matching Engine for production-scale deployments
- **Semantic Search**: Find relevant document sections based on natural language queries
- **Progress Tracking**: Visual progress indicators during processing
- **Configurable Verbosity**: Control the amount of output during execution
- **Parallel Processing**: Process multiple documents concurrently for improved speed
- **Extensible Architecture**: Easily add support for custom document formats

## Project Structure

```
documentor/
├── __init__.py               # Package initialization
├── __main__.py               # Entry point for CLI
├── cli.py                    # Command line interface
├── config.py                 # Configuration settings
├── processors/               # Document processing modules
│   ├── __init__.py           # Processor initialization and registry
│   ├── base.py               # Base document processor class
│   ├── pdf.py                # PDF document processor
│   └── docx.py               # DOCX document processor
├── text/                     # Text processing modules
│   ├── __init__.py           # Text processing initialization
│   └── chunker.py            # Text chunking functionality
├── embedding/                # Embedding generation modules
│   ├── __init__.py           # Embedding initialization
│   └── vertex.py             # Vertex AI embeddings implementation
├── storage/                  # Vector storage modules
│   ├── __init__.py           # Storage initialization
│   ├── base.py               # Base vector store class
│   ├── local.py              # Local vector store implementation
│   └── vertex.py             # Vertex AI Matching Engine store
└── core/                     # Core functionality
    ├── __init__.py           # Core initialization
    ├── embedder.py           # Main document embedder class
    └── utils.py              # Utility functions

examples/                     # Example usage scripts
├── basic_usage.py            # Simple usage example
├── vertex_matching_engine.py # Advanced Vertex AI example
└── custom_processors.py      # Example of extending with custom processors

tests/                        # Test suite (not included in this version)
```

This modular structure allows for:
- Easier maintenance and understanding of codebase
- Clear separation of concerns
- Simplified extension with new processors or storage backends
- Better testability of individual components

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Installation

### Prerequisites

- Python 3.8+
- Google Cloud Platform account with Vertex AI API enabled
- Service account with appropriate permissions

### Setting Up Your Environment

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/documentor.git
   cd documentor
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Install the package in development mode:
   ```bash
   pip install -e .
   ```

5. Set up Google Cloud credentials (see [GOOGLE_SETUP.md](GOOGLE_SETUP.md) for detailed instructions):
   ```bash
   export GOOGLE_APPLICATION_CREDENTIALS="/path/to/your-service-account-key.json"
   ```

## Usage

### Command Line Interface

The package includes a robust command-line interface:

```bash
# Process documents in a directory
documentor process --project-id=your-gcp-project --directory=path/to/docs

# Search for documents
documentor search --query="customer onboarding process" --top-k=5 --store-path=documents.pkl

# Get information about a vector store
documentor info --store-path=documents.pkl
```

For help on specific commands:
```bash
documentor --help
documentor process --help
documentor search --help
```

### Python API

```python
from documentor import DocumentEmbedder

# Initialize the embedder
embedder = DocumentEmbedder(
    project_id="your-gcp-project-id",
    verbose=True  # Show detailed progress
)

# Process a directory of documents
embedder.process_directory("path/to/documents")

# Search for relevant content
results = embedder.search("What is the procedure for handling customer complaints?")

# Display results
for result in results:
    print(f"Source: {result['source']}")
    print(f"Similarity: {result['similarity']:.4f}")
    print(f"Text: {result['text']}\n")
```

### Storage Options

Choose the appropriate storage backend based on your needs:

```python
# Use local vector store (default)
embedder = DocumentEmbedder(
    project_id="your-gcp-project-id",
    store_type="local",
    store_path="embeddings.pkl"  # Save to disk
)

# Use Vertex Matching Engine (production)
embedder = DocumentEmbedder(
    project_id="your-gcp-project-id",
    store_type="vertex",
    index_name="my_document_index"
)
```

### Adding Custom Document Processors

Extend Documetor to support additional document formats:

```python
from documentor import DocumentProcessor
from documentor.processors import register_processor

class CSVProcessor(DocumentProcessor):
    """Custom processor for CSV files"""
    
    def extract_text(self, file_path):
        # Implementation for CSV extraction
        # ...
        return extracted_text

# Register the processor
register_processor('.csv', CSVProcessor)

# Now Documetor will automatically use the CSVProcessor for .csv files
```

See the `examples/custom_processors.py` file for complete examples.

## Configuration Options

### Text Chunking

```python
embedder = DocumentEmbedder(
    project_id="your-gcp-project-id",
    chunk_size=1500,       # Characters per chunk
    chunk_overlap=300,     # Overlap between chunks
    chunk_strategy="sentence"  # Split by sentence boundaries (options: hybrid, sentence, fixed)
)
```

### Processing Performance

```python
embedder = DocumentEmbedder(
    project_id="your-gcp-project-id",
    batch_size=10,     # Number of documents to process in a batch
    max_workers=8,     # Maximum number of parallel workers
)
```

### Verbosity and Logging

```python
# Silent mode (minimal output)
embedder = DocumentEmbedder(
    project_id="your-gcp-project-id",
    verbose=False,
    silent=True
)

# Debug mode (maximum output)
embedder = DocumentEmbedder(
    project_id="your-gcp-project-id",
    verbose=True,
    log_level="DEBUG"
)
```

## Troubleshooting

### Installation Issues

**Problem**: `ImportError: No module named 'documentor'`  
**Solution**: Make sure you've installed the package:
```bash
pip install -e .
```

**Problem**: Missing dependencies despite installation  
**Solution**: Try reinstalling the requirements:
```bash
pip install --force-reinstall -r requirements.txt
```

**Problem**: OCR functionality not working  
**Solution**: Install optional OCR dependencies:
```bash
pip install pytesseract pdf2image
```
On Linux, you may also need to install system packages:
```bash
sudo apt-get install -y tesseract-ocr poppler-utils
```

### Google Cloud Authentication

**Problem**: "Could not automatically determine credentials" error  
**Solution**: Check that your service account key file path is correctly set:
```bash
echo $GOOGLE_APPLICATION_CREDENTIALS
# Should output the path to your service account key file

# If not set or incorrect, set it:
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/your-service-account-key.json"
```

**Problem**: "Permission denied" errors  
**Solution**: Verify your service account has the required permissions (see [GOOGLE_SETUP.md](GOOGLE_SETUP.md)):
```bash
# Check roles assigned to your service account
gcloud projects get-iam-policy your-project-id --format=json | grep -A 5 your-service-account@
```

**Problem**: `google.api_core.exceptions.PermissionDenied`  
**Solution**: Your service account may be missing necessary roles. Ensure it has:
- Vertex AI User
- Storage Admin
- Vertex AI Matching Engine Admin

### Processing Issues

**Problem**: Empty or limited text extraction from PDFs  
**Solution**: Try enabling OCR for scanned documents:
```python
embedder = DocumentEmbedder(
    project_id="your-gcp-project-id",
    use_ocr=True  # Enable OCR for PDF processing
)
```

**Problem**: Memory errors with large documents  
**Solution**: Adjust the batch settings:
```python
embedder = DocumentEmbedder(
    project_id="your-gcp-project-id",
    batch_size=5,     # Process fewer documents at a time
    max_workers=2,    # Limit parallel processing
    chunk_size=500    # Use smaller chunks
)
```

**Problem**: "Matching Engine index not found" error  
**Solution**: Check if you need to create the index first:
```bash
# First run with create_if_not_exists=True
documentor process --project-id=your-project --directory=docs --store-type=vertex
```

### Search Quality Issues

**Problem**: Poor search results  
**Solution**: 
1. Try using different embedding models:
```python
embedder = DocumentEmbedder(
    project_id="your-gcp-project-id",
    embedding_model="textembedding-gecko-multilingual@latest"  # Different model
)
```

2. Adjust chunk settings to capture more context:
```python
embedder = DocumentEmbedder(
    project_id="your-gcp-project-id",
    chunk_size=2000,       # Larger chunks
    chunk_overlap=400,     # More overlap
    chunk_strategy="hybrid" # Try different chunking strategies
)
```

**Problem**: Search returning zero results  
**Solution**: Check if your vector store exists and contains data:
```bash
# For local stores:
documentor info --store-path=your-store.pkl

# For Vertex stores, check the index is properly deployed:
gcloud ai index-endpoints list --region=your-region
```

### Vertex AI Matching Engine Issues

**Problem**: "Failed to find the deployed index" errors  
**Solution**: The index deployment may take several minutes. Wait for it to complete or check the status:
```bash
gcloud ai index-endpoints list --region=your-region
```

**Problem**: Slow index updates  
**Solution**: Matching Engine has eventual consistency. After adding embeddings, wait a few minutes before searching:
```python
import time
embedder.process_directory("path/to/docs")
print("Waiting for index to update...")
time.sleep(60)  # Wait for index to update
results = embedder.search("your query")
```

## Common Questions

**Q: How much does Vertex AI usage cost?**  
A: Documetor uses Vertex AI services that incur costs. See [Google Cloud Pricing](https://cloud.google.com/vertex-ai/pricing) for details. Use the local storage option for development to minimize costs.

**Q: How many documents can I process?**  
A: The local vector store is limited by RAM and disk space. Vertex Matching Engine scales to millions of vectors, making it suitable for large document collections.

**Q: How do I backup my embeddings?**  
A: For local storage, just copy the pickle file. For Vertex Matching Engine, you can export the embeddings:
```python
from google.cloud import aiplatform
index = aiplatform.MatchingEngineIndex('your-index-id')
index.export_embeddings('gs://your-bucket/export-path')
```

## Advanced Usage

See the [examples](examples/) directory for more advanced usage patterns, including:
- Implementing custom document processors
- Using Vertex Matching Engine for production deployments
- Building search applications with Documetor

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Support

For questions, issues, or feature requests, please open an issue in the GitHub repository.
