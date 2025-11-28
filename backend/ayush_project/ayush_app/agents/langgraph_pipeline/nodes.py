# agents/langgraph_pipeline/nodes.py
import asyncio
from typing import Dict, Any
from concurrent.futures import ThreadPoolExecutor

from ..extraction_agent import ExtractionAgent
from ..mapping_agent import MappingAgent
from ..validation_agent import ValidationAgent
from ..output_agent import OutputAgent

import os
GROQ_KEY = os.getenv("GROQ_API_KEY")

# small thread pool for blocking IO calls
_executor = ThreadPoolExecutor(max_workers=6)

async def run_in_thread(func, *args, **kwargs):
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(_executor, lambda: func(*args, **kwargs))


# -------------------------
# NODE: Extract AYUSH Term
# -------------------------
async def extract_node(state: Dict[str, Any]):
    try:
        extractor = ExtractionAgent(GROQ_KEY)
        # extractor.run is sync -> run in thread
        ayush = await run_in_thread(extractor.run, state["raw_text"])
        state["ayush_term"] = ayush
        state.setdefault("provenance", []).append({"step": "extract", "value": ayush})
    except Exception as e:
        print(f"Extraction node error: {str(e)}")
        state["ayush_term"] = state.get("raw_text", "Unknown")[:50]
        state.setdefault("provenance", []).append({"step": "extract", "error": str(e)})
    return state


# -------------------------
# NODE: Map to ICD
# -------------------------
async def mapping_node(state: Dict[str, Any]):
    try:
        mapper = MappingAgent()
        # mapping_agent.run is async in your code -> await it
        result = await mapper.run(state.get("ayush_term", ""))
        state["candidates"] = result.get("candidates", [])
        state["mapping_source"] = result.get("mapping_source", "unknown")
        state["needs_manual_review"] = result.get("needs_manual_review", False)
        # Store translations in state
        if result.get("english_translation"):
            state["english_translation"] = result.get("english_translation")
        if result.get("detailed_translation"):
            state["detailed_translation"] = result.get("detailed_translation")
        if result.get("manual_review_reason"):
            state.setdefault("review_reasons", []).append(result["manual_review_reason"])
        if state.get("needs_manual_review"):
            state["manual_review_candidates"] = result.get("candidates", [])
        state.setdefault("provenance", []).append({"step": "mapping", "value": result})
    except Exception as e:
        print(f"Mapping node error: {str(e)}")
        state["candidates"] = []
        state["mapping_source"] = "error"
        state["needs_manual_review"] = True
        state.setdefault("review_reasons", []).append("Mapping agent failed; manual review required.")
        state.setdefault("provenance", []).append({"step": "mapping", "error": str(e)})
    return state


# -------------------------
# NODE: Validate
# -------------------------
async def validation_node(state: Dict[str, Any]):
    try:
        validator = ValidationAgent(GROQ_KEY)
        # validator.run is sync -> run in thread
        out = await run_in_thread(validator.run, state.get("ayush_term", ""), state.get("raw_text", ""), state.get("candidates", []))
        state["best"] = out.get("best", {"code": "UNK"})
        state["confidence"] = out.get("confidence", 0.0)
        state["reason"] = out.get("reason", "")
        manual_flag = state.get("needs_manual_review", False)
        state["needs_human_review"] = out.get("needs_human_review", True) or manual_flag
        if manual_flag and state.get("review_reasons"):
            state.setdefault("provenance", []).append({"step": "manual_review", "value": state["review_reasons"]})
        state.setdefault("provenance", []).append({"step": "validation", "value": out})
    except Exception as e:
        print(f"Validation node error: {str(e)}")
        # Use first candidate if available, otherwise UNK
        candidates = state.get("candidates", [])
        state["best"] = candidates[0] if candidates else {"code": "UNK", "title": "Error"}
        state["confidence"] = 0.0
        state["reason"] = f"Validation failed: {str(e)}"
        state["needs_human_review"] = True
        state.setdefault("provenance", []).append({"step": "validation", "error": str(e)})
    return state


# -------------------------
# NODE: Output (FHIR + push)
# -------------------------
async def output_node(state: Dict[str, Any]):
    try:
        agent = OutputAgent()
        # agent.run is sync -> run in thread
        out = await run_in_thread(agent.run, state, patient_ref=state.get("patient_ref", "Patient/example"), auto_push=state.get("auto_push", False))
        state["fhir"] = out.get("fhir")
        state["pushed"] = out.get("pushed", False)
        state["push_response"] = out.get("push_response")
        state.setdefault("provenance", []).append({"step": "output", "value": out})
    except Exception as e:
        print(f"Output node error: {str(e)}")
        state["fhir"] = None
        state["pushed"] = False
        state["push_response"] = {"error": str(e)}
        state.setdefault("provenance", []).append({"step": "output", "error": str(e)})
    return state
