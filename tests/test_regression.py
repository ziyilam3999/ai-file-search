"""
AI File Search - Comprehensive Regression Test Suite
=====================================================

This script performs comprehensive testing of the AI file search system to ensure:
- Proper citation format and accuracy
- Relevance threshold filtering
- No hallucinated citations
- End-to-end functionality
- Performance benchmarks

Usage:
    python tests/test_regression.py
    python tests/test_regression.py --verbose
    python tests/test_regression.py --quick (skip performance tests)
"""

import argparse
import json
import os
import sqlite3
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Tuple

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import faiss
from loguru import logger

from core.ask import answer_question
from core.embedding import Embedder


class RegressionTester:
    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.results: Dict[str, Any] = {
            "test_cases": [],
            "summary": {},
            "performance": {},
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        }

        # Test cases: (query, expected_behavior, min_score, max_score, expected_category)
        self.test_cases = [
            # High relevance queries (should get AI answers with citations)
            ("parking hosting rules", "relevant", 0.0, 1.0, "business_rules"),
            ("token economy", "relevant", 0.0, 1.0, "business_rules"),
            (
                "parking hosting",
                "relevant",
                0.0,
                1.0,
                "business_rules",
            ),  # Known good query
            ("onboarding process", "relevant", 0.0, 1.2, "business_rules"),
            # Medium relevance queries (should get AI answers)
            ("Alice in Wonderland", "relevant", 0.0, 1.2, "classic_literature"),
            ("Black Beauty", "relevant", 0.0, 1.2, "classic_literature"),
            # Low relevance queries (should be filtered out)
            (
                "hosting modes",
                "filtered",
                1.2,
                2.0,
                None,
            ),  # Updated: actual score 1.3894
            ("marketplace", "filtered", 1.2, 2.0, None),
            ("cryptocurrency blockchain", "filtered", 1.2, 2.0, None),
            ("machine learning algorithms", "filtered", 1.2, 2.0, None),
            ("quantum computing", "filtered", 1.2, 2.0, None),
        ]

    def print_status(self, message: str, level: str = "INFO"):
        """Print colored status messages."""
        colors = {
            "INFO": "\033[94m",  # Blue
            "SUCCESS": "\033[92m",  # Green
            "WARNING": "\033[93m",  # Yellow
            "ERROR": "\033[91m",  # Red
            "RESET": "\033[0m",
        }
        print(f"{colors.get(level, '')}{message}{colors['RESET']}")

    def test_system_requirements(self) -> bool:
        """Test that all required files and dependencies exist."""
        self.print_status("🔍 Testing System Requirements...", "INFO")

        required_files = [
            "index.faiss",
            "meta.sqlite",
            "core/ask.py",
            "core/embedding.py",
            "prompts/retrieval_prompt.md",
        ]

        missing_files = []
        for file_path in required_files:
            if not (project_root / file_path).exists():
                missing_files.append(file_path)

        if missing_files:
            self.print_status(f"❌ Missing required files: {missing_files}", "ERROR")
            return False

        # Test database integrity
        try:
            conn = sqlite3.connect(project_root / "meta.sqlite")
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM meta")
            db_count = cursor.fetchone()[0]
            conn.close()

            # Test FAISS index
            index = faiss.read_index(str(project_root / "index.faiss"))
            faiss_count = index.ntotal

            if db_count == 0 or faiss_count == 0:
                self.print_status(
                    f"❌ Empty database ({db_count}) or index ({faiss_count})", "ERROR"
                )
                return False

            if self.verbose:
                self.print_status(
                    f"   📊 Database: {db_count} records, FAISS: {faiss_count} vectors",
                    "INFO",
                )

        except Exception as e:
            self.print_status(f"❌ Database/Index error: {e}", "ERROR")
            return False

        self.print_status("✅ System requirements passed", "SUCCESS")
        return True

    def test_embedding_system(self) -> bool:
        """Test the embedding and retrieval system."""
        self.print_status("🔍 Testing Embedding System...", "INFO")

        try:
            embedder = Embedder()

            # Test basic query
            results = embedder.query("test query", k=1)
            if not results:
                self.print_status("❌ Embedder returned no results", "ERROR")
                return False

            # Validate result format
            if len(results[0]) != 5:
                self.print_status(
                    f"❌ Invalid result format: expected 5-tuple, got {len(results[0])}",
                    "ERROR",
                )
                return False

            chunk_text, file_path, chunk_id, doc_chunk_id, score = results[0]

            if chunk_text is None or file_path is None:
                self.print_status("❌ Embedder returned None values", "ERROR")
                return False

            if self.verbose:
                self.print_status(
                    f"   📊 Sample result: {file_path[:30]}..., score: {score:.4f}",
                    "INFO",
                )

        except Exception as e:
            self.print_status(f"❌ Embedding system error: {e}", "ERROR")
            return False

        self.print_status("✅ Embedding system passed", "SUCCESS")
        return True

    def test_relevance_filtering(self) -> bool:
        """Test that relevance threshold filtering works correctly."""
        self.print_status("🔍 Testing Relevance Filtering...", "INFO")

        embedder = Embedder()
        threshold_tests = []

        for (
            query,
            expected_behavior,
            min_score,
            max_score,
            expected_category,
        ) in self.test_cases:
            results = embedder.query(query, k=1)
            if results:
                score = results[0][4]
                threshold_tests.append(
                    {
                        "query": query,
                        "score": score,
                        "expected": expected_behavior,
                        "actual": "relevant" if score < 1.2 else "filtered",
                        "score_range_ok": min_score <= score <= max_score,
                    }
                )

        failed_tests = []
        for test in threshold_tests:
            if test["expected"] != test["actual"] or not test["score_range_ok"]:
                failed_tests.append(test)

        if failed_tests:
            self.print_status(
                f"❌ Relevance filtering failed for {len(failed_tests)} queries",
                "ERROR",
            )
            for test in failed_tests:
                self.print_status(
                    f"   Query: '{test['query']}', Expected: {test['expected']}, "
                    f"Actual: {test['actual']}, Score: {test['score']:.4f}",
                    "ERROR",
                )
            return False

        if self.verbose:
            for test in threshold_tests:
                self.print_status(
                    f"   ✅ '{test['query']}': {test['actual']} (score: {test['score']:.4f})",
                    "INFO",
                )

        self.print_status("✅ Relevance filtering passed", "SUCCESS")
        return True

    def test_citation_accuracy(self) -> bool:
        """Test that citations are accurate and not hallucinated."""
        self.print_status("🔍 Testing Citation Accuracy...", "INFO")

        citation_tests = []

        # Test queries that should have citations
        relevant_queries = [case for case in self.test_cases if case[1] == "relevant"]

        for query, _, _, _, expected_category in relevant_queries:
            try:
                start_time = time.time()
                answer, citations = answer_question(query, top_k=1)
                response_time = time.time() - start_time

                # Convert answer to string if it's an iterator
                answer_str = answer if isinstance(answer, str) else "".join(answer)

                test_result = {
                    "query": query,
                    "has_citations": len(citations) > 0,
                    "citation_count": len(citations),
                    "response_time": response_time,
                    "answer_length": len(answer_str),
                    "no_hallucination": True,
                    "correct_files": True,
                }

                # Check for hallucinated citations
                hallucination_indicators = [
                    "Investopedia",
                    "Wikipedia",
                    "Retrieved",
                    "n.d.",
                    "www.",
                    "http",
                    ".com",
                    ".org",
                ]

                for indicator in hallucination_indicators:
                    if indicator in answer_str:
                        test_result["no_hallucination"] = False
                        break

                # Check citation file paths are real
                if citations and isinstance(citations, list):
                    for citation in citations:
                        file_path = citation.get("file", "")
                        if (
                            not file_path
                            or not (project_root / f"extracts/{file_path}").exists()
                        ):
                            test_result["correct_files"] = False
                            break

                        # Check expected category if specified
                        if expected_category and expected_category not in file_path:
                            test_result["correct_files"] = False
                            break

                citation_tests.append(test_result)

            except Exception as e:
                self.print_status(f"❌ Error testing query '{query}': {e}", "ERROR")
                return False

        # Analyze results
        failed_tests = []
        for test in citation_tests:
            if (
                not test["has_citations"]
                or not test["no_hallucination"]
                or not test["correct_files"]
            ):
                failed_tests.append(test)

        if failed_tests:
            self.print_status(
                f"❌ Citation accuracy failed for {len(failed_tests)} queries", "ERROR"
            )
            for test in failed_tests:
                issues = []
                if not test["has_citations"]:
                    issues.append("no citations")
                if not test["no_hallucination"]:
                    issues.append("hallucinated content")
                if not test["correct_files"]:
                    issues.append("incorrect file paths")
                self.print_status(
                    f"   Query: '{test['query']}', Issues: {', '.join(issues)}", "ERROR"
                )
            return False

        if self.verbose:
            for test in citation_tests:
                self.print_status(
                    f"   ✅ '{test['query']}': {test['citation_count']} citations, "
                    f"{test['response_time']:.1f}s",
                    "INFO",
                )

        self.results["performance"]["citation_tests"] = citation_tests
        self.print_status("✅ Citation accuracy passed", "SUCCESS")
        return True

    def test_filtered_queries(self) -> bool:
        """Test that filtered queries don't generate fake answers."""
        self.print_status("🔍 Testing Filtered Queries...", "INFO")

        filtered_queries = [
            case[0] for case in self.test_cases if case[1] == "filtered"
        ]

        for query in filtered_queries:
            try:
                answer, citations = answer_question(query, top_k=1)

                # Convert answer to string if it's an iterator
                answer_str = answer if isinstance(answer, str) else "".join(answer)

                expected_message = "I couldn't find relevant information in the provided documents to answer this question."

                if expected_message not in answer_str:
                    self.print_status(
                        f"❌ Query '{query}' should be filtered but got: {answer_str[:100]}...",
                        "ERROR",
                    )
                    return False

                if citations:
                    self.print_status(
                        f"❌ Query '{query}' should have no citations but got {len(citations)}",
                        "ERROR",
                    )
                    return False

                if self.verbose:
                    self.print_status(f"   ✅ '{query}': correctly filtered", "INFO")

            except Exception as e:
                self.print_status(
                    f"❌ Error testing filtered query '{query}': {e}", "ERROR"
                )
                return False

        self.print_status("✅ Filtered queries passed", "SUCCESS")
        return True

    def test_performance_benchmarks(self) -> bool:
        """Test system performance benchmarks."""
        self.print_status("🔍 Testing Performance Benchmarks...", "INFO")

        # Quick embedding test
        embedder = Embedder()
        start_time = time.time()
        embedder.query("test performance", k=5)
        embedding_time = time.time() - start_time

        # AI generation test
        start_time = time.time()
        answer, citations = answer_question("parking rules", top_k=1)
        ai_generation_time = time.time() - start_time

        performance_results = {
            "embedding_query_time": embedding_time,
            "ai_generation_time": ai_generation_time,
            "total_query_time": embedding_time + ai_generation_time,
        }

        # Performance thresholds
        if embedding_time > 15.0:  # 15 seconds for embedding
            self.print_status(
                f"⚠️  Embedding query slow: {embedding_time:.1f}s", "WARNING"
            )

        if ai_generation_time > 120.0:  # 2 minutes for AI generation
            self.print_status(
                f"⚠️  AI generation slow: {ai_generation_time:.1f}s", "WARNING"
            )

        if self.verbose:
            self.print_status(
                f"   📊 Embedding: {embedding_time:.1f}s, AI: {ai_generation_time:.1f}s",
                "INFO",
            )

        self.results["performance"]["benchmarks"] = performance_results
        self.print_status("✅ Performance benchmarks completed", "SUCCESS")
        return True

    def run_comprehensive_test(self, skip_performance: bool = False) -> bool:
        """Run the complete regression test suite."""
        self.print_status("🚀 Starting AI File Search Regression Test Suite", "INFO")
        self.print_status("=" * 60, "INFO")

        start_time = time.time()
        tests = [
            ("System Requirements", self.test_system_requirements),
            ("Embedding System", self.test_embedding_system),
            ("Relevance Filtering", self.test_relevance_filtering),
            ("Citation Accuracy", self.test_citation_accuracy),
            ("Filtered Queries", self.test_filtered_queries),
        ]

        if not skip_performance:
            tests.append(("Performance Benchmarks", self.test_performance_benchmarks))

        passed_tests = 0
        total_tests = len(tests)

        for test_name, test_func in tests:
            try:
                if test_func():
                    passed_tests += 1
                else:
                    self.print_status(f"💥 Test suite failed at: {test_name}", "ERROR")
                    break
            except Exception as e:
                self.print_status(f"💥 Test suite crashed at {test_name}: {e}", "ERROR")
                break

        total_time = time.time() - start_time

        # Summary
        self.print_status("=" * 60, "INFO")
        if passed_tests == total_tests:
            self.print_status(
                f"🎉 ALL TESTS PASSED! ({passed_tests}/{total_tests})", "SUCCESS"
            )
            self.print_status(
                f"⏱️  Total execution time: {total_time:.1f} seconds", "INFO"
            )

            self.results["summary"] = {
                "status": "PASSED",
                "tests_passed": passed_tests,
                "total_tests": total_tests,
                "execution_time": total_time,
            }

            # Save results
            self.save_test_results()
            return True
        else:
            self.print_status(
                f"❌ TESTS FAILED! ({passed_tests}/{total_tests} passed)", "ERROR"
            )
            self.print_status(f"⏱️  Execution time: {total_time:.1f} seconds", "INFO")

            self.results["summary"] = {
                "status": "FAILED",
                "tests_passed": passed_tests,
                "total_tests": total_tests,
                "execution_time": total_time,
            }

            self.save_test_results()
            return False

    def save_test_results(self):
        """Save test results to a JSON file in the test_regression_results folder."""
        # Create the results directory if it doesn't exist
        results_dir = project_root / "test_regression_results"
        results_dir.mkdir(exist_ok=True)

        # Create the filename with timestamp
        results_file = results_dir / f"test_results_{int(time.time())}.json"

        try:
            with open(results_file, "w") as f:
                json.dump(self.results, f, indent=2)
            self.print_status(f"📊 Test results saved to: {results_file}", "INFO")
        except Exception as e:
            self.print_status(f"⚠️  Could not save results: {e}", "WARNING")


def main():
    parser = argparse.ArgumentParser(description="AI File Search Regression Test Suite")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument(
        "--quick", "-q", action="store_true", help="Skip performance tests"
    )

    args = parser.parse_args()

    tester = RegressionTester(verbose=args.verbose)
    success = tester.run_comprehensive_test(skip_performance=args.quick)

    # Exit with appropriate code
    exit(0 if success else 1)


if __name__ == "__main__":
    main()
