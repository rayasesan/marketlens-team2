import copy
import json
from pathlib import Path

from fastapi.testclient import TestClient

from marketlens import api


SAMPLE = json.loads((Path(__file__).resolve().parents[1] / "sample_payload_BBCA.json").read_text())


def test_profile_assets_and_shared_engine(tmp_path, monkeypatch):
    monkeypatch.setenv("MARKETLENS_DB_PATH", str(tmp_path / "profiles.sqlite3"))
    monkeypatch.setenv("MARKETLENS_DISCOVERY_UNIVERSE", "BBCA")

    async def fake_fetch(symbol, horizon_days):
        payload = copy.deepcopy(SAMPLE)
        payload["_marketlens_retrieved_at"] = "2026-09-23T00:00:00Z"
        return payload

    monkeypatch.setattr(api, "fetch_asset", fake_fetch)
    client = TestClient(api.app)
    profile = client.post("/api/profiles", json={"sectors": ["Financials"], "research_focus": ["growth"], "horizon_days": 30}).json()
    profile_id = profile["id"]
    assert client.put(f"/api/profiles/{profile_id}/assets/BBCA").status_code == 200
    discovery = client.get(f"/api/profiles/{profile_id}/discovery").json()["findings"][0]
    assets = client.get(f"/api/profiles/{profile_id}/assets").json()["findings"][0]
    assert discovery == assets
    assert client.get(f"/api/profiles/{profile_id}").json()["saved_assets"] == ["BBCA"]
    assert client.delete(f"/api/profiles/{profile_id}/assets/BBCA").json()["saved_assets"] == []


def test_profile_horizon_respects_team1_series_limit(tmp_path, monkeypatch):
    monkeypatch.setenv("MARKETLENS_DB_PATH", str(tmp_path / "profiles.sqlite3"))
    client = TestClient(api.app)
    body = {"sectors": [], "research_focus": [], "horizon_days": 91}
    assert client.post("/api/profiles", json=body).status_code == 422
    body["horizon_days"] = 90
    assert client.post("/api/profiles", json=body).status_code == 201


def test_explanation_context_uses_only_structured_finding(tmp_path, monkeypatch):
    monkeypatch.setenv("MARKETLENS_DB_PATH", str(tmp_path / "profiles.sqlite3"))

    async def fake_fetch(symbol, horizon_days):
        payload = copy.deepcopy(SAMPLE)
        payload["_marketlens_retrieved_at"] = "2026-09-23T00:00:00Z"
        return payload

    monkeypatch.setattr(api, "fetch_asset", fake_fetch)
    client = TestClient(api.app)
    profile = client.post("/api/profiles", json={"sectors": ["Financials"], "research_focus": ["growth"], "horizon_days": 30}).json()
    path = f"/api/profiles/{profile['id']}/assets/BBCA"
    finding = client.get(f"{path}/finding").json()
    context = client.get(f"{path}/explanation-context").json()
    assert context["finding"]["evidence"] == finding["evidence"]
    assert context["finding"]["limitations"] == finding["limitations"]
    assert context["evidence_boundary"]["causal_explanation_available"] is False
    assert context["evidence_boundary"]["document_context_available"] is False
    assert "api_key" not in str(context).lower()
