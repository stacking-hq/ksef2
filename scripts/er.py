import erdantic

from ksef2.domain.models.fa3 import KsefInvoice

diagram = erdantic.create(KsefInvoice)

diagram.draw("er_diagram.png")
