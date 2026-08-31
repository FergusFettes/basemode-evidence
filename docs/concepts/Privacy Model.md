# Privacy Model

The primary privacy boundary is a closed schema: unknown fields are rejected at every level. The
repository accepts fixed dimensions, counts, totals, and fixed percentile summaries, never arbitrary
metadata.

## Prohibited data

A contribution must never contain:

- prompt or response text, hashes, or fingerprints;
- provider exception messages, response bodies, authorization headers, keys, or tokens;
- account, user, installation, host, region, IP, document, tree, or node identifiers;
- local paths, URLs, arbitrary tags, or request parameters;
- individual call timestamps or measurements.

The scanner additionally rejects suspicious keys, token-shaped values, URLs, filesystem paths, and
long natural-language strings. This is defence in depth after schema validation, not a substitute for
basemode's local privacy filtering.

## Provenance and trust

Every accepted bundle retains its path, bundle ID, and SHA-256 digest in compiled provenance. GitHub
associates a PR with an account, so this is not an anonymous system. Poisoning resistance beyond
strict validation and maintainer review is deferred, but preserved provenance allows stronger trust
policies later.

See [[Validation]] for enforced limits and [[Revocations and Releases]] for correcting producer bugs
without deleting history.
