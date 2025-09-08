#!/usr/bin/env python3
"""
Setup Auto-Discovery for AI File Search

This script helps you set up the automatic document discovery system.
Run this once to prepare your system for auto-discovery.
"""

import os
import shutil
from pathlib import Path


def setup_sample_structure():
    """Create sample folder structure to demonstrate auto-discovery."""
    print("SETUP: Setting up sample folder structure...")

    # Create sample categories
    sample_categories = [
        "research_papers",
        "user_manuals",
        "meeting_notes",
        "technical_docs",
        "personal_notes",
    ]

    for category in sample_categories:
        sample_path = Path(f"ai_search_docs/{category}")
        extracts_path = Path(f"extracts/{category}")

        sample_path.mkdir(parents=True, exist_ok=True)
        extracts_path.mkdir(parents=True, exist_ok=True)

        # Create a README in each sample folder
        readme_content = f"""# {category.replace('_', ' ').title()} Category

This folder is for {category.replace('_', ' ')} documents.

The AI File Search system will automatically:
- Watch this folder for new files
- Extract and index content
- Provide intelligent search across these documents

Simply add your files here and the system will handle the rest!
"""

        readme_path = sample_path / "README.md"
        with open(readme_path, "w") as f:
            f.write(readme_content)

    print(f"SUCCESS: Created {len(sample_categories)} sample categories")
    return sample_categories


def migrate_existing_docs():
    """Move existing documents to the new structure."""
    print("MIGRATE: Checking for existing documents to migrate...")

    # Check if we have existing children_stories and software_dev folders
    migrations = []

    if Path("ai_search_docs/children_stories").exists():
        migrations.append(("children_stories", "classic_literature"))
    if Path("ai_search_docs/software_dev").exists():
        migrations.append(("software_dev", "technical_docs"))

    for old_name, new_name in migrations:
        old_path = Path(f"ai_search_docs/{old_name}")
        new_path = Path(f"ai_search_docs/{new_name}")

        if old_path.exists() and not new_path.exists():
            print(f"MOVE: Moving {old_name} -> {new_name}")
            shutil.move(str(old_path), str(new_path))

            # Also move extracts
            old_extracts = Path(f"extracts/{old_name}")
            new_extracts = Path(f"extracts/{new_name}")
            if old_extracts.exists() and not new_extracts.exists():
                shutil.move(str(old_extracts), str(new_extracts))

    return migrations


def create_user_guide():
    """Create a user guide for the auto-discovery system."""
    guide_content = """# AI File Search Auto-Discovery User Guide

## OVERVIEW: How It Works

The AI File Search system now automatically discovers document categories based on your folder structure in `ai_search_docs/`.

## STRUCTURE: Folder Structure

Your documents should be organized in the `ai_search_docs/` directory. Each subfolder represents a category of documents. For example:

```
ai_search_docs/
├── research_papers/
│   ├── paper1.pdf
│   └── paper2.pdf
├── user_manuals/
│   ├── manual1.pdf
│   └── manual2.pdf
└── meeting_notes/
    ├── notes1.md
    └── notes2.md
```

## GETTING STARTED: Quick Setup

1. **Add your documents**: Put files in the appropriate `ai_search_docs/` subfolder
2. **Start the watcher**: `python run_watcher.py`
3. **Switch categories**: `python switch_documents.py <category_name>`

## COMMANDS: Available Operations

- `python switch_documents.py discover` - See all available categories
- `python switch_documents.py status` - Check current configuration
- `python switch_documents.py all` - Enable all categories
- `python switch_documents.py research_papers` - Switch to specific category

## BENEFITS: Why Use This System

- **Zero Configuration**: Just create folders and add files
- **Automatic Discovery**: System finds new categories automatically
- **Smart Organization**: Each category gets its own search index
- **Easy Switching**: Change focus between document types instantly

## 📂 Adding New Categories

1. Create a new folder in `ai_search_docs/` (e.g., `ai_search_docs/contracts/`)
2. Add your files to the folder
3. Run `python switch_documents.py discover` to see it appear
4. Switch to it: `python switch_documents.py contracts`

That's it! The system handles everything else automatically.
"""

    guide_path = Path("AUTO_DISCOVERY_GUIDE.md")
    with open(guide_path, "w") as f:
        f.write(guide_content)

    print(f"📚 Created user guide: {guide_path}")


def main():
    print("🎉 Setting up AI File Search Auto-Discovery System")
    print("=" * 50)

    # Setup folder structure
    setup_sample_structure()

    # Migrate existing documents
    migrations = migrate_existing_docs()
    if migrations:
        print(f"✅ Migrated {len(migrations)} existing categories")

    # Create user guide
    create_user_guide()

    print("\n🎉 Setup Complete!")
    print("=" * 50)
    print("Next steps:")
    print("1. Add your documents to ai_search_docs/ subfolders")
    print("2. Run: python switch_documents.py discover")
    print("3. Start the watcher: python run_watcher.py")
    print("4. Test switching: python switch_documents.py <category_name>")
    print("\nRead AUTO_DISCOVERY_GUIDE.md for detailed instructions!")


if __name__ == "__main__":
    main()
