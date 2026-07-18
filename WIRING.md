# Wiring Sentinel live — safe checklist

The bot defaults to **DRY_RUN=true** and places **zero real bets** until you deliberately turn it
off. Do these in order. Do not skip the paper-trading step.

## 1. Local setup
```bash
cp .env.example .env          # fill in keys; .env is gitignored
pip install -r requirements.txt
pytest -q                     # 34 tests should pass
DRY_RUN=true python -m src.main   # end-to-end dry run, no real bets
```

## 2. Add real research keys (still DRY_RUN)
Set in `.env`, keep `DRY_RUN=true`:
- `ODDS_API_KEY` — real markets from The Odds API (without it you get stub markets).
- `OPENAI_API_KEY` — enables the real LLM bet analyst (otherwise a stub approves everything).
- Leave `SPORTSBOOK_KEY` / `SPORTSBOOK_BASE_URL` **blank** — no live betting yet.
Run again and review `data/runs.csv`: are the edges, stakes, and LLM reasons sane?

## 3. Paper-trade for a while
Keep `DRY_RUN=true` for days/weeks. Track whether the model's picks would have won. Do NOT go live
on unproven picks. This is the step that protects your money.

## 4. Only then, go live (real money)
Set `SPORTSBOOK_KEY`, `SPORTSBOOK_BASE_URL`, and `DRY_RUN=false`. Start with a SMALL
`INITIAL_BANKROLL` and conservative `MAX_STAKE_PCT` / `DAILY_LOSS_LIMIT`. The bot validates required
live keys and exits if any are missing.

## Risk controls (already enforced in code)
- Fractional Kelly (`KELLY_FRACTION=0.25`) — quarter-Kelly reduces variance.
- `MAX_STAKE_PCT=0.05` — no single bet over 5% of bankroll.
- `MIN_EDGE_THRESHOLD=0.03` — skip thin edges.
- `MAX_BETS_PER_RUN`, `DAILY_LOSS_LIMIT` — per-run and per-day circuit breakers.

## Notes
- Run logs and bankroll state are gitignored and stay local. Set `GIT_AUTOCOMMIT=true` only if you
  want the bot to push logs (needs git write creds on the runner).
- The scheduler (.github/workflows/scheduler.yml) runs every 2h — keep it OFF or DRY_RUN until step 4.

**Reality check:** sports betting is negative-sum after the bookmaker margin. Even correct Kelly on a
real edge is high-variance, and a modeled "edge" may not be a real one. Treat this as research;
risk only what you can lose.
