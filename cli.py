"""CLI: AI File Search CLI
A command-line interface for semantic document search with citations.

Usage:
    python cli.py "Who is Alice?"
    python cli.py "What happens in Wonderland?"
    python cli.py sync-confluence --space SPACE_KEY
    python cli.py --help
"""

import argparse
import sys
import time
from pathlib import Path
from typing import Optional

from core.ask import answer_question
from core.index_manager import IndexManager


def print_banner():
    """Print a nice welcome banner."""
    print("AI File Search")
    print("=" * 50)


def print_help():
    """Print usage help."""
    print(
        """
AI File Search CLI

USAGE:
    python cli.py "your question here"
    python cli.py --interactive
    python cli.py sync-confluence --space SPACE_KEY
    python cli.py confluence-status
    python cli.py --help

EXAMPLES:
    python cli.py "Who is Alice?"
    python cli.py "What is Wonderland?"
    python cli.py "Who is Ebenezer Scrooge?"
    python cli.py sync-confluence --space "~7120204a948e27a13f46bcbef088b0aa7a498b"

OPTIONS:
    --interactive, -i    Start interactive mode
    --verbose, -v        Show detailed output
    --citations, -c      Show detailed citation info
    --no-llm            Disable LLM (use context-based answers)
    --help, -h          Show this help message

CONFLUENCE COMMANDS:
    sync-confluence      Sync pages from Confluence space
      --space KEY        Space key to sync (required)
      --full             Force full sync (not incremental)
    confluence-status    Show Confluence connection status
    """
    )


def format_answer(
    answer: str, citations: list, show_citations: bool = True, verbose: bool = False
) -> str:
    """Format the answer and citations for display."""
    output = []

    # Main answer
    output.append("ANSWER:")
    output.append("-" * 30)
    output.append(answer)

    if show_citations and citations:
        output.append(f"\nCITATIONS: ({len(citations)} sources):")
        output.append("-" * 30)

        for citation in citations:
            if verbose:
                # Detailed citation info
                score_bar = "=" * int(citation["score"] * 10) + "-" * (
                    10 - int(citation["score"] * 10)
                )
                output.append(
                    f"[{citation['id']}] {citation['file']}, page {citation['page']}"
                )
                output.append(f"    Score: {citation['score']:.3f} {score_bar}")
                output.append(f"    Preview: {citation['chunk'][:100]}...")
                output.append("")
            else:
                # Simple citation
                output.append(
                    f"  [{citation['id']}] {citation['file']}, page {citation['page']}"
                )

    return "\n".join(output)


def print_search_results(results):
    for result in results:
        print(f"Found in: {result['path']}")
        print(result["chunk"])
        print("-" * 40)


def ask_question(
    question: str,
    verbose: bool = False,
    show_citations: bool = True,
    use_llm: bool = True,
) -> None:
    """Process a single question and display results."""
    print(f"SEARCHING: '{question}'")
    print()

    # Check if index exists
    if not Path("index.faiss").exists():
        print("ERROR: No search index found!")
        print("   Please run: python bench_embedding.py")
        return

    # Time the query
    start_time = time.time()

    try:
        if use_llm:
            print("GENERATING: AI-powered answer...")
        else:
            print("INFO: Using context-based answer...")

        answer, citations = answer_question(question)
        query_time = (time.time() - start_time) * 1000

        # Display results (answer is always str when not streaming)
        formatted_output = format_answer(
            str(answer), citations, show_citations, verbose
        )
        print(formatted_output)

        # Performance info
        print(f"\nTIMING: Query completed in {query_time:.1f}ms")

        if verbose and citations:
            avg_score = sum(c["score"] for c in citations) / len(citations)
            print(f"STATS: Average relevance score: {avg_score:.3f}")

    except Exception as e:
        print(f"ERROR: {e}")
        if verbose:
            import traceback

            traceback.print_exc()


def interactive_mode(
    verbose: bool = False, show_citations: bool = True, use_llm: bool = True
) -> None:
    """Start interactive question-asking mode."""
    print_banner()
    print("Interactive mode - type 'quit' or 'exit' to stop")
    print("Type 'help' for usage examples")
    if not use_llm:
        print("WARNING: LLM disabled - using context-based answers")
    print()

    while True:
        try:
            question = input("Ask a question: ").strip()

            if not question:
                continue

            if question.lower() in ["quit", "exit", "q"]:
                print("Goodbye!")
                break

            if question.lower() in ["help", "h", "?"]:
                print(
                    """
Example questions you can try:
• "Who is Alice?"
• "What is Wonderland?"
• "Who is Ebenezer Scrooge?"
• "What happens in the secret garden?"
• "Who is Peter Pan?"
• "What is treasure island about?"
                """
                )
                continue

            print()
            ask_question(question, verbose, show_citations, use_llm)
            print("\n" + "=" * 50 + "\n")

        except KeyboardInterrupt:
            print("\nGoodbye!")
            break
        except EOFError:
            print("\nGoodbye!")
            break


def sync_confluence_command(space_key: str, full_sync: bool = False) -> None:
    """Sync Confluence space to the search index."""
    print_banner()
    print(f"CONFLUENCE SYNC: Space '{space_key}'")
    print("-" * 50)

    index_manager = IndexManager()
    incremental = not full_sync

    if incremental:
        print("Mode: Incremental (only changed pages)")
    else:
        print("Mode: Full sync (all pages)")

    print()
    print("Starting sync...")

    start_time = time.time()

    # Use synchronous mode for CLI (shows progress)
    success, message, _ = index_manager.sync_confluence(
        space_key=space_key,
        async_mode=False,
        incremental=incremental,
    )

    elapsed = time.time() - start_time

    print()
    if success:
        print(f"SUCCESS: {message}")
    else:
        print(f"ERROR: {message}")

    print(f"TIMING: Completed in {elapsed:.1f}s")


def confluence_status_command() -> None:
    """Show Confluence connection status."""
    print_banner()
    print("CONFLUENCE STATUS")
    print("-" * 50)

    index_manager = IndexManager()
    status = index_manager.get_confluence_status()

    if not status.get("configured"):
        print(f"Status: Not configured")
        print(f"Error: {status.get('error', 'Unknown')}")
        print()
        print("To configure Confluence:")
        print("  1. Copy .env.example to .env")
        print("  2. Fill in CONFLUENCE_URL, CONFLUENCE_EMAIL, CONFLUENCE_API_TOKEN")
        print("  3. Run: python cli.py confluence-status")
        return

    print(f"Configured: Yes")
    print(f"Connected: {'Yes' if status.get('connected') else 'No'}")
    print(f"Connection: {status.get('connection_message', 'N/A')}")
    print()

    if status.get("last_sync"):
        print(f"Last Sync: {status.get('last_sync')}")
        print(f"Pages Indexed: {status.get('pages_indexed', 0)}")
        print(f"Space Key: {status.get('space_key', 'N/A')}")

        errors = status.get("errors", [])
        if errors:
            print(f"Errors: {len(errors)}")
            for err in errors[:3]:  # Show first 3 errors
                print(f"  - {err}")
    else:
        print("Last Sync: Never")
        print()
        print("To sync Confluence:")
        print("  python cli.py sync-confluence --space YOUR_SPACE_KEY")

    # Show available spaces if connected
    if status.get("connected"):
        print()
        print("Available spaces:")
        spaces = index_manager.get_confluence_spaces()
        if spaces:
            for space in spaces[:10]:  # Show first 10
                print(f"  - {space['key']}: {space['name']}")
        else:
            print("  (No spaces found or no access)")


def main():
    """Main CLI entry point."""
    # Check for Confluence subcommands first
    if len(sys.argv) > 1:
        if sys.argv[1] == "sync-confluence":
            # Parse sync-confluence arguments
            parser = argparse.ArgumentParser(description="Sync Confluence space")
            parser.add_argument("command", help="Command name")
            parser.add_argument(
                "--space", "-s", required=True, help="Confluence space key"
            )
            parser.add_argument(
                "--full", action="store_true", help="Force full sync (not incremental)"
            )
            args = parser.parse_args()
            sync_confluence_command(args.space, args.full)
            return

        if sys.argv[1] == "confluence-status":
            confluence_status_command()
            return

    parser = argparse.ArgumentParser(
        description="AI File Search - Semantic document search with citations",
        add_help=False,  # We'll handle help ourselves
    )

    parser.add_argument("question", nargs="*", help="Question to search for")
    parser.add_argument(
        "--interactive", "-i", action="store_true", help="Start interactive mode"
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Show detailed output including relevance scores",
    )
    parser.add_argument(
        "--citations",
        "-c",
        action="store_true",
        help="Show detailed citation information",
    )
    parser.add_argument(
        "--no-llm",
        action="store_true",
        help="Disable LLM and use context-based answers",
    )
    parser.add_argument("--help", "-h", action="store_true", help="Show help message")

    args = parser.parse_args()

    # Handle help
    if args.help or (not args.question and not args.interactive):
        print_help()
        return

    # Handle interactive mode
    if args.interactive:
        use_llm = not args.no_llm
        interactive_mode(args.verbose, args.citations, use_llm)
        return

    # Handle single question
    if args.question:
        question = " ".join(args.question)
        use_llm = not args.no_llm
        print_banner()
        ask_question(question, args.verbose, args.citations, use_llm)
    else:
        print_help()


if __name__ == "__main__":
    main()
