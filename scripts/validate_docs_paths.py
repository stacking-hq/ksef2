#!/usr/bin/env python3
"""Keep documented SDK profile paths aligned with the implementation."""

import sys
from pathlib import Path

DOCS_ROOT = Path(__file__).resolve().parents[1] / "docs"
EXPECTED_PROFILE_PATH = "~/.config/ksef2/config.toml"
WRONG_PROFILE_PATH = "~/.config/ksef/config.toml"
PROFILE_DOCS = tuple(
    sorted(
        path
        for locale in ("en", "pl")
        for path in (DOCS_ROOT / locale / "how-to-guides").glob("*.mdx")
    )
)


def main() -> int:
    failures: list[str] = []
    for path in PROFILE_DOCS:
        text = path.read_text(encoding="utf-8")
        if WRONG_PROFILE_PATH in text:
            failures.append(
                f"{path}: contains the obsolete profile path {WRONG_PROFILE_PATH}"
            )
        if (
            path.name in {"profiles.mdx", "migrate-to-1-0-0.mdx"}
            and EXPECTED_PROFILE_PATH not in text
        ):
            failures.append(
                f"{path}: missing the canonical profile path {EXPECTED_PROFILE_PATH}"
            )

    if failures:
        print("Documentation path validation failed:", file=sys.stderr)
        print("\n".join(f"- {failure}" for failure in failures), file=sys.stderr)
        return 1

    print(f"Validated profile paths in {len(PROFILE_DOCS)} documentation files.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
