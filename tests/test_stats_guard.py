"""The executor must NEVER bet when team stats aren't from real data."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from src.research.normalization import NormalizedEvent
from src.execution.executor import Executor
from src.execution.bankroll import BankrollManager
from config.settings import Settings


class _FakeBook:
    def place_bet(self, bet): raise AssertionError("should not place a bet in this test")


class _Book2:
    class R:
        success = True; bet_id = "x"
    def place_bet(self, bet): return self.R()


def _event(stats_real):
    # strong fake edge so ONLY the guard can stop the bet
    return NormalizedEvent(
        event_id="e1", home_team="A", away_team="B", market_type="1X2",
        home_odds=5.0, draw_odds=4.0, away_odds=4.0,
        home_lambda=2.5, away_lambda=0.5, timestamp=0.0, stats_real=stats_real,
    )


def _settings(tmp):
    os.environ["DRY_RUN"] = "true"
    os.environ["BANKROLL_FILE"] = str(tmp / "bank.json")
    return Settings()


def test_no_bet_when_stats_not_real(tmp_path):
    s = _settings(tmp_path)
    ex = Executor(_FakeBook(), BankrollManager(s.BANKROLL_FILE, 1000.0), s)
    records = ex.run([_event(stats_real=False)])
    assert records == []


def test_bet_considered_when_stats_real(tmp_path):
    s = _settings(tmp_path)
    ex = Executor(_Book2(), BankrollManager(s.BANKROLL_FILE, 1000.0), s)
    records = ex.run([_event(stats_real=True)])
    # with a real edge and real stats, at least it is NOT blocked by the guard
    assert len(records) == 1
