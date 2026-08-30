"""Declarative inbound email routing contract and its loader."""

import os
from functools import lru_cache
from pathlib import Path

import yaml
from pydantic import BaseModel, EmailStr, Field

from amail.logging_config import get_logger

log = get_logger(__name__)

# Source precedence: env text -> env file path -> dev file.
ENV_ROUTES = "AMAIL_ROUTES"
ENV_ROUTES_FILE = "AMAIL_ROUTES_FILE"
DEV_ROUTES_PATH = (
    Path(__file__).resolve().parent.parent.parent / "config" / "amail.yaml"
)


class InboundRule(BaseModel):
    """A single inbound recipient mapped to one or more forward targets."""

    to: str
    forwards: list[EmailStr] = Field(default_factory=list)


class Fallback(BaseModel):
    """Forward targets used when no inbound rule matches."""

    forwards: list[EmailStr] = Field(default_factory=list)


class RoutingConfig(BaseModel):
    """The routing contract: domain, inbound rules, and a fallback."""

    domain: str
    inbound: list[InboundRule] = Field(default_factory=list)
    fallback: Fallback = Field(default_factory=Fallback)

    @property
    def accepted_recipients(self) -> set[str]:
        """Return the set of all inbound rule `to` addresses."""
        return {f"{rule.to}@{self.domain}" for rule in self.inbound}

    def resolve(self, recipients: list[str]) -> list[str]:
        """Resolve the union of forwards for matched rules, fallback otherwise."""
        matched = [
            rule for rule in self.inbound if f"{rule.to}@{self.domain}" in recipients
        ]
        resolved: list[str] = []
        if matched:
            for rule in matched:
                for target in rule.forwards:
                    if target not in resolved:
                        resolved.append(target)
        else:
            for target in self.fallback.forwards:
                if target not in resolved:
                    resolved.append(target)
        return resolved


def _read_source() -> str | None:
    """Return the routing YAML text from the first available source."""
    if os.environ.get(ENV_ROUTES):
        return os.environ[ENV_ROUTES]
    file_path = os.environ.get(ENV_ROUTES_FILE)
    if file_path and Path(file_path).is_file():
        return Path(file_path).read_text()
    if DEV_ROUTES_PATH.is_file():
        return DEV_ROUTES_PATH.read_text()
    return None


@lru_cache(maxsize=1)
def _load_cached() -> RoutingConfig | None:
    """Load and validate the routing contract, cached for the process."""
    source = _read_source()
    if source is None:
        log.error(
            "routing_missing",
            hint="set AMAIL_ROUTES/AMAIL_ROUTES_FILE or config/amail.yaml",
        )
        return None
    try:
        data = yaml.safe_load(source)
        return RoutingConfig.model_validate(data)
    except Exception as e:
        log.error("routing_parse_error", error=str(e))
        return None


def load_routing_config() -> RoutingConfig | None:
    """Return the cached routing contract, or None if absent or invalid."""
    return _load_cached()


def reset_routing_cache() -> None:
    """Clear the cached routing contract so tests can force a reload."""
    _load_cached.cache_clear()
