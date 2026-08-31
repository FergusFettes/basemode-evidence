# Agent Quickstart

Use this page when changing `basemode-evidence`. It is repository guidance; [[Contributing Evidence]]
is the guide for submitting generated evidence.

## First five minutes

```bash
uv sync --locked --group dev
make check
```

`make check` runs Ruff lint and formatting checks, the test suite with branch-aware coverage, a strict
documentation build, and wheel/sdist builds. CI repeats this gate on Python 3.11 and tests Python
3.12–3.14. Run `uv run pre-commit run --all-files` after changing tooling or broad file sets.

## Repository invariants

- Contribution PRs add exactly one immutable JSON file under `contributions/v1/YYYY/MM/`.
- Unknown fields are a privacy failure, not a forward-compatibility feature.
- Validation and compilation never need provider credentials or network calls.
- Do not average submitted percentiles or invent daily precision.
- Corrections use versioned revocations; accepted evidence and Git history stay intact.
- The provisional contribution schema stays isolated until basemode supplies its canonical schema,
  fixtures, and byte serializer.

## Change map

| Area | Start here | Verify with |
|---|---|---|
| Contribution schema | `schemas/contribution-v1.schema.json` | schema fixtures and validator tests |
| Semantic/privacy checks | `src/basemode_evidence/validate.py` | `tests/test_validate.py` |
| Aggregation/artifacts | `src/basemode_evidence/compile.py` | deterministic and revocation tests |
| CLI | `src/basemode_evidence/cli.py` | `tests/test_cli.py` |
| Intake/release policy | `.github/workflows/` | strict YAML hooks and trusted-boundary review |
| Public contract | `docs/` | `make docs-build` |

## Gotchas

- `validate-pr` checks the complete diff before reading the candidate bundle. Preserve that ordering:
  the contribution workflow intentionally installs trusted base-revision code before checking out the
  head revision.
- Compilation ignores future-clock skew for already accepted bundles. Making it depend on the current
  time would violate deterministic rebuilds.
- SQLite insertion order, canonical JSON separators, and evidence-derived build time are deliberate
  reproducibility controls.
- `dist/` is ignored and serves both packaging and dataset builds. Release workflows name dataset
  assets explicitly so wheels are not accidentally published with the ledger.

## Change checklist

1. Make the smallest coherent change and add a regression.
2. Update the relevant wiki page when behavior or policy changes.
3. Run focused tests, then `make check`.
4. Run pre-commit when configuration or documentation changes.
5. Commit in small logical units; update `uv.lock` whenever dependency constraints change.

For public behavior, read [[Architecture]], [[Privacy Model]], [[Validation]], and
[[Compiled Dataset]].
