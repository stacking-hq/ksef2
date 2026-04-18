from ksef2.domain.models.fa3 import InvoiceHeader
from ksef2.infra.mappers.invoices.fa3.domain.header import to_spec

from dataclasses import asdict

header = InvoiceHeader()


spec_header = to_spec(header)


print(asdict(spec_header))
