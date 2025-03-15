"""
PDF document processor.
"""

import PyPDF2
from documentor.config import logger
from documentor.processors.base import DocumentProcessor


class PDFProcessor(DocumentProcessor):
    """Processor for PDF files"""
    
    def __init__(self, use_ocr: bool = False):
        """
        Initialize PDF processor
        
        Args:
            use_ocr: Whether to use OCR for text extraction
        """
        self.use_ocr = use_ocr
    
    def extract_text(self, file_path: str) -> str:
        """
        Extract text from a PDF file
        
        Args:
            file_path: Path to the PDF file
            
        Returns:
            Extracted text from the PDF
        """
        text = ""
        try:
            with open(file_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                for page_num in range(len(reader.pages)):
                    page_text = reader.pages[page_num].extract_text() or ""
                    text += page_text
            
            # If text is empty or OCR is requested, try OCR
            if (not text.strip() or self.use_ocr) and self.use_ocr:
                text = self._extract_with_ocr(file_path)
        except Exception as e:
            logger.error(f"Error extracting text from PDF {file_path}: {str(e)}")
        
        return text
    
    def _extract_with_ocr(self, file_path: str) -> str:
        """
        Extract text from PDF using OCR
        
        Args:
            file_path: Path to the PDF file
            
        Returns:
            Extracted text using OCR
        """
        logger.info(f"Using OCR for {file_path}")
        try:
            # Try to import the necessary libraries
            try:
                import pytesseract
                from pdf2image import convert_from_path
            except ImportError:
                logger.warning(
                    "OCR requested but pytesseract or pdf2image not installed. "
                    "Install with: pip install pytesseract pdf2image"
                )
                return ""
            
            # Convert PDF to images
            images = convert_from_path(file_path)
            
            # Extract text from each image
            ocr_text = []
            for img in images:
                ocr_text.append(pytesseract.image_to_string(img))
            
            return "\n".join(ocr_text)
        except Exception as e:
            logger.error(f"Error performing OCR on {file_path}: {str(e)}")
            return ""
