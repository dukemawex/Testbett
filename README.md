# Sentinel Forecast & Betting Bot

A production-ready Python 3.11+ sports-betting research and execution bot that uses
Poisson modelling, Bayesian lambda updates, Kelly staking, **LLM-powered bet analysis
(OpenAI)**, real-time odds via The Odds API, and a live generic-REST sportsbook client.
Runs safely in DRY_RUN by default.

---

## File Tree

```
.
├── .github/
│   └── workflows/
│       └── scheduler.yml       # Runs every 2 hours via cron
├── config/
│   ├── __init__.py
│   ├── constants.py            # APP_NAME, VERSION, market type constants
│   ├── logging.yaml            # YAML logging config
│   └── settings.py             # Reads all config from environment variables
├── data/
│   └── .gitkeep                # Placeholder – bankroll.json & runs.csv live here
├── src/
│   ├── __init__.py
│   ├── logging_filter.py       # Injects run_id into every log record
│   ├── main.py                 # Entry point: `python -m src.main`
│   ├── execution/
│   │   ├── __init__.py
│   │   ├── bankroll.py         # BankrollManager – JSON persistence
│   │   ├── executor.py         # Orchestrates edge calc → LLM → staking → placement
│   │   ├── kelly.py            # Kelly Criterion + fractional Kelly
│   │   └── sportsbook_api.py   # StubSportsbook / LiveSportsbook (generic HTTP)
│   ├── llm/
│   │   ├── __init__.py
│   │   ├── llm_client.py       # OpenAI ChatCompletion + deterministic stub
│   │   └── bet_analyst.py      # Analyses each bet: approved/reasoning/stake_multiplier
│   ├── models/
│   │   ├── __init__.py
│   │   ├── bayesian_update.py  # Gamma-Poisson conjugate update
│   │   ├── calibration.py      # Brier score & calibration scaling
│   │   ├── poisson.py          # Poisson PMF, score matrix, 1X2 / O-U probs
│   │   └── true_probability.py # Devig, edge computation, MarketProbabilities
│   ├── research/
│   │   ├── __init__.py
│   │   ├── normalization.py    # Merges OddsMarket + TeamStats → NormalizedEvent
│   │   ├── odds_client.py      # StubOddsClient + TheOddsApiClient (live)
│   │   ├── stats_client.py     # TeamStats dataclass + StubStatsClient
│   │   └── web_search.py       # SearchResult dataclass + StubWebSearch
│   └── storage/
│       ├── __init__.py
│       ├── csv_logger.py       # Append bet records to CSV
│       └── git_commit.py       # Stage, commit, push data files
├── tests/
│   ├── __init__.py
│   ├── test_kelly.py
│   ├── test_llm_analyst.py     # LLM stub tests (no API key needed)
│   ├── test_poisson.py
│   └── test_true_probability.py
└── requirements.txt
```

---

## Module Descriptions

| Module | Purpose |
|---|---|
| `config/settings.py` | Single `Settings` class; reads every config value from env vars with sensible defaults |
| `config/constants.py` | Immutable app-level constants (name, version, market types, default lambdas) |
| `src/llm/llm_client.py` | `OpenAILLMClient` using `openai>=1.0` + `StubLLMClient` (deterministic, offline) |
| `src/llm/bet_analyst.py` | `BetAnalyst`: sends bet signal to LLM, parses structured JSON → `BetAnalysis` (approved, confidence, reasoning, stake_multiplier) |
| `src/models/poisson.py` | Independent-Poisson score matrix; computes P(home wins), P(draw), P(away wins), P(over 2.5), P(under 2.5) |
| `src/models/bayesian_update.py` | Gamma-Poisson conjugate prior update of λ from observed goal data |
| `src/models/true_probability.py` | Converts Poisson results to `MarketProbabilities`; removes bookmaker vig; computes edge |
| `src/models/calibration.py` | Brier score and a simple calibration scaling factor |
| `src/research/odds_client.py` | `TheOddsApiClient` (live, requires `ODDS_API_KEY`) + `StubOddsClient` (deterministic, no key) |
| `src/research/stats_client.py` | `TeamStats` dataclass + stub with 6 pre-seeded teams |
| `src/research/web_search.py` | `SearchResult` dataclass + stub returning empty results (offline safe) |
| `src/research/normalization.py` | Combines market + team stats into a `NormalizedEvent` with estimated lambdas |
| `src/execution/kelly.py` | Full Kelly, fractional Kelly, and `compute_stake` with cap + floor |
| `src/execution/bankroll.py` | `BankrollManager`: load/save JSON, record bets, enforce daily loss limit |
| `src/execution/sportsbook_api.py` | `StubSportsbook` (DRY_RUN) and `LiveSportsbook` (generic REST, configurable via env vars) |
| `src/execution/executor.py` | Main loop: normalise → Poisson → edge filter → **LLM analysis** → Kelly → place/log |
| `src/storage/csv_logger.py` | Append-only CSV writer; creates header on first write |
| `src/storage/git_commit.py` | Safe `git add / commit / push` wrapper; logs warning on failure |
| `src/main.py` | Entry point: wires everything together, respects DRY_RUN |

---

## Setup & Install

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Python **3.11+** required (uses `list[...]` and `tuple[...]` built-in generics).

---

## Running

```bash
# DRY_RUN (default – no real money, no API key needed)
python -m src.main

# With real odds (The Odds API) + LLM analysis, still DRY_RUN
ODDS_API_KEY=xxx OPENAI_API_KEY=sk-... python -m src.main

# Full LIVE mode – places real bets
DRY_RUN=false \
  ODDS_API_KEY=xxx \
  OPENAI_API_KEY=sk-... \
  SPORTSBOOK_KEY=yyy \
  SPORTSBOOK_BASE_URL=https://api.yourbook.com/v1 \
  python -m src.main
```

---

## DRY_RUN vs LIVE Mode

| | DRY_RUN=true (default) | DRY_RUN=false (LIVE) |
|---|---|---|
| API keys needed | No | `ODDS_API_KEY`, `SPORTSBOOK_KEY`, `SPORTSBOOK_BASE_URL` |
| LLM analysis | Stub (offline) | Real OpenAI (if `OPENAI_API_KEY` set) |
| Bets placed | Logged only | Real HTTP POST to `SPORTSBOOK_BASE_URL/bets` |
| Bankroll file | Updated | Updated |
| CSV log | Written | Written |
| Git push | Attempted | Attempted |

---

## LLM Integration

When `OPENAI_API_KEY` is set, the bot calls OpenAI's chat-completions API (default
model: `gpt-4o-mini`) to analyse each betting opportunity before sizing or placing.

The LLM receives a structured JSON prompt containing:
- Event teams and market odds
- Poisson model estimates (lambdas, true probability, implied probability)
- Computed edge and proposed Kelly stake

It returns a JSON verdict:
```json
{
  "approved": true,
  "confidence": 0.82,
  "reasoning": "Strong home advantage; away team missing key midfielder...",
  "stake_multiplier": 0.9
}
```

If no key is provided, a deterministic **stub** is used – the bot runs fully offline.
The LLM never sees or logs API keys.

---

## Live Sportsbook (Generic REST)

`LiveSportsbook` in `src/execution/sportsbook_api.py` implements a generic REST
client. Configure it to point at your sportsbook's API:

| Env var | Default | Purpose |
|---|---|---|
| `SPORTSBOOK_BASE_URL` | _(required in LIVE mode)_ | API base URL, e.g. `https://api.yourbook.com/v1` |
| `SPORTSBOOK_KEY` | _(required in LIVE mode)_ | API key / Bearer token |
| `SPORTSBOOK_AUTH_HEADER` | `Authorization` | HTTP header for auth |
| `SPORTSBOOK_AUTH_PREFIX` | `Bearer` | Prefix before the key value |

Expected endpoints (adapt by subclassing `LiveSportsbook` if needed):
- `POST {base_url}/bets` – body: `{event_id, market_type, selection, stake, odds}`
- `GET  {base_url}/account/balance` – response: `{balance: <float>}`

---

## Required Secrets (GitHub Actions)

| Secret / Var | Purpose |
|---|---|
| `ODDS_API_KEY` | The Odds API key for live odds (https://the-odds-api.com) |
| `OPENAI_API_KEY` | OpenAI API key for LLM bet analysis |
| `OPENAI_MODEL` (var) | OpenAI model name (default: `gpt-4o-mini`) |
| `SPORTSBOOK_KEY` | Exchange / sportsbook API key for LIVE mode |
| `SPORTSBOOK_BASE_URL` | Sportsbook API base URL for LIVE mode |
| `SEARCH_API_KEY` | Web search for injury news (future use) |
| `SLACK_WEBHOOK_URL` | Slack incoming webhook for failure alerts |
| `vars.DRY_RUN` | Repository variable (`"true"` / `"false"`) |

---

## GitHub Actions Schedule

The workflow at `.github/workflows/scheduler.yml` runs every 2 hours and on
`workflow_dispatch`. It commits updated `data/runs.csv` and `data/bankroll.json`
back to the repository after each run. Slack is notified on failure if
`SLACK_WEBHOOK_URL` is set.

```yaml
on:
  schedule:
    - cron: '0 */2 * * *'
  workflow_dispatch:
```

---

## Running Tests

```bash
python -m pytest tests/ -v
```

All 34 tests are deterministic and require no external services or API keys.

---

## Safety Notes

* `DRY_RUN=true` is the hard default – the bot cannot place real bets without an
  explicit opt-in.
* Secret values are never logged.
* `LiveSportsbook` makes real HTTP calls only when `DRY_RUN=false` **and** both
  `SPORTSBOOK_KEY` and `SPORTSBOOK_BASE_URL` are set; missing either causes a
  hard exit before any bet is placed.
* The daily loss limit (`DAILY_LOSS_LIMIT`, default 50.0) halts all betting for the
  day if breached.
* `MAX_BETS_PER_RUN` (default 5) caps exposure per invocation.
* Kelly stakes are further capped at `MAX_STAKE_PCT` (default 5 %) of bankroll.
* The LLM `stake_multiplier` is clamped to `[0.0, 2.0]`; a rejected bet is never
  placed regardless of statistical edge.

