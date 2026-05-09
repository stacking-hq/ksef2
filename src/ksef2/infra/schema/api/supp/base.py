from typing import Any

from pydantic import BaseModel, ConfigDict, model_validator

from ksef2.logging import get_logger

logger = get_logger(__name__)


class BaseSupp(BaseModel):
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
