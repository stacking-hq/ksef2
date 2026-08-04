# Run integration tests (requires KSEF credentials in .env)
integration:
    source .env.test && uv run --extra pdf python -m pytest tests/integration/ -v -m integration

# Run end-to-end example tests only (requires KSEF credentials in .env)
e2e:
    source .env.test && uv run --extra pdf python -m pytest tests/integration/test_examples.py -v -m integration


sync:
    uv sync --all-groups


test:
    uv run python -m pytest tests/unit/ -v


test-runtime-checks:
    KSEF2_RUNTIME_CHECKS=1 uv run --extra runtime-checks python -m pytest tests/unit/ -q


test-fa3-contracts:
    uv run python -m pytest tests/integration/builders/fa3/ -m integration -q


test-coverage:
    uv run python -m pytest --cov=ksef2 --cov-config=.coveragerc.toml --cov-report=xml tests/unit/ -v
    uv run python scripts/test_coverage_badge.py


release-check:
    just lint
    just format-check
    just validate-docs-paths
    just validate-examples
    just check-ksef-api-version
    just check-generated-artifacts
    just check-gen-sync
    just typecheck
    just test-coverage
    just test-runtime-checks
    just test-fa3-contracts
    uv build


coverage:
    uv run python scripts/api_coverage.py


lint:
    uv run ruff check src/ tests/ scripts/examples scripts/advanced_examples scripts/extract_release_notes.py scripts/gen_sync.py scripts/sync_generated_artifacts.py scripts/test_coverage_badge.py scripts/verify_release.py scripts/validate_examples.py scripts/validate_docs_paths.py

format-check:
    uv run ruff format --check src/ tests/ scripts/examples scripts/advanced_examples scripts/extract_release_notes.py scripts/gen_sync.py scripts/sync_generated_artifacts.py scripts/test_coverage_badge.py scripts/verify_release.py scripts/validate_examples.py scripts/validate_docs_paths.py

validate-examples:
    uv run python scripts/validate_examples.py

validate-docs-paths:
    uv run python scripts/validate_docs_paths.py

gen-sync:
    uv run --group codegen python scripts/gen_sync.py

check-gen-sync:
    uv run --group codegen python scripts/gen_sync.py --check

typecheck:
    GITHUB_ACTIONS= uv run --extra runtime-checks basedpyright src --level warning --warnings
    GITHUB_ACTIONS= uv run --extra runtime-checks basedpyright tests --level error
    GITHUB_ACTIONS= uv run --extra runtime-checks --group codegen basedpyright scripts/extract_release_notes.py scripts/gen_sync.py scripts/sync_generated_artifacts.py scripts/test_coverage_badge.py scripts/verify_release.py scripts/validate_examples.py scripts/validate_docs_paths.py --level warning --warnings


sync-ksef-api-version:
    uv run python scripts/sync_ksef_api_version.py

check-ksef-api-version:
    uv run python scripts/sync_ksef_api_version.py --check


fetch-spec:
    wget https://api-test.ksef.mf.gov.pl/docs/v2/openapi.json -O openapi.json
    just sync-ksef-api-version


regenerate-models:
    uv run --group codegen python scripts/sync_generated_artifacts.py --only openapi


regenerate-fa3-models:
    uv run --group codegen python scripts/sync_generated_artifacts.py --only fa3


regenerate-artifacts:
    uv run --group codegen python scripts/sync_generated_artifacts.py


check-generated-artifacts:
    uv run --group codegen python scripts/sync_generated_artifacts.py --check
