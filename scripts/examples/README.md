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

The batch examples need only the TEST seller NIP; they build their own FA(3) invoices:

```bash
export KSEF2_EXAMPLE_SELLER_NIP=5261040828
uv run -m scripts.examples.invoices.send_batch
uv run -m scripts.examples.invoices.submit_batch
```

Every invoice in the batch gets its own number, because KSeF identifies an invoice by
seller plus number and rejects a repeat with `440 Duplikat faktury`. Set
`KSEF2_EXAMPLE_INVOICE_XML` to send your own FA(3) file instead; the examples keep
that document as-is and rewrite only its `<P_2>` invoice number per invoice.

The single-invoice examples build one FA(3) invoice the same way, so they need only
the seller NIP too:

```bash
export KSEF2_EXAMPLE_SELLER_NIP=5261040828
uv run -m scripts.examples.quickstart
uv run -m scripts.examples.invoices.send_invoice
```

`quickstart.py` sends twice, once per session style, so it builds two invoices: one
document sent twice would be rejected as `440 Duplikat faktury` on the second pass,
and because the example does not poll invoice status it would print a reference
number for an invoice that never landed.

When `KSEF2_EXAMPLE_INVOICE_XML` points at a file, each send still gets its own
`<P_2>`: the file is reused as-is apart from that number.
