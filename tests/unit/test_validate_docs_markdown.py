from pathlib import Path

from scripts.validate_docs_markdown import (
    main,
    validate_docs_markdown,
    validate_page,
)


def write_page(root: Path, relative: str, body: str) -> None:
    page = root / relative
    page.parent.mkdir(parents=True, exist_ok=True)
    _ = page.write_text(body, encoding="utf-8")


def test_validate_page_accepts_plain_markdown_and_directives() -> None:
    page = "\n".join(
        [
            "---",
            "title: Page",
            "---",
            "",
            ":::note[Heads up]",
            "Plain text with `<Aside>` in inline code.",
            ":::",
            "",
            "1. First step",
            "2. Second step",
        ]
    )

    assert validate_page(page) == []


def test_validate_page_ignores_mdx_lookalikes_inside_code_fences() -> None:
    page = "\n".join(
        [
            "```python",
            "import os",
            "```",
            "",
            "````mdx",
            "```",
            "import { Aside } from '@astrojs/starlight/components';",
            "```",
            '<Aside type="note">still code</Aside>',
            "````",
            "",
            "~~~bash",
            "export KSEF2_ENV=test",
            "~~~",
        ]
    )

    assert validate_page(page) == []


def test_validate_page_flags_import_and_export_lines() -> None:
    page = (
        "import { Aside } from '@astrojs/starlight/components';\n\nexport const x = 1\n"
    )

    assert validate_page(page) == [
        "line 1: MDX import statement",
        "line 3: MDX export statement",
    ]


def test_validate_page_flags_jsx_component_tags() -> None:
    page = "\n".join(
        [
            '<Aside type="note" title="T">',
            "text",
            "</Aside>",
            "<Tabs>",
            '<LinkCard title="x" href="y" />',
        ]
    )

    assert validate_page(page) == [
        "line 1: JSX component tag <Aside>",
        "line 3: JSX component tag </Aside>",
        "line 4: JSX component tag <Tabs>",
        "line 5: JSX component tag <LinkCard>",
    ]


def test_validate_page_flags_jsx_attributes_on_html_elements() -> None:
    assert validate_page('<div className="logo">\n') == [
        "line 1: JSX attribute className"
    ]


def test_validate_page_allows_lowercase_html() -> None:
    assert validate_page("<details><summary>More</summary>text</details>\n") == []


def test_validate_docs_markdown_rejects_mdx_files(tmp_path: Path) -> None:
    write_page(tmp_path, "en/a.mdx", "plain text\n")
    write_page(tmp_path, "en/b.md", "plain text\n")

    assert validate_docs_markdown(tmp_path) == [
        "en/a.mdx: .mdx pages are not allowed; use plain .md"
    ]


def test_validate_docs_markdown_prefixes_page_errors(tmp_path: Path) -> None:
    write_page(tmp_path, "pl/how-to/a.md", "ok\n\n<Steps>\n")

    assert validate_docs_markdown(tmp_path) == [
        "pl/how-to/a.md: line 3: JSX component tag <Steps>"
    ]


def test_validate_docs_markdown_requires_pages(tmp_path: Path) -> None:
    assert validate_docs_markdown(tmp_path) == [
        f"{tmp_path}: no Markdown pages found to validate"
    ]


def test_main_returns_nonzero_for_violations(tmp_path: Path) -> None:
    write_page(tmp_path, "en/a.md", "import x from 'y'\n")

    assert main([str(tmp_path)]) == 1


def test_main_returns_zero_for_plain_markdown(tmp_path: Path) -> None:
    write_page(tmp_path, "en/a.md", "# Title\n\nText.\n")

    assert main([str(tmp_path)]) == 0
