from __future__ import annotations

import json
import shutil
from datetime import UTC, datetime
from pathlib import Path

import pytest

from basemode_evidence.validate import ValidationError, validate_bundle

ROOT = Path(__file__).parents[1]
FIXTURE = ROOT / "tests/fixtures/valid-bundle.json"
NOW = datetime(2026, 8, 31, 13, tzinfo=UTC)


def contribution(tmp_path: Path) -> Path:
    (tmp_path / "schemas").mkdir()
    shutil.copy(ROOT / "schemas/contribution-v1.schema.json", tmp_path / "schemas")
    target = tmp_path / "contributions/v1/2026/08/01992df4-6c28-72f0-a67e-15fc23e6a912.json"
    target.parent.mkdir(parents=True)
    shutil.copy(FIXTURE, target)
    return target


def mutate(path: Path, callback) -> None:
    payload = json.loads(path.read_text())
    callback(payload)
    path.write_text(json.dumps(payload))


def test_valid_bundle(tmp_path: Path) -> None:
    path = contribution(tmp_path)
    result = validate_bundle(path, root=tmp_path, now=NOW)
    assert result.bundle["schema_version"] == 1
    assert "operations: 184" in result.summary
    assert "no content-bearing fields accepted" in result.summary


@pytest.mark.parametrize(
    "callback, expected",
    [
        (lambda data: data.update({"prompt": "secret"}), "Additional properties"),
        (
            lambda data: data["observations"][0].update({"operations": 1}),
            "successful_operations must not exceed operations",
        ),
        (
            lambda data: data["observations"][0]["latency_ms"].update({"p50": 7000}),
            "p50 must not exceed p95",
        ),
        (
            lambda data: data["observations"][0].update({"endpoint": "https://example.com"}),
            "does not match",
        ),
    ],
)
def test_rejects_invalid_bundle(tmp_path: Path, callback, expected: str) -> None:
    path = contribution(tmp_path)
    mutate(path, callback)
    with pytest.raises(ValidationError, match=expected):
        validate_bundle(path, root=tmp_path, now=NOW)


def test_path_must_match_bundle(tmp_path: Path) -> None:
    path = contribution(tmp_path)
    wrong = path.with_name("01992df4-6c28-72f0-a67e-15fc23e6a913.json")
    path.rename(wrong)
    with pytest.raises(ValidationError, match="filename stem"):
        validate_bundle(wrong, root=tmp_path, now=NOW)


def test_source_version_may_be_omitted(tmp_path: Path) -> None:
    path = contribution(tmp_path)
    mutate(path, lambda data: data["observations"][0].pop("source_version"))
    validate_bundle(path, root=tmp_path, now=NOW)
