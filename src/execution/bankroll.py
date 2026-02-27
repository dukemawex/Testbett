import json
import logging
import os
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)


@dataclass
class BankrollState:
    balance: float
    initial_balance: float
    total_wagered: float
    total_profit_loss: float
    daily_loss: float
    bets_today: int


class BankrollManager:
    def __init__(self, filepath: str, initial_balance: float = 1000.0):
        self.filepath = filepath
        self.initial_balance = initial_balance
        self._state: BankrollState | None = None

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------

    def load(self) -> BankrollState:
        if os.path.exists(self.filepath):
            try:
                with open(self.filepath) as fh:
                    data = json.load(fh)
                self._state = BankrollState(**data)
                logger.debug("Bankroll loaded from %s", self.filepath)
                return self._state
            except (json.JSONDecodeError, TypeError, KeyError) as exc:
                logger.warning("Could not parse bankroll file (%s); resetting.", exc)

        # Create fresh state
        self._state = BankrollState(
            balance=self.initial_balance,
            initial_balance=self.initial_balance,
            total_wagered=0.0,
            total_profit_loss=0.0,
            daily_loss=0.0,
            bets_today=0,
        )
        self.save(self._state)
        return self._state

    def save(self, state: BankrollState) -> None:
        os.makedirs(os.path.dirname(self.filepath) or ".", exist_ok=True)
        with open(self.filepath, "w") as fh:
            json.dump(asdict(state), fh, indent=2)
        logger.debug("Bankroll saved to %s", self.filepath)

    # ------------------------------------------------------------------
    # Mutations
    # ------------------------------------------------------------------

    def record_bet(self, stake: float) -> None:
        state = self._state or self.load()
        state.balance -= stake
        state.total_wagered += stake
        state.bets_today += 1
        self.save(state)

    def record_result(self, profit_loss: float) -> None:
        """Record the P&L after a bet settles (negative = loss)."""
        state = self._state or self.load()
        state.balance += profit_loss
        state.total_profit_loss += profit_loss
        if profit_loss < 0:
            state.daily_loss += abs(profit_loss)
        self.save(state)

    def check_daily_loss_limit(self, daily_loss_limit: float) -> bool:
        """Return True if we are still within the daily loss limit."""
        state = self._state or self.load()
        return state.daily_loss < daily_loss_limit
