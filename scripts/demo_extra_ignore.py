"""Demonstrate KSeFBaseModel extra="ignore" with warning logging."""

from ksef2.domain.models.base import KSeFBaseModel
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
# 6. Required field missing — still raises ValidationError
# ---------------------------------------------------------------------------
print("=== Missing required field — still fails ===\n")
try:
    DemoModel(name="Dan")
except Exception as e:
    print(f"Expected error: {type(e).__name__}: {e}\n")

print("Done.")
