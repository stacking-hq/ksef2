from pathlib import Path
from .styles import DEFAULT_CSS_OVERRIDES


STYLESHEET_PATH = Path(__file__).parent / "definitions" / "styl.xsl"


__all__ = ["DEFAULT_CSS_OVERRIDES", "STYLESHEET_PATH"]
