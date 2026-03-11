# Run integration tests (requires KSEF credentials in .env)
integration:
    source .env.test && uv run pytest tests/integration/ -v -m integration

# Run end-to-end example tests only (requires KSEF credentials in .env)
e2e:
    source .env.test && uv run pytest tests/integration/test_examples.py -v -m integration


sync:
    uv sync --all-groups


test:
    uv run pytest tests/unit/ -v


release-check:
    just lint
    just format-check
    just typecheck
    just test
    uv build


coverage:
    uv run python scripts/api_coverage.py


lint:
    uv run ruff check src/ tests/

format-check:
    uv run ruff format --check src/ tests/

typecheck:
    #!/usr/bin/env bash
    output=$(uv run basedpyright --level error 2>&1)
    echo "$output"
    echo "$output" | grep -q "0 errors"


sync-ksef-api-version:
    uv run python scripts/sync_ksef_api_version.py


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
      --output pydantic \
      --unnest-classes \
      --relative-imports \
      --package src.ksef2.infra.schema.fa3.models \
      --structure-style filenames \
      --generic-collections \
      --docstring-style Google \
      --no-wrapper-fields \
      --ignore-patterns
