# ayush_app/agents/mapping_agent.py

import asyncio
import re
from .tools import deterministic_lookup
from .icd_client import ICD11Client
from groq import Groq
import os
from pathlib import Path
from dotenv import load_dotenv

# Load env vars
ENV_PATH = Path(__file__).resolve().parents[4] / ".env"
if ENV_PATH.exists():
    load_dotenv(ENV_PATH)
else:
    load_dotenv()

client = ICD11Client()

# Initialize Groq client
groq_client = None
def get_groq_client():
    global groq_client
    if not groq_client:
        api_key = os.getenv("GROQ_API_KEY")
        if api_key:
            groq_client = Groq(api_key=api_key)
    return groq_client

async def async_icd(term):
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, client.search, term)

def normalize_ayush_term(term):
    """Normalize AYUSH term variants."""
    if not term:
        return term
    normalized = re.sub(r'\s+', ' ', term.strip())
    # Common synonym patterns
    normalized = re.sub(r'\bVata\s+Jwara\b', 'Vataja Jwara', normalized, flags=re.IGNORECASE)
    normalized = re.sub(r'\bPitta\s+Jwara\b', 'Pittaja Jwara', normalized, flags=re.IGNORECASE)
    normalized = re.sub(r'\bKapha\s+Jwara\b', 'Kaphaja Jwara', normalized, flags=re.IGNORECASE)
    return normalized

def extract_base_term(term):
    """Extract base term from compound AYUSH terms."""
    if not term:
        return term
    base = re.sub(r'\([^)]*\)', '', term).strip()
    base = re.sub(r'^(Vataja|Pittaja|Kaphaja|Vata|Pitta|Kapha)\s+', '', base, flags=re.IGNORECASE)
    base = re.sub(r'\s+', ' ', base).strip()
    return base if base else term

def derive_simple_from_title(title: str) -> str | None:
    """
    Derive a simple English search term from an ICD title, e.g.:
    - 'Fever (unspecified)' -> 'fever'
    - 'Fever with chills' -> 'fever'
    - 'Cough' -> 'cough'
    - 'Vitiligo' -> 'vitiligo'
    """
    if not title:
        return None
    t = title.lower()
    # Remove text in parentheses
    t = re.sub(r'\([^)]*\)', '', t)
    # Drop common adjectives / suffixes
    t = t.replace('acute ', '').replace('chronic ', '')
    t = t.replace('unspecified', '').replace('other or unknown', '')
    t = t.replace('disorder', '').replace('illness', '').replace('disease', '')
    # Keep first word as the core symptom/condition
    parts = re.findall(r'[a-z]+', t)
    if not parts:
        return None
    core = parts[0]
    return core

def derive_simple_from_csv(det) -> str | None:
    """
    Use deterministic CSV mapping to derive a simple English term
    to search in ICD API. This works even when Groq/LLM is not configured.
    """
    if not det:
        return None
    # Prefer primary if present, else first match
    row = det.get("primary") or (det.get("matches") or [None])[0]
    if not row:
        return None
    title = row.get("icd_title") or ""
    simple = derive_simple_from_title(title)
    if simple:
        print(f"🔎 Derived ICD search term '{simple}' from CSV title '{title}'")
    return simple

async def translate_ayush_to_english_simple(ayush_term, use_base_term=False):
    """Translate to simplest medical term."""
    try:
        groq = get_groq_client()
        if not groq:
            return None
        
        term_to_translate = extract_base_term(ayush_term) if use_base_term else ayush_term
        
        prompt = f"""Translate this Ayurvedic term to the SIMPLEST English medical word that ICD-11 would recognize.

Return ONLY a single, simple medical word (e.g., "fever", "cough", "diarrhea").
Do NOT use phrases.

Examples:
- "Vataja Jwara" → "fever"
- "Kaphaja Kasa" → "cough"
- "Pandu" → "anaemia"

Term: {term_to_translate}

Simple word:"""
        
        loop = asyncio.get_event_loop()
        resp = await loop.run_in_executor(
            None,
            lambda: groq.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=10,
                temperature=0
            )
        )
        
        english_term = resp.choices[0].message.content.strip()
        english_term = english_term.split()[0] if english_term.split() else english_term
        english_term = re.sub(r'[^a-zA-Z]', '', english_term)
        print(f"✅ Translated '{term_to_translate}' → '{english_term}'")
        return english_term.lower() if english_term else None
    except Exception as e:
        print(f"❌ Translation failed: {str(e)}")
        return None

async def translate_ayush_to_english_detailed(ayush_term):
    """Translate to detailed English term (for description matching)."""
    try:
        groq = get_groq_client()
        if not groq:
            return None
        
        prompt = f"""Translate this Ayurvedic term to a descriptive English medical phrase that ICD-11 would recognize.

Examples:
- "Vataja Jwara" → "fever with chills"
- "Kaphaja Kasa" → "productive cough"
- "Pittaja Jwara" → "fever with sweating"

Return ONLY the medical phrase, nothing else.

Term: {ayush_term}

Medical phrase:"""
        
        loop = asyncio.get_event_loop()
        resp = await loop.run_in_executor(
            None,
            lambda: groq.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=30,
                temperature=0
            )
        )
        
        english_term = resp.choices[0].message.content.strip()
        english_term = english_term.split('\n')[0].strip()
        english_term = re.sub(r'\([^)]*\)', '', english_term).strip()
        print(f"✅ Detailed translation '{ayush_term}' → '{english_term}'")
        return english_term.lower() if english_term else None
    except Exception as e:
        print(f"❌ Detailed translation failed: {str(e)}")
        return None

async def enrich_description_with_llm(code, title, translated_term):
    """Use LLM to understand if an ICD code matches the translated term."""
    try:
        groq = get_groq_client()
        if not groq:
            return None
        
        prompt = f"""Does this ICD-11 code match the medical term?

ICD Code: {code}
ICD Title: {title}
Medical Term: {translated_term}

Answer with ONLY "yes" or "no" and a brief reason (one sentence).

Format: yes/no - reason"""
        
        loop = asyncio.get_event_loop()
        resp = await loop.run_in_executor(
            None,
            lambda: groq.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=50,
                temperature=0
            )
        )
        
        result = resp.choices[0].message.content.strip()
        is_match = result.lower().startswith("yes")
        reason = result.split("-", 1)[1].strip() if "-" in result else ""
        
        return {
            "matches": is_match,
            "reason": reason,
            "enriched_description": f"{title}. {reason}" if reason else title
        }
    except Exception as e:
        print(f"❌ LLM enrichment failed for {code}: {str(e)}")
        return None

def prioritize_icd_results_by_description(results, translated_term, detailed_term=None):
    """
    Prioritize ICD results based on description matching.
    Priority order:
    1. Results where description contains the detailed translated term
    2. Results where description contains the simple translated term
    3. Generic/unspecified codes
    4. Other results
    """
    if not results:
        return results
    
    description_matches = []
    simple_matches = []
    generic_codes = []
    others = []
    
    # Keywords for generic/unspecified codes
    generic_keywords = ['unspecified', 'nos', 'not elsewhere classified', 'other or unknown']
    
    for r in results:
        title = (r.get("title") or "").lower()
        description = (r.get("description") or "").lower()
        code = r.get("code") or r.get("theCode", "")
        
        # Check if description matches detailed term
        if detailed_term and description:
            if detailed_term.lower() in description:
                description_matches.append(r)
                continue
        
        # Check if description matches simple term
        if translated_term and description:
            if translated_term.lower() in description:
                simple_matches.append(r)
                continue
        
        # Check if it's generic/unspecified
        is_generic = any(keyword in title for keyword in generic_keywords)
        is_base_code = code and '.' not in code.split('/')[0]
        
        if is_generic or is_base_code:
            generic_codes.append(r)
        else:
            others.append(r)
    
    # Combine in priority order
    prioritized = description_matches + simple_matches + generic_codes + others
    
    return prioritized

class MappingAgent:
    def __init__(self):
        pass

    async def run(self, ayush_term):
        """
        Enhanced mapping with description-based prioritization:
        1. Normalize term
        2. Translate to simple and detailed English
        3. Call ICD API
        4. Prioritize by description matching
        5. Enrich missing descriptions with LLM
        6. Fallback to CSV
        """
        print(f"🔍 Mapping Agent: Processing '{ayush_term}'")
        
        # Normalize
        normalized_term = normalize_ayush_term(ayush_term)
        base_term = extract_base_term(normalized_term)
        print(f"📝 Normalized: '{ayush_term}' → '{normalized_term}' (base: '{base_term}')")
        
        # Check CSV for specific mappings (also used to derive a simple ICD search term)
        csv_results = None
        det = deterministic_lookup(normalized_term)
        if det:
            csv_results = {
                "candidates": [
                    {
                        "code": m["icd_code"],
                        "title": m["icd_title"],
                        "source_term": m["ayush_term"],
                        "score": 0.6 if det.get("needs_review") else 0.8,
                        "source": "csv"
                    }
                    for m in det.get("matches", [])
                ],
                "needs_review": det.get("needs_review", False),
                "review_reason": det.get("review_reason")
            }
            print(f"📋 CSV found {len(csv_results['candidates'])} mappings")
        
        # Translate to simple term (for ICD API search) - try multiple strategies
        simple_term = None
        
        # Strategy 1: Try Groq translation of full term
        simple_term = await translate_ayush_to_english_simple(normalized_term, use_base_term=False)
        
        # Strategy 2: Try Groq translation of base term
        if not simple_term and base_term != normalized_term:
            simple_term = await translate_ayush_to_english_simple(base_term, use_base_term=True)
        
        # Strategy 3: Derive from CSV title (works even without Groq)
        if not simple_term:
            simple_term = derive_simple_from_csv(det)
        
        # Strategy 4: Last resort - use base term directly (might work for some terms)
        if not simple_term and base_term:
            # Try base term as-is (e.g., "Jwara" might work directly)
            simple_term = base_term.lower()
            print(f"🔎 Using base term '{simple_term}' directly for ICD API search")
        
        # Translate to detailed term (for description matching)
        detailed_term = await translate_ayush_to_english_detailed(normalized_term)
        
        # Call ICD API with simple term
        all_icd_results = []
        if simple_term:
            print(f"🌐 Calling ICD-11 API with: '{simple_term}'")
            try:
                results = await async_icd(simple_term)
                
                if results and isinstance(results, list) and len(results) > 0:
                    print(f"✅ ICD API returned {len(results)} results")
                    
                    # Prioritize by description matching
                    prioritized = prioritize_icd_results_by_description(
                        results, 
                        simple_term, 
                        detailed_term
                    )
                    
                    # Enrich results with LLM if description is missing
                    for r in prioritized[:5]:  # Process top 5
                        if not r.get("description"):
                            print(f"🤖 Enriching description for {r.get('code')} using LLM")
                            enrichment = await enrich_description_with_llm(
                                r.get("code"),
                                r.get("title"),
                                detailed_term or simple_term
                            )
                            if enrichment:
                                r["llm_enriched"] = True
                                r["llm_match"] = enrichment["matches"]
                                r["llm_reason"] = enrichment["reason"]
                                if enrichment["matches"]:
                                    # Boost score if LLM confirms match
                                    r["score"] = 0.9
                    
                    # Convert to candidate format
                    for r in prioritized:
                        code = r.get("code") or r.get("theCode")
                        title = r.get("title")
                        description = r.get("description")
                        
                        if code and title:
                            all_icd_results.append({
                                "code": code,
                                "title": title,
                                "description": description,  # Include description
                                "score": r.get("score", 0.8),
                                "english_term": simple_term,
                                "detailed_term": detailed_term,
                                "source": "icd_api",
                                "llm_enriched": r.get("llm_enriched", False),
                                "llm_match": r.get("llm_match"),
                                "llm_reason": r.get("llm_reason")
                            })
                    
                    print(f"✅ Prioritized {len(all_icd_results)} ICD API results")
            except Exception as e:
                print(f"❌ ICD API call failed: {str(e)}")
        
        # PRIORITIZE ICD API RESULTS - Only use CSV as fallback if ICD API returns nothing
        if all_icd_results:
            # ICD API returned results - use them as primary, CSV only as additional options
            all_candidates = all_icd_results.copy()
            if csv_results:
                # Add CSV candidates that aren't already in ICD results
                for csv_cand in csv_results["candidates"]:
                    if not any(c["code"] == csv_cand["code"] for c in all_candidates):
                        all_candidates.append(csv_cand)
            
            needs_review = len(all_candidates) > 1
            review_reason = None
            if len(all_icd_results) > 1:
                review_reason = f"ICD API returned {len(all_icd_results)} results. Please select the most appropriate ICD-11 code."
            
            print(f"✅ Using ICD API results (primary) with {len(all_icd_results)} ICD candidates")
            return {
                "candidates": all_candidates,
                "mapping_source": "icd11_search",  # Always icd11_search if we have ICD results
                "needs_manual_review": needs_review,
                "manual_review_reason": review_reason,
                "english_translation": simple_term,
                "detailed_translation": detailed_term
            }
        else:
            # ICD API returned no results - fallback to CSV
            if csv_results and csv_results.get("candidates"):
                print(f"⚠️ ICD API returned 0 results, falling back to CSV with {len(csv_results['candidates'])} candidates")
                return {
                    "candidates": csv_results["candidates"],
                    "mapping_source": "deterministic",
                    "needs_manual_review": csv_results.get("needs_review", False),
                    "manual_review_reason": csv_results.get("review_reason") or "ICD API returned 0 results. Using CSV fallback.",
                    "english_translation": None,
                    "detailed_translation": detailed_term
                }
            else:
                # No results from either source
                print(f"❌ No results from ICD API or CSV")
                return {
                    "candidates": [],
                    "mapping_source": "unknown"
                }
