# basemode-evidence

`basemode-evidence` is the public, append-only repository for privacy-preserving aggregates of real
basemode endpoint calls. Evidence arrives as one-file GitHub pull requests, is validated against a
pinned schema and defensive semantic rules, and is compiled into checksum-verifiable release
artifacts for humans and tools.

It records operational evidence: logical operations, provider attempts, recovery, safe failure
categories, aggregate latency and time-to-first-token, token usage, cost, endpoint, strategy, source,
and software versions.

It does **not** call providers or retain prompts, responses, event-level measurements, stable user
identifiers, provider errors, account metadata, or arbitrary request parameters. GitHub pull requests
remain attributable to their accounts, so contributions are privacy-preserving rather than anonymous.

## Start here

- [[Architecture]] explains the boundary between basemode and this repository.
- [[Privacy Model]] describes what may and may not enter the ledger.
- [[Contribution Format]] is the v1 data contract.
- [[Contributing Evidence]] covers local and pull-request validation.
- [[Compiled Dataset]] documents the supported machine-consumption interface.
- [[Revocations and Releases]] covers corrections without history rewriting.

!!! note "Provisional schema"

    The current pinned v1 schema implements the documented contract while basemode's canonical
    exporter is being completed. It stays isolated and will be reconciled with the canonical schema,
    fixtures, and byte serializer before accepting the first real contribution.
