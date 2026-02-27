"""Tests for the LLM analyst layer (all use the stub – no API key required)."""
import json
import pytest

from src.llm.llm_client import StubLLMClient, get_llm_client, LLMMessage
from src.llm.bet_analyst import BetAnalyst, BetAnalysis, get_bet_analyst
from src.research.normalization import NormalizedEvent


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _event() -> NormalizedEvent:
    return NormalizedEvent(
        event_id="test_001",
        home_team="HomeFC",
        away_team="AwayFC",
        market_type="1X2",
        home_odds=2.10,
        draw_odds=3.40,
        away_odds=3.60,
        home_lambda=1.8,
        away_lambda=1.2,
        timestamp=0.0,
    )


# ---------------------------------------------------------------------------
# StubLLMClient
# ---------------------------------------------------------------------------


def test_stub_returns_valid_json():
    client = StubLLMClient()
    response = client.chat([LLMMessage(role="user", content="test")])
    data = json.loads(response.content)
    assert isinstance(data["approved"], bool)
    assert 0.0 <= data["confidence"] <= 1.0
    assert isinstance(data["reasoning"], str)
    assert 0.0 <= data["stake_multiplier"] <= 2.0


def test_stub_is_deterministic():
    client = StubLLMClient()
    msg = [LLMMessage(role="user", content="any")]
    assert client.chat(msg).content == client.chat(msg).content


def test_get_llm_client_no_key_returns_stub():
    client = get_llm_client(api_key="")
    assert isinstance(client, StubLLMClient)


def test_get_llm_client_with_key_returns_openai_type():
    # Verify the factory returns OpenAILLMClient type without making real API calls
    try:
        from src.llm.llm_client import OpenAILLMClient
        client = get_llm_client(api_key="sk-fake", model="gpt-4o-mini")
        assert isinstance(client, OpenAILLMClient)
    except ImportError:
        pytest.skip("openai package not installed")


# ---------------------------------------------------------------------------
# BetAnalyst
# ---------------------------------------------------------------------------


def test_analyst_returns_bet_analysis():
    analyst = get_bet_analyst(StubLLMClient())
    ev = _event()
    result = analyst.analyse(
        event=ev,
        selection="home",
        decimal_odds=2.10,
        true_prob=0.57,
        edge=0.10,
        kelly_stake=25.0,
    )
    assert isinstance(result, BetAnalysis)


def test_analyst_approved_is_bool():
    analyst = get_bet_analyst(StubLLMClient())
    result = analyst.analyse(_event(), "home", 2.10, 0.57, 0.10, 25.0)
    assert isinstance(result.approved, bool)


def test_analyst_stake_multiplier_in_range():
    analyst = get_bet_analyst(StubLLMClient())
    result = analyst.analyse(_event(), "home", 2.10, 0.57, 0.10, 25.0)
    assert 0.0 <= result.stake_multiplier <= 2.0


def test_analyst_parse_error_returns_safe_default():
    """Malformed LLM JSON → conservative default (approved=False)."""

    class BadLLM:
        def chat(self, messages, temperature=0.2):
            from src.llm.llm_client import LLMResponse
            return LLMResponse(content="not json {{{", model="test", finish_reason="stop")

    analyst = BetAnalyst(BadLLM())
    result = analyst.analyse(_event(), "home", 2.10, 0.57, 0.10, 25.0)
    assert result.approved is False
    assert result.confidence == 0.0


def test_analyst_stake_multiplier_clamped():
    """stake_multiplier out of [0, 2] range is clamped."""

    class HighMultiplierLLM:
        def chat(self, messages, temperature=0.2):
            from src.llm.llm_client import LLMResponse
            payload = json.dumps({
                "approved": True,
                "confidence": 0.9,
                "reasoning": "Great bet",
                "stake_multiplier": 99.0,  # way too high
            })
            return LLMResponse(content=payload, model="test", finish_reason="stop")

    analyst = BetAnalyst(HighMultiplierLLM())
    result = analyst.analyse(_event(), "home", 2.10, 0.57, 0.10, 25.0)
    assert result.stake_multiplier <= 2.0
