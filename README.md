# basemode-evidence

Public, append-only, privacy-preserving aggregates of real basemode endpoint calls.

The repository validates one-file contribution pull requests and compiles accepted bundles into
deterministic JSON and SQLite datasets. It never accepts prompts, generated text, individual call
records, stable user identifiers, or provider credentials.

The implementation is under active development. See [SPEC.md](SPEC.md) for the complete contract.

## Development

```bash
python -m venv .venv
.venv/bin/pip install -e '.[dev]'
.venv/bin/pytest
```
