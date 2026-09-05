import pytest
from app.services.document_service import DocumentService

def test_extract_pages_unsupported():
    """Verify that unsupported extensions are rejected."""
    with pytest.raises(ValueError, match="Only PDF and DOCX files are supported"):
        DocumentService.extract_pages(b"dummy bytes", "resume.txt")

def test_extract_pages_docx_empty():
    """Verify that parsing an invalid DOCX raises an exception."""
    with pytest.raises(ValueError, match="Failed to parse DOCX"):
        DocumentService.extract_pages(b"invalid docx data", "resume.docx")
