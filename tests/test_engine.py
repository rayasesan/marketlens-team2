import copy
import json
from pathlib import Path

from marketlens.engine import analyze_asset, rank_assets


SAMPLE = json.loads((Path(__file__).resolve().parents[1] / "sample_payload_BBCA.json").read_text())
PROFILE = {"sectors": ["Financials"], "research_focus": ["growth", "market_activity"]}


def test_single_point_does_not_create_market_change():
    finding = analyze_asset(SAMPLE, PROFILE, retrieved_at="2026-09-23T00:00:00Z")
    assert not any(e["group"] == "market_activity" for e in finding["evidence"])
    assert any("at least two" in item for item in finding["limitations"])
    assert any(e["metric"] == "foreign_imbalance" for e in finding["evidence"])
    assert all(e["source"] and e["retrieved_at"] for e in finding["evidence"])


def test_market_change_requires_real_baseline():
    payload = copy.deepcopy(SAMPLE)
    payload["market"].insert(0, {"observed_at": "2026-09-01", "price": 6000, "volume": 40000000})
    finding = analyze_asset(payload, PROFILE)
    price = next(e for e in finding["evidence"] if e["metric"] == "price_change")
    assert round(price["value"], 6) == 0.0375
    assert price["baseline"] == 6000


def test_profile_changes_relevance_and_ranking_is_deterministic():
    growth = analyze_asset(SAMPLE, {"sectors": ["Financials"], "research_focus": ["growth"]})
    flow = analyze_asset(SAMPLE, {"sectors": ["Financials"], "research_focus": ["flow"]})
    assert growth["research_relevance"] != flow["research_relevance"]
    other = copy.deepcopy(SAMPLE)
    other["symbol"] = "AAAA"
    assert [x["symbol"] for x in rank_assets([SAMPLE, other], PROFILE)] == ["AAAA", "BBCA"]
