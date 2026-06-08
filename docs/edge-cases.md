# Edge Cases: AI-Powered Restaurant Recommendation (Epicurean Pulse)

Catalog of boundary conditions, failure modes, and abnormal inputs for the Zomato milestone project (Epicurean Pulse). Use this during implementation and testing alongside [context.md](./context.md), [architecture.md](./architecture.md), [design.md](./design.md), and [implementation-plan.md](./implementation-plan.md).

**Conventions**

| Column | Meaning |
|--------|---------|
| **ID** | Stable identifier for tests and issues (e.g. `EC-ING-01`) |
| **Severity** | `critical` — data loss or wrong recommendations; `high` — broken flow; `medium` — degraded UX; `low` — cosmetic or rare |
| **Expected behavior** | What v1 should do per architecture |

---

## 1. Data ingestion and restaurant store

| ID | Edge case | Severity | Expected behavior |
|----|-----------|----------|-------------------|
| EC-ING-01 | Hugging Face unreachable (network down, DNS failure) | critical | Fail with clear error; do not write partial/corrupt cache; suggest retry and offline fixture for dev |
| EC-ING-02 | HF dataset URL changed or dataset removed | critical | Log HTTP/404; fail ingestion; document `DATASET_URL` override in README |
| EC-ING-03 | HF schema changed (column names missing or renamed) | critical | Normalizer maps known columns; log unmapped columns; fail if required fields cannot be derived |
| EC-ING-04 | Empty dataset returned (0 rows) | critical | Abort ingestion; `IngestionReport` with error; app refuses recommendations until fixed |
| EC-ING-05 | All rows missing `name`, `location`, or `rating` after clean | critical | Same as EC-ING-04 |
| EC-ING-06 | Duplicate restaurants (same name + location) | medium | Deduplicate by stable `id`; keep first or highest-rated row (document choice in code) |
| EC-ING-07 | Duplicate `id` after hash collision (extremely rare) | low | Append suffix or use secondary key; log collision |
| EC-ING-08 | `rating` non-numeric (`"4.5/5"`, `"-"`, empty) | high | Parse best-effort; drop row if unrated and rating required for catalog |
| EC-ING-09 | `rating` out of expected range (e.g. 6.0, negative) | medium | Clamp or drop per config; document in normalizer |
| EC-ING-10 | Cost field missing | high | Set `approx_cost` null; exclude from budget filter or assign default band `unknown` |
| EC-ING-11 | Cost unparsable (`"₹300-600"`, `"$$$"`) | high | Parse range lower bound or mark unknown; do not crash ingestion |
| EC-ING-12 | `cuisines` as string vs list vs null | medium | Normalize to `list[str]`; empty list → row kept but may fail cuisine filter later |
| EC-ING-13 | Very long `name` or `location` strings | low | Trim to max length for storage; preserve full string in raw backup if needed |
| EC-ING-14 | Special characters / Unicode in names (emoji, Devanagari) | medium | UTF-8 throughout; no mojibake in Parquet or UI |
| EC-ING-15 | `FORCE_REFRESH=true` while app serving requests | medium | v1: run ingestion only at startup; document no hot reload |
| EC-ING-16 | Corrupt or truncated Parquet cache file | high | Detect on load; delete or ignore cache; re-run ingestion or fail with repair instructions |
| EC-ING-17 | `CACHE_PATH` points to read-only or missing parent directory | high | Create parent dir if possible; else fail with permission error |
| EC-ING-18 | Disk full during Parquet write | critical | Do not replace existing cache atomically; write to temp then rename |
| EC-ING-19 | Cache exists but older than dataset (stale) | low | v1: manual `FORCE_REFRESH`; future: version metadata in cache |
| EC-ING-20 | Dataset larger than available RAM | high | v1: document max size; use chunked read or SQLite if profiling shows risk |
| EC-ING-21 | Single-city dataset but user expects pan-India | medium | Document coverage in README; no fake cities in results |

### Store read path

| ID | Edge case | Severity | Expected behavior |
|----|-----------|----------|-------------------|
| EC-STR-01 | Store not loaded before `get_all()` | critical | Orchestrator always calls `run_if_needed()` first |
| EC-STR-02 | `get_by_id` for unknown id | medium | Return `None`; engine drops recommendation; log warning |
| EC-STR-03 | Concurrent reads (Streamlit rerun) | medium | Read-only store after load; no mutation during request |

---

## 2. User input and validation

| ID | Edge case | Severity | Expected behavior |
|----|-----------|----------|-------------------|
| EC-INP-01 | Empty `location` | high | Pydantic validation error; UI blocks submit |
| EC-INP-02 | `location` whitespace only (`"   "`) | high | Treat as empty; validation error |
| EC-INP-03 | `location` very long (>500 chars) | medium | Reject or truncate at max length (e.g. 200) |
| EC-INP-04 | `location` with injection-like content (`<script>`, SQL fragments) | medium | Store as plain text; escape on HTML render; no eval |
| EC-INP-05 | Unknown city not in dataset (`"Tokyo"`) | high | Filter returns zero candidates → `no_matches` (not LLM hallucination) |
| EC-INP-06 | City alias mismatch (`"Bengaluru"` vs `"Bangalore"`) | high | Use `LOCATION_ALIASES` if configured; else substring match may still fail → document supported names |
| EC-INP-07 | Location substring false positive (`"Del"` matches `"Model Town, Delhi"`) | medium | Prefer `city` field exact match when available; document substring behavior |
| EC-INP-08 | Empty `cuisine` | high | Validation error |
| EC-INP-09 | Cuisine case mismatch (`"north indian"` vs `"North Indian"`) | medium | Case-insensitive substring match in filter |
| EC-INP-10 | Multi-word cuisine (`"North Indian"`) | medium | Match against combined cuisine string or list tokens |
| EC-INP-11 | Invalid `budget` (not low/medium/high) | high | Enum validation error |
| EC-INP-12 | `min_rating` below 0 or above dataset max (e.g. 5.5) | high | Clamp to [0, 5] or reject with message |
| EC-INP-13 | `min_rating` = 0 | medium | Allow; returns all ratings ≥ 0 |
| EC-INP-14 | `min_rating` = 5.0 (very strict) | medium | Valid; often yields `no_matches` |
| EC-INP-15 | `additional_preferences` null vs empty string | low | Treat both as “no extra prefs” for prompt |
| EC-INP-16 | `additional_preferences` extremely long (>2000 chars) | medium | Truncate for prompt with warning; bound token size |
| EC-INP-17 | `additional_preferences` contradicts hard filters (“cheap” + budget high) | low | LLM may reconcile in explanation; filters unchanged |
| EC-INP-18 | Non-ASCII / emoji in additional prefs | low | Pass through UTF-8 to LLM |
| EC-INP-19 | Streamlit double-click / duplicate submit | medium | Disable button while request in flight; idempotent display |
| EC-INP-20 | Missing `.env` / invalid API key at submit time | critical | Error before or after LLM call with setup instructions |

---

## 3. Filter and prepare service

| ID | Edge case | Severity | Expected behavior |
|----|-----------|----------|-------------------|
| EC-FLT-01 | Zero restaurants after all filters | high | `status=no_matches`; user message with suggestions (relax rating, cuisine, budget); **no LLM call** |
| EC-FLT-02 | Exactly one restaurant matches | medium | Pass single candidate to LLM; return 1 result (not pad to TOP_N with fictions) |
| EC-FLT-03 | More than `MAX_CANDIDATES` match (e.g. 200) | medium | Sort by rating desc; cap at 20; document that LLM sees subset |
| EC-FLT-04 | All matches have null `rating` | high | Excluded by min_rating filter → likely `no_matches` |
| EC-FLT-05 | Restaurant rating equals `min_rating` (boundary) | low | Include (`>=`) |
| EC-FLT-06 | Budget filter excludes all but location+cuisine matched | high | `no_matches`; message mentions budget |
| EC-FLT-07 | Restaurant `approx_cost` null | medium | Exclude from budget filter or treat as non-match (document policy) |
| EC-FLT-08 | Cost on band boundary (500 vs 501 INR) | medium | Consistent inclusive/exclusive rules per [architecture.md §6.3](./architecture.md#63-budget-to-cost-mapping-v1-proposal) |
| EC-FLT-09 | User budget `low` but only `high`-cost venues in city | high | `no_matches`; do not widen band automatically in v1 |
| EC-FLT-10 | Cuisine appears as substring of another (`"Indian"` vs `"North Indian"`) | medium | Substring match may over-match; acceptable v1; note in README |
| EC-FLT-11 | Restaurant lists multiple cuisines; user wants one | low | Match if any cuisine token matches |
| EC-FLT-12 | Additional prefs imply constraints not in data (halal, rooftop) | medium | Ignored by filter; LLM uses only for ranking/explanation |
| EC-FLT-13 | Filter order dependency | low | Pipeline order: location → cuisine → rating → budget → sort → cap (fixed) |
| EC-FLT-14 | Empty store (ingestion failed) | critical | Orchestrator error before filter; “dataset not available” |

---

## 4. Prompt builder

| ID | Edge case | Severity | Expected behavior |
|----|-----------|----------|-------------------|
| EC-PRM-01 | `PROMPT_VERSION` missing or unknown | high | Fall back to `v1` or fail fast with config error |
| EC-PRM-02 | Template file missing on disk | critical | Fail at startup or first build with file path in error |
| EC-PRM-03 | Single candidate in list | medium | Prompt still valid; instruct rank up to min(1, TOP_N) |
| EC-PRM-04 | Candidate with null optional fields in JSON payload | medium | Omit nulls or send explicit null; stable template |
| EC-PRM-05 | Prompt exceeds model context window | high | Cap `MAX_CANDIDATES`; truncate `additional_preferences`; log token estimate if possible |
| EC-PRM-06 | Special characters in restaurant names break JSON | high | Use `json.dumps` for candidate array; never manual string concat |
| EC-PRM-07 | Identical names different ids in candidates | medium | Prompt includes `id`; instructions stress id in response |

---

## 5. LLM provider, parser, and recommendation engine

| ID | Edge case | Severity | Expected behavior |
|----|-----------|----------|-------------------|
| EC-LLM-01 | API key missing or invalid | critical | Structured error; no retry on 401 |
| EC-LLM-02 | Rate limit (429) | high | Exponential backoff; max 2 retries; then user-facing error |
| EC-LLM-03 | Provider timeout | high | Retry then error with “try again” |
| EC-LLM-04 | Provider 5xx | high | Same as EC-LLM-03 |
| EC-LLM-05 | Empty response body | high | Treat as parse failure; repair or error |
| EC-LLM-06 | Response is markdown-wrapped JSON (` ```json `) | high | Strip fences before parse |
| EC-LLM-07 | Response is plain text, not JSON | high | One repair prompt; then error |
| EC-LLM-08 | JSON with trailing commas or minor syntax errors | medium | Repair pass or `json.loads` after cleanup |
| EC-LLM-09 | Valid JSON but wrong schema (missing `recommendations`) | high | Repair or error |
| EC-LLM-10 | Fewer than `TOP_N` items returned | medium | Return what was valid; no padding |
| EC-LLM-11 | More than `TOP_N` items returned | medium | Take first `TOP_N` by rank after validation |
| EC-LLM-12 | Duplicate `rank` values | high | Dedupe or renumber; log warning |
| EC-LLM-13 | Duplicate `restaurant_id` in response | high | Keep first occurrence; log warning |
| EC-LLM-14 | `restaurant_id` not in candidate list | high | Drop entry; log warning; continue if ≥1 valid left |
| EC-LLM-15 | All ids invalid (hallucinated ids) | critical | Return error; do not show unenriched rows |
| EC-LLM-16 | LLM returns correct id but wrong name in JSON | medium | **Enrichment overrides** name/cuisine/rating/cost from store |
| EC-LLM-17 | LLM invents restaurants not in candidate list | critical | Prevented by id validation; never display without store join |
| EC-LLM-18 | Empty `explanation` string | medium | Show fallback: “No explanation provided.” |
| EC-LLM-19 | Very long explanation (>2k chars) | low | Truncate in UI with ellipsis |
| EC-LLM-20 | `summary` missing | low | Omit summary section in UI |
| EC-LLM-21 | `summary` present but generic | low | Display as-is |
| EC-LLM-22 | LLM ranks clearly worse-rated venues first | medium | Accept v1 (LLM choice); optional post-sort by rank field only |
| EC-LLM-23 | Repair prompt also fails | high | Return `status=error` with safe message |
| EC-LLM-24 | Mock provider used in production by misconfig | medium | `LLM_PROVIDER=mock` only in tests; warn if mock in non-test env |
| EC-LLM-25 | Token/cost spike from huge additional prefs | medium | Truncate prefs; cap candidates |

---

## 6. Orchestrator and output formatter

| ID | Edge case | Severity | Expected behavior |
|----|-----------|----------|-------------------|
| EC-ORC-01 | `no_matches` then user retries with same prefs | low | Same result; consistent message |
| EC-ORC-02 | Partial success: 3 valid ids, 2 dropped | medium | Return 3 results; log dropped count |
| EC-ORC-03 | LLM returns 0 valid recommendations after parse | high | `status=error`; suggest retry |
| EC-ORC-04 | Enrichment: store record deleted since filter (impossible v1) | low | Skip row if `get_by_id` returns None |
| EC-ORC-05 | `approx_cost` null at format time | medium | Display “Cost not available” |
| EC-ORC-06 | `cuisines` is empty list | medium | Display “—” or “Not specified” |
| EC-ORC-07 | Format cost for display (`₹` locale) | low | Consistent formatting; no float with 10 decimals |
| EC-ORC-08 | Exception in one pipeline stage | critical | Catch; return `status=error`; log stack trace; no partial leak of API key |
| EC-ORC-09 | TOP_N=0 or negative in config | high | Validate settings at startup; default to 5 |

---

## 7. Presentation layer (Streamlit)

| ID | Edge case | Severity | Expected behavior |
|----|-----------|----------|-------------------|
| EC-UI-01 | Long-running LLM blocks UI | medium | Spinner; disable submit |
| EC-UI-02 | Streamlit session rerun mid-request | medium | Handle stale state; avoid duplicate API calls where possible |
| EC-UI-03 | Display LLM markdown in explanation | medium | Render safely; prefer text mode or sanitized markdown |
| EC-UI-04 | No results state | high | Clear copy: adjust location, cuisine, rating, or budget |
| EC-UI-05 | Error state (API down) | high | Actionable message; no stack trace to user |
| EC-UI-06 | Rating displayed with many decimal places | low | Format to 1 decimal |
| EC-UI-07 | Browser refresh during load | medium | New session; user re-enters prefs |
| EC-UI-08 | Mobile narrow viewport | low | Layout readable; no horizontal scroll required for core fields |

---

## 8. Configuration and environment

| ID | Edge case | Severity | Expected behavior |
|----|-----------|----------|-------------------|
| EC-CFG-01 | Missing `LLM_API_KEY` | critical | Fail at engine call with setup hint |
| EC-CFG-02 | Invalid `LLM_MODEL` name | high | Provider error surfaced to user |
| EC-CFG-03 | `MAX_CANDIDATES=0` | high | Reject at settings validation; minimum 1 |
| EC-CFG-04 | `TOP_N` > `MAX_CANDIDATES` | medium | Allow but LLM cannot return more than candidates; cap effectively min(TOP_N, len(candidates)) |
| EC-CFG-05 | Relative vs absolute `CACHE_PATH` | medium | Resolve from project root consistently |
| EC-CFG-06 | Running from wrong working directory | high | Document `cd` to project root; or resolve paths from package location |
| EC-CFG-07 | `.env` committed to git | critical | `.gitignore`; never log secrets |

---

## 9. Security and abuse

| ID | Edge case | Severity | Expected behavior |
|----|-----------|----------|-------------------|
| EC-SEC-01 | Prompt injection in `additional_preferences` (“ignore instructions”) | high | System prompt reinforces JSON-only and candidate-only; do not execute instructions |
| EC-SEC-02 | PII in free-text field | medium | Ephemeral; not logged in full in production logs |
| EC-SEC-03 | Oversized request body / prefs | medium | Length limits on strings |
| EC-SEC-04 | Public Streamlit without auth | low | v1 acceptable for demo; document not for production |

---

## 10. Testing and CI

| ID | Edge case | Severity | Expected behavior |
|----|-----------|----------|-------------------|
| EC-TST-01 | CI has no network | high | Tests use fixture Parquet + `MockLLMProvider` only |
| EC-TST-02 | Fixture with &lt; TOP_N rows | medium | Tests expect fewer results |
| EC-TST-03 | Snapshot prompt drift | low | Review intentional template changes |
| EC-TST-04 | Flaky LLM integration test | medium | Mark live LLM tests `@pytest.mark.integration`; skip in CI |

---

## 11. Cross-cutting end-to-end scenarios

Composite scenarios tying multiple layers together.

| ID | Scenario | Severity | Expected behavior |
|----|----------|----------|-------------------|
| EC-E2E-01 | Valid prefs, happy path | — | ≤5 enriched results + optional summary |
| EC-E2E-02 | Valid city, impossible cuisine + min 5.0 | high | `no_matches`; zero LLM spend |
| EC-E2E-03 | Strict budget + strict rating in sparse city | high | `no_matches` with helpful copy |
| EC-E2E-04 | First app start (cold cache) | medium | Ingestion runs; may take minutes; show progress |
| EC-E2E-05 | Second app start (warm cache) | low | Fast load from Parquet |
| EC-E2E-06 | Family-friendly in additional prefs only | medium | Filter unchanged; explanations reference it |
| EC-E2E-07 | LLM down mid-demo | high | Graceful error; cached data still usable for filter-only debug |
| EC-E2E-08 | Same restaurant name two locations in candidates | medium | Distinct ids; explanations distinguish by location |

---

## 12. Priority matrix for v1 test implementation

| Priority | IDs (implement tests first) |
|----------|------------------------------|
| P0 (must) | EC-ING-01, EC-ING-04, EC-FLT-01, EC-LLM-15, EC-LLM-17, EC-INP-01, EC-INP-05, EC-ORC-08, EC-E2E-02, EC-E2E-01 |
| P1 (should) | EC-ING-08, EC-ING-11, EC-FLT-03, EC-LLM-06–14, EC-LLM-02–04, EC-INP-12, EC-PRM-06, EC-STR-02 |
| P2 (nice) | Remaining IDs |

Suggested test file mapping:

| Test module | Edge case prefix |
|-------------|------------------|
| `test_normalizer.py` | EC-ING-*, EC-STR-* |
| `test_filter_service.py` | EC-FLT-* |
| `test_models.py` | EC-INP-* |
| `test_prompt_builder.py` | EC-PRM-* |
| `test_parser.py` | EC-LLM-06–15 |
| `test_engine.py` | EC-LLM-01–05, EC-LLM-16–25 |
| `test_orchestrator.py` | EC-ORC-*, EC-E2E-* |

---

## 13. Traceability

| Source document | Edge case sections |
|-----------------|-------------------|
| [context.md](./context.md) — user inputs, output schema, LLM duties | §2, §5, §6, §7 |
| [architecture.md](./architecture.md) — failure modes, filter rules, enrichment | §1, §3, §5, §6 |
| [implementation-plan.md](./implementation-plan.md) — risks, manual E2E | §11, §12 |

When behavior changes, update this file and the corresponding test in the same PR.

---

## 14. Out of scope (document only)

These are known limitations for v1, not bugs:

- No automatic spelling correction for city/cuisine
- No fuzzy semantic match for soft preferences
- No retry with relaxed filters on `no_matches`
- No multi-language UI
- No handling of real-time restaurant closures or live Zomato API

See [architecture.md §13](./architecture.md#13-future-extensions) for planned improvements.
