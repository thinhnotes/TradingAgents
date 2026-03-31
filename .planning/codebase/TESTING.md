# TESTING.md — Test Structure & Practices

## Test Framework

- **Framework**: Python `unittest` (stdlib)
- **Test runner**: Standard `python -m unittest` or any compatible runner (pytest, etc.)
- **Test location**: `tests/` directory at project root (not inside package)
- **No pytest** detected — `pytest` not listed in `pyproject.toml` dependencies
- **No CI configuration found** (no `.github/workflows/`, no `tox.ini`, no `Makefile`)

## Test Files

| File | What it tests | Pattern |
|---|---|---|
| `tests/test_model_validation.py` | LLM model catalog + `validate_model()` | Unit, uses mock `DummyLLMClient` |
| `tests/test_google_api_key.py` | `GoogleClient` API key parameter handling | Unit, uses `unittest.mock.patch` |
| `tests/test_ticker_symbol_handling.py` | Ticker symbol parsing edge cases | Unit, 614 bytes (small) |

## Test Patterns

### unittest.TestCase Subclassing

```python
class ModelValidationTests(unittest.TestCase):
    def test_{what_is_tested}(self):
        ...
    
    def test_{scenario}_with_{condition}(self):
        ...
```

### Mock Usage

```python
from unittest.mock import patch

@patch("tradingagents.llm_clients.google_client.NormalizedChatGoogleGenerativeAI")
def test_api_key_handling(self, mock_chat):
    client = GoogleClient("gemini-2.5-flash", api_key="test-key")
    client.get_llm()
    call_kwargs = mock_chat.call_args[1]
    self.assertEqual(call_kwargs.get("google_api_key"), "test-key")
```

- Mocking at the module import path (not object reference) — standard unittest.mock pattern
- `reset_mock()` called between subtests in loops

### Subtest Pattern

```python
for provider, model in test_cases:
    with self.subTest(provider=provider, model=model):
        self.assertTrue(validate_model(provider, model))
```

Used in `test_model_validation.py` to test all provider/model combinations.

### Stub Classes

```python
class DummyLLMClient(BaseLLMClient):
    """Minimal concrete subclass for testing abstract BaseLLMClient."""
    def get_llm(self):
        self.warn_if_unknown_model()
        return object()  # No real LLM initialized
    
    def validate_model(self):
        return validate_model(self.provider, self.model)
```

### Warning Testing

```python
with warnings.catch_warnings(record=True) as caught:
    warnings.simplefilter("always")
    client.get_llm()
self.assertEqual(len(caught), 1)
self.assertIn("model-name", str(caught[0].message))
```

Pattern used to verify unknown model warning behavior.

## Test Coverage Assessment

### Well-Covered Areas
- LLM client model validation logic
- Google client API key parameter handling
- Model catalog consistency

### Gaps / Not Tested
- **No agent integration tests** — no tests for any `create_*` agent functions
- **No dataflow tests** — no tests for `y_finance.py`, `alpha_vantage_*.py`, or `interface.py`
- **No graph tests** — `TradingAgentsGraph` has no unit or integration tests
- **No CLI tests** — `cli/main.py` (50KB, the largest file) has no tests
- **No memory tests** — `FinancialSituationMemory` / BM25 retrieval untested
- **No reflection tests** — `Reflector` class untested
- **No edge/routing tests** — `ConditionalLogic` untested
- Overall test coverage is **very low** — tests only cover ~3 small utility modules

## Running Tests

```bash
# Run all tests
python -m unittest discover tests/

# Run specific test file
python -m unittest tests.test_model_validation

# Ad-hoc test script (not part of test suite)
python test.py
```

## `test.py` (Root Level)

Ad-hoc script (648 bytes) — not part of the `tests/` suite. Likely a quick smoke test or scratch file.

## Recommendations for Future Tests

Given current gaps, priority test areas would be:
1. `dataflows/interface.py` — vendor routing logic (pure logic, easy to mock)
2. `agents/utils/memory.py` — BM25 retrieval (pure Python, no external deps)
3. `graph/conditional_logic.py` — routing conditions (pure logic)
4. `graph/signal_processing.py` — signal parsing (pure string processing)
5. Integration test for `TradingAgentsGraph.propagate()` with mocked LLM responses
