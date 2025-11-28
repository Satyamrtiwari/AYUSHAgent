# agents/extraction_agent.py
import os
from pathlib import Path
from dotenv import load_dotenv
from groq import Groq

ENV_PATH = Path(__file__).resolve().parents[4] / ".env"
if ENV_PATH.exists():
    load_dotenv(ENV_PATH)
else:
    load_dotenv()

from .tools import find_term_in_text

DEFAULT_MODEL = os.getenv("GROQ_EXTRACTION_MODEL", "llama-3.3-70b-versatile")


class ExtractionAgent:
    def __init__(self, groq_api_key=None):
        api_key = groq_api_key or os.getenv("GROQ_API_KEY")
        self.client = Groq(api_key=api_key) if api_key else None

    def run(self, text):
        """
        Always tries Groq API first. Only falls back to CSV if Groq API fails.
        """
        prompt = f"Extract only the AYUSH disease term from this text: {text}"
        
        # Step 1: ALWAYS try Groq API first (real API call)
        try:
            if not self.client:
                raise RuntimeError("Groq client missing - check GROQ_API_KEY in .env")
            
            resp = self.client.chat.completions.create(
                model=DEFAULT_MODEL,
                messages=[{"role": "user", "content": prompt}],
            max_tokens=20,
                temperature=0,
        )
            
            extracted = resp.choices[0].message.content.strip()
            if extracted:
                return extracted
        except Exception as e:
            # Log error but continue to CSV fallback
            print(f"Groq API call failed for extraction: {str(e)}")
            # Continue to CSV fallback below
        
        # Step 2: Fallback to CSV ONLY if Groq API failed
        fallback = find_term_in_text(text)
        if fallback:
            return fallback
        
        # Last resort: return original text
        return text
