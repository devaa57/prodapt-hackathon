from io import BytesIO

from app.services.pdf_service import PageText, PDFService

try:
    from docx import Document
    HAS_DOCX = True
except ImportError:
    HAS_DOCX = False


class DocumentService:
    """General document parsing abstraction covering PDF and DOCX."""

    @staticmethod
    def extract_pages(file_bytes: bytes, filename: str) -> list[PageText]:
        """
        Extract text from PDF or DOCX and return as a list of PageText.
        """
        extension = filename.lower().split(".")[-1]

        if extension == "pdf":
            return PDFService.extract_pages(file_bytes)

        if extension == "docx":
            return DocumentService._parse_docx(file_bytes)

        raise ValueError("Only PDF and DOCX files are supported.")

    @staticmethod
    def _parse_docx(file_bytes: bytes) -> list[PageText]:
        """
        Parse a DOCX file.
        DOCX doesn't have a reliable concept of 'pages' when extracting raw text,
        so we treat the entire document as a single long page (page=1).
        """
        if not HAS_DOCX:
            raise RuntimeError(
                "python-docx is not installed. "
                "Install with: pip install python-docx"
            )

        try:
            document = Document(BytesIO(file_bytes))
        except Exception as exc:
            raise ValueError(f"Failed to parse DOCX: {exc}") from exc

        paragraphs = []
        for paragraph in document.paragraphs:
            text = paragraph.text.strip()
            if text:
                paragraphs.append(text)

        full_text = "\n".join(paragraphs).strip()

        if not full_text:
            raise ValueError("DOCX contains no extractable text.")

        # Treat the entire DOCX as a single page for the retrieval layer
        return [PageText(page=1, text=full_text)]
