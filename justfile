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


test-coverage:
    uv run python -m pytest --cov=ksef2 --cov-config=.coveragerc.toml --cov-report=xml tests/unit/ -v
    uv run python scripts/test_coverage_badge.py


release-check:
    just lint
    just format-check
    just check-ksef-api-version
    just check-gen-sync
    just typecheck
    just test
    just test-runtime-checks
    uv build


coverage:
    uv run python scripts/api_coverage.py


lint:
    uv run ruff check src/ tests/ scripts/gen_sync.py

format-check:
    uv run ruff format --check src/ tests/ scripts/gen_sync.py

gen-sync:
    uv run python scripts/gen_sync.py

check-gen-sync:
    uv run python scripts/gen_sync.py --check

typecheck:
    #!/usr/bin/env bash
    output=$(uv run --extra runtime-checks basedpyright --level error 2>&1)
    echo "$output"
    echo "$output" | grep -q "0 errors"
    uv run --extra runtime-checks basedpyright scripts/gen_sync.py


sync-ksef-api-version:
    uv run python scripts/sync_ksef_api_version.py

check-ksef-api-version:
    uv run python scripts/sync_ksef_api_version.py --check


fetch-spec:
    wget https://api-test.ksef.mf.gov.pl/docs/v2/openapi.json -O openapi.json
    just sync-ksef-api-version


regenerate-models:
    uv run --group codegen datamodel-codegen \
      --input openapi.json \
      --input-file-type openapi \
      --output models.py \
      --output-model-type pydantic_v2.BaseModel \
      --use-annotated \
      --field-constraints \
      --use-standard-collections \
      --use-union-operator \
      --strict-nullable \
      --collapse-root-models \
      --use-schema-description \
      --use-field-description \
      --disable-timestamp \
      --target-python-version 3.12 \
      --output src/ksef2/infra/schema/api/spec/models.py
    uv run ruff format src/ksef2/infra/schema/api/spec/models.py


regenerate-fa3-models:
    xsdata generate schemas/FA3/schemat.xsd \
      --output dataclasses \
      --unnest-classes \
      --relative-imports \
      --package ksef2.infra.schema.fa3.models \
      --structure-style filenames \
      --docstring-style Google
