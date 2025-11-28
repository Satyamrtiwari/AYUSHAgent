from typing import List, Dict, Any, TypedDict, Optional

class PipelineState(TypedDict, total=False):
    raw_text: str
    ayush_term: str
    candidates: List[Dict[str, Any]]
    best: Dict[str, Any]
    confidence: float
    reason: str
    needs_human_review: bool
    needs_manual_review: bool
    manual_review_candidates: List[Dict[str, Any]]
    review_reasons: List[str]
    manual_review_selected: Dict[str, Any]
    mapping_source: str
    fhir: Dict[str, Any]
    pushed: bool
    push_response: Any
    provenance: List[Dict[str, Any]]
    patient_ref: str
    auto_push: bool
