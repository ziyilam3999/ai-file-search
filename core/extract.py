"""⚙️  core/extract.py
Purpose : Convert PDF, DOCX, TXT to plain UTF-8.
Inputs  : pathlib.Path
Outputs : str
"""

from pathlib import Path

from loguru import logger

PDF_EXT = ".pdf"
DOCX_EXT = ".docx"


class Extractor:
    """TODO(copilot): implement _extract_pdf, _extract_docx, run."""

    def _extract_pdf(self, path: Path) -> str:
        """Extract text from PDF file."""
        try:
            from pdfminer.high_level import extract_text
        except ImportError:
            logger.error(
                "pdfminer.six is not installed. "
                "Please install it to extract PDF files."
            )
            return ""

        try:
            text = extract_text(str(path))
        except Exception as e:
            logger.error(f"Failed to extract PDF: {e}")
            return ""
        return text or ""

    def _extract_docx(self, path: Path) -> str:
        """Extract text from DOCX file."""
        try:
            import docx
        except ImportError:
            logger.error(
                "docx is not installed. "
                "Please install it to extract DOCX files."  # noqa: E501
            )
            return ""

        doc = docx.Document(path)
        text = ""
        for para in doc.paragraphs:
            text += para.text + "\n"
        return text

    def run(self, path: Path) -> str:
        """Run the extractor based on file type."""
        if not path.exists():
            logger.error(f"File {path} does not exist.")
            return ""

        if path.suffix.lower() == PDF_EXT:
            return self._extract_pdf(path)
        elif path.suffix.lower() == DOCX_EXT:
            return self._extract_docx(path)
        elif path.suffix.lower() == ".txt":
            return path.read_text(encoding="utf-8")
        else:
            logger.error(f"Unsupported file type: {path.suffix}")
            return ""
