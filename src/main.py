import logging
import logging.config
import uuid
import yaml
import os
import sys
from pathlib import Path

# Ensure the project root is on the path when running as `python -m src.main`
_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))


def setup_logging(run_id: str) -> None:
    """Configure logging from YAML config, injecting the run_id filter."""
    from src.logging_filter import RunIdFilter

    config_path = _ROOT / "config" / "logging.yaml"
    if config_path.exists():
        with open(config_path) as fh:
            cfg = yaml.safe_load(fh)
        # Remove the custom filter config that requires the class to be importable
        # at yaml-load time; we add it manually below.
        for handler in cfg.get("handlers", {}).values():
            handler.pop("filters", None)
        cfg.pop("filters", None)
        logging.config.dictConfig(cfg)
    else:
        logging.basicConfig(level=logging.INFO)

    RunIdFilter.set_run_id(run_id)
    run_id_filter = RunIdFilter()
    for handler in logging.root.handlers:
        handler.addFilter(run_id_filter)


def check_secrets(settings) -> bool:
    """In LIVE mode, validate required env vars exist. Return False if missing."""
    if settings.DRY_RUN:
        return True
    missing = []
    if not settings.ODDS_API_KEY:
        missing.append("ODDS_API_KEY")
    if not settings.SPORTSBOOK_KEY:
        missing.append("SPORTSBOOK_KEY")
    if missing:
        logging.getLogger(__name__).error(
            "LIVE mode requires env vars: %s", ", ".join(missing)
        )
        return False
    return True


def main() -> None:
    run_id = str(uuid.uuid4())[:8]

    # 1. Logging
    setup_logging(run_id)
    logger = logging.getLogger(__name__)
    logger.info("Starting run %s", run_id)

    # 2. Settings
    from config.settings import Settings
    settings = Settings()
    logger.info("DRY_RUN=%s  LOG_LEVEL=%s", settings.DRY_RUN, settings.LOG_LEVEL)

    # 3. Secrets check
    if not check_secrets(settings):
        sys.exit(1)

    # 4. Fetch odds + stats
    from src.research.odds_client import get_odds_client
    from src.research.stats_client import get_stats_client
    from src.research.normalization import normalize

    odds_client = get_odds_client(settings.ODDS_API_KEY)
    stats_client = get_stats_client(settings.SEARCH_API_KEY)
    markets = odds_client.fetch_markets()
    logger.info("Fetched %d markets", len(markets))

    # 5. Normalise events
    events = []
    for market in markets:
        home_stats = stats_client.fetch_team_stats(market.home_team)
        away_stats = stats_client.fetch_team_stats(market.away_team)
        events.append(normalize(market, home_stats, away_stats))
    logger.info("Normalised %d events", len(events))

    # 6. Executor
    from src.execution.sportsbook_api import get_sportsbook
    from src.execution.bankroll import BankrollManager
    from src.execution.executor import Executor

    sportsbook = get_sportsbook(dry_run=settings.DRY_RUN, api_key=settings.SPORTSBOOK_KEY)
    bankroll = BankrollManager(settings.BANKROLL_FILE, settings.INITIAL_BANKROLL)
    executor = Executor(sportsbook, bankroll, settings)
    records = executor.run(events)
    logger.info("Placed %d bets this run", len(records))

    # 7. CSV log
    if records:
        from src.storage.csv_logger import append_run_log
        append_run_log(settings.CSV_LOG_FILE, records)
        logger.info("Appended %d records to %s", len(records), settings.CSV_LOG_FILE)

    # 8. Git commit (always attempt so CSV stays up to date in repo)
    from src.storage.git_commit import commit_and_push
    commit_and_push(
        [settings.CSV_LOG_FILE, settings.BANKROLL_FILE],
        message=f"chore: update run logs {run_id} [skip ci]",
    )

    logger.info("Run %s complete.", run_id)


if __name__ == "__main__":
    main()
