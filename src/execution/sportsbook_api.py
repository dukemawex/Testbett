from dataclasses import dataclass
from typing import Protocol
import logging

logger = logging.getLogger(__name__)


@dataclass
class BetRequest:
    event_id: str
    market_type: str
    selection: str  # "home", "draw", "away", "over", "under"
    stake: float
    odds: float


@dataclass
class BetResponse:
    success: bool
    bet_id: str
    message: str


class SportsbookProtocol(Protocol):
    def place_bet(self, bet: BetRequest) -> BetResponse: ...
    def check_balance(self) -> float: ...


class StubSportsbook:
    """Stub sportsbook – simulates placement, never touches real money."""

    def place_bet(self, bet: BetRequest) -> BetResponse:
        logger.info("STUB: Would place bet %s", bet)
        return BetResponse(success=True, bet_id=f"stub_{bet.event_id}", message="DRY_RUN stub")

    def check_balance(self) -> float:
        return 10000.0


class LiveSportsbook:
    """Placeholder for real sportsbook. Raises NotImplementedError."""

    def __init__(self, api_key: str):
        self.api_key = api_key

    def place_bet(self, bet: BetRequest) -> BetResponse:
        raise NotImplementedError(
            "Real sportsbook integration not implemented. Use DRY_RUN mode."
        )

    def check_balance(self) -> float:
        raise NotImplementedError(
            "Real sportsbook integration not implemented."
        )


def get_sportsbook(dry_run: bool = True, api_key: str = "") -> SportsbookProtocol:
    if dry_run:
        return StubSportsbook()
    if not api_key:
        raise ValueError("SPORTSBOOK_KEY required for LIVE mode")
    return LiveSportsbook(api_key)
