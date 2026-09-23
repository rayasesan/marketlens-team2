# MarketLens — Team 2

An **intelligence engine and Research Relevance API** based on MarketLens PRD v0.3 and the unified response contract in the [Team 1 repository](https://github.com/Mighty-Phoenix-team/Team-1). This service consumes Team 1's `GET /api/assets/{symbol}` endpoint. Team 2 does not store or use a Sectors API key.

## Current status

- **Implemented:** deterministic analysis, structured evidence, a documented relevance formula, SQLite research profiles, a configurable Discovery universe, My Assets, finding details, structured context for an explanation layer, upstream response caching, and deterministic reasoning without an LLM.
- **Not yet tested end to end:** the contract and fixture match the Team 1 repository, but the two services have not been run together against live Sectors data. `sample_payload_BBCA.json` has the same content as Team 1's fixture.
- **Not yet implemented:** the Next.js frontend and an LLM call for `Explain with AI`. The P0 engine and API work without an LLM. The complete MVP should not be described as finished yet.
- **Data limitation:** the BBCA fixture contains only one price/volume observation and one foreign-flow observation. The engine does not claim a price or volume change from one data point. It calculates the foreign-flow *imbalance level* on the observation date, not a trend or a claim that flow "turned positive."

## Run locally

Start the Team 1 backend on port 8000 using the instructions in its README. Keep `SECTORS_API_KEY` only in Team 1's backend environment. Then run Team 2 from this repository in a separate terminal:

```powershell
python -m pip install -r requirements.txt
$env:MARKETLENS_ASSET_API_BASE_URL = "http://127.0.0.1:8000"
$env:MARKETLENS_DISCOVERY_UNIVERSE = "BBCA,BBRI,BMRI,TLKM,ASII"
python -m uvicorn marketlens.api:app --host 127.0.0.1 --port 8001
```

`MARKETLENS_ASSET_API_BASE_URL` is the Team 1 backend **origin**, without `/api/assets`. The five tickers above are examples from the API audit, not a list hardcoded in the engine. Adjust the universe to symbols the running Team 1 backend supports. Profile horizons are limited to 2–90 days because Team 1 documents a 90-day maximum for historical Sectors data. `MARKETLENS_DB_PATH` (default: `marketlens.sqlite3`) and `MARKETLENS_CACHE_TTL_SECONDS` (default: `300`) are optional. Swagger UI is available at `http://127.0.0.1:8001/docs`.

API flow:

1. `POST /api/profiles` with `{"sectors":["Financials"],"research_focus":["growth","market_activity"],"horizon_days":30}`.
2. `GET /api/profiles/{id}/discovery` for Your Relevance Findings.
3. `PUT /api/profiles/{id}/assets/BBCA` to save an asset. A symbol can be saved even if it does not appear in Discovery.
4. `GET /api/profiles/{id}/assets` or `GET /api/profiles/{id}/assets/BBCA/finding` to analyze saved assets with the same engine.
5. `PUT /api/profiles/{id}` to update a research profile; `DELETE /api/profiles/{id}/assets/BBCA` to remove an asset.
6. `GET /api/profiles/{id}/assets/BBCA/explanation-context` to obtain the profile, finding, evidence, sources, timestamps, limitations, and claim boundaries for an explanation layer. This endpoint **does not call an LLM**.

## Method and assumptions

The engine uses three evidence groups verified in the API audit:

| Group | Metrics | Requirement | Normalization threshold |
|---|---|---|---:|
| Fundamental | Revenue, earnings, and EPS growth from the company report | Numeric value available | 10% |
| Market Activity | Price and volume change | Two different dates and a positive baseline | 5% for price; 50% for volume |
| Investor Flow | `net_foreign_inflow / (foreign_buy_idr + foreign_sell_idr)` | Valid buy/sell amounts on one date | 20% |

Each metric has `strength = min(abs(value) / threshold, 1)`. A group's strength is its highest available metric strength. Magnitudes are **direction-neutral**: a large decline is not presented as positive investment quality. Thresholds and weights are in `marketlens/methodology.json`. They are MVP methodology assumptions and have not been empirically calibrated.

`Research Relevance = 10 × [Σ(group strength × focus weight) / Σ(focus weight)] × (available groups / 3) × sector factor`, rounded to two decimals. The focus weight is 1 for a selected group and 0.4 for other groups; when no focus is selected, all weights are 1. The sector factor is 1 when no sector filter is set or the sector matches, and 0.5 otherwise. `horizon_days` sets the date range requested from Team 1; Team 1 is expected to limit data to that range. Discovery sorts by descending score and then alphabetically by ticker. Assets without evidence are excluded from Discovery findings.

Each evidence item includes a value, baseline where relevant, period, calculation method, source endpoint, observation timestamp when available, and retrieval timestamp. If the company report does not provide a financial reporting date, the engine says "year-over-year quarter (source supplied)" rather than inventing one. `limitations` carries forward Team 1's limitations and adds methodological ones. The engine does not infer causes, predict returns, or recommend trades.

## MVP boundary and structured grounding

The two-dashboard roadmap dated 23 September 2026 is a draft and has not received final approval. Its immediate direction is reflected here: the Intelligence Dashboard and Watchlist/My Assets use the same analysis engine, and the explanation layer can receive a structured package from `explanation-context`. That package contains measured data and explicitly states that market and foreign-flow measurements alone do not establish why a change occurred. If an LLM is connected later, it must explain the supplied evidence without inventing numbers or causes.

Document Intelligence/RAG (company documents, embeddings, a vector database, and retrieval), cross-dashboard comparisons, and historical research memory are future work after both dashboards are stable. The draft roadmap also mentions `Stability` and `Dividend` research focuses; these are not added to scoring until supporting metrics are verified and the scope change is approved.

## Integration checks before the demo

- Team 1 currently provides `symbol`, `company`, `market`, `foreign_flow`, `limitations`, and `source_endpoints`, and accepts `start`/`end` parameters. Historical price, volume, and flow rows must include an ISO `observed_at` date.
- Team 1 source code is available, but a running live endpoint and Sectors credentials are not included here. Test against the real backend before the demo.
- The sample payload is a **test fixture**, not live market data. Do not present it as current data in the UI or demo.
- The cache is local to one process. If deploying multiple workers, consider a shared cache to manage API credits consistently.

## Tests

```powershell
python -m pytest -q
```
