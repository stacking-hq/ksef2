from ksef2.infra.mappers.permissions.responses.grants import (
    from_spec as grant_from_spec,
)
from ksef2.infra.mappers.permissions.responses.query_entity import (
    entity_from_spec,
)
from ksef2.infra.mappers.permissions.responses.query_eu_entity import (
    eu_entity_from_spec,
)
from ksef2.infra.mappers.permissions.responses.query_person import person_from_spec
from ksef2.infra.mappers.permissions.responses.query_personal import (
    personal_from_spec,
)
from ksef2.infra.mappers.permissions.responses.query_subordinate_roles import (
    subordinate_roles_from_spec,
)
from ksef2.infra.mappers.permissions.responses.query_subunit import subunit_from_spec

__all__ = [
    "entity_from_spec",
    "eu_entity_from_spec",
    "grant_from_spec",
    "person_from_spec",
    "personal_from_spec",
    "subordinate_roles_from_spec",
    "subunit_from_spec",
]
