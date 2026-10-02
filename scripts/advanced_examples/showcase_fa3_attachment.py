from dataclasses import asdict
from pprint import pprint

from ksef2.domain.models.fa3.attachment import Attachment, AttachmentTable, DataBlock
from ksef2.infra.mappers.invoices.fa3.domain.attachment import to_spec

RAW_ATTACHMENT_JSON = """
{
  "data_blocks": [
    {
      "header": "Attachment created from raw JSON",
      "meta_data": [
        {"source": "json"},
        {"document_role": "showcase"}
      ],
      "paragraphs": [
        "This attachment is parsed with Attachment.model_validate_json.",
        "It uses the same domain model as the manual example."
      ],
      "tables": [
        {
          "meta_data": [
            {"table_id": "json-table"}
          ],
          "description": "Products included in the invoice attachment",
          "columns_names": ["Service", "Quantity", "NetAmount", "SupplyDate"],
          "columns_format": ["txt", "integer", "decimal", "date"],
          "rows": [
            ["Hosting", "12", "99.99", "2026-04-01"],
            ["Support", "3", "49.50", "2026-04-02"]
          ]
        }
      ]
    }
  ]
}
"""


def build_manual_attachment() -> Attachment:
    return Attachment(
        data_blocks=[
            DataBlock(
                header="Attachment created from domain models",
                meta_data=[
                    {"source": "manual"},
                    {"document_role": "showcase"},
                ],
                paragraphs=[
                    "This attachment is assembled directly with Attachment, DataBlock, and AttachmentTable.",
                    "The domain model auto-computes the summary for numeric columns when it is omitted.",
                ],
                tables=[
                    AttachmentTable(
                        meta_data=[{"table_id": "manual-table"}],
                        description="Service positions included in the attachment",
                        columns_names=["Service", "NetAmount", "Hours", "SupplyDate"],
                        columns_format=["txt", "decimal", "integer", "date"],
                        rows=[
                            ["Consulting", "1000.50", "10", "2026-03-29"],
                            ["Support", "250.00", "2", "2026-03-30"],
                        ],
                    )
                ],
            )
        ]
    )


def showcase(title: str, attachment: Attachment) -> None:
    print(f"\n=== {title} ===")
    print("\nDomain model:")
    pprint(attachment.model_dump(mode="json"))

    print("\nMapped spec model:")
    pprint(asdict(to_spec(attachment)))


def main() -> int:
    manual_attachment = build_manual_attachment()
    json_attachment = Attachment.model_validate_json(RAW_ATTACHMENT_JSON)

    showcase("Manual domain attachment", manual_attachment)
    showcase("Attachment parsed from raw JSON", json_attachment)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
