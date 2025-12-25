"""Test streaming performance in isolation (without Flask)."""

import sys
import time

# Add parent to path
sys.path.insert(0, ".")

from core.ask import answer_question


def test_streaming():
    print("=" * 60)
    print("Testing STREAMING mode (without Flask)")
    print("=" * 60)

    start = time.time()
    gen, cit = answer_question("What is machine learning?", streaming=True)

    first_token_time = None
    token_count = 0
    answer = ""

    for token in gen:
        if first_token_time is None:
            first_token_time = time.time() - start
            print(f"\n[FIRST TOKEN: {first_token_time:.2f}s]\n")
        token_count += 1
        answer += token
        print(token, end="", flush=True)

    total_time = time.time() - start
    print(f"\n\n{'=' * 60}")
    print(f"STREAMING RESULTS:")
    print(f"  First token: {first_token_time:.2f}s")
    print(f"  Total time:  {total_time:.2f}s")
    print(f"  Tokens:      {token_count}")
    print(f"  Citations:   {len(cit)}")
    print("=" * 60)


def test_non_streaming():
    print("\n" + "=" * 60)
    print("Testing NON-STREAMING mode")
    print("=" * 60)

    start = time.time()
    answer, cit = answer_question("What is machine learning?", streaming=False)
    total_time = time.time() - start

    print(f"\nAnswer: {answer[:200]}...")
    print(f"\n{'=' * 60}")
    print(f"NON-STREAMING RESULTS:")
    print(f"  Total time:  {total_time:.2f}s")
    print(f"  Citations:   {len(cit)}")
    print("=" * 60)


if __name__ == "__main__":
    # Run non-streaming first to warm up models
    test_non_streaming()

    # Then run streaming with warm models
    test_streaming()
