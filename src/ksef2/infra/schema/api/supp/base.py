from typing import Any

from pydantic import (
    AliasChoices,
    AliasGenerator,
    AliasPath,
    BaseModel,
    ConfigDict,
    model_validator,
)

from ksef2.logging import get_logger

logger = get_logger(__name__)


_AliasSpec = str | AliasPath | AliasChoices | None


def _resolve_aliases(alias: _AliasSpec) -> set[str]:
    """Return all string alternatives from a single alias specification."""
    if alias is None:
        return set()
    if isinstance(alias, str):
        return {alias}
    if isinstance(alias, AliasChoices):
        return {c for c in alias.choices if isinstance(c, str)}
    return set()  # AliasPath — nested path, not a flat key


def _build_known_keys(cls: type[BaseModel]) -> set[str]:
    """Collect every key that Pydantic will accept as input for *cls*."""
    known: set[str] = set()
    alias_gen = cls.model_config.get("alias_generator")

    for name, field in cls.model_fields.items():
        known.add(name)

        if field.validation_alias is not None:
            known |= _resolve_aliases(field.validation_alias)
        elif (
            isinstance(alias_gen, AliasGenerator)
            and alias_gen.validation_alias is not None
        ):
            va = alias_gen.validation_alias(name)
            if isinstance(va, str):
                known.add(va)

        if field.alias is not None:
            known |= _resolve_aliases(field.alias)
        elif (
            field.validation_alias is None
            and isinstance(alias_gen, AliasGenerator)
            and alias_gen.alias is not None
        ):
            known.add(alias_gen.alias(name))

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
