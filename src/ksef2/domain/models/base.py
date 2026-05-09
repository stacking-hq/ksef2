"""Shared Pydantic base classes for SDK models and query parameter models."""

from typing import Any, cast

from pydantic import BaseModel, ConfigDict, AliasGenerator, model_validator
from pydantic.alias_generators import to_camel

from ksef2.logging import get_logger

logger = get_logger(__name__)


class KSeFBaseModel(BaseModel):
    """Base model that ignores undeclared fields and logs warnings about them."""

    model_config = ConfigDict(extra="ignore")

    @model_validator(mode="before")
    @classmethod
    def _warn_extra_fields(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return data
        known = set(cls.model_fields.keys())
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
