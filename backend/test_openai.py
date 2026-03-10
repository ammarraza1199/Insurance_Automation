import os
import sys
sys.path.insert(0, '.')

# No env vars needed – Ollama is used with hardcoded base_url in code
import llm_service
import authorization_service

print("=== CPT Description (phi3 via Ollama) ===")
try:
    result = llm_service.get_cpt_details("99213")
    print(result)
except Exception as e:
    print("Error:", e)

print()
print("=== Authorization Check (phi3 via Ollama) ===")
try:
    result2 = authorization_service.check_authorization(
        "99213",
        ["J01.90"],
        "Patient has acute sinusitis with persistent symptoms for more than 10 days."
    )
    print(result2)
except Exception as e:
    print("Error:", e)
