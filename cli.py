"""🔍 AI File Search CLI
A command-line interface for semantic document search with citations.

Usage:
    python cli.py "Who is Alice?"
    python cli.py "What happens in Wonderland?"
    python cli.py --help
"""

import argparse
import sys
import time
from pathlib import Path
from typing import Optional

from core.ask import answer_question


def print_banner():
    """Print a nice welcome banner."""
    print("🔍 AI File Search")
    print("=" * 50)


def print_help():
    """Print usage help."""
    print(
        """
🔍 AI File Search CLI

USAGE:
    python cli.py "your question here"
    python cli.py --interactive
    python cli.py --help

EXAMPLES:
    python cli.py "Who is Alice?"
    python cli.py "What is Wonderland?"
    python cli.py "Who is Ebenezer Scrooge?"

OPTIONS:
    --interactive, -i    Start interactive mode
    --verbose, -v        Show detailed output
    --citations, -c      Show detailed citation info
    --no-phi3           Disable Phi-3 LLM (use context-based answers)
    --help, -h          Show this help message
    """
    )


def format_answer(
    answer: str, citations: list, show_citations: bool = True, verbose: bool = False
) -> str:
    """Format the answer and citations for display."""
    output = []

    # Main answer
    output.append("🤖 Answer:")
    output.append("-" * 30)
    output.append(answer)

    if show_citations and citations:
        output.append(f"\n📚 Citations ({len(citations)} sources):")
        output.append("-" * 30)

        for citation in citations:
            if verbose:
                # Detailed citation info
                score_bar = "█" * int(citation["score"] * 10) + "░" * (
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
    use_phi3: bool = True,
) -> None:
    """Process a single question and display results."""
    print(f"🤔 Searching for: '{question}'")
    print()

    # Check if index exists
    if not Path("index.faiss").exists():
        print("❌ Error: No search index found!")
        print("   Please run: python bench_embedding.py")
        return

    # Time the query
    start_time = time.time()

    try:
        if use_phi3:
            print("🤖 Generating AI-powered answer...")
        else:
            print("📝 Using context-based answer...")

        answer, citations = answer_question(question)
        query_time = (time.time() - start_time) * 1000

        # Display results
        formatted_output = format_answer(answer, citations, show_citations, verbose)
        print(formatted_output)

        # Performance info
        print(f"\n⚡ Query completed in {query_time:.1f}ms")

        if verbose and citations:
            avg_score = sum(c["score"] for c in citations) / len(citations)
            print(f"📊 Average relevance score: {avg_score:.3f}")

    except Exception as e:
        print(f"❌ Error: {e}")
        if verbose:
            import traceback

            traceback.print_exc()


def interactive_mode(
    verbose: bool = False, show_citations: bool = True, use_phi3: bool = True
) -> None:
    """Start interactive question-asking mode."""
    print_banner()
    print("Interactive mode - type 'quit' or 'exit' to stop")
    print("Type 'help' for usage examples")
    if not use_phi3:
        print("⚠️  Phi-3 disabled - using context-based answers")
    print()

    while True:
        try:
            question = input("🔍 Ask a question: ").strip()

            if not question:
                continue

            if question.lower() in ["quit", "exit", "q"]:
                print("👋 Goodbye!")
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
            ask_question(question, verbose, show_citations, use_phi3)
            print("\n" + "=" * 50 + "\n")

        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            break
        except EOFError:
            print("\n👋 Goodbye!")
            break


def main():
    """Main CLI entry point."""
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
        "--no-phi3",
        action="store_true",
        help="Disable Phi-3 LLM and use context-based answers",
    )
    parser.add_argument("--help", "-h", action="store_true", help="Show help message")

    args = parser.parse_args()

    # Handle help
    if args.help or (not args.question and not args.interactive):
        print_help()
        return

    # Handle interactive mode
    if args.interactive:
        use_phi3 = not args.no_phi3
        interactive_mode(args.verbose, args.citations, use_phi3)
        return

    # Handle single question
    if args.question:
        question = " ".join(args.question)
        use_phi3 = not args.no_phi3
        print_banner()
        ask_question(question, args.verbose, args.citations, use_phi3)
    else:
        print_help()


if __name__ == "__main__":
    main()
