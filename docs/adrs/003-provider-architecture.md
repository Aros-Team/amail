# ADR-003: Provider-Agnostic Architecture + Singleton Pattern

## Status

Accepted

## Context

Amail is a lightweight email microservice that currently supports Resend as the only provider but is designed to support multiple providers (SendGrid, AWS SES, etc.) via a registry pattern.

### Current architecture

- `EmailProvider` ABC (base class) with `name`, `sender`, `receiver`
- `EmailSender` and `EmailReceiver` as `typing.Protocol`s (duck typing)
- Self-registration in each provider's `__init__.py`
- `get_provider()` factory that resolves the active provider from `EMAIL_PROVIDER` env var

### The problem

`get_provider()` creates a new provider instance on every call. For Resend, this means `ResendSender.__init__` sets `resend.api_key` as a module-level global on every instantiation — wasteful and fragile. Repeatedly mutating global state on every request is both a performance concern and a correctness risk if initialization order ever becomes relevant.

## Decision

### 1. Registry pattern

Providers self-register in their package's `__init__.py`. At runtime, `get_provider()` resolves the active provider from the `EMAIL_PROVIDER` environment variable and looks it up in the registry. No provider package needs to be imported unless selected.

### 2. Protocol contracts

`EmailSender` and `EmailReceiver` are `typing.Protocol`s — any class with matching method signatures satisfies the contract. This means:

- No forced inheritance hierarchy for providers
- Providers are decoupled from core abstractions
- New providers just need to implement the right methods, nothing else

### 3. Singleton provider instance

`get_provider()` caches the provider instance for the process lifetime. Provider-specific global state (like `resend.api_key`) is set once during initialization, not on every request.

Implementation:

```python
_provider: EmailProvider | None = None

def get_provider() -> EmailProvider:
    global _provider
    if _provider is None:
        name = os.getenv("EMAIL_PROVIDER", "resend")
        _provider = _registry[name]()  # instantiate once
    return _provider
```

### 4. Adding a new provider

1. Create a new package under `src/amail/` (e.g., `src/amail/sendgrid/`)
2. Implement `EmailSender` and `EmailReceiver` protocols
3. Register in the provider's `__init__.py`
4. Import the new package in `main.py` to trigger registration

No changes to core code required — the registry and `get_provider()` are already in place.

## Consequences

- **Provider initialization happens once at startup** — no repeated setup per request
- **Global provider state (like API keys) is set once** — eliminates the `resend.api_key` mutation on every instantiation
- **New providers are added by creating a package** — no changes to core code, no factory modifications
- **Tests can mock `get_provider()`** to inject test providers without touching env vars or real implementations
- **Protocol contracts mean no forced inheritance** — providers just need matching methods, keeping the contract lightweight
