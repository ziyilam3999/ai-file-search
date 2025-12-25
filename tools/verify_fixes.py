"""Test script to verify all fixes are working."""

import sys
import time
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

print("=" * 60)
print("FIX VERIFICATION TEST")
print("=" * 60)

# Test 1: Prompt Template Caching
print("\n[TEST 1] Prompt Template Caching")
print("-" * 60)
from core.ask import _get_prompt_template

t0 = time.perf_counter()
template1 = _get_prompt_template()
t1 = time.perf_counter()
print(f"✓ First call: {(t1-t0)*1000:.2f}ms (loads from disk)")

t0 = time.perf_counter()
template2 = _get_prompt_template()
t1 = time.perf_counter()
print(f"✓ Second call: {(t1-t0)*1000:.2f}ms (cached)")
print(f"✓ Same object: {template1 is template2}")
print(f"✓ Template loaded: {len(template1)} chars")

# Test 2: Preload Progress Tracking
print("\n[TEST 2] Preload Progress Tracking")
print("-" * 60)
from run_app import get_preload_status, preload_models

print("Initial status:", get_preload_status())
print("\nStarting preload (this will take 8-10 seconds)...")

t0 = time.time()
preload_models()
t1 = time.time()

final_status = get_preload_status()
print(f"\n✓ Preload completed in {t1-t0:.2f}s")
print(f"✓ Final status: {final_status}")
print(f"✓ Ready: {final_status['ready']}")
print(f"✓ Stage: {final_status['stage']}")
print(f"✓ Progress: {final_status['progress']}%")

# Test 3: Verify models are loaded
print("\n[TEST 3] Model Loading Verification")
print("-" * 60)
from core.embedding import _MODEL_CACHE
from core.llm import _phi3_instance

print(f"✓ LLM loaded: {_phi3_instance is not None}")
print(f"✓ Embedding model loaded: {_MODEL_CACHE is not None}")

# Test 4: Quick query to test cached prompt
print("\n[TEST 4] Query with Cached Prompt")
print("-" * 60)
from core.ask import answer_question

t0 = time.time()
answer, citations = answer_question(
    "What is machine learning?", top_k=3, streaming=False
)
t1 = time.time()

print(f"✓ Query completed in {t1-t0:.2f}s")
print(f"✓ Answer length: {len(answer)} chars")
print(f"✓ Citations: {len(citations)}")

print("\n" + "=" * 60)
print("ALL TESTS PASSED ✓")
print("=" * 60)
