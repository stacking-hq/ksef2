from typing import Any

from pydantic import (
    AliasChoices,
    BaseModel,
    ConfigDict,
    model_validator,
)

from ksef2.logging import get_logger

logger = get_logger(__name__)


def _resolve_aliases(alias: str | AliasChoices | None) -> set[str]:
    """Return all string alternatives from a single alias specification."""
    if alias is None:
        return set()
    if isinstance(alias, str):
        return {alias}
    if isinstance(alias, AliasChoices):
        return set(alias.choices)
    return set()


def _build_known_keys(cls: type[BaseModel]) -> set[str]:
    """Collect every key that Pydantic will accept as input for *cls*."""
    known: set[str] = set()
    alias_gen = cls.model_config.get("alias_generator")

    for name, field in cls.model_fields.items():
        known.add(name)

        if field.validation_alias is not None:
            known |= _resolve_aliases(field.validation_alias)
        elif alias_gen is not None and hasattr(alias_gen, "validation_alias"):
            va = alias_gen.validation_alias
            if callable(va):
                known.add(va(name))

        if field.alias is not None:
            known |= _resolve_aliases(field.alias)
        elif (
            field.validation_alias is None
            and alias_gen is not None
            and hasattr(alias_gen, "alias")
        ):
            a = alias_gen.alias
            if callable(a):
                known.add(a(name))

    return known


class BaseSupp(BaseModel):
    model_config = ConfigDict(extra="ignore")

    @model_validator(mode="before")
    @classmethod
    def _warn_extra_fields(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return data
        known = _build_known_keys(cls)
        extra = [k for k in data if k not in known]
        if extra:
            logger.warning(
                "ignoring undeclared fields", model=cls.__name__, fields=extra
            )
        return data
