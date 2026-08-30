import pytest

from amail.config.routing import (
    Fallback,
    InboundRule,
    RoutingConfig,
    load_routing_config,
    reset_routing_cache,
)


def test_load_routing_config_reads_from_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify a valid YAML in AMAIL_ROUTES yields a RoutingConfig."""
    yaml_text = """
domain: example.com
inbound:
  - to: support
    forwards: [ops@example.com]
  - to: team
    forwards: [team@example.com, backup@example.com]
fallback:
  forwards: [default@example.com]
"""
    monkeypatch.setenv("AMAIL_ROUTES", yaml_text)
    monkeypatch.delenv("AMAIL_ROUTES_FILE", raising=False)
    reset_routing_cache()
    try:
        config = load_routing_config()
    finally:
        reset_routing_cache()
    assert config is not None
    assert config.domain == "example.com"
    assert len(config.inbound) == 2


def test_load_routing_config_missing_is_none(monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify load_routing_config returns None when every source is absent."""
    monkeypatch.delenv("AMAIL_ROUTES", raising=False)
    monkeypatch.delenv("AMAIL_ROUTES_FILE", raising=False)
    reset_routing_cache()
    try:
        assert load_routing_config() is None
    finally:
        reset_routing_cache()


def test_resolve_single_rule_returns_its_forwards() -> None:
    """Verify resolve returns the forward list of the single matching rule."""
    config = RoutingConfig(
        domain="example.com",
        inbound=[InboundRule(to="support", forwards=["ops@example.com"])],
    )
    assert config.resolve(["support@example.com"]) == ["ops@example.com"]


def test_resolve_multiple_matched_rules_unions_and_dedups() -> None:
    """Verify multiple matched rules contribute their forwards deduped."""
    config = RoutingConfig(
        domain="example.com",
        inbound=[
            InboundRule(
                to="support",
                forwards=["ops@example.com", "admin@example.com"],
            ),
            InboundRule(to="team", forwards=["admin@example.com", "pm@example.com"]),
        ],
    )
    result = config.resolve(["support@example.com", "team@example.com"])
    assert result == ["ops@example.com", "admin@example.com", "pm@example.com"]


def test_resolve_uses_fallback_when_no_rule_matches() -> None:
    """Verify fallback forwards are used when no rule matches the recipients."""
    config = RoutingConfig(
        domain="example.com",
        inbound=[InboundRule(to="support", forwards=["ops@example.com"])],
        fallback=Fallback(forwards=["default@example.com"]),
    )
    assert config.resolve(["unknown@example.com"]) == ["default@example.com"]


def test_resolve_returns_empty_when_no_match_and_empty_fallback() -> None:
    """Verify resolve returns [] when nothing matches and fallback is empty."""
    config = RoutingConfig(
        domain="example.com",
        inbound=[InboundRule(to="support", forwards=["ops@example.com"])],
    )
    assert config.resolve(["unknown@example.com"]) == []


def test_invalid_yaml_yields_none(monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify unparsable YAML in AMAIL_ROUTES yields None, not a crash."""
    monkeypatch.setenv("AMAIL_ROUTES", "not: [valid: yaml")
    monkeypatch.delenv("AMAIL_ROUTES_FILE", raising=False)
    reset_routing_cache()
    try:
        assert load_routing_config() is None
    finally:
        reset_routing_cache()


def test_accepted_recipients_returns_rules_to_set() -> None:
    """Verify accepted_recipients is the set of all rule `to` addresses."""
    config = RoutingConfig(
        domain="example.com",
        inbound=[
            InboundRule(to="support", forwards=["a@example.com"]),
            InboundRule(to="team", forwards=["b@example.com"]),
        ],
    )
    assert config.accepted_recipients == {"support@example.com", "team@example.com"}
