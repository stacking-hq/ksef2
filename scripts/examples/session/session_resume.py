"""Open an online session, serialize its state, and resume it later.

Prerequisites:
- none; the script provisions and cleans up its own TEST-environment data

What it demonstrates:
- temporary test subject and person setup
- permission grants for invoice work
- serializing and restoring online session state
"""

from dataclasses import dataclass

from ksef2 import Client, Environment, FormSchema
from ksef2.core.tools import generate_nip, generate_pesel
from ksef2.domain.models.session import OnlineSessionResumeState
from ksef2.domain.models.testdata import Identifier, Permission


@dataclass
class ExampleConfig:
    environment: Environment = Environment.TEST


def run(config: ExampleConfig) -> None:
    client = Client(environment=config.environment)
    organization_nip = generate_nip()
    person_nip = generate_nip()
    person_pesel = generate_pesel()

    with client.testdata.temporal() as temp:
        print("Creating test subject...")
        temp.create_subject(
            nip=organization_nip,
            subject_type="enforcement_authority",
            description="Session resume test",
        )

        print("Creating test person...")
        temp.create_person(
            nip=person_nip,
            pesel=person_pesel,
            description="Example person",
        )

        temp.grant_permissions(
            permissions=[
                Permission(type="invoice_write", description="Send invoices"),
            ],
            grant_to=Identifier(type="nip", value=person_nip),
            in_context_of=Identifier(type="nip", value=organization_nip),
        )

        auth = client.authentication.with_test_certificate(nip=person_nip)
        print("Opening session (manual mode)...")
        session = auth.online_session(form_code=FormSchema.FA3)

        state: OnlineSessionResumeState = session.resume_state()
        state_json = state.to_json()

        print(f"Session state saved ({len(state_json)} bytes)")
        print(f"  Reference: {state.reference_number}")
        print(f"  Valid until: {state.valid_until}")

        print("Resuming session from saved state...")
        restored_state = OnlineSessionResumeState.from_json(state_json)

        print("Terminating resumed session...")
        with auth.resume_online_session(state=restored_state):
            pass
        print("Session terminated.")


def main() -> int:
    run(ExampleConfig())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
