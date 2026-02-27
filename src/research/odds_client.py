from dataclasses import dataclass, field
from typing import Protocol, List
import time


@dataclass
class OddsMarket:
    """Represents a market's odds for a single event."""
    event_id: str
    home_team: str
    away_team: str
    market_type: str  # e.g. "1X2", "totals"
    home_odds: float
    draw_odds: float
    away_odds: float
    timestamp: float = field(default_factory=time.time)


class OddsClientProtocol(Protocol):
    def fetch_markets(self, sport: str = "soccer") -> List[OddsMarket]: ...


class StubOddsClient:
    """Deterministic stub – no external calls, no API key needed."""

    _MARKETS = [
        OddsMarket(
            event_id="evt_001",
            home_team="HomeFC",
            away_team="AwayFC",
            market_type="1X2",
            home_odds=2.10,
            draw_odds=3.40,
            away_odds=3.60,
            timestamp=0.0,
        ),
        OddsMarket(
            event_id="evt_002",
            home_team="NorthCity",
            away_team="SouthUnited",
            market_type="1X2",
            home_odds=1.85,
            draw_odds=3.50,
            away_odds=4.20,
            timestamp=0.0,
        ),
        OddsMarket(
            event_id="evt_003",
            home_team="EastRovers",
            away_team="WestWanderers",
            market_type="1X2",
            home_odds=2.50,
            draw_odds=3.20,
            away_odds=2.80,
            timestamp=0.0,
        ),
    ]

    def fetch_markets(self, sport: str = "soccer") -> List[OddsMarket]:
        return list(self._MARKETS)


def get_odds_client(api_key: str = "") -> OddsClientProtocol:
    # Real client not implemented; always return the stub.
    return StubOddsClient()
