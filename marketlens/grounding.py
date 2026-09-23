"""Structured, source-bound input for an optional explanation layer."""

from __future__ import annotations


def build_explanation_context(profile: dict, finding: dict) -> dict:
    """Expose measured facts and boundaries without producing an AI answer."""
    return {
        "research_profile": {
            "sectors": profile.get("sectors", []),
            "research_focus": profile.get("research_focus", []),
            "horizon_days": profile.get("horizon_days"),
        },
        "finding": {
            "symbol": finding["symbol"],
            "company_name": finding["company_name"],
            "sector": finding["sector"],
            "research_relevance": finding["research_relevance"],
            "relevance_reason": finding["relevance_reason"],
            "observation": finding["observation"],
            "evidence": finding["evidence"],
            "reasoning": finding["reasoning"],
            "method": finding["method"],
            "source_endpoints": finding["source_endpoints"],
            "retrieved_at": finding["retrieved_at"],
            "limitations": finding["limitations"],
        },
        "evidence_boundary": {
            "scope": "Measured market and company-report evidence in this finding only.",
            "causal_explanation_available": False,
            "document_context_available": False,
            "instructions": [
                "Use only the supplied evidence for numerical claims and cite its source and period.",
                "Explain research relevance as a match to the profile, not investment quality.",
                "If asked why a market metric moved, say that these measurements do not establish its cause.",
                "State unavailable metrics and limitations explicitly; do not fill gaps with invented facts.",
                "Do not give buy or sell instructions, price targets, or return predictions.",
            ],
        },
    }
