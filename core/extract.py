"""⚙️ core/extract.py
-------------------
Purpose : Convert PDF, DOCX, and TXT files to plain UTF-8 text.
Inputs  : pathlib.Path object
Outputs : str (clean text)

Example :
    >>> Extractor().run(Path('invoice.pdf'))
"""

from pathlib import Path  # noqa: F401


class Extractor:
    """TODO(copilot): implement PDF and DOCX extraction methods."""
