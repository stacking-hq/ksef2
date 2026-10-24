import json
from datetime import UTC, datetime

import pytest
from pydantic import BaseModel, SecretStr, TypeAdapter, ValidationError
from pydantic.json_schema import JsonSchemaMode

from ksef2._domain.models.invoices import InvoicesFilter
from ksef2._domain.models.session import FormSchema, OnlineSessionResumeState


class _FormModel(BaseModel):
    form_code: FormSchema


def _invoice_filter(member: FormSchema) -> InvoicesFilter:
    return InvoicesFilter(
        role="seller",
        date_type="issue_date",
        date_from=datetime(2026, 1, 1, tzinfo=UTC),
        invoice_schema=member,
    )


@pytest.mark.parametrize("member", FormSchema)
def test_json_dump_writes_the_member_name(member: FormSchema) -> None:
    model = _FormModel(form_code=member)
    filters = _invoice_filter(member)

    assert json.loads(model.model_dump_json()) == {"form_code": member.name}
    assert model.model_dump(mode="json") == {"form_code": member.name}
    assert model.model_dump()["form_code"] is member
    assert json.loads(filters.model_dump_json())["invoice_schema"] == member.name
    assert filters.model_dump(mode="json")["invoice_schema"] == member.name
    assert filters.model_dump()["invoice_schema"] is member


@pytest.mark.parametrize("member", FormSchema)
def test_reads_name_value_list_and_member(member: FormSchema) -> None:
    for value in (member.name, member.value, list(member.value), member):
        assert _FormModel.model_validate({"form_code": value}).form_code is member
    for value in (member.name, list(member.value)):
        serialized = json.dumps({"form_code": value})
        assert _FormModel.model_validate_json(serialized).form_code is member


@pytest.mark.parametrize("value", ["XX", "fa3", 3, ["FA (9)", "1-0E", "FA"], {}])
def test_rejects_unknown_input_without_echoing_it(value: object) -> None:
    for validate in (
        lambda: _FormModel.model_validate({"form_code": value}),
        lambda: _FormModel.model_validate_json(json.dumps({"form_code": value})),
    ):
        with pytest.raises(ValidationError) as caught:
            validate()

        message = caught.value.errors(include_input=False)[0]["msg"]
        assert "expected one of FA2, FA3, FA_RR1, PEF3, PEF_KOR3" in message
        assert "FA (9)" not in message


@pytest.mark.parametrize("mode", ["validation", "serialization"])
def test_json_schema_is_a_named_string_enum(mode: JsonSchemaMode) -> None:
    expected = {
        "title": "FormSchema",
        "description": "Supported form schemas for online sessions.",
        "type": "string",
        "enum": ["FA2", "FA3", "FA_RR1", "PEF3", "PEF_KOR3"],
    }
    assert TypeAdapter(FormSchema).json_schema(mode=mode) == expected

    schema = InvoicesFilter.model_json_schema(mode=mode)
    assert schema["$defs"]["FormSchema"] == expected
    reference = {"$ref": "#/$defs/FormSchema"}
    assert reference in schema["properties"]["invoice_schema"]["anyOf"]

    class DefaultFormModel(BaseModel):
        form_code: FormSchema = FormSchema.FA3

    default_schema = DefaultFormModel.model_json_schema(mode=mode)
    assert default_schema["$defs"]["FormSchema"] == expected
    assert default_schema["properties"]["form_code"] == {
        **reference,
        "default": "FA3",
    }


@pytest.mark.parametrize("member", FormSchema)
def test_invoices_filter_json_round_trip_keeps_invoice_schema(
    member: FormSchema,
) -> None:
    filters = _invoice_filter(member)

    assert InvoicesFilter.model_validate_json(filters.model_dump_json()) == filters


def test_online_session_resume_state_format_is_unchanged() -> None:
    state = OnlineSessionResumeState(
        reference_number="20250625-SO-2C3E6C8000-B675CF5D68-07",
        aes_key=SecretStr("MDEyMzQ1Njc4OWFiY2RlZjAxMjM0NTY3ODlhYmNkZWY="),
        iv=SecretStr("MDEyMzQ1Njc4OWFiY2RlZg=="),
        valid_until=datetime(2026, 1, 1, tzinfo=UTC),
        form_code=FormSchema.FA3,
    )
    data = state.to_dict()

    assert data["form_code"] == "FA3"
    assert OnlineSessionResumeState.from_dict(data) == state
    assert (
        OnlineSessionResumeState.from_dict(
            {**data, "form_code": ["FA (3)", "1-0E", "FA"]}
        )
        == state
    )
    assert (
        OnlineSessionResumeState.from_dict({**data, "form_code": "PEF3"}).form_code
        is FormSchema.PEF3
    )
