"""Quick test script to verify the refactored LLM code works."""
import os
import sys

def test_with_model(model_name):
    """Test loading and generation with a specific model."""
    print(f"\n{'='*60}")
    print(f"Testing with: {model_name}")
    print('='*60)
    
    # Set model via environment variable
    os.environ['MODEL_NAME'] = model_name
    
    try:
        # Import after setting env var
        from core.llm import get_llm
        
        print("✓ Import successful")
        
        # Get LLM instance
        llm = get_llm()
        print(f"✓ Model loaded: {llm.is_available()}")
        
        # Test generation
        print("\nTesting generation...")
        response = llm.generate_answer("Say hello in 3 words", max_tokens=10)
        print(f"✓ Generation works: '{response}'")
        
        return True
        
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run tests with both models."""
    print("Testing LLM refactoring...")
    
    # Test with Phi-3.5 first (verify no regression)
    phi_ok = test_with_model("Phi-3.5-mini-instruct-Q4_K_M.gguf")
    
    # Test with Qwen2.5 (new model)
    qwen_ok = test_with_model("qwen2.5-1.5b-instruct-q4_k_m.gguf")
    
    print("\n" + "="*60)
    print("RESULTS:")
    print(f"  Phi-3.5:  {'✓ PASS' if phi_ok else '✗ FAIL'}")
    print(f"  Qwen2.5:  {'✓ PASS' if qwen_ok else '✗ FAIL'}")
    print("="*60)
    
    if phi_ok and qwen_ok:
        print("\n🎉 All tests passed! Migration successful.")
        return 0
    else:
        print("\n⚠️  Some tests failed. Check errors above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
