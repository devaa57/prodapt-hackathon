"""
PDF parsing service — page-aware text extraction.

Uses PyMuPDF (pymupdf) to extract text from PDF files while
preserving page boundaries so that downstream evidence citations
can include page numbers.
"""

from __future__ import annotations

import logging
from typing import Optional

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

try:
    import pymupdf
    HAS_PYMUPDF = True
except ImportError:
    try:
        import fitz as pymupdf  # type: ignore[no-redef]
        HAS_PYMUPDF = True
    except ImportError:
        pymupdf = None  # type: ignore[assignment]
        HAS_PYMUPDF = False


class PageText(BaseModel):
    """Text content of a single PDF page."""
    page: int = Field(ge=1, description="1-indexed page number")
    text: str = Field(description="Extracted text from this page")


class PDFService:
    """Extract text from PDF files with page-number awareness."""

    @staticmethod
    def is_available() -> bool:
        return HAS_PYMUPDF

    @staticmethod
    def extract_pages(file_bytes: bytes) -> list[PageText]:
        """
        Extract text from each page of a PDF.

        Args:
            file_bytes: Raw PDF file content.

        Returns:
            List of PageText objects, one per page.

        Raises:
            RuntimeError: If PyMuPDF is not installed.
            ValueError: If the file cannot be parsed.
        """
        if not HAS_PYMUPDF:
            raise RuntimeError(
                "PyMuPDF is not installed. "
                "Install with: pip install pymupdf"
            )

        try:
            doc = pymupdf.open(stream=file_bytes, filetype="pdf")
        except Exception as exc:
            raise ValueError(f"Failed to parse PDF: {exc}") from exc

        pages: list[PageText] = []
        for page_num in range(len(doc)):
            page = doc[page_num]
            text = page.get_text().strip()
            if text:
                pages.append(PageText(page=page_num + 1, text=text))

        doc.close()

        if not pages:
            raise ValueError("PDF contains no extractable text.")

        logger.info("Extracted %d pages from PDF", len(pages))
        return pages

    @staticmethod
    def pages_to_text(pages: list[PageText]) -> str:
        """Join all pages into a single text string."""
        return "\n\n".join(p.text for p in pages)
