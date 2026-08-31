# Compiled Dataset

`basemode-evidence compile` validates the complete ledger, excludes revoked bundles, and writes:

| Artifact | Contents |
|---|---|
| `endpoint_summary.json` | Endpoint totals, rates, failures, source/strategy counts, and contribution-level percentile summaries |
| `endpoint_evidence.sqlite` | Normalized bundles, observations, failures, and revocations |
| `provenance.json` | Bundle paths, IDs, hashes, inclusion status, source commit, and revocations |
| `manifest.json` | Dataset version, source commit, deterministic build time, counts, artifact sizes, and hashes |
| `SHA256SUMS` | Independent checksums for every published artifact |

The summary reports logical success rate, initial-attempt success rate, recovery rate, token and cost
totals where supplied, bundle count, and last-observed time. Verification traffic stays distinguishable
from organic sources.

Submitted p50/p95 values are not mergeable. The compiler retains them with their bundle IDs and labels
their semantics; it never averages them into a purported global percentile.

Compilation is idempotent and byte-stable for the same repository tree. Build time is derived from
the newest evidence or revocation timestamp instead of the wall clock. Release assets, not scans of
individual contribution files, are the supported machine-consumption interface.
