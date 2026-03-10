"""
Module 8: CPT Authorization Engine
Uses local Ollama LLM to reason medical necessity and predict authorization outcome.
Outputs: Approved / Denied / Manual Review + confidence score + reason.
"""
from openai import OpenAI # type: ignore
import os # type: ignore
import json # type: ignore
import re # type: ignore

OLLAMA_BASE_URL = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434/v1")
OLLAMA_MODEL    = os.environ.get("OLLAMA_MODEL", "phi3")

client = OpenAI(
    base_url=OLLAMA_BASE_URL,
    api_key="ollama"
)


def check_authorization(cpt_code: str, diagnosis_codes: list, medical_summary: str) -> dict:
    """
    Uses the local LLM to evaluate whether a CPT procedure will be authorized.
    Returns authorization_status, confidence_score (0-1), and reason.
    """
    diagnosis_str = ", ".join(diagnosis_codes) if diagnosis_codes else "Not specified"

    system_prompt = (
        "You are a senior medical insurance reviewer AI. Your job is to evaluate whether a procedure "
        "request meets medical necessity criteria and should be authorized by the insurance payer.\n\n"
        "Respond ONLY with a valid JSON object (no markdown, no extra text) in this exact format:\n"
        '{"authorization_status": "Approved", "confidence_score": 0.87, "reason": "Brief clinical justification"}\n\n'
        'authorization_status must be exactly one of: "Approved", "Denied", "Manual Review"\n'
        "confidence_score must be a float between 0.0 and 1.0\n"
        "reason must be a concise 1-2 sentence clinical justification."
    )

    user_prompt = (
        f"CPT Code: {cpt_code}\n"
        f"Diagnosis Codes: {diagnosis_str}\n"
        f"Medical Summary: {medical_summary}\n\n"
        "Based on the clinical information above, evaluate medical necessity and provide your authorization decision."
    )

    try:
        response = client.chat.completions.create(
            model=OLLAMA_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user",   "content": user_prompt},
            ],
            temperature=0.1,
            max_tokens=300,
        )
        content = response.choices[0].message.content.strip()
        result  = _parse_auth_response(content, cpt_code)
        return result

    except Exception as e:
        print(f"[Authorization Engine] LLM error: {e}")
        return _fallback_auth(cpt_code, diagnosis_codes, medical_summary)


def _parse_auth_response(content: str, cpt_code: str) -> dict:
    """Parse LLM JSON response with fallback."""
    # Strip markdown code fences if present
    content = re.sub(r'```[a-z]*\n?', '', content).strip()

    try:
        data = json.loads(content)
        status = data.get("authorization_status", "Manual Review")
        if status not in ("Approved", "Denied", "Manual Review"):
            status = "Manual Review"
        score = float(data.get("confidence_score", 0.5))
        score = max(0.0, min(1.0, score))
        reason = data.get("reason", "Review required.")
        return {
            "cpt_code":             cpt_code,
            "authorization_status": status,
            "confidence_score":     round(score, 2), # type: ignore
            "reason":               reason,
            "source":               "LLM",
        }
    except (json.JSONDecodeError, ValueError):
        # Try to extract status from plain text
        cl = content.lower()
        # Ensure string slicing is safe
        max_len = 200
        safe_reason = content[0:max_len] # type: ignore
        
        if "approved" in cl:
            return {"cpt_code": cpt_code, "authorization_status": "Approved",      "confidence_score": 0.70, "reason": safe_reason, "source": "LLM-text"}
        elif "denied" in cl:
            return {"cpt_code": cpt_code, "authorization_status": "Denied",        "confidence_score": 0.70, "reason": safe_reason, "source": "LLM-text"}
        else:
            return {"cpt_code": cpt_code, "authorization_status": "Manual Review", "confidence_score": 0.50, "reason": safe_reason, "source": "LLM-text"}


def _fallback_auth(cpt_code: str, diagnosis_codes: list, medical_summary: str) -> dict:
    """Rule-based fallback when LLM is unavailable."""
    # Very basic heuristics
    summary_lower = (medical_summary or "").lower()
    urgent_keywords = ["emergency", "urgent", "critical", "severe", "acute", "persistent"]
    denial_keywords = ["cosmetic", "elective", "optional", "aesthetic"]

    has_urgent  = any(w in summary_lower for w in urgent_keywords)
    has_denial  = any(w in summary_lower for w in denial_keywords)

    if has_denial:
        return {
            "cpt_code": cpt_code,
            "authorization_status": "Denied",
            "confidence_score": 0.72,
            "reason": "Procedure appears cosmetic/elective and may not meet medical necessity criteria.",
            "source": "Rule-based fallback",
        }
    elif has_urgent or len(diagnosis_codes) > 0:
        return {
            "cpt_code": cpt_code,
            "authorization_status": "Approved",
            "confidence_score": 0.65,
            "reason": "Clinical indicators suggest medical necessity. LLM unavailable — rule-based approval.",
            "source": "Rule-based fallback",
        }
    else:
        return {
            "cpt_code": cpt_code,
            "authorization_status": "Manual Review",
            "confidence_score": 0.50,
            "reason": "Insufficient clinical information for automated decision. Manual review recommended.",
            "source": "Rule-based fallback",
        }
