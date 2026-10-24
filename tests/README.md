# Tests

The top-level directories separate tests by how they run:

| Directory | Scope |
| --- | --- |
| `unit/` | Local SDK tests with fakes, HTTP mocks, and temporary files, plus repository contract and tooling checks. |
| `integration/` | Tests against the real KSeF TEST environment, marked `integration`. Requires credentials. |
| `e2e/` | Local FA3 invoice roundtrips through builders, models, and XML mappers. |
| `compat/` | Consumer programs and configuration for the legacy compatibility gate. These run through `just check-legacy-compat`. |

## Unit test placement

Place a test beside others for the implementation or contract it exercises:

| Directory | Scope |
| --- | --- |
| `clients/` | Client operations, handles, pagination, exports, raw access, and resume behavior. |
| `core/` | Transport, cryptography, XAdES, errors, logging, stores, and other shared SDK infrastructure. |
| `endpoints/` | Endpoint request and response handling. |
| `middlewares/` | Request and response middleware behavior. |
| `services/` | Batch and invoice workflows, export parts, and document renderers. |
| `models/` | API models, validation, serialization, persisted state, and sensitive data handling. |
| `mappers/` | API request and response mapping. |
| `fa3/` | FA3 parsing, drafts, and public entry points, with `builders/`, `models/`, and `mappers/` subdirectories. |
| `contracts/` | Imports, public API visibility, deprecations, docstrings, and sync/async parity. |
| `tooling/` | Code generation, example scripts, documentation validators, coverage badges, and release checks. |

`support/` contains shared helpers and test data. `fakes/` contains test transports.
`factories/` contains model factories registered by `unit/conftest.py`.
Keep shared fixtures in `conftest.py`; keep test modules out of the unit root.

## Commands

Run commands from the repository root:

```sh
uv run python -m pytest -q                         # All local tests, including e2e
just test                                         # Unit tests
just test-runtime-checks                           # Unit tests with runtime type checks
just test-parity                                   # Sync/async parity in both modes
uv run python -m pytest tests/unit/fa3/ -q          # FA3 unit tests
uv run python -m pytest tests/e2e/ -q               # Local FA3 roundtrips
just integration                                  # Live tests with .env.test credentials
just check-legacy-compat                           # Legacy consumer compatibility
```

The default pytest selection excludes the `integration` marker. Moving a test
must preserve its fixtures, markers, assertions, and collection. Update imports,
repository-relative paths, documentation, and command references with the move.
