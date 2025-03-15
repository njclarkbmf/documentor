"""
Configuration settings for the Documetor package.
"""

import os
import logging
from rich.logging import RichHandler

# Logging configuration
FORMAT = "%(message)s"
logging.basicConfig(
    level=logging.INFO,
    format=FORMAT,
    datefmt="[%X]",
    handlers=[RichHandler(rich_tracebacks=True)]
)

# Create logger
logger = logging.getLogger("documetor")

# Default values
DEFAULT_CHUNK_SIZE = 1000
DEFAULT_CHUNK_OVERLAP = 200
DEFAULT_BATCH_SIZE = 5
DEFAULT_MAX_WORKERS = 4
DEFAULT_LOCATION = "us-central1"
DEFAULT_EMBEDDING_MODEL = "textembedding-gecko@latest"
DEFAULT_CHUNK_STRATEGY = "hybrid"

# Context manager for "no operation" when progress is disabled
class NullContext:
    """Context manager that does nothing."""
    def __enter__(self): return None
    def __exit__(self, *excinfo): pass

# Check if running in a Google Cloud environment
def is_running_on_gcp():
    """Check if the code is running on Google Cloud Platform."""
    try:
        import google.auth
        _, project = google.auth.default()
        return project is not None
    except Exception:
        return False

# Get project ID from environment or default credentials
def get_default_project_id():
    """Get the default Google Cloud project ID."""
    # Check environment variable first
    project_id = os.environ.get("GOOGLE_CLOUD_PROJECT")
    if project_id:
        return project_id
    
    # Try to get from default credentials
    try:
        import google.auth
        _, project_id = google.auth.default()
        return project_id
    except Exception:
        return None
