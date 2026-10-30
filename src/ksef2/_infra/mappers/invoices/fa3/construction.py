"""Separate XML mapping from draft business validation."""

from collections.abc import Iterator
from contextlib import contextmanager
from contextvars import ContextVar

from pydantic import BaseModel

_XML_MAPPING = ContextVar("fa3_xml_mapping", default=False)


@contextmanager
def xml_mapping() -> Iterator[None]:
    """Construct typed mapper output without applying draft business rules."""
    token = _XML_MAPPING.set(True)
    try:
        yield
    finally:
        _XML_MAPPING.reset(token)


def mapped_model[T: BaseModel](
    model: type[T],
    /,
    **values: object,
) -> T:
    """Use already converted mapper values from XML, or validate drafts."""
    if _XML_MAPPING.get():
        return model.model_construct(_fields_set=set(values), **values)
    return model(**values)
