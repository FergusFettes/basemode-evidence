from __future__ import annotations

import json
from pathlib import Path

from basemode_evidence import cli

ROOT = Path(__file__).parents[1]
FIXTURE = ROOT / "tests/fixtures/valid-bundle.json"


def test_validate_command(capsys) -> None:
    status = cli.main(["validate", str(FIXTURE), "--no-path-check"])
    captured = capsys.readouterr()
    assert status == 0
    assert "operations: 184" in captured.out
    assert captured.err == ""


def test_validation_error_is_concise(tmp_path: Path, capsys) -> None:
    invalid = tmp_path / "invalid.json"
    invalid.write_text("{}")
    status = cli.main(["validate", str(invalid), "--no-path-check"])
    captured = capsys.readouterr()
    assert status == 1
    assert captured.out == ""
    assert captured.err.startswith("error: schema validation failed:")


def test_compile_command(monkeypatch, capsys) -> None:
    expected = {"dataset_schema_version": 1, "bundle_count": 0}
    monkeypatch.setattr(cli, "compile_dataset", lambda output: expected)
    status = cli.main(["compile", "--output", "somewhere"])
    assert status == 0
    assert json.loads(capsys.readouterr().out) == expected


def test_validate_pr_command(monkeypatch, capsys) -> None:
    class Result:
        summary = "valid contribution"

    monkeypatch.setattr(cli, "validate_pr", lambda base, head: Result())
    status = cli.main(["validate-pr", "--base", "base", "--head", "head"])
    assert status == 0
    assert capsys.readouterr().out == "valid contribution\n"
