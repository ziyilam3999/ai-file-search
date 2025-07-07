import pathlib

from llama_cpp import Llama

_PROJECT_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
_MODEL = _PROJECT_ROOT / "ai_models" / "Phi-3-mini-4k-instruct-q4.gguf"


def run_hello() -> None:
    """Generate a one-sentence greeting with Phi-3 Mini."""
    llm = Llama(model_path=str(_MODEL), n_ctx=2048, n_threads=4)
    out = llm.create_chat_completion(
        messages=[{"role": "user", "content": "Say hello in one sentence."}],
        max_tokens=32,
    )
    print(out["choices"][0]["message"]["content"].strip())


# Allow “python -m ai_file_search.hello” to work too
if __name__ == "__main__":
    run_hello()
