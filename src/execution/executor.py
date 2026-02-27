import logging
import uuid
from typing import List

from src.research.normalization import NormalizedEvent
from src.models.true_probability import compute_edge, compute_true_probabilities
from src.models.poisson import compute_probabilities
from src.execution.kelly import compute_stake
from src.execution.sportsbook_api import BetRequest, SportsbookProtocol
from src.execution.bankroll import BankrollManager
from config.settings import Settings

logger = logging.getLogger(__name__)

# Maps selection name → (market probability attribute, odds attribute on event)
_SELECTION_MAP = {
    "home": ("home_win", "home_odds"),
    "draw": ("draw", "draw_odds"),
    "away": ("away_win", "away_odds"),
}


class Executor:
    def __init__(
        self,
        sportsbook: SportsbookProtocol,
        bankroll: BankrollManager,
        settings: Settings,
        llm_analyst=None,
    ):
        self.sportsbook = sportsbook
        self.bankroll = bankroll
        self.settings = settings
        self.llm_analyst = llm_analyst  # optional BetAnalyst; None = disabled

    def run(self, events: List[NormalizedEvent]) -> List[dict]:
        """Process events, compute edges, and place bets (or log in DRY_RUN).

        Returns a list of bet records (one dict per placed bet).
        """
        state = self.bankroll.load()
        records: List[dict] = []
        bets_placed = 0

        for event in events:
            if bets_placed >= self.settings.MAX_BETS_PER_RUN:
                logger.info("MAX_BETS_PER_RUN (%d) reached.", self.settings.MAX_BETS_PER_RUN)
                break

            if not self.bankroll.check_daily_loss_limit(self.settings.DAILY_LOSS_LIMIT):
                logger.warning("Daily loss limit reached – stopping.")
                break

            poisson_result = compute_probabilities(event.home_lambda, event.away_lambda)
            true_probs = compute_true_probabilities(poisson_result)

            best_selection, best_edge, best_odds, best_true_prob = self._best_selection(
                event, true_probs
            )

            if best_edge is None or best_edge < self.settings.MIN_EDGE_THRESHOLD:
                logger.debug(
                    "Event %s: edge %.4f below threshold %.4f – skip",
                    event.event_id,
                    best_edge or 0.0,
                    self.settings.MIN_EDGE_THRESHOLD,
                )
                continue

            stake = compute_stake(
                bankroll=state.balance,
                true_prob=best_true_prob,
                decimal_odds=best_odds,
                kelly_frac=self.settings.KELLY_FRACTION,
                max_stake_pct=self.settings.MAX_STAKE_PCT,
                min_stake=self.settings.MIN_STAKE,
            )

            if stake <= 0:
                logger.debug("Event %s: computed stake too small – skip", event.event_id)
                continue

            # ----------------------------------------------------------
            # Optional LLM second-opinion
            # ----------------------------------------------------------
            llm_reasoning = ""
            if self.llm_analyst is not None:
                analysis = self.llm_analyst.analyse(
                    event=event,
                    selection=best_selection,
                    decimal_odds=best_odds,
                    true_prob=best_true_prob,
                    edge=best_edge,
                    kelly_stake=stake,
                )
                llm_reasoning = analysis.reasoning
                if not analysis.approved:
                    logger.info(
                        "LLM rejected %s/%s (confidence=%.2f): %s",
                        event.event_id, best_selection, analysis.confidence, analysis.reasoning,
                    )
                    continue
                # Apply stake multiplier, then re-check minimum stake
                stake = min(
                    round(stake * analysis.stake_multiplier, 2),
                    round(state.balance * self.settings.MAX_STAKE_PCT, 2),
                )
                if stake < self.settings.MIN_STAKE:
                    logger.debug(
                        "Event %s: stake %.2f below MIN_STAKE after LLM multiplier – skip",
                        event.event_id, stake,
                    )
                    continue
                logger.info(
                    "LLM approved %s/%s (confidence=%.2f, multiplier=%.2f): %s",
                    event.event_id, best_selection,
                    analysis.confidence, analysis.stake_multiplier,
                    analysis.reasoning,
                )

            bet = BetRequest(
                event_id=event.event_id,
                market_type=event.market_type,
                selection=best_selection,
                stake=stake,
                odds=best_odds,
            )

            if self.settings.DRY_RUN:
                logger.info(
                    "[DRY_RUN] Would bet %.2f on %s/%s @ %.2f (edge=%.4f)",
                    stake,
                    event.event_id,
                    best_selection,
                    best_odds,
                    best_edge,
                )
                response_success = True
                bet_id = f"dry_{uuid.uuid4().hex[:8]}"
            else:
                response = self.sportsbook.place_bet(bet)
                response_success = response.success
                bet_id = response.bet_id
                if response_success:
                    self.bankroll.record_bet(stake)

            record = {
                "bet_id": bet_id,
                "event_id": event.event_id,
                "home_team": event.home_team,
                "away_team": event.away_team,
                "market_type": event.market_type,
                "selection": best_selection,
                "stake": stake,
                "odds": best_odds,
                "true_prob": round(best_true_prob, 4),
                "edge": round(best_edge, 4),
                "llm_reasoning": llm_reasoning,
                "dry_run": self.settings.DRY_RUN,
                "success": response_success,
            }
            records.append(record)
            bets_placed += 1
            logger.info("Bet recorded: %s", record)

        return records

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _best_selection(self, event: NormalizedEvent, true_probs):
        """Return (selection, edge, odds, true_prob) for the highest-edge selection."""
        candidates = [
            ("home", getattr(true_probs, "home_win"), event.home_odds),
            ("draw", getattr(true_probs, "draw"), event.draw_odds),
            ("away", getattr(true_probs, "away_win"), event.away_odds),
        ]
        best = max(
            candidates,
            key=lambda x: compute_edge(x[1], x[2]),
        )
        selection, true_prob, odds = best
        edge = compute_edge(true_prob, odds)
        return selection, edge, odds, true_prob

