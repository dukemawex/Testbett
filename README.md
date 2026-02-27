# Sentinel Forecast & Betting Bot

A production-ready Python 3.11+ sports-betting research and execution bot that uses
Poisson modelling, Bayesian lambda updates, Kelly staking, and a full DRY_RUN / LIVE
mode switch. No external ML libraries – only the Python stdlib, `pytest`, and `pyyaml`.

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
│   │   ├── executor.py         # Orchestrates edge calc → staking → placement
│   │   ├── kelly.py            # Kelly Criterion + fractional Kelly
│   │   └── sportsbook_api.py   # StubSportsbook / LiveSportsbook (placeholder)
│   ├── models/
│   │   ├── __init__.py
│   │   ├── bayesian_update.py  # Gamma-Poisson conjugate update
│   │   ├── calibration.py      # Brier score & calibration scaling
│   │   ├── poisson.py          # Poisson PMF, score matrix, 1X2 / O-U probs
│   │   └── true_probability.py # Devig, edge computation, MarketProbabilities
│   ├── research/
│   │   ├── __init__.py
│   │   ├── normalization.py    # Merges OddsMarket + TeamStats → NormalizedEvent
│   │   ├── odds_client.py      # OddsMarket dataclass + StubOddsClient
│   │   ├── stats_client.py     # TeamStats dataclass + StubStatsClient
│   │   └── web_search.py       # SearchResult dataclass + StubWebSearch
│   └── storage/
│       ├── __init__.py
│       ├── csv_logger.py       # Append bet records to CSV
│       └── git_commit.py       # Stage, commit, push data files
├── tests/
│   ├── __init__.py
│   ├── test_kelly.py
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
| `src/models/poisson.py` | Independent-Poisson score matrix; computes P(home wins), P(draw), P(away wins), P(over 2.5), P(under 2.5) |
| `src/models/bayesian_update.py` | Gamma-Poisson conjugate prior update of λ from observed goal data |
| `src/models/true_probability.py` | Converts Poisson results to `MarketProbabilities`; removes bookmaker vig; computes edge |
| `src/models/calibration.py` | Brier score and a simple calibration scaling factor |
| `src/research/odds_client.py` | `OddsMarket` dataclass + stub returning 3 deterministic markets |
| `src/research/stats_client.py` | `TeamStats` dataclass + stub with 6 pre-seeded teams |
| `src/research/web_search.py` | `SearchResult` dataclass + stub returning empty results (offline safe) |
| `src/research/normalization.py` | Combines market + team stats into a `NormalizedEvent` with estimated lambdas |
| `src/execution/kelly.py` | Full Kelly, fractional Kelly, and `compute_stake` with cap + floor |
| `src/execution/bankroll.py` | `BankrollManager`: load/save JSON, record bets, enforce daily loss limit |
| `src/execution/sportsbook_api.py` | `StubSportsbook` (DRY_RUN) and `LiveSportsbook` (raises `NotImplementedError`) |
| `src/execution/executor.py` | Main loop: normalise → Poisson → edge filter → Kelly → place/log |
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

# LIVE mode (requires SPORTSBOOK_KEY + ODDS_API_KEY)
DRY_RUN=false ODDS_API_KEY=xxx SPORTSBOOK_KEY=yyy python -m src.main
```

---

## DRY_RUN vs LIVE Mode

| | DRY_RUN=true (default) | DRY_RUN=false (LIVE) |
|---|---|---|
| API keys needed | No | `ODDS_API_KEY`, `SPORTSBOOK_KEY` |
| Bets placed | Logged only | Real money (not yet implemented) |
| Bankroll file | Updated | Updated |
| CSV log | Written | Written |
| Git push | Attempted | Attempted |

> **Safety**: `LiveSportsbook.place_bet` raises `NotImplementedError`. Real exchange
> integration must be coded before enabling LIVE mode.

---

## Required Secrets (GitHub Actions)

| Secret / Var | Purpose |
|---|---|
| `ODDS_API_KEY` | Odds data provider (e.g. The Odds API) |
| `SEARCH_API_KEY` | Web search for injury news (future use) |
| `SPORTSBOOK_KEY` | Exchange / sportsbook API key for LIVE mode |
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

All 25 tests are deterministic and require no external services.

---

## Safety Notes

* `DRY_RUN=true` is the hard default – the bot cannot place real bets without an
  explicit opt-in.
* Secret values are never logged.
* The daily loss limit (`DAILY_LOSS_LIMIT`, default 50.0) halts all betting for the
  day if breached.
* `MAX_BETS_PER_RUN` (default 5) caps exposure per invocation.
* Kelly stakes are further capped at `MAX_STAKE_PCT` (default 5 %) of bankroll.
