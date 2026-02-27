"""LLM-powered bet analyst.

For each candidate bet the analyst:
  1. Builds a structured prompt from statistical signals (Poisson probabilities,
     Kelly edge, market odds).
  2. Calls the LLM with a JSON-response instruction.
  3. Parses the structured reply into a ``BetAnalysis`` dataclass.
  4. Falls back gracefully if the LLM returns malformed JSON.

The analyst never logs the API key and is safe to use with the stub client
(no external calls).
"""
from __future__ import annotations

import json
import logging
from dataclasses import dataclass

from src.llm.llm_client import LLMClientProtocol, LLMMessage, StubLLMClient
from src.research.normalization import NormalizedEvent

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Output contract
# ---------------------------------------------------------------------------


@dataclass
class BetAnalysis:
    """LLM verdict for a single bet candidate."""

    approved: bool
    """Whether the LLM endorses placing this bet."""

    confidence: float
    """Model's confidence in its recommendation (0.0 – 1.0)."""

    reasoning: str
    """Human-readable explanation from the LLM."""

    stake_multiplier: float
    """Scaling factor applied to the Kelly stake (0.0 – 2.0; default 1.0)."""


# ---------------------------------------------------------------------------
# System prompt
# ---------------------------------------------------------------------------

_SYSTEM_PROMPT = """\
You are a professional sports-betting analyst with expertise in Poisson goal-scoring \
models, expected-value betting, and bankroll management.

You will receive a JSON object describing a single betting opportunity and must respond \
with a JSON object containing EXACTLY these keys:
  - "approved"          (boolean) – true if the bet has sufficient edge and quality
  - "confidence"        (number 0.0–1.0) – how confident you are in your verdict
  - "reasoning"         (string) – concise explanation (≤ 120 words)
  - "stake_multiplier"  (number 0.5–1.5) – scale the Kelly stake up/down (1.0 = no change)

Rules:
• Approve only when the statistical edge is genuine and not an artefact of thin liquidity.
• Reduce stake_multiplier when uncertainty is high or when model assumptions may be stale.
• Never approve bets where edge < 0.01.
• stake_multiplier must be between 0.0 and 2.0 (0.0 = skip, 1.0 = no change, 2.0 = double).
• Return only the JSON object; no markdown, no extra keys.
"""


# ---------------------------------------------------------------------------
# Analyst
# ---------------------------------------------------------------------------


class BetAnalyst:
    """Uses an LLM to provide a second opinion on each betting candidate."""

    def __init__(self, llm_client: LLMClientProtocol):
        self._client = llm_client

    def analyse(
        self,
        event: NormalizedEvent,
        selection: str,
        decimal_odds: float,
        true_prob: float,
        edge: float,
        kelly_stake: float,
    ) -> BetAnalysis:
        """Return an LLM-driven analysis for the candidate bet.

        Args:
            event: Normalised event (teams, market, lambdas, raw odds).
            selection: Chosen side – "home", "draw", or "away".
            decimal_odds: Market decimal odds for the selection.
            true_prob: Model-estimated true probability for the selection.
            edge: true_prob – implied_prob (positive = value bet).
            kelly_stake: Proposed stake computed by Kelly criterion (£ / $).
        """
        payload = {
            "event_id": event.event_id,
            "home_team": event.home_team,
            "away_team": event.away_team,
            "market_type": event.market_type,
            "selection": selection,
            "market_odds": {
                "home": event.home_odds,
                "draw": event.draw_odds,
                "away": event.away_odds,
            },
            "model_estimates": {
                "home_lambda": round(event.home_lambda, 3),
                "away_lambda": round(event.away_lambda, 3),
                "true_prob_for_selection": round(true_prob, 4),
                "implied_prob": round(1.0 / decimal_odds, 4),
                "edge": round(edge, 4),
            },
            "proposed_kelly_stake": round(kelly_stake, 2),
        }

        messages = [
            LLMMessage(role="system", content=_SYSTEM_PROMPT),
            LLMMessage(role="user", content=json.dumps(payload)),
        ]

        response = self._client.chat(messages, temperature=0.2)
        return self._parse(response.content)

    # ------------------------------------------------------------------

    @staticmethod
    def _parse(raw: str) -> BetAnalysis:
        """Parse LLM JSON response; fall back to a conservative default on error."""
        try:
            data = json.loads(raw)
            return BetAnalysis(
                approved=bool(data.get("approved", False)),
                confidence=float(data.get("confidence", 0.5)),
                reasoning=str(data.get("reasoning", "")),
                stake_multiplier=max(0.0, min(2.0, float(data.get("stake_multiplier", 1.0)))),
            )
        except (json.JSONDecodeError, TypeError, ValueError) as exc:
            logger.warning("Could not parse LLM response (%s) – using conservative default", exc)
            return BetAnalysis(
                approved=False,
                confidence=0.0,
                reasoning="LLM response parse error – bet skipped as a precaution.",
                stake_multiplier=1.0,
            )


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------


def get_bet_analyst(llm_client: LLMClientProtocol | None = None) -> BetAnalyst:
    """Return a BetAnalyst, defaulting to the stub client when none is supplied."""
    if llm_client is None:
        llm_client = StubLLMClient()
    return BetAnalyst(llm_client)
