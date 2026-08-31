from __future__ import annotations

import json
import shutil
import sqlite3
from pathlib import Path

from basemode_evidence.compile import compile_dataset

ROOT = Path(__file__).parents[1]
BUNDLE_ID = "01992df4-6c28-72f0-a67e-15fc23e6a912"


def repository(tmp_path: Path) -> tuple[Path, Path]:
    repo = tmp_path / "repo"
    (repo / "schemas").mkdir(parents=True)
    shutil.copy(ROOT / "schemas/contribution-v1.schema.json", repo / "schemas")
    shutil.copy(ROOT / "schemas/revocation-v1.schema.json", repo / "schemas")
    bundle = repo / f"contributions/v1/2026/08/{BUNDLE_ID}.json"
    bundle.parent.mkdir(parents=True)
    shutil.copy(ROOT / "tests/fixtures/valid-bundle.json", bundle)
    (repo / "revocations/v1").mkdir(parents=True)
    return repo, bundle


def test_compiles_json_and_sqlite(tmp_path: Path) -> None:
    repo, _ = repository(tmp_path)
    output = tmp_path / "output"
    manifest = compile_dataset(root=repo, output=output)

    assert manifest["bundle_count"] == 1
    assert manifest["row_count"] == 1
    summary = json.loads((output / "endpoint_summary.json").read_text())
    endpoint = summary["endpoints"][0]
    assert endpoint["operations"] == 184
    assert endpoint["logical_success_rate"] == 181 / 184
    assert endpoint["percentile_summaries"][0]["bundle_id"] == BUNDLE_ID

    with sqlite3.connect(output / "endpoint_evidence.sqlite") as connection:
        assert connection.execute("SELECT count(*) FROM bundles").fetchone() == (1,)
        assert connection.execute("SELECT operations FROM observations").fetchone() == (184,)

    listed = {line.split("  ")[1] for line in (output / "SHA256SUMS").read_text().splitlines()}
    assert listed == {
        "endpoint_summary.json",
        "endpoint_evidence.sqlite",
        "provenance.json",
        "manifest.json",
    }


def test_compilation_is_byte_deterministic(tmp_path: Path) -> None:
    repo, _ = repository(tmp_path)
    first = tmp_path / "first"
    second = tmp_path / "second"
    compile_dataset(root=repo, output=first)
    compile_dataset(root=repo, output=second)
    assert {path.name: path.read_bytes() for path in first.iterdir()} == {
        path.name: path.read_bytes() for path in second.iterdir()
    }


def test_revocation_excludes_bundle_and_preserves_provenance(tmp_path: Path) -> None:
    repo, _ = repository(tmp_path)
    revocation = {
        "schema_version": 1,
        "bundle_id": BUNDLE_ID,
        "revoked_at": "2026-08-31T13:00:00Z",
        "reason": "producer_bug",
    }
    (repo / f"revocations/v1/{BUNDLE_ID}.json").write_text(json.dumps(revocation))
    output = tmp_path / "output"
    manifest = compile_dataset(root=repo, output=output)

    assert manifest["bundle_count"] == 0
    assert json.loads((output / "endpoint_summary.json").read_text())["endpoints"] == []
    provenance = json.loads((output / "provenance.json").read_text())
    assert provenance["bundles"][0]["status"] == "revoked"
    assert provenance["revocations"] == [revocation]

    with sqlite3.connect(output / "endpoint_evidence.sqlite") as connection:
        assert connection.execute("SELECT count(*) FROM bundles").fetchone() == (0,)
        assert connection.execute("SELECT reason FROM revocations").fetchone() == ("producer_bug",)
