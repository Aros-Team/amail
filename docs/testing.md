# Testing Policy

> How to write tests that actually catch bugs.
> A test's value = its ability to **fail when the code is wrong**.

---

## 0. Core principle: the mutation mindset

Before writing a test, ask: *"If this function were broken — deleted, returned the
wrong value, or crashed on input X — would this test fail?"*

If the test would still pass, it has no value. Rewrite it or delete it.

---

## 1. Test-first (Red-Green-Refactor)

Tests are written **before** the implementation. The test is the contract; the
code is what makes it pass.

1. **Write the test** for the new function/route — it must fail on the current
   code (or fail to import because the symbol doesn't exist yet).
2. **Run it → confirm RED** (`uv run pytest tests/test_x.py -k <name>`). A test
   that passes before any implementation exists is a signal it asserts nothing
   meaningful.
3. **Implement** the minimal code to make it pass.
4. **Run → confirm GREEN**.
5. **Refactor** (clean up; tests stay green).

Enforcement:
- A task is `in_progress` only after its tests exist.
- The reviewer asks: *"would this test have failed before the implementation?"*
  If not, the test wasn't written first (or is too weak) — reject.

---

## 2. Structure

- **AAA**: Arrange (build inputs/mocks) → Act (call the unit once) → Assert (verify
  the observable outcome).
- **One scenario per test.** No test that asserts three unrelated things.
- **Naming**: `test_<unit>_<behavior>_<condition>` — the name states the contract.

---

## 3. Assertion quality

Assert the **observable contract**, not a side effect or a weak signal.

### Strong assertions

- Deterministic results → assert the **exact** value/structure.
- Routes → assert status code **and** the meaningful body fields.
- HTML/template output → assert **context**, not bare containment. Use unique
  markers (`>123456<`, `href="..."`) or parse the HTML. Assert security properties:
  user input must be HTML-escaped.
- Every public entry point → negative path (missing, malformed, not-found) **and**
  edge cases (empty, `None`, special characters, unicode, boundaries).

### Forbidden anti-patterns

| Pattern | Why it's weak |
|---|---|
| `assert x in html` (bare containment) | Passes even if the value lands in the wrong place or repeats |
| `assert a in html or b in html` | Tautology — at least one side usually passes |
| Asserting "no exception"/"didn't crash" | Verifies nothing about the outcome |
| `assert result is not None` alone | Almost always true |
| Reading private state (`obj._attr`) | Tests implementation, not behavior |

### Example: weak → strong

Weak (`tests/test_templates.py` today):

```python
def test_render_verification():
    html = render_template("verification", {"code": "123456", "lang": "en"})
    assert "123456" in html
```

Passes even if the code renders into the wrong section, appears twice, or the
email's title is missing entirely.

Strong:

```python
def test_render_verification_places_code_exactly_once():
    html = render_template("verification", {"code": "123456", "lang": "en"})
    assert html.count("123456") == 1

def test_render_verification_uses_the_code_box_marker():
    html = render_template("verification", {"code": "123456", "lang": "en"})
    assert '<div class="code">123456</div>' in html

def test_render_escapes_user_input_to_prevent_xss():
    html = render_template("action", {"message": "<script>alert(1)</script>", "lang": "en"})
    assert "<script>alert(1)</script>" not in html
    assert "&lt;script&gt;" in html
```

---

## 4. Mocking: only at boundaries
- Mock **external** boundaries: network, SDK, filesystem, time, random.
- **Never** mock the unit's own logic. A test that mocks everything the function
  does passes no matter what the implementation does.
- Assert mocks were called with the **exact** contract arguments
  (`assert_called_once_with(to=[...], subject="FWD: ...")`), not just "called".
- Keep real inputs as realistic as production payloads.

---

## 5. Minimum coverage per new function/route

For every new public function or route, ship all four:

1. **Happy path** — exact expected result.
2. **Error paths** — each error branch (400/404/500, typed provider errors).
3. **Edge cases** — empty input, `None`, boundaries, unicode.
4. **Security-relevant inputs** where applicable — HTML escaping, injection.

A new function without all four is not `done`; the reviewer must reject it.

---

## 6. Reviewer gate

The reviewer checks every PR/activity against this policy:

- [ ] Mutation mindset: each test would fail if its unit were broken
- [ ] Exact-value assertions on deterministic results; no containment-only or
      tautological asserts
- [ ] Negative + edge paths tested for every new entry point
- [ ] HTML/template output: contextual assertions + escaping test
- [ ] Mocks only at boundaries; call arguments asserted precisely
- [ ] No private-state access in tests
- [ ] Deterministic: no randomness, no wall-clock asserts without frozen time
