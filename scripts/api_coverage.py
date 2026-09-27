import json
from pathlib import Path
from typing import TypedDict, cast

from ksef2.core.routes import ALL_ROUTES

OPENAPI_PATH = Path(__file__).resolve().parent.parent / "openapi.json"
BADGE_PATH = Path(__file__).resolve().parent.parent / "coverage.json"

Endpoint = tuple[str, str]  # (method, path)


class CoverageBadge(TypedDict):
    schemaVersion: int
    label: str
    message: str
    color: str


def load_openapi_endpoints() -> set[Endpoint]:
    data = cast(object, json.loads(OPENAPI_PATH.read_text()))
    if not isinstance(data, dict):
        raise ValueError(f"{OPENAPI_PATH.name} must contain a JSON object")

    paths = cast(dict[str, object], data).get("paths")
    if not isinstance(paths, dict):
        raise ValueError(f"{OPENAPI_PATH.name} is missing the paths object")

    endpoints: set[Endpoint] = set()
    for path, operations in cast(dict[str, object], paths).items():
        if not isinstance(operations, dict):
            raise ValueError(f"{OPENAPI_PATH.name} {path} must contain a JSON object")
        for method in cast(dict[str, object], operations):
            endpoints.add((method.upper(), path))
    return endpoints


def badge_color(pct: int) -> str:
    if pct >= 80:
        return "44cc11"
    if pct >= 60:
        return "dfb317"
    if pct >= 40:
        return "fe7d37"
    return "e05d44"


def render_badge(badge: CoverageBadge) -> str:
    return json.dumps(badge, indent=2) + "\n"


def sort_by_path(endpoint: Endpoint) -> tuple[str, str]:
    method, path = endpoint
    return path, method


def report(label: str, endpoints: set[Endpoint]) -> None:
    if not endpoints:
        return
    print(f"\n{label} ({len(endpoints)}):")
    for method, path in sorted(endpoints, key=sort_by_path):
        print(f"    {method:6} {path}")


def main() -> int:
    api_endpoints = load_openapi_endpoints()
    sdk_endpoints: set[Endpoint] = {(route.method, route.path) for route in ALL_ROUTES}
    covered = api_endpoints & sdk_endpoints
    missing = api_endpoints - sdk_endpoints
    unexpected = sdk_endpoints - api_endpoints
    pct = round(len(covered) / len(api_endpoints) * 100) if api_endpoints else 0

    badge: CoverageBadge = {
        "schemaVersion": 1,
        "label": "KSeF API coverage",
        "message": f"{len(covered)} / {len(api_endpoints)} ({pct}%)",
        "color": badge_color(pct),
    }
    badge_text = render_badge(badge)
    _ = BADGE_PATH.write_text(badge_text)
    print(badge_text, end="")

    report("Missing endpoints", missing)
    report("SDK endpoints not in OpenAPI", unexpected)

    if missing or unexpected:
        print("\nCoverage check failed: every (method, path) pair must match the spec.")
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
