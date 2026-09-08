# Release the SDK

Version 1.0.0 includes the `ksef2` Python SDK and its documentation. The CLI
and MCP products are excluded. Their pull requests, packages, documentation,
and deployments are not release requirements.

Track release sign-off in [issue #105](https://github.com/stacking-hq/ksef2/issues/105).

## Verify the candidate

Run the offline release checks:

```sh
just release-check
```

Set `KSEF_TEST_SUBJECT_NIP`, `KSEF_TEST_PERSON_NIP`, and
`KSEF_TEST_PERSON_PESEL` in the environment or the ignored `.env.test` file.
These identities are used only against KSeF TEST.

```sh
just release-integration
```

The integration suite builds fresh FA(3) invoices with unique numbers. A
caller-supplied `KSEF2_TEST_INVOICE_XML` still overrides generated invoices.
Required invoice workflows must pass. Missing, skipped, failed, or errored
required tests reject sign-off. The legacy CLI export test is excluded.

## Prepare publication

1. Verify that `DOCS_DISPATCH_TOKEN` can dispatch to `stacking-hq/ksef2-docs`.
2. Configure the PyPI Trusted Publisher for this repository's `publish.yml`
   workflow and the GitHub environment `pypi`.
3. Verify the SDK-only docs build, deployment access, and public smoke check.
4. Set the actual release date in `CHANGELOG.md` immediately before the final
   SDK merge. Keep the heading unreleased until that date is known.
5. Merge the SDK release changes with green required checks. Record the exact
   merged commit SHA in issue #105.
6. Run **Publish to PyPI** manually on the frozen branch with
   `expected_tag=v1.0.0`. Confirm that the run's SHA matches the recorded SHA.
   This run performs preflight checks without publishing.
7. Record the integration result, artifact digest, and SHA-256 checksums.

## Publish and verify

1. Create and push one annotated `v1.0.0` tag on the recorded commit.
2. Inspect the tag workflow's verified artifact before approving the `pypi`
   environment. The tag run builds its own artifact; publication and the
   GitHub Release reuse that artifact.
3. Verify installation from PyPI on Python 3.12 and 3.13.
4. Check that the GitHub Release distributions and checksums match the tag
   workflow artifact.
5. Verify the tagged SDK docs deployment and public smoke check.

Published tags and distributions are immutable. Release later fixes as 1.0.1.
