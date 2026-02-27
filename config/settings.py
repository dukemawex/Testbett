import os


class Settings:
    def __init__(self):
        self.DRY_RUN: bool = os.environ.get("DRY_RUN", "true").lower() not in (
            "false", "0", "no"
        )  # Falsy values: "false", "0", "no" (case-insensitive); everything else is truthy
        self.LOG_LEVEL: str = os.environ.get("LOG_LEVEL", "INFO")
        self.KELLY_FRACTION: float = float(os.environ.get("KELLY_FRACTION", "0.25"))
        self.MAX_STAKE_PCT: float = float(os.environ.get("MAX_STAKE_PCT", "0.05"))
        self.MIN_STAKE: float = float(os.environ.get("MIN_STAKE", "1.0"))
        self.MAX_BETS_PER_RUN: int = int(os.environ.get("MAX_BETS_PER_RUN", "5"))
        self.DAILY_LOSS_LIMIT: float = float(os.environ.get("DAILY_LOSS_LIMIT", "50.0"))
        self.MIN_EDGE_THRESHOLD: float = float(os.environ.get("MIN_EDGE_THRESHOLD", "0.03"))
        self.INITIAL_BANKROLL: float = float(os.environ.get("INITIAL_BANKROLL", "1000.0"))
        self.BANKROLL_FILE: str = os.environ.get("BANKROLL_FILE", "data/bankroll.json")
        self.CSV_LOG_FILE: str = os.environ.get("CSV_LOG_FILE", "data/runs.csv")
        self.ODDS_API_KEY: str = os.environ.get("ODDS_API_KEY", "")
        self.SEARCH_API_KEY: str = os.environ.get("SEARCH_API_KEY", "")
        self.SPORTSBOOK_KEY: str = os.environ.get("SPORTSBOOK_KEY", "")
        self.SPORTSBOOK_BASE_URL: str = os.environ.get("SPORTSBOOK_BASE_URL", "")
        self.SLACK_WEBHOOK_URL: str = os.environ.get("SLACK_WEBHOOK_URL", "")
        # LLM settings
        self.OPENAI_API_KEY: str = os.environ.get("OPENAI_API_KEY", "")
        self.OPENAI_MODEL: str = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")
