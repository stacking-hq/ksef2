class InvoiceTemplater:
    @staticmethod
    def create(template_xml: str | bytes, replacements: dict[str, str]) -> bytes:
        text = (
            template_xml.decode("utf-8")
            if isinstance(template_xml, bytes)
            else template_xml
        )

        for placeholder, value in replacements.items():
            text = text.replace(placeholder, value)

        return text.encode("utf-8")
