# agents/validation_agent.py
import json
import os
from pathlib import Path
from dotenv import load_dotenv
from groq import Groq

ENV_PATH = Path(__file__).resolve().parents[4] / ".env"
if ENV_PATH.exists():
    load_dotenv(ENV_PATH)
else:
    load_dotenv()

DEFAULT_MODEL = os.getenv("GROQ_VALIDATION_MODEL", "llama-3.3-70b-versatile")


class ValidationAgent:
    def __init__(self, groq_api_key=None):
        api_key = groq_api_key or os.getenv("GROQ_API_KEY")
        self.client = Groq(api_key=api_key) if api_key else None

    def run(self, ayush_term, raw_text, candidates):
        # If no candidates, return early
        if not candidates:
            return {
                "best": {"code": "UNK", "title": "Unknown"},
                "confidence": 0.0,
                "reason": "No mapping candidates found",
                "needs_human_review": True
            }
        
        # ALWAYS try Groq API validation first (real API call)
        # Even for single deterministic candidates, validate with Groq to ensure accuracy
        # Build better prompt for LLM validation
        prompt_text = f"""You are a medical coding expert. Given an AYUSH term "{ayush_term}" and clinical context: "{raw_text[:200]}", 
evaluate these ICD-11 mapping candidates and return ONLY valid JSON:
{{
    "best_index": <0-based index of best match>,
    "confidence": <0.0-1.0>,
    "reason": "<brief explanation>"
}}

Candidates:
{json.dumps(candidates, indent=2)}

Return ONLY the JSON object, no other text."""

        try:
            if not self.client:
                raise RuntimeError("Groq client missing - check GROQ_API_KEY in .env")
            
            # ALWAYS make real Groq API call for validation
            resp = self.client.chat.completions.create(
                model=DEFAULT_MODEL,
                messages=[{"role": "user", "content": prompt_text}],
                temperature=0,
                max_tokens=200
            )
            content = resp.choices[0].message.content.strip()
            # Remove markdown code blocks if present
            if content.startswith("```"):
                content = content.split("```")[1]
                if content.startswith("json"):
                    content = content[4:]
            content = content.strip()
            js = json.loads(content)
        except json.JSONDecodeError as e:
            # If JSON parsing fails, use first candidate with lower confidence
            return {
                "best": candidates[0] if candidates else {"code": "UNK"},
                "confidence": candidates[0].get("score", 0.7) if candidates else 0.5,
                "reason": f"LLM validation failed: JSON parse error. Using first candidate.",
                "needs_human_review": True
            }
        except Exception as e:
            # Fallback ONLY if Groq API fails - use first candidate with its score
            print(f"Groq API validation failed for '{ayush_term}': {str(e)}")
            fallback_confidence = candidates[0].get("score", 0.80) if candidates else 0.5
            return {
                "best": candidates[0] if candidates else {"code": "UNK"},
                "confidence": fallback_confidence,
                "reason": f"Groq API validation failed: {str(e)[:50]}. Using candidate without LLM validation.",
                "needs_human_review": True  # Always require review if API fails
            }

        idx = int(js.get("best_index", 0))
        if idx < 0 or idx >= len(candidates):
            idx = 0
        best = candidates[idx]
        # Use candidate's base score if available, otherwise use LLM confidence
        base_score = best.get("score", 0.80)
        llm_confidence = float(js.get("confidence", base_score))
        # Use the candidate's base score (from deterministic/ICD API) as the confidence
        # LLM validation confirms the selection but doesn't change the confidence
        conf = base_score
        
        return {
            "best": best,
            "confidence": conf,
            "reason": js.get("reason", "Validated by LLM"),
            "needs_human_review": conf < 0.9
        }
