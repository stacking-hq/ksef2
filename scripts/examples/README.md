# Example Scripts

The examples are organized by shape, not just by API area.

- `quickstart.py`: the shortest possible happy path.
- `<domain>/...`: focused examples for one API area such as auth, invoices, or sessions.
- `scenarios/...`: multi-step demos that coordinate test data, multiple actors, or several SDK surfaces in one flow.

Run examples as modules from the repository root.
Use `uv run -m ...`:

```bash
uv run -m scripts.examples.quickstart
uv run -m scripts.examples.invoices.send_invoice
uv run -m scripts.examples.invoices.send_batch
uv run -m scripts.examples.invoices.submit_batch
uv run --extra pdf -m scripts.examples.invoices.batch_export_to_pdf
```

Invoice-submission examples read caller-provided XML:

```bash
export KSEF2_EXAMPLE_SELLER_NIP=5261040828
export KSEF2_EXAMPLE_INVOICE_XML=/path/to/invoice.xml
uv run -m scripts.examples.invoices.send_invoice
```
