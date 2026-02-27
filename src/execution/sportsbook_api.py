from dataclasses import dataclass
from typing import Protocol
import json
import logging
import urllib.error
import urllib.request

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
    """Generic REST sportsbook client.

    Requires the following environment variables (passed in via the constructor):
      - *base_url*  – e.g. ``https://api.yourbook.com/v1``
      - *api_key*   – Bearer token / API key

    Optional (set via env vars before calling the factory):
      - ``SPORTSBOOK_AUTH_HEADER``  – HTTP header name for auth (default: ``Authorization``)
      - ``SPORTSBOOK_AUTH_PREFIX``  – value prefix          (default: ``Bearer``)

    Expected endpoints (standard REST contract):
      POST  {base_url}/bets
        Request body::

          {
            "event_id":    "<str>",
            "market_type": "<str>",
            "selection":   "<str>",
            "stake":       <float>,
            "odds":        <float>
          }

        Success response (HTTP 200/201)::

          {"bet_id": "<str>", "status": "accepted", ...}

      GET   {base_url}/account/balance
        Success response::

          {"balance": <float>, ...}

    Adapt this to your sportsbook's actual API by wrapping or subclassing.
    """

    def __init__(
        self,
        api_key: str,
        base_url: str,
        auth_header: str = "Authorization",
        auth_prefix: str = "Bearer",
        timeout: int = 15,
    ):
        if not base_url:
            raise ValueError(
                "SPORTSBOOK_BASE_URL is required for LIVE mode. "
                "Set it to your sportsbook's API base URL."
            )
        self._base_url = base_url.rstrip("/")
        self._api_key = api_key
        self._auth_header = auth_header
        self._auth_prefix = auth_prefix
        self._timeout = timeout

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _headers(self) -> dict:
        return {
            "Content-Type": "application/json",
            self._auth_header: f"{self._auth_prefix} {self._api_key}",
        }

    def _post(self, path: str, body: dict) -> dict:
        url = f"{self._base_url}{path}"
        data = json.dumps(body).encode()
        req = urllib.request.Request(url, data=data, headers=self._headers(), method="POST")
        try:
            with urllib.request.urlopen(req, timeout=self._timeout) as resp:
                return json.loads(resp.read().decode())
        except urllib.error.HTTPError as exc:
            body_text = exc.read().decode(errors="replace")
            raise RuntimeError(f"Sportsbook POST {path} failed [{exc.code}]: {body_text}") from exc

    def _get(self, path: str) -> dict:
        url = f"{self._base_url}{path}"
        req = urllib.request.Request(url, headers=self._headers(), method="GET")
        try:
            with urllib.request.urlopen(req, timeout=self._timeout) as resp:
                return json.loads(resp.read().decode())
        except urllib.error.HTTPError as exc:
            body_text = exc.read().decode(errors="replace")
            raise RuntimeError(f"Sportsbook GET {path} failed [{exc.code}]: {body_text}") from exc

    # ------------------------------------------------------------------
    # Protocol implementation
    # ------------------------------------------------------------------

    def place_bet(self, bet: BetRequest) -> BetResponse:
        logger.info(
            "LIVE: placing bet %s/%s %.2f @ %.2f",
            bet.event_id, bet.selection, bet.stake, bet.odds,
        )
        payload = {
            "event_id": bet.event_id,
            "market_type": bet.market_type,
            "selection": bet.selection,
            "stake": bet.stake,
            "odds": bet.odds,
        }
        result = self._post("/bets", payload)
        bet_id = str(result.get("bet_id") or result.get("id") or "unknown")
        status = str(result.get("status") or result.get("message") or "accepted")
        logger.info("LIVE: bet placed – id=%s status=%s", bet_id, status)
        return BetResponse(success=True, bet_id=bet_id, message=status)

    def check_balance(self) -> float:
        result = self._get("/account/balance")
        return float(result.get("balance") or result.get("available_balance") or 0.0)


def get_sportsbook(
    dry_run: bool = True,
    api_key: str = "",
    base_url: str = "",
) -> SportsbookProtocol:
    if dry_run:
        return StubSportsbook()
    if not api_key:
        raise ValueError("SPORTSBOOK_KEY required for LIVE mode")
    import os
    auth_header = os.environ.get("SPORTSBOOK_AUTH_HEADER", "Authorization")
    auth_prefix = os.environ.get("SPORTSBOOK_AUTH_PREFIX", "Bearer")
    return LiveSportsbook(
        api_key=api_key,
        base_url=base_url,
        auth_header=auth_header,
        auth_prefix=auth_prefix,
    )

