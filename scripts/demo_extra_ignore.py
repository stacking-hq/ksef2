"""Demonstrate KSeFBaseModel extra="ignore" with warning logging."""

from pydantic import Field

from ksef2.domain.models.base import KSeFBaseModel, KSeFBaseParams
from ksef2.logging import configure_logging

# ---------------------------------------------------------------------------
# 1. Enable structlog console output so we can see the warnings
# ---------------------------------------------------------------------------
configure_logging(level="WARNING", renderer="console")


# ---------------------------------------------------------------------------
# 2. Define a minimal model for the demo
# ---------------------------------------------------------------------------
class DemoModel(KSeFBaseModel):
    name: str
    age: int


# ---------------------------------------------------------------------------
# 3. Normal usage — no warnings
# ---------------------------------------------------------------------------
print("=== Normal usage (no warnings expected) ===\n")
m = DemoModel(name="Alice", age=30)
print(f"OK: {m}\n")

# ---------------------------------------------------------------------------
# 4. Extra field — silently ignored, warning logged
# ---------------------------------------------------------------------------
print("=== Extra field — ignored + warning ===\n")
m = DemoModel(name="Bob", age=25, new_api_field="this is new")
print(f"OK: {m}\n")

# ---------------------------------------------------------------------------
# 5. Multiple extra fields (simulating a bigger API update)
# ---------------------------------------------------------------------------
print("=== Multiple extra fields ===\n")
m = DemoModel(
    name="Carol",
    age=40,
    certificate_metadata={"alg": "RS256"},
    session_ttl=3600,
    deprecated_flag=True,
)
print(f"OK: {m}\n")

# ---------------------------------------------------------------------------
# 6. Missing required field — still raises ValidationError
# ---------------------------------------------------------------------------
print("=== Missing required field — still fails ===\n")
try:
    DemoModel(name="Dan")
except Exception as e:
    print(f"Expected error: {type(e).__name__}: {e}\n")

# ---------------------------------------------------------------------------
# 7. Alias-aware — camelCase keys on KSeFBaseParams do NOT trigger warnings
# ---------------------------------------------------------------------------
print("=== Alias-aware: camelCase keys on KSeFBaseParams ===\n")


class DemoParams(KSeFBaseParams[dict[str, object]]):
    page_offset: int = Field(default=0)
    page_size: int = Field(default=10)


# Both the Python name and the camelCase alias are accepted — no warnings
m = DemoParams(pageOffset=1, pageSize=50)
print(f"OK: {m}")
print(f"  -> to_query_params(): {m.to_query_params()}\n")

# Same model with actual extra field — warning still fires
m = DemoParams(pageOffset=0, pageSize=20, unknown="should warn")
print(f"OK: {m}\n")

# ---------------------------------------------------------------------------
# 8. Explicit validation_alias on a field
# ---------------------------------------------------------------------------
print("=== Explicit validation_alias ===\n")


class AliasedModel(KSeFBaseModel):
    value: int = Field(validation_alias="val")


m = AliasedModel(val=42)
print(f"OK: {m}\n")

print("Done.")
