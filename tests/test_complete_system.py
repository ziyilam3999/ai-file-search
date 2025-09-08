#!/usr/bin/env python3
"""
Comprehensive Test Suite for AI File Search Zero-Config Smart Watcher System

This test verifies all major components and functionality:
- Complete setup script execution
- Smart watcher process management
- Document auto-discovery system
- Configuration synchronization
- File search and citation functionality
- UI integration readiness
"""

import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

import yaml

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))


class ComprehensiveSystemTest:
    def __init__(self):
        self.test_results = []
        self.errors = []
        self.base_dir = Path(__file__).parent.parent  # Project root directory
        self.temp_test_dir = None

    def log_test(self, test_name, success, message=""):
        """Log test results"""
        status = "PASS" if success else "FAIL"
        self.test_results.append((test_name, success, message))
        print(f"[{status}]: {test_name}")
        if message:
            print(f"   {message}")
        if not success:
            self.errors.append(f"{test_name}: {message}")

    def test_complete_setup_script(self):
        """Test the complete_setup.py script execution"""
        try:
            # Test 1: Script runs without errors
            result = subprocess.run(
                [sys.executable, "complete_setup.py"],
                capture_output=True,
                text=True,
                timeout=60,
                cwd=self.base_dir,
            )
            success = result.returncode == 0
            message = (
                "Script executed successfully"
                if success
                else f"Exit code: {result.returncode}, Error: {result.stderr[:200]}"
            )
            self.log_test("Complete Setup Script Execution", success, message)

            # Test 2: Guide files are created
            quick_start_exists = (self.base_dir / "QUICK_START.md").exists()
            complete_guide_exists = (self.base_dir / "COMPLETE_USER_GUIDE.md").exists()
            self.log_test(
                "Guide Files Created", quick_start_exists and complete_guide_exists
            )

            # Test 3: Guide content is correct (no emoji characters)
            if complete_guide_exists:
                with open(
                    self.base_dir / "COMPLETE_USER_GUIDE.md", "r", encoding="utf-8"
                ) as f:
                    content = f.read()
                    has_streamlit_cmd = "python -m streamlit run ui/app.py" in content
                    has_no_config_yml = "config.yml" not in content
                    has_smart_watcher_cmds = "python smart_watcher.py start" in content

                    content_correct = (
                        has_streamlit_cmd
                        and has_no_config_yml
                        and has_smart_watcher_cmds
                    )
                    details = f"Streamlit: {has_streamlit_cmd}, No config.yml: {has_no_config_yml}, Smart watcher: {has_smart_watcher_cmds}"
                    self.log_test("Guide Content Correctness", content_correct, details)

        except subprocess.TimeoutExpired:
            self.log_test(
                "Complete Setup Script Execution",
                False,
                "Script timed out after 60 seconds",
            )
        except Exception as e:
            self.log_test("Complete Setup Script Execution", False, str(e))

    def test_smart_watcher_functionality(self):
        """Test smart watcher process management"""
        try:
            # Test 1: Check current status first
            result = subprocess.run(
                [sys.executable, "smart_watcher.py", "status"],
                capture_output=True,
                text=True,
                timeout=10,
                cwd=self.base_dir,
            )
            status_works = result.returncode == 0
            was_running = (
                "RUNNING" in result.stdout or "already running" in result.stdout.lower()
            )
            status_message = f"Status check successful, watcher {'running' if was_running else 'stopped'}"
            self.log_test("Smart Watcher Status Command", status_works, status_message)

            if was_running:
                # If already running, test stop and restart cycle
                # Test 2: Stop the running watcher
                result = subprocess.run(
                    [sys.executable, "smart_watcher.py", "stop"],
                    capture_output=True,
                    text=True,
                    timeout=10,
                    cwd=self.base_dir,
                )
                stop_success = result.returncode == 0
                stop_message = (
                    "Successfully stopped running watcher"
                    if stop_success
                    else f"Failed to stop: {result.stderr[:100]}"
                )
                self.log_test("Smart Watcher Stop Command", stop_success, stop_message)

                # Test 3: Verify it's stopped
                time.sleep(2)
                result = subprocess.run(
                    [sys.executable, "smart_watcher.py", "status"],
                    capture_output=True,
                    text=True,
                    timeout=10,
                    cwd=self.base_dir,
                )
                is_stopped = (
                    "STOPPED" in result.stdout or "not running" in result.stdout.lower()
                )
                stopped_message = (
                    "Confirmed watcher is stopped"
                    if is_stopped
                    else "Watcher still running after stop command"
                )
                self.log_test(
                    "Smart Watcher Stopped Status", is_stopped, stopped_message
                )

                # Test 4: Start watcher after stopping
                result = subprocess.run(
                    [sys.executable, "smart_watcher.py", "start"],
                    capture_output=True,
                    text=True,
                    timeout=30,
                    cwd=self.base_dir,
                )
                start_success = result.returncode == 0
                start_message = (
                    "Successfully started watcher"
                    if start_success
                    else f"Failed to start: {result.stderr[:100]}"
                )
                self.log_test(
                    "Smart Watcher Start After Stop", start_success, start_message
                )
            else:
                # If not running, just test start
                # Test 4: Start watcher when stopped
                result = subprocess.run(
                    [sys.executable, "smart_watcher.py", "start"],
                    capture_output=True,
                    text=True,
                    timeout=30,
                    cwd=self.base_dir,
                )
                start_success = result.returncode == 0
                start_message = (
                    "Successfully started watcher"
                    if start_success
                    else f"Failed to start: {result.stderr[:100]}"
                )
                self.log_test(
                    "Smart Watcher Start When Stopped", start_success, start_message
                )

            # Test 5: Final verification that it's running
            time.sleep(2)
            result = subprocess.run(
                [sys.executable, "smart_watcher.py", "status"],
                capture_output=True,
                text=True,
                timeout=10,
                cwd=self.base_dir,
            )
            is_running = (
                "RUNNING" in result.stdout or "already running" in result.stdout.lower()
            )
            final_message = (
                "Confirmed watcher is running"
                if is_running
                else "Watcher is not running after start command"
            )
            self.log_test("Smart Watcher Final Status Check", is_running, final_message)

        except subprocess.TimeoutExpired:
            self.log_test("Smart Watcher Functionality", False, "Commands timed out")
        except Exception as e:
            self.log_test("Smart Watcher Functionality", False, str(e))

    def test_document_discovery_system(self):
        """Test document auto-discovery and configuration sync"""
        try:
            # Test 1: Import and run discovery
            from switch_documents import (
                discover_document_categories,
                sync_config_with_filesystem,
            )

            categories = discover_document_categories()
            discovery_works = len(categories) > 0
            self.log_test(
                "Document Category Discovery",
                discovery_works,
                f"Found {len(categories)} categories",
            )

            # Test 2: Configuration synchronization
            config = sync_config_with_filesystem()
            sync_works = (
                "document_categories" in config
                and len(config["document_categories"]) > 0
            )
            enabled_count = sum(
                1
                for cat in config["document_categories"].values()
                if cat.get("enabled", False)
            )
            self.log_test(
                "Configuration Synchronization",
                sync_works,
                f"Synced {enabled_count} enabled categories",
            )

            # Test 3: All discovered categories are enabled by default
            all_enabled = all(
                cat.get("enabled", False)
                for cat in config["document_categories"].values()
            )
            self.log_test("Default Enable All Categories", all_enabled)

        except ImportError as e:
            self.log_test("Document Discovery System", False, f"Import error: {e}")
        except Exception as e:
            self.log_test("Document Discovery System", False, str(e))

    def test_file_structure_and_dependencies(self):
        """Test file structure and required dependencies"""
        try:
            # Test 1: Core files exist
            core_files = [
                "smart_watcher.py",
                "switch_documents.py",
                "complete_setup.py",
                "core/embedding.py",
                "core/ask.py",
                "ui/app.py",
            ]
            missing_files = [f for f in core_files if not (self.base_dir / f).exists()]
            self.log_test(
                "Core Files Exist",
                len(missing_files) == 0,
                f"Missing: {missing_files}" if missing_files else "All files present",
            )

            # Test 2: Required directories exist
            required_dirs = ["ai_search_docs", "extracts", "logs", "prompts"]
            missing_dirs = [
                d for d in required_dirs if not (self.base_dir / d).exists()
            ]
            self.log_test(
                "Required Directories Exist",
                len(missing_dirs) == 0,
                (
                    f"Missing: {missing_dirs}"
                    if missing_dirs
                    else "All directories present"
                ),
            )

            # Test 3: Python dependencies are importable
            dependencies = ["psutil", "yaml", "sentence_transformers", "faiss"]
            failed_imports = []
            for dep in dependencies:
                try:
                    if dep == "yaml":
                        import yaml
                    elif dep == "sentence_transformers":
                        import sentence_transformers
                    elif dep == "faiss":
                        import faiss
                    elif dep == "psutil":
                        import psutil
                except ImportError:
                    failed_imports.append(dep)

            self.log_test(
                "Python Dependencies Available",
                len(failed_imports) == 0,
                (
                    f"Failed: {failed_imports}"
                    if failed_imports
                    else "All dependencies available"
                ),
            )

        except Exception as e:
            self.log_test("File Structure and Dependencies", False, str(e))

    def test_configuration_files(self):
        """Test configuration file integrity"""
        try:
            # Test 1: Watcher config exists and is valid YAML
            config_path = self.base_dir / "prompts/watcher_config.yaml"
            if config_path.exists():
                with open(config_path, "r", encoding="utf-8") as f:
                    config = yaml.safe_load(f)
                has_categories = "document_categories" in config
                self.log_test(
                    "Watcher Config Valid",
                    has_categories,
                    "Contains document_categories section",
                )
            else:
                self.log_test("Watcher Config Valid", False, "Config file not found")

            # Test 2: FAISS index exists
            index_exists = (self.base_dir / "index.faiss").exists()
            meta_exists = (self.base_dir / "meta.sqlite").exists()
            self.log_test("FAISS Index Files Exist", index_exists and meta_exists)

        except Exception as e:
            self.log_test("Configuration Files", False, str(e))

    def test_search_functionality(self):
        """Test core search functionality"""
        try:
            # Test 1: Import core modules
            from core.ask import answer_question
            from core.embedding import Embedder

            # Test 2: Initialize embedder
            em = Embedder()
            init_success = em is not None
            self.log_test("Embedder Initialization", init_success)

            if init_success:
                # Test 3: Simple query test (if index has data)
                try:
                    results = em.query("Christmas story", k=1)
                    query_works = (
                        len(results) > 0 and len(results[0]) == 5  # Updated for 5-tuple
                    )  # 5-tuple format
                    details = (
                        f"Returned {len(results)} results with correct format"
                        if query_works
                        else "Query failed or wrong format"
                    )
                    self.log_test("Search Query Functionality", query_works, details)
                except Exception as query_error:
                    self.log_test(
                        "Search Query Functionality",
                        False,
                        f"Query error: {query_error}",
                    )

        except ImportError as e:
            self.log_test("Search Functionality", False, f"Import error: {e}")
        except Exception as e:
            self.log_test("Search Functionality", False, str(e))

    def test_ui_readiness(self):
        """Test UI component readiness"""
        try:
            # Test 1: UI app file exists and is importable
            ui_path = self.base_dir / "ui/app.py"
            if ui_path.exists():
                # Just check if the file is valid Python
                try:
                    with open(ui_path, "r", encoding="utf-8") as f:
                        content = f.read()
                    compile(content, str(ui_path), "exec")
                    self.log_test(
                        "UI App File Valid", True, "UI file compiles successfully"
                    )
                except SyntaxError as se:
                    self.log_test("UI App File Valid", False, f"Syntax error: {se}")
            else:
                self.log_test("UI App File Valid", False, "UI app file not found")

            # Test 2: Check if streamlit command would work (without actually running it)
            streamlit_cmd = [sys.executable, "-m", "streamlit", "--version"]
            try:
                result = subprocess.run(
                    streamlit_cmd, capture_output=True, timeout=10, cwd=self.base_dir
                )
                streamlit_available = result.returncode == 0
                self.log_test("Streamlit Available", streamlit_available)
            except (subprocess.TimeoutExpired, FileNotFoundError):
                self.log_test(
                    "Streamlit Available",
                    False,
                    "Streamlit not installed or not accessible",
                )

        except Exception as e:
            self.log_test("UI Readiness", False, str(e))

    def run_all_tests(self):
        """Run comprehensive test suite"""
        print("AI File Search System - Comprehensive Test Suite")
        print("=" * 60)
        print()

        # Run all test categories
        print("Testing Complete Setup Script...")
        self.test_complete_setup_script()
        print()

        print("Testing Smart Watcher Functionality...")
        self.test_smart_watcher_functionality()
        print()

        print("Testing Document Discovery System...")
        self.test_document_discovery_system()
        print()

        print("Testing File Structure and Dependencies...")
        self.test_file_structure_and_dependencies()
        print()

        print("Testing Configuration Files...")
        self.test_configuration_files()
        print()

        print("Testing Search Functionality...")
        self.test_search_functionality()
        print()

        print("Testing UI Readiness...")
        self.test_ui_readiness()
        print()

        # Summary
        total_tests = len(self.test_results)
        passed_tests = sum(1 for _, success, _ in self.test_results if success)
        failed_tests = total_tests - passed_tests

        print("TEST SUMMARY")
        print("=" * 60)
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {failed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")

        if self.errors:
            print("\nFAILED TESTS:")
            for error in self.errors:
                print(f"   - {error}")

        print()
        if failed_tests == 0:
            print("ALL TESTS PASSED! Your AI File Search system is fully operational.")
        else:
            print(f"{failed_tests} test(s) failed. Review the issues above.")

        return failed_tests == 0


if __name__ == "__main__":
    tester = ComprehensiveSystemTest()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)
