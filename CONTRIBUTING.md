# Contributing

There are two deliberately separate contribution paths.

## Evidence bundles

Evidence pull requests add exactly one JSON file under
`contributions/v1/YYYY/MM/<bundle-id>.json`. They must not change any other file. Run:

```bash
uv run basemode-evidence validate contributions/v1/YYYY/MM/<bundle-id>.json
```

The dedicated workflow builds its validator from the trusted base revision, validates the pull
request boundary and payload, and posts a content-free summary. Please do not include prompts,
responses, exception bodies, identifiers, or explanatory prose in a bundle.

## Code, policy, and revocations

Use a separate pull request for implementation, documentation, schema policy, workflow, or
revocation changes. Before opening it:

```bash
uv sync --locked --group dev
make check
uv run pre-commit run --all-files
```

Add tests for observable behavior and keep commits small and logically scoped. Schema compatibility
changes require a new schema version. Accepted evidence is never edited or deleted; use a versioned
revocation instead.

Daily aggregation and Parquet remain deferred until the canonical basemode exporter provides data
that can support them without inventing precision.
