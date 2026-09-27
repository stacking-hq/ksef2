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

`quickstart.py` needs no configuration at all: it carries a TEST seller NIP,
because KSeF TEST accepts any well-formed NIP together with a generated test
certificate. Pass `ExampleConfig(seller_nip=...)` to `run()` to submit as another
subject.

The other invoice examples read the seller NIP from the environment and build
their own FA(3) invoices:

```bash
export KSEF2_EXAMPLE_SELLER_NIP=5261040828
uv run -m scripts.examples.invoices.send_invoice
uv run -m scripts.examples.invoices.send_batch
```

Every invoice gets its own number, because KSeF identifies an invoice by seller
plus number and rejects a repeat with `440 Duplikat faktury`. That includes the
two invoices `quickstart.py` sends, one per session style: a single document sent
twice would be rejected on the second pass, and because the example does not poll
invoice status it would print a reference number for an invoice that never landed.
