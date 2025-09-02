#!/usr/bin/env python3
"""
Project Structure Validator for AI Agents

This tool helps AI agents understand and validate the project structure
before creating or moving files.

Usage:
    python validate_structure.py
    python validate_structure.py --check-file "new_test.py"
    python validate_structure.py --suggest-location "performance_benchmark.py"
"""

import argparse
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


class ProjectStructureValidator:
    """Validates and suggests file placements according to project rules."""

    def __init__(self) -> None:
        self.project_root = Path(__file__).parent.parent
        self.rules = self._load_rules()

    def _load_rules(self) -> Dict[str, Any]:
        """Load project structure rules."""
        return {
            "protected_files": [
                "README.md",
                "index.faiss",
                "meta.sqlite",
                "pyproject.toml",
                "poetry.toml",
                "cli.py",
                "smart_watcher.py",
                "complete_setup.py",
                "run_watcher.py",
                "setup_auto_discovery.py",
                "switch_documents.py",
            ],
            "forbidden_dirs": [
                "src",
                "data",
                "tests/unit",
                "tests/integration",
                "tests/regression",
                "tools/scripts",
                "tools/utilities",
            ],
            "required_flat": ["tests", "tools"],
            "clean_root_policy": {
                "max_root_files": 15,
                "documentation_in_root": ["README.md"],  # Only main README
                "forbidden_in_root": [
                    "PROJECT_STRUCTURE.md",
                    "AI_AGENT_RULES.md",
                    "BUILD_LOG.md",
                    "USER_GUIDE.md",
                    "API_SPECIFICATION.md",
                    "project_structure.toml",
                ],
            },
            "directory_purposes": {
                "tests": "All testing files (test_*.py)",
                "tools": "Development utilities and scripts",
                "docs": "ALL documentation except README.md",
                "config": "Configuration files and templates",
                "core": "Core system functionality",
                "daemon": "Background services",
                "ui": "User interface components",
                "root": "Essential user commands and main README only",
            },
        }

    def suggest_location(self, filename: str) -> Tuple[str, str]:
        """Suggest the correct location for a new file."""
        filename_lower = filename.lower()

        # Main README stays in root
        if filename == "README.md":
            return "", "Main project documentation - stays in root"

        # Documentation files go to docs/
        if filename.endswith(".md"):
            return "docs/", f"Documentation file - goes in docs/{filename}"

        # Configuration files go to config/
        config_extensions = [".toml", ".yaml", ".yml", ".json"]
        if any(filename_lower.endswith(ext) for ext in config_extensions):
            # Exception for essential project configs
            if filename in ["pyproject.toml", "poetry.toml", "package.json"]:
                return "", f"Essential project config - stays in root"
            return "config/", f"Configuration file - goes in config/{filename}"

        # Test files
        if filename_lower.startswith("test_") or "test" in filename_lower:
            return "tests/", f"Test file - goes in tests/{filename}"

        # Tool/utility files
        tool_indicators = [
            "debug_",
            "bench_",
            "analyze_",
            "monitor_",
            "check_",
            "validate_",
            "extract_",
            "download_",
            "tool",
            "script",
            "utility",
            "helper",
        ]
        if any(indicator in filename_lower for indicator in tool_indicators):
            return "tools/", f"Development tool - goes in tools/{filename}"

        # Core system files
        core_indicators = ["ask", "embedding", "extract", "config", "llm"]
        if any(indicator in filename_lower for indicator in core_indicators):
            return "core/", f"Core functionality - goes in core/{filename}"

        # UI files
        if any(ui in filename_lower for ui in ["app", "dashboard", "ui", "interface"]):
            return "ui/", f"User interface - goes in ui/{filename}"

        # Background services
        if any(svc in filename_lower for svc in ["daemon", "watch", "service"]):
            return "daemon/", f"Background service - goes in daemon/{filename}"

        # User commands (setup, management scripts)
        user_command_indicators = ["setup_", "switch_", "run_", "complete_", "cli"]
        if any(cmd in filename_lower for cmd in user_command_indicators):
            return "", f"User command - goes in root/{filename} (if essential)"

        return "tools/", f"Default: Development utility - goes in tools/{filename}"

    def validate_file_placement(self, filepath: str) -> List[str]:
        """Validate if a file is in the correct location."""
        issues = []
        path = Path(filepath)

        # Check if it's a protected file in wrong location
        if path.name in self.rules["protected_files"]:
            if path.name == "README.md" and str(path.parent) != ".":
                issues.append(f"❌ Main README.md must be in root directory")
            elif (
                path.name in ["cli.py", "smart_watcher.py"] and str(path.parent) != "."
            ):
                issues.append(f"❌ User command {path.name} must be in root directory")

        # Check for forbidden directories
        for forbidden in self.rules["forbidden_dirs"]:
            if forbidden in str(path):
                issues.append(
                    f"❌ Forbidden directory: {forbidden} (use flat structure)"
                )

        # Check clean root policy violations
        if (
            str(path.parent) == "."
            and path.name.endswith(".md")
            and path.name != "README.md"
        ):
            issues.append(
                f"❌ Documentation file {path.name} should be in docs/ directory"
            )

        if (
            str(path.parent) == "."
            and path.name in self.rules["clean_root_policy"]["forbidden_in_root"]
        ):
            issues.append(
                f"❌ {path.name} should not be in root - use docs/ or config/"
            )

        # Check test files
        if path.name.startswith("test_"):
            if path.parent.name != "tests":
                issues.append(f"❌ Test file should be in tests/ directory")
            if len(path.parts) > 2:  # More than tests/test_file.py
                issues.append(f"❌ Tests should be flat: tests/{path.name}")

        # Check tool files
        tool_indicators = ["debug_", "bench_", "analyze_", "monitor_", "validate_"]
        if any(path.name.startswith(ind) for ind in tool_indicators):
            if path.parent.name != "tools":
                issues.append(f"❌ Tool file should be in tools/ directory")

        return issues

    def scan_project_structure(self) -> Dict[str, Any]:
        """Scan and report on current project structure."""
        report: Dict[str, Any] = {
            "protected_files_status": [],
            "forbidden_dirs_found": [],
            "structure_violations": [],
            "file_counts": {},
            "root_cleanliness": {},
        }

        # Check protected files
        for protected in self.rules["protected_files"]:
            if (self.project_root / protected).exists():
                report["protected_files_status"].append(f"✅ {protected}")
            else:
                report["protected_files_status"].append(f"❌ Missing: {protected}")

        # Check for forbidden directories
        for forbidden in self.rules["forbidden_dirs"]:
            if (self.project_root / forbidden).exists():
                report["forbidden_dirs_found"].append(forbidden)

        # Check root cleanliness
        root_files = [f for f in self.project_root.iterdir() if f.is_file()]
        root_docs = [f for f in root_files if f.suffix == ".md"]
        root_configs = [f for f in root_files if f.suffix in [".toml", ".yaml", ".yml"]]

        report["root_cleanliness"] = {
            "total_files": len(root_files),
            "documentation_files": len(root_docs),
            "config_files": len(root_configs),
            "within_limits": len(root_files)
            <= self.rules["clean_root_policy"]["max_root_files"],
            "clean_docs": len(root_docs) <= 1,  # Only README.md
        }

        # Count files in each directory
        for item in self.project_root.iterdir():
            if item.is_dir():
                py_files = len(list(item.glob("*.py")))
                md_files = len(list(item.glob("*.md")))
                config_files = len(list(item.glob("*.toml"))) + len(
                    list(item.glob("*.yaml"))
                )
                if py_files > 0 or md_files > 0 or config_files > 0:
                    report["file_counts"][item.name] = {
                        "python": py_files,
                        "documentation": md_files,
                        "configuration": config_files,
                    }

        return report

    def generate_ai_guidance(self) -> str:
        """Generate guidance text for AI agents."""
        return """
🤖 AI AGENT GUIDANCE - Clean Root File Placement Rules

🧹 CLEAN ROOT STRATEGY:
   • Root = ESSENTIAL ONLY (max 15 files)
   • User commands, main README, critical data, project configs

📝 DOCUMENTATION → docs/
   • ALL .md files except README.md
   • Examples: docs/PROJECT_STRUCTURE.md, docs/API_GUIDE.md

⚙️ CONFIGURATION → config/
   • ALL .toml/.yaml config files except pyproject.toml/poetry.toml
   • Examples: config/project_structure.toml, config/settings.yaml

📋 TESTS → tests/test_*.py
   • All test files use tests/ directory (flat structure)
   • Example: test_embedding.py

🔧 TOOLS → tools/<name>.py
   • Development utilities, scripts, debugging tools
   • Example: tools/debug_database.py

⚙️ CORE → core/<module>.py
   • Core system functionality only
   • Example: core/ask.py, embedding.py

🎯 USER COMMANDS → <name>.py (root, ESSENTIAL ONLY)
   • Commands users run directly
   • Example: cli.py, setup_auto_discovery.py

🚫 NEVER PUT IN ROOT:
   • PROJECT_STRUCTURE.md, AI_AGENT_RULES.md → docs/
   • project_structure.toml, settings.yaml → config/
   • test_*.py → tests/
   • debug_*.py, tools → tools/

🔒 NEVER MOVE FROM ROOT:
   • README.md (main project doc)
   • index.faiss, meta.sqlite (system dependencies)
   • cli.py, smart_watcher.py (essential user commands)
   • pyproject.toml, poetry.toml (project configs)

✅ VALIDATION COMMANDS:
   python validate_structure.py --scan
   python validate_structure.py --suggest-location "file.py"

📖 REFERENCES:
   • Complete guide: PROJECT_STRUCTURE.md
   • Configuration: project_structure.toml
"""


def main() -> None:
    """Main CLI interface."""
    parser = argparse.ArgumentParser(description="Project Structure Validator")
    parser.add_argument("--check-file", help="Check if file placement is correct")
    parser.add_argument("--suggest-location", help="Suggest location for new file")
    parser.add_argument("--scan", action="store_true", help="Scan project structure")
    parser.add_argument(
        "--guidance", action="store_true", help="Show AI agent guidance"
    )

    args = parser.parse_args()
    validator = ProjectStructureValidator()

    if args.check_file:
        issues = validator.validate_file_placement(args.check_file)
        if issues:
            print(f"❌ Issues with {args.check_file}:")
            for issue in issues:
                print(f"   {issue}")
        else:
            print(f"✅ {args.check_file} is correctly placed")

    elif args.suggest_location:
        location, reason = validator.suggest_location(args.suggest_location)
        print(f"📍 Suggested location: {location}{args.suggest_location}")
        print(f"📝 Reason: {reason}")

    elif args.scan:
        report = validator.scan_project_structure()
        print("📊 Project Structure Report")
        print("=" * 40)

        print("\n🔒 Protected Files:")
        for status in report["protected_files_status"]:
            print(f"   {status}")

        print(f"\n🧹 Root Directory Cleanliness:")
        root_clean = report["root_cleanliness"]
        print(f"   📁 Total files in root: {root_clean['total_files']}")
        print(
            f"   📝 Documentation files: {root_clean['documentation_files']} (should be 1)"
        )
        print(f"   ⚙️  Configuration files: {root_clean['config_files']}")

        if root_clean["within_limits"]:
            print(f"   ✅ Root file count OK")
        else:
            print(f"   ⚠️  Root has too many files (>15)")

        if root_clean["clean_docs"]:
            print(f"   ✅ Documentation organization OK")
        else:
            print(f"   ⚠️  Too many docs in root (move to docs/)")

        if report["forbidden_dirs_found"]:
            print("\n🚫 Forbidden Directories Found:")
            for forbidden in report["forbidden_dirs_found"]:
                print(f"   ❌ {forbidden} (should be removed)")

        print("\n📁 File Distribution:")
        for dir_name, counts in sorted(report["file_counts"].items()):
            total = counts["python"] + counts["documentation"] + counts["configuration"]
            print(
                f"   {dir_name}/: {total} files (py:{counts['python']}, "
                f"md:{counts['documentation']}, config:{counts['configuration']})"
            )

    elif args.guidance:
        print(validator.generate_ai_guidance())

    else:
        print("🏗️  Project Structure Validator")
        print("🧹 Enforces clean root directory strategy")
        print("\nUsage examples:")
        print("  python validate_structure.py --guidance")
        print("  python validate_structure.py --suggest-location 'new_test.py'")
        print("  python validate_structure.py --scan")


if __name__ == "__main__":
    main()
