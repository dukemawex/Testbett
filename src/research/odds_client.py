from dataclasses import dataclass, field
from typing import Protocol, List
import json
import logging
import time
import urllib.error
import urllib.parse
import urllib.request

logger = logging.getLogger(__name__)


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


class TheOddsApiClient:
    """Live client for The Odds API (https://the-odds-api.com).

    Fetches real-time 1X2 markets.  Requires an ``ODDS_API_KEY``.
    Free tier: 500 requests/month.

    The sport key follows The Odds API convention, e.g.:
      ``soccer_epl``, ``soccer_usa_mls``, ``soccer_spain_la_liga``
    Pass the full sport key as the ``sport`` argument.
    """

    _BASE = "https://api.the-odds-api.com/v4"
    _TIMEOUT = 15

    def __init__(self, api_key: str):
        self._api_key = api_key

    def fetch_markets(self, sport: str = "soccer_epl") -> List[OddsMarket]:
        """Fetch head-to-head markets for *sport* and return normalised OddsMarket objects.

        Averages decimal odds across all bookmakers that offer the event.
        Falls back to an empty list (and logs a warning) on any HTTP error.
        """
        params = urllib.parse.urlencode({
            "apiKey": self._api_key,
            "regions": "eu",
            "markets": "h2h",
            "oddsFormat": "decimal",
        })
        url = f"{self._BASE}/sports/{urllib.parse.quote(sport, safe='_')}/odds?{params}"
        try:
            with urllib.request.urlopen(url, timeout=self._TIMEOUT) as resp:
                events = json.loads(resp.read().decode())
        except urllib.error.HTTPError as exc:
            logger.warning("TheOddsApi HTTP %s for sport=%s", exc.code, sport)
            return []
        except Exception as exc:
            logger.warning("TheOddsApi fetch failed: %s", exc)
            return []

        markets: List[OddsMarket] = []
        ts = time.time()
        for ev in events:
            market = self._parse_event(ev, ts)
            if market:
                markets.append(market)
        logger.info("TheOddsApi returned %d markets for sport=%s", len(markets), sport)
        return markets

    # ------------------------------------------------------------------

    @staticmethod
    def _parse_event(ev: dict, ts: float) -> OddsMarket | None:
        """Convert a single Odds API event dict to an OddsMarket."""
        home_team = ev.get("home_team", "")
        away_team = ev.get("away_team", "")
        event_id = ev.get("id", f"{home_team}_{away_team}")

        home_acc: list[float] = []
        draw_acc: list[float] = []
        away_acc: list[float] = []

        for bookmaker in ev.get("bookmakers", []):
            for mkt in bookmaker.get("markets", []):
                if mkt.get("key") != "h2h":
                    continue
                outcomes = {o["name"]: o["price"] for o in mkt.get("outcomes", [])}
                h = outcomes.get(home_team)
                a = outcomes.get(away_team)
                d = outcomes.get("Draw")
                if h and a and d:
                    home_acc.append(h)
                    away_acc.append(a)
                    draw_acc.append(d)

        if not home_acc:
            return None

        def _avg(lst: list[float]) -> float:
            return round(sum(lst) / len(lst), 4)

        return OddsMarket(
            event_id=event_id,
            home_team=home_team,
            away_team=away_team,
            market_type="1X2",
            home_odds=_avg(home_acc),
            draw_odds=_avg(draw_acc),
            away_odds=_avg(away_acc),
            timestamp=ts,
        )


def get_odds_client(api_key: str = "") -> OddsClientProtocol:
    """Return a live client when *api_key* is provided, otherwise the stub."""
    if api_key:
        return TheOddsApiClient(api_key)
    return StubOddsClient()

