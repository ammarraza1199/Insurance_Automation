from openai import OpenAI # type: ignore
import os # type: ignore

# Set up standard OpenAI client but point it to a local Ollama instance
# Default points to a local Ollama server running phi3 or mistral
OLLAMA_BASE_URL = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434/v1")
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "phi3")

client = OpenAI(
    base_url=OLLAMA_BASE_URL,
    api_key="ollama"  # api key is ignored but required by the openai client library
)

def get_cpt_details(cpt_code: str) -> str:
    try:
        response = client.chat.completions.create(
            model=OLLAMA_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": "You are a professional medical coding and billing assistant. When provided a CPT code, provide a clear, concise medical description of the procedure and typical use cases. Do not hallucinate."
                },
                {
                    "role": "user",
                    "content": f"Please provide the description and medical context for CPT code: {cpt_code}"
                }
            ],
            temperature=0.2, # Low temperature for more factual, less creative outputs
            max_tokens=300
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"Error querying LLM: {e}")
        return "Failed to fetch description from local LLM. Please make sure Ollama is running."
