from llama_cpp import Llama
import pathlib

model_path = pathlib.Path(__file__).parent / "ai_models" / "Phi-3-mini-4k-instruct-q4.gguf"

llm = Llama(
    model_path=str(model_path),
    n_ctx=2048,
    n_threads=4
)

output = llm.create_chat_completion(
    messages=[
        {"role": "user", "content": "Say hello in one sentence."}
    ],
    max_tokens=32
)

print(output["choices"][0]["message"]["content"].strip())
