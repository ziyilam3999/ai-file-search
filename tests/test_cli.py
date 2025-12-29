"""Unit tests for cli.py module

Tests CLI functions: format_answer, ask_question, main argument parsing
Uses mocking to avoid LLM loading and file I/O
"""

import io
import sys
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Mock heavy dependencies BEFORE importing cli
_MOCK_MODULES = [
    "faiss",
    "llama_cpp",
    "sentence_transformers",
    "core.embedding",
    "core.ask",
    "core.llm",
    "core.index_manager",
    "smart_watcher",
]

for module_name in _MOCK_MODULES:
    if module_name not in sys.modules:
        sys.modules[module_name] = MagicMock()

from cli import (
    ask_question,
    format_answer,
    interactive_mode,
    main,
    print_banner,
    print_help,
)


class TestFormatAnswer:
    """Test answer and citation formatting."""

    def test_format_answer_basic(self):
        """Test basic answer with citations."""
        answer = "Alice is a fictional character from Alice in Wonderland."
        citations = [
            {
                "id": 1,
                "file": "alice.txt",
                "page": 1,
                "score": 0.95,
                "chunk": "Alice is a girl...",
            }
        ]

        result = format_answer(answer, citations, show_citations=True, verbose=False)

        assert "ANSWER:" in result
        assert answer in result
        assert "CITATIONS:" in result
        assert "[1] alice.txt, page 1" in result

    def test_format_answer_no_citations(self):
        """Test answer without citations displayed."""
        answer = "No information found."
        citations = []

        result = format_answer(answer, citations, show_citations=True, verbose=False)

        assert "ANSWER:" in result
        assert answer in result
        assert "CITATIONS:" not in result

    def test_format_answer_hide_citations(self):
        """Test answer with show_citations=False."""
        answer = "Test answer."
        citations = [
            {"id": 1, "file": "test.txt", "page": 1, "score": 0.9, "chunk": ""}
        ]

        result = format_answer(answer, citations, show_citations=False, verbose=False)

        assert "ANSWER:" in result
        assert answer in result
        assert "CITATIONS:" not in result

    def test_format_answer_verbose_mode(self):
        """Test verbose mode with detailed citation info."""
        answer = "Alice is a character."
        citations = [
            {
                "id": 1,
                "file": "alice.txt",
                "page": 1,
                "score": 0.95,
                "chunk": "Alice in Wonderland is a classic...",
            }
        ]

        result = format_answer(answer, citations, show_citations=True, verbose=True)

        assert "ANSWER:" in result
        assert "[1] alice.txt, page 1" in result
        assert "Score: 0.950" in result
        assert "Preview:" in result
        assert "Alice in Wonderland" in result

    def test_format_answer_score_bar_visualization(self):
        """Test score bar rendering in verbose mode."""
        citations = [
            {"id": 1, "file": "test.txt", "page": 1, "score": 0.8, "chunk": "test"},
            {
                "id": 2,
                "file": "test.txt",
                "page": 2,
                "score": 0.3,
                "chunk": "test",
            },
        ]

        result = format_answer("Answer", citations, show_citations=True, verbose=True)

        # High score should have more = signs
        assert "========" in result
        # Low score should have more - signs
        assert "---" in result

    def test_format_answer_multiple_citations(self):
        """Test formatting with multiple citations."""
        answer = "Information from multiple sources."
        citations = [
            {"id": 1, "file": "file1.txt", "page": 1, "score": 0.9, "chunk": ""},
            {"id": 2, "file": "file2.txt", "page": 2, "score": 0.85, "chunk": ""},
            {"id": 3, "file": "file3.txt", "page": 3, "score": 0.8, "chunk": ""},
        ]

        result = format_answer(answer, citations, show_citations=True, verbose=False)

        for i in range(1, 4):
            assert f"[{i}]" in result


class TestAskQuestion:
    """Test ask_question function."""

    @patch("cli.answer_question")
    @patch("pathlib.Path.exists")
    def test_ask_question_success(self, mock_exists, mock_answer):
        """Test successful question answering."""
        mock_exists.return_value = True
        mock_answer.return_value = (
            "Test answer",
            [{"id": 1, "file": "test.txt", "page": 1, "score": 0.9, "chunk": ""}],
        )

        with patch("builtins.print") as mock_print:
            ask_question("Test question?", verbose=False, show_citations=True)

            # Verify answer_question was called
            mock_answer.assert_called_once_with("Test question?")

            # Verify output was printed
            calls = [str(c) for c in mock_print.call_args_list]
            assert any("SEARCHING" in str(c) for c in calls)
            assert any("ANSWER:" in str(c) for c in calls)

    @patch("pathlib.Path.exists")
    def test_ask_question_missing_index(self, mock_exists):
        """Test error when index doesn't exist."""
        mock_exists.return_value = False

        with patch("builtins.print") as mock_print:
            ask_question("Test question?")

            calls = [str(c) for c in mock_print.call_args_list]
            assert any("No search index found" in str(c) for c in calls)

    @patch("cli.answer_question")
    @patch("pathlib.Path.exists")
    def test_ask_question_verbose_mode(self, mock_exists, mock_answer):
        """Test verbose mode shows additional statistics."""
        mock_exists.return_value = True
        mock_answer.return_value = (
            "Answer",
            [
                {"id": 1, "file": "file1.txt", "page": 1, "score": 0.9, "chunk": ""},
                {
                    "id": 2,
                    "file": "file2.txt",
                    "page": 2,
                    "score": 0.85,
                    "chunk": "",
                },
            ],
        )

        with patch("builtins.print") as mock_print:
            ask_question("Test?", verbose=True, show_citations=True)

            calls = [str(c) for c in mock_print.call_args_list]
            assert any("Average relevance score" in str(c) for c in calls)

    @patch("cli.answer_question")
    @patch("pathlib.Path.exists")
    def test_ask_question_exception_handling(self, mock_exists, mock_answer):
        """Test exception is caught and displayed."""
        mock_exists.return_value = True
        mock_answer.side_effect = Exception("Test error")

        with patch("builtins.print") as mock_print:
            ask_question("Test?", verbose=False)

            calls = [str(c) for c in mock_print.call_args_list]
            assert any("ERROR:" in str(c) for c in calls)


class TestMainParsing:
    """Test main() CLI argument parsing."""

    def test_main_help_flag(self):
        """Test --help flag shows usage."""
        with patch("sys.argv", ["cli.py", "--help"]):
            with patch("builtins.print") as mock_print:
                main()

                calls = [str(c) for c in mock_print.call_args_list]
                assert any("USAGE:" in str(c) for c in calls)

    def test_main_no_args_shows_help(self):
        """Test no arguments shows help."""
        with patch("sys.argv", ["cli.py"]):
            with patch("builtins.print") as mock_print:
                main()

                calls = [str(c) for c in mock_print.call_args_list]
                assert any("USAGE:" in str(c) for c in calls)

    @patch("cli.ask_question")
    def test_main_single_question(self, mock_ask):
        """Test single question argument."""
        with patch("sys.argv", ["cli.py", "Who is Alice?"]):
            main()

            mock_ask.assert_called_once()
            args = mock_ask.call_args[0]
            assert "Alice" in args[0]

    @patch("cli.interactive_mode")
    def test_main_interactive_flag(self, mock_interactive):
        """Test --interactive flag."""
        with patch("sys.argv", ["cli.py", "--interactive"]):
            main()

            mock_interactive.assert_called_once()

    @patch("cli.ask_question")
    def test_main_no_llm_flag(self, mock_ask):
        """Test --no-llm flag disables LLM."""
        with patch("sys.argv", ["cli.py", "--no-llm", "Test?"]):
            main()

            # Verify use_llm=False is passed
            kwargs = mock_ask.call_args[1]
            assert kwargs.get("use_llm") is False or (
                len(mock_ask.call_args[0]) > 3 and mock_ask.call_args[0][3] is False
            )

    @patch("cli.ask_question")
    def test_main_verbose_flag(self, mock_ask):
        """Test --verbose flag."""
        with patch("sys.argv", ["cli.py", "--verbose", "Test?"]):
            main()

            # Verify verbose=True is passed
            kwargs = mock_ask.call_args[1]
            assert kwargs.get("verbose") is True or (
                len(mock_ask.call_args[0]) > 1 and mock_ask.call_args[0][1] is True
            )

    @patch("cli.ask_question")
    def test_main_citations_flag(self, mock_ask):
        """Test --citations flag."""
        with patch("sys.argv", ["cli.py", "--citations", "Test?"]):
            main()

            # Verify show_citations=True is passed
            kwargs = mock_ask.call_args[1]
            assert kwargs.get("show_citations") is True or (
                len(mock_ask.call_args[0]) > 2 and mock_ask.call_args[0][2] is True
            )


class TestPrintFunctions:
    """Test banner and help printing."""

    def test_print_banner_output(self):
        """Test banner contains expected text."""
        with patch("builtins.print") as mock_print:
            print_banner()

            calls = [str(c) for c in mock_print.call_args_list]
            output = "\n".join(calls)
            assert "AI File Search" in output

    def test_print_help_output(self):
        """Test help contains expected sections."""
        with patch("builtins.print") as mock_print:
            print_help()

            calls = [str(c) for c in mock_print.call_args_list]
            output = "\n".join(calls)
            assert "USAGE:" in output
            assert "--interactive" in output
            assert "--verbose" in output
            assert "--no-llm" in output
            assert "EXAMPLES:" in output
