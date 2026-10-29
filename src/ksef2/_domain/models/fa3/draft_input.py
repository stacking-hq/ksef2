"""Unknown-field checks scoped to serialized FA(3) draft input."""

from collections.abc import Mapping, Sequence
from functools import lru_cache
from typing import cast

from pydantic import BaseModel, GetJsonSchemaHandler, ValidationError
from pydantic.json_schema import JsonSchemaValue
from pydantic_core import InitErrorDetails


def forbid_model_extras(schema: JsonSchemaValue, handler: GetJsonSchemaHandler) -> None:
    """Close model objects in a draft schema, leaving metadata dictionaries open."""
    visited: set[int] = set()

    def visit(node: object) -> None:
        if isinstance(node, dict):
            node = cast(dict[str, object], node)
            if "$ref" in node:
                visit(handler.resolve_ref_schema(node))
            elif id(node) not in visited:
                visited.add(id(node))
                if "properties" in node:
                    node["additionalProperties"] = False
                for child in node.values():
                    visit(child)
        elif isinstance(node, list):
            for child in cast(list[object], node):
                visit(child)

    visit(schema)


@lru_cache
def _input_schema(model: type[BaseModel]) -> dict[str, object]:
    return model.model_json_schema(by_alias=False, mode="validation")


def check_draft_fields(model: type[BaseModel], data: object) -> object:
    """Reject undeclared raw fields before nested validators can discard them."""
    schema = _input_schema(model)
    definitions = cast(dict[str, dict[str, object]], schema.get("$defs", {}))
    errors: list[InitErrorDetails] = []

    def visit(
        value: object, node: dict[str, object], path: tuple[str | int, ...]
    ) -> None:
        if "$ref" in node:
            visit(value, definitions[str(node["$ref"]).rsplit("/", 1)[1]], path)
        elif "anyOf" in node:
            # Draft unions contain nullable fields, scalar alternatives, or a
            # contact object/list. Only the matching container has field names.
            for branch in cast(list[dict[str, object]], node["anyOf"]):
                visit(value, branch, path)
        elif isinstance(value, Mapping) and "properties" in node:
            properties = cast(dict[str, dict[str, object]], node["properties"])
            for key, item in cast(Mapping[str, object], value).items():
                if key not in properties:
                    errors.append(
                        {"type": "extra_forbidden", "loc": (*path, key), "input": item}
                    )
                else:
                    visit(item, properties[key], (*path, key))
        elif isinstance(value, (list, tuple)) and "items" in node:
            for index, item in enumerate(cast(Sequence[object], value)):
                visit(item, cast(dict[str, object], node["items"]), (*path, index))

    visit(data, schema, ())
    if errors:
        raise ValidationError.from_exception_data(model.__name__, errors)
    return data
