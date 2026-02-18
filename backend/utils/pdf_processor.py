"""
File text extraction utility.
Supports PDF, TXT, and DOCX files.
"""
import logging
from pathlib import Path
from typing import Optional
import PyPDF2
import pdfplumber
try:
    import docx
except ImportError:
    docx = None

logger = logging.getLogger(__name__)


class FileProcessor:
    """Handles text extraction from various file types."""
    
    @staticmethod
    def extract_text_pypdf2(pdf_path: Path) -> str:
        """Extract text using PyPDF2."""
        try:
            text_parts = []
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                for page in pdf_reader.pages:
                    text = page.extract_text()
                    if text:
                        text_parts.append(text)
            
            return "\n\n".join(text_parts)
        
        except Exception as e:
            logger.error(f"PyPDF2 extraction failed: {e}")
            return ""
    
    @staticmethod
    def extract_text_pdfplumber(pdf_path: Path) -> str:
        """Extract text using pdfplumber."""
        try:
            text_parts = []
            with pdfplumber.open(pdf_path) as pdf:
                for page in pdf.pages:
                    text = page.extract_text()
                    if text:
                        text_parts.append(text)
            
            return "\n\n".join(text_parts)
        
        except Exception as e:
            logger.error(f"pdfplumber extraction failed: {e}")
            return ""
            
    @staticmethod
    def extract_text_docx(docx_path: Path) -> str:
        """Extract text from DOCX file."""
        if not docx:
            logger.error("python-docx not installed. Cannot process DOCX.")
            return "Error: python-docx not installed on server."
            
        try:
            doc = docx.Document(docx_path)
            return "\n".join([para.text for para in doc.paragraphs])
        except Exception as e:
            logger.error(f"DOCX extraction failed: {e}")
            return ""

    @staticmethod
    def extract_text_txt(txt_path: Path) -> str:
        """Extract text from TXT file."""
        try:
            return txt_path.read_text(encoding='utf-8', errors='replace')
        except Exception as e:
            logger.error(f"TXT extraction failed: {e}")
            return ""

    @classmethod
    def extract_text(cls, file_path: Path) -> Optional[str]:
        """
        Extract text from file based on extension.
        """
        if not file_path.exists():
            logger.error(f"File not found: {file_path}")
            return None
            
        extension = file_path.suffix.lower()
        
        if extension == '.pdf':
            text = cls.extract_text_pdfplumber(file_path)
            if not text or len(text.strip()) < 50:
                text = cls.extract_text_pypdf2(file_path)
        elif extension == '.docx':
            text = cls.extract_text_docx(file_path)
        elif extension == '.txt':
            text = cls.extract_text_txt(file_path)
        else:
            logger.warning(f"Unsupported file type: {extension}")
            return None
        
        if not text or len(text.strip()) < 10:
            logger.warning(f"No meaningful text extracted from: {file_path}")
            return None
        
        logger.info(f"Extracted {len(text)} characters from {extension} file")
        return text.strip()


# Create global instance
pdf_processor = FileProcessor() # Keep name for backwards compatibility
file_processor = pdf_processor
