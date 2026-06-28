"""CLI tool for downloading invoices from KSeF and exporting them to PDF.

Usage examples::

    # Token auth, last 7 days
    python scripts/cli/export_invoices.py --nip 1234567890 --token "abc123" --days 7 --output ./invoices/

    # XAdES auth with PEM cert + key (RSA or EC)
    python scripts/cli/export_invoices.py --nip 1234567890 --cert cert.pem --key key.pem --days 30

    # XAdES auth with PKCS#12 file (RSA or EC key)
    python scripts/cli/export_invoices.py --nip 1234567890 --p12 creds.p12 --p12-password secret --days 30

    # Use demo environment
    python scripts/cli/export_invoices.py --nip 1234567890 --token "abc123" --env demo
"""

import argparse
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

from ksef2 import Client, Environment, FormSchema
from ksef2.core.packages import PackageReader
from ksef2.core.exceptions import (
    KSeFApiError,
    KSeFAuthError,
    KSeFExportTimeoutError,
    KSeFInvoiceQueryTimeoutError,
)
from ksef2.domain.models import InvoicesFilter

ENVIRONMENTS = {
    "production": Environment.PRODUCTION,
    "test": Environment.TEST,
    "demo": Environment.DEMO,
}

FORM_SCHEMAS = {
    "FA2": FormSchema.FA2,
    "FA3": FormSchema.FA3,
    "PEF3": FormSchema.PEF3,
    "PEF_KOR3": FormSchema.PEF_KOR3,
}


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Download invoices from KSeF and export to PDF.",
    )

    _ = parser.add_argument("--nip", required=True, help="Taxpayer NIP number")

    # Auth: token
    _ = parser.add_argument("--token", help="KSeF authorization token")

    # Auth: XAdES PEM
    _ = parser.add_argument("--cert", help="Path to PEM certificate file")
    _ = parser.add_argument("--key", help="Path to PEM private key file")
    _ = parser.add_argument(
        "--key-password", help="Password for the PEM private key (if encrypted)"
    )

    # Auth: XAdES PKCS#12
    _ = parser.add_argument(
        "--p12", help="Path to PKCS#12 (.p12/.pfx) file (RSA or EC key)"
    )
    _ = parser.add_argument("--p12-password", help="Password for the PKCS#12 file")

    _ = parser.add_argument(
        "--days", type=int, default=7, help="Number of days back to query (default: 7)"
    )
    _ = parser.add_argument(
        "--output",
        type=Path,
        default=Path("./invoices"),
        help="Output directory for PDFs (default: ./invoices)",
    )
    _ = parser.add_argument(
        "--env",
        choices=ENVIRONMENTS,
        default="production",
        help="KSeF environment (default: production)",
    )
    _ = parser.add_argument(
        "--form",
        choices=FORM_SCHEMAS,
        default="FA3",
        help="Invoice form schema (default: FA3)",
    )

    args = parser.parse_args(argv)

    # Validate auth method
    has_token = args.token is not None
    has_pem = args.cert is not None or args.key is not None
    has_p12 = args.p12 is not None

    methods = sum([has_token, has_pem, has_p12])
    if methods == 0:
        parser.error("Provide one auth method: --token, --cert/--key, or --p12")
    if methods > 1:
        parser.error("Provide only one auth method: --token, --cert/--key, or --p12")

    if has_pem and (args.cert is None or args.key is None):
        parser.error("Both --cert and --key are required for PEM authentication")

    return args


def authenticate(client: Client, args: argparse.Namespace):
    """Authenticate and return an AuthenticatedClient."""
    if args.token:
        return client.authentication.with_token(ksef_token=args.token, nip=args.nip)

    if args.p12:
        from ksef2.core.xades import load_certificate_and_key_from_p12

        password = args.p12_password.encode() if args.p12_password else None
        cert, key = load_certificate_and_key_from_p12(args.p12, password=password)
    else:
        from ksef2.core.xades import (
            load_certificate_from_pem,
            load_private_key_from_pem,
        )

        cert = load_certificate_from_pem(args.cert)
        password = args.key_password.encode() if args.key_password else None
        key = load_private_key_from_pem(args.key, password=password)

    return client.authentication.with_xades(nip=args.nip, cert=cert, private_key=key)


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)
    environment = ENVIRONMENTS[args.env]
    _ = FORM_SCHEMAS[args.form]

    client = Client(environment=environment)

    print(f"Authenticating (NIP: {args.nip}, env: {args.env}) ...")
    try:
        auth = authenticate(client, args)
    except KSeFAuthError as exc:
        print(f"Authentication failed: {exc}", file=sys.stderr)
        sys.exit(1)

    query_filters = InvoicesFilter.for_buyer(
        date_from=datetime.now(tz=timezone.utc) - timedelta(days=args.days),
        date_to=datetime.now(tz=timezone.utc),
    )

    try:
        print(f"Waiting for invoices (last {args.days} days) ...")
        metadata = auth.invoices.wait_for_invoices(filters=query_filters)
        print(f"Found {len(metadata.invoices)} invoice(s). Exporting ...")

        zip_parts = auth.invoices.export_and_download(filters=query_filters)

        from ksef2.services.renderers import InvoicePDFExporter

        output_dir = args.output
        output_dir.mkdir(parents=True, exist_ok=True)
        exporter = InvoicePDFExporter()
        count = 0

        for invoice in PackageReader(zip_parts):
            pdf_bytes = exporter.export_from_string(invoice_xml=invoice.xml)
            pdf_path = output_dir / f"{Path(invoice.name).stem}.pdf"
            pdf_path.write_bytes(pdf_bytes)
            print(f"  Saved: {pdf_path}")
            count += 1

    except KSeFInvoiceQueryTimeoutError:
        print(
            "Timed out waiting for invoices to appear. ",
            "Try again later or increase the date range with --days.",
            file=sys.stderr,
        )
        sys.exit(2)
    except KSeFExportTimeoutError as exc:
        print(
            f"Export timed out (ref: {exc.reference_number}). ",
            "The KSeF server may be busy — try again later.",
            file=sys.stderr,
        )
        sys.exit(2)
    except KSeFApiError as exc:
        print(f"KSeF API error: {exc}", file=sys.stderr)
        sys.exit(3)

    print(f"Done. Exported {count} PDF(s) to {output_dir.resolve()}")


if __name__ == "__main__":
    main()
