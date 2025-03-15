"""
Document processors for extracting text from various file formats.
"""

import os
from typing import Dict, Type

from documetor.processors.base import DocumentProcessor
from documetor.processors.pdf import PDFProcessor
from documetor.processors.docx import DocxProcessor

# Register built-in processors
_PROCESSORS: Dict[str, Type[DocumentProcessor]] = {
    '.pdf': PDFProcessor,
    '.docx': DocxProcessor,
    '.doc': DocxProcessor,
}

def register_processor(extension: str, processor_class: Type[DocumentProcessor]) -> None:
    """
    Register a processor for a file extension
    
    Args:
        extension: File extension (e.g., '.pdf')
        processor_class: Document processor class
    """
    _PROCESSORS[extension.lower()] = processor_class

def get_processor_for_file(file_path: str) -> DocumentProcessor:
    """
    Get the appropriate processor for a file
    
    Args:
        file_path: Path to the file
        
    Returns:
        DocumentProcessor instance for the file type
        
    Raises:
        ValueError: If no processor is found for the file extension
    """
    ext = os.path.splitext(file_path)[1].lower()
    
    if ext in _PROCESSORS:
        return _PROCESSORS[ext]()
    
    supported = ', '.join(_PROCESSORS.keys())
    raise ValueError(f"Unsupported file type: {ext}. Supported types: {supported}")

def get_supported_extensions() -> list:
    """
    Get a list of supported file extensions
    
    Returns:
        List of supported file extensions
    """
    return list(_PROCESSORS.keys())

__all__ = [
    'DocumentProcessor',
    'PDFProcessor',
    'DocxProcessor',
    'register_processor',
    'get_processor_for_file',
    'get_supported_extensions',
]
