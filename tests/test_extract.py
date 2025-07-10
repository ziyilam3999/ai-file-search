"""Tests Extractor against 20 sample files."""

import sys
from pathlib import Path

import pytest

from core.extract import Extractor

sys.path.insert(0, str(Path(__file__).parent.parent))

FILES = list(Path("sample_docs").iterdir())[:20]


@pytest.mark.parametrize("file", FILES)
def test_extract_nonempty(file: Path):
    txt = Extractor().run(file)
    assert len(txt) > 100
