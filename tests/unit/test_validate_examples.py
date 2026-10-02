from pathlib import Path

import pytest

from scripts.validate_examples import (
    check_markdown_source,
    check_python_source,
    is_public_module,
    main,
    validate,
)


@pytest.mark.parametrize(
    "module",
    [
        "ksef2",
        "ksef2.models",
        "ksef2.clients",
        "ksef2.fa3",
        "ksef2.xades",
        "ksef2.profiles",
        "ksef2.renderers",
        "ksef2.testdata",
        "ksef2.raw",
        "ksef2.raw.mappers",
        "ksef2.raw.spec",
        "datetime",
        "pydantic",
    ],
)
def test_public_modules_are_accepted(module: str) -> None:
    assert is_public_module(module)


@pytest.mark.parametrize(
    "module",
    [
        "ksef2.domain",
        "ksef2.domain.models.encryption",
        "ksef2.core.tools",
        "ksef2.infra.mappers",
        "ksef2.services.renderers",
        "ksef2.endpoints.auth",
        "ksef2.rawish",
    ],
)
def test_internal_modules_are_rejected(module: str) -> None:
    assert not is_public_module(module)


def test_python_source_reports_internal_imports_with_line_numbers() -> None:
    source = (
        "from ksef2 import Client\n"
        "from ksef2.core.tools import generate_nip\n"
        "import ksef2.domain.models\n"
    )

    errors = check_python_source(source)

    assert len(errors) == 2
    assert errors[0].startswith("line 2:") and "ksef2.core.tools" in errors[0]
    assert errors[1].startswith("line 3:") and "ksef2.domain.models" in errors[1]


def test_python_source_accepts_public_imports_and_ignores_relative_imports() -> None:
    source = "from ksef2.models import Identifier\nfrom . import helpers\n"

    assert check_python_source(source) == []


def test_python_source_reports_syntax_errors() -> None:
    assert check_python_source("def broken(:\n")[0].startswith("syntax error")


def test_markdown_checks_only_fenced_python_blocks() -> None:
    text = "\n".join(
        [
            "Prose mentioning `from ksef2.core.tools import generate_nip`.",
            "",
            "```bash",
            "from ksef2.infra import nothing",
            "```",
            "",
            "<Tabs>",
            '  ```python title="x.py"',
            "  from ksef2 import Client",
            "  from ksef2.domain.models.encryption import CertUsage",
            "  ```",
            "</Tabs>",
            "",
            "```python",
            "import ksef2.services.invoices",
            "```",
            "",
            "```python",
            "from ksef2.models import Identifier",
            "```",
        ]
    )

    errors = check_markdown_source(text)

    assert len(errors) == 2
    assert errors[0].startswith("line 10:") and "ksef2.domain" in errors[0]
    assert errors[1].startswith("line 15:") and "ksef2.services" in errors[1]


def make_repo(root: Path, *, example: str, page: str) -> None:
    (root / "scripts" / "examples").mkdir(parents=True)
    (root / "scripts" / "examples" / "demo.py").write_text(example)
    for locale in ("en", "pl"):
        (root / "docs" / locale).mkdir(parents=True)
        (root / "docs" / locale / "page.mdx").write_text(page)
    (root / "README.md").write_text("```python\nfrom ksef2 import Client\n```\n")


GOOD_PAGE = "```python\nfrom ksef2.models import Identifier\n```\n"


def test_validate_accepts_a_public_only_repo(tmp_path: Path) -> None:
    make_repo(tmp_path, example="from ksef2 import Client\n", page=GOOD_PAGE)

    failures, examples, pages = validate(tmp_path)

    assert failures == []
    assert examples == 1
    assert pages == 3


def test_validate_reports_failures_per_file(tmp_path: Path) -> None:
    make_repo(
        tmp_path,
        example="from ksef2.core.tools import generate_nip\n",
        page="```python\nfrom ksef2.domain.models import X\n```\n",
    )

    failures, _, _ = validate(tmp_path)

    assert any(f.startswith("scripts/examples/demo.py: line 1:") for f in failures)
    assert any(f.startswith("docs/en/page.mdx: line 2:") for f in failures)
    assert any(f.startswith("docs/pl/page.mdx: line 2:") for f in failures)


def test_validate_fails_when_nothing_matches(tmp_path: Path) -> None:
    failures, examples, pages = validate(tmp_path)

    assert examples == 0
    assert pages == 0
    assert any("no example scripts" in f for f in failures)
    assert any("no documentation pages" in f for f in failures)


def test_main_exit_codes(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    assert main([str(tmp_path)]) == 1
    assert "Example validation failed" in capsys.readouterr().err

    make_repo(tmp_path, example="from ksef2 import Client\n", page=GOOD_PAGE)
    assert main([str(tmp_path)]) == 0
    assert "Validated 1 example files" in capsys.readouterr().out


def test_repository_examples_and_docs_use_the_public_surface() -> None:
    failures, examples, pages = validate(Path(__file__).resolve().parents[2])

    assert failures == []
    assert examples > 0
    assert pages > 0
