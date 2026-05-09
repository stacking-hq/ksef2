"""Shared Pydantic base classes for SDK models and query parameter models."""

from typing import Any, cast

from pydantic import (
    AliasChoices,
    AliasGenerator,
    AliasPath,
    BaseModel,
    ConfigDict,
    model_validator,
)
from pydantic.alias_generators import to_camel

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
    """Collect every key that Pydantic will accept as input for *cls*.

    Covers field names, explicit ``validation_alias`` / ``alias``, and
    ``AliasGenerator``-produced aliases (e.g. camelCase on ``KSeFBaseParams``).
    """
    known: set[str] = set()
    alias_gen = cls.model_config.get("alias_generator")

    for name, field in cls.model_fields.items():
        known.add(name)

        # Explicit validation_alias takes precedence over alias_generator
        if field.validation_alias is not None:
            known |= _resolve_aliases(field.validation_alias)
        elif (
            isinstance(alias_gen, AliasGenerator)
            and alias_gen.validation_alias is not None
        ):
            va = alias_gen.validation_alias(name)
            if isinstance(va, str):
                known.add(va)

        # alias is used as a fallback when validation_alias is not set
        if field.alias is not None:
            known |= _resolve_aliases(field.alias)
        elif (
            field.validation_alias is None
            and isinstance(alias_gen, AliasGenerator)
            and alias_gen.alias is not None
        ):
            known.add(alias_gen.alias(name))

    return known


class KSeFBaseModel(BaseModel):
    """Base model that ignores undeclared fields and logs warnings about them."""

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


class KSeFBaseParams[ParamsT](KSeFBaseModel):
    """Base model for query-parameter objects serialized with camelCase aliases."""

    model_config = ConfigDict(
        extra="ignore",
        populate_by_name=True,
        alias_generator=AliasGenerator(
            validation_alias=to_camel,
            serialization_alias=to_camel,
        ),
        use_enum_values=True,
        serialize_by_alias=True,
    )

    def to_query_params(self) -> ParamsT:
        """Serialize the model into a JSON-safe query-parameter mapping."""
        return cast(
            ParamsT, self.model_dump(by_alias=True, exclude_none=True, mode="json")
        )
