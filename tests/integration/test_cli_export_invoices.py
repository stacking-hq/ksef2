"""Integration test for the CLI export_invoices script.

Provisions test subjects, sends an invoice, then runs the CLI to download
and export it to PDF using PEM cert/key files.

Run with:
    uv run pytest tests/integration/test_cli_export_invoices.py -v -m integration
"""

from __future__ import annotations

import time
from pathlib import Path

import pytest
from cryptography.hazmat.primitives.serialization import (
    Encoding,
    NoEncryption,
    PrivateFormat,
)

from ksef2 import Client, Environment, FormSchema
from ksef2.xades import generate_test_certificate
from tests.integration.invoice_payload import invoice_buyer_nip
from tests.integration.invoice_payload import invoice_seller_nip
from tests.integration.invoice_payload import load_test_invoice_xml


@pytest.mark.integration
def test_cli_export_invoices_with_pem(tmp_path: Path) -> None:
    """End-to-end: send invoice, then use CLI to download and export to PDF."""
    client = Client(environment=Environment.TEST)

    seller_nip = invoice_seller_nip()
    buyer_nip = invoice_buyer_nip()
    seller_cert, seller_key = generate_test_certificate(seller_nip)
    buyer_cert, buyer_key = generate_test_certificate(buyer_nip)
    invoice_xml = load_test_invoice_xml()

    # Write buyer cert/key to PEM files for the CLI
    cert_path = tmp_path / "buyer_cert.pem"
    key_path = tmp_path / "buyer_key.pem"
    cert_path.write_bytes(buyer_cert.public_bytes(Encoding.PEM))
    key_path.write_bytes(
        buyer_key.private_bytes(Encoding.PEM, PrivateFormat.PKCS8, NoEncryption())
    )

    seller_auth = client.authentication.with_xades(
        nip=seller_nip, cert=seller_cert, private_key=seller_key
    )
    with seller_auth.online_session(form_code=FormSchema.FA3) as session:
        result = session.send_invoice(invoice_xml=invoice_xml)
        print(f"Invoice sent: {result.reference_number}")

    # Wait for KSeF to process the invoice
    time.sleep(8)

    # Run the CLI as the buyer
    from scripts.cli.export_invoices import main

    output_dir = tmp_path / "pdf_output"
    main(
        argv=[
            "--nip",
            buyer_nip,
            "--cert",
            str(cert_path),
            "--key",
            str(key_path),
            "--days",
            "1",
            "--output",
            str(output_dir),
            "--env",
            "test",
        ]
    )

    # Verify at least one PDF was created
    pdfs = list(output_dir.glob("*.pdf"))
    assert len(pdfs) >= 1, f"Expected at least 1 PDF, found {len(pdfs)} in {output_dir}"
    for pdf in pdfs:
        assert pdf.stat().st_size > 0, f"PDF file {pdf} is empty"
        print(f"Verified: {pdf.name} ({pdf.stat().st_size:,} bytes)")
