"""Deterministically compile accepted evidence into public artifacts."""

from __future__ import annotations

import hashlib
import json
import os
import sqlite3
import subprocess
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker

from .validate import ValidationError, repository_root, validate_bundle

FAILURES = (
    "authentication",
    "quota",
    "rate_limit",
    "timeout",
    "network",
    "provider_unavailable",
    "invalid_request",
    "empty_response",
    "content_filter",
    "provider_error",
    "cancelled",
    "unknown",
)
COUNT_FIELDS = (
    "operations",
    "successful_operations",
    "initial_attempts",
    "successful_initial_attempts",
    "recovered_operations",
    "attempts",
    "input_tokens",
    "output_tokens",
)
ARTIFACTS = (
    "endpoint_summary.json",
    "endpoint_evidence.sqlite",
    "provenance.json",
    "manifest.json",
)


def _canonical_json(value: Any) -> bytes:
    return (
        json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n"
    ).encode()


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(131072), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _source_commit(repo: Path) -> str:
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=repo, text=True, capture_output=True, check=False
    )
    return result.stdout.strip() if result.returncode == 0 else "unknown"


def _load_revocations(repo: Path) -> dict[str, dict[str, Any]]:
    schema = json.loads((repo / "schemas/revocation-v1.schema.json").read_text())
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    revocations: dict[str, dict[str, Any]] = {}
    for path in sorted((repo / "revocations/v1").glob("*.json")):
        try:
            value = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            raise ValidationError(f"invalid revocation {path}: {exc}") from exc
        errors = sorted(validator.iter_errors(value), key=lambda error: list(error.path))
        if errors:
            raise ValidationError(f"invalid revocation {path}: {errors[0].message}")
        if path.stem != value["bundle_id"]:
            raise ValidationError(f"revocation filename does not match bundle_id: {path}")
        if value["bundle_id"] in revocations:
            raise ValidationError(f"duplicate revocation: {value['bundle_id']}")
        revocations[value["bundle_id"]] = value
    return revocations


def _empty_total(endpoint: str) -> dict[str, Any]:
    return {
        "endpoint": endpoint,
        **{field: 0 for field in COUNT_FIELDS},
        "cost_usd": 0.0,
        "cost_observation_count": 0,
        "failures": {failure: 0 for failure in FAILURES},
        "sources": {},
        "strategies": {},
        "bundle_ids": set(),
        "last_observed": "",
        "percentile_summaries": [],
    }


def _rate(numerator: int, denominator: int) -> float | None:
    return numerator / denominator if denominator else None


def _aggregate(bundles: list[tuple[Path, dict[str, Any]]]) -> dict[str, Any]:
    totals: dict[str, dict[str, Any]] = {}
    for _path, bundle in bundles:
        for row in bundle["observations"]:
            total = totals.setdefault(row["endpoint"], _empty_total(row["endpoint"]))
            for field in COUNT_FIELDS:
                total[field] += row.get(field, 0)
            if "cost_usd" in row:
                total["cost_usd"] += row["cost_usd"]
                total["cost_observation_count"] += 1
            for failure, count in row["failures"].items():
                total["failures"][failure] += count
            total["sources"][row["source"]] = (
                total["sources"].get(row["source"], 0) + row["operations"]
            )
            total["strategies"][row["strategy"]] = (
                total["strategies"].get(row["strategy"], 0) + row["operations"]
            )
            total["bundle_ids"].add(bundle["bundle_id"])
            total["last_observed"] = max(total["last_observed"], bundle["window_end"])
            for metric in ("latency_ms", "ttft_ms"):
                if metric in row:
                    total["percentile_summaries"].append(
                        {
                            "bundle_id": bundle["bundle_id"],
                            "metric": metric,
                            **row[metric],
                        }
                    )

    output = []
    for endpoint in sorted(totals):
        total = totals[endpoint]
        total["bundle_count"] = len(total.pop("bundle_ids"))
        total["logical_success_rate"] = _rate(total["successful_operations"], total["operations"])
        total["initial_attempt_success_rate"] = _rate(
            total["successful_initial_attempts"], total["initial_attempts"]
        )
        total["recovery_rate"] = _rate(total["recovered_operations"], total["operations"])
        total["sources"] = dict(sorted(total["sources"].items()))
        total["strategies"] = dict(sorted(total["strategies"].items()))
        total["percentile_summaries"].sort(key=lambda item: (item["bundle_id"], item["metric"]))
        output.append(total)
    return {
        "dataset_schema_version": 1,
        "percentile_semantics": "contribution-level; not globally mergeable",
        "endpoints": output,
    }


def _write_sqlite(
    path: Path,
    bundles: list[tuple[Path, dict[str, Any]]],
    revocations: dict[str, dict[str, Any]],
) -> None:
    temporary = path.with_suffix(".sqlite.tmp")
    temporary.unlink(missing_ok=True)
    connection = sqlite3.connect(temporary)
    try:
        connection.executescript(
            """
            PRAGMA page_size=4096;
            PRAGMA encoding='UTF-8';
            PRAGMA journal_mode=DELETE;
            PRAGMA user_version=1;
            CREATE TABLE bundles (
                bundle_id TEXT PRIMARY KEY, generated_at TEXT NOT NULL,
                basemode_version TEXT NOT NULL, window_start TEXT NOT NULL,
                window_end TEXT NOT NULL, path TEXT NOT NULL UNIQUE
            ) WITHOUT ROWID;
            CREATE TABLE observations (
                bundle_id TEXT NOT NULL, row_number INTEGER NOT NULL,
                endpoint TEXT NOT NULL, strategy TEXT NOT NULL, source TEXT NOT NULL,
                source_version TEXT, operations INTEGER NOT NULL,
                successful_operations INTEGER NOT NULL, initial_attempts INTEGER NOT NULL,
                successful_initial_attempts INTEGER NOT NULL, recovered_operations INTEGER NOT NULL,
                attempts INTEGER NOT NULL, input_tokens INTEGER, output_tokens INTEGER,
                cost_usd REAL,
                latency_count INTEGER, latency_p50 REAL, latency_p95 REAL,
                ttft_count INTEGER, ttft_p50 REAL, ttft_p95 REAL,
                PRIMARY KEY (bundle_id, row_number)
            ) WITHOUT ROWID;
            CREATE TABLE failures (
                bundle_id TEXT NOT NULL, row_number INTEGER NOT NULL,
                category TEXT NOT NULL, count INTEGER NOT NULL,
                PRIMARY KEY (bundle_id, row_number, category)
            ) WITHOUT ROWID;
            CREATE TABLE revocations (
                bundle_id TEXT PRIMARY KEY, revoked_at TEXT NOT NULL, reason TEXT NOT NULL
            ) WITHOUT ROWID;
            """
        )
        for relative, bundle in bundles:
            connection.execute(
                "INSERT INTO bundles VALUES (?, ?, ?, ?, ?, ?)",
                (
                    bundle["bundle_id"],
                    bundle["generated_at"],
                    bundle["basemode_version"],
                    bundle["window_start"],
                    bundle["window_end"],
                    relative.as_posix(),
                ),
            )
            for index, row in enumerate(bundle["observations"]):
                latency = row.get("latency_ms", {})
                ttft = row.get("ttft_ms", {})
                connection.execute(
                    "INSERT INTO observations VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                    (
                        bundle["bundle_id"],
                        index,
                        row["endpoint"],
                        row["strategy"],
                        row["source"],
                        row.get("source_version"),
                        row["operations"],
                        row["successful_operations"],
                        row["initial_attempts"],
                        row["successful_initial_attempts"],
                        row["recovered_operations"],
                        row["attempts"],
                        row.get("input_tokens"),
                        row.get("output_tokens"),
                        row.get("cost_usd"),
                        latency.get("count"),
                        latency.get("p50"),
                        latency.get("p95"),
                        ttft.get("count"),
                        ttft.get("p50"),
                        ttft.get("p95"),
                    ),
                )
                for category, count in sorted(row["failures"].items()):
                    connection.execute(
                        "INSERT INTO failures VALUES (?, ?, ?, ?)",
                        (bundle["bundle_id"], index, category, count),
                    )
        for bundle_id, revocation in sorted(revocations.items()):
            connection.execute(
                "INSERT INTO revocations VALUES (?, ?, ?)",
                (bundle_id, revocation["revoked_at"], revocation["reason"]),
            )
        connection.commit()
        connection.execute("VACUUM")
    finally:
        connection.close()
    os.replace(temporary, path)


def compile_dataset(
    *, root: str | Path | None = None, output: str | Path | None = None
) -> dict[str, Any]:
    """Compile every valid, non-revoked bundle and return the manifest."""
    repo = Path(root).resolve() if root else repository_root()
    destination = Path(output).resolve() if output else repo / "dist"
    destination.mkdir(parents=True, exist_ok=True)
    revocations = _load_revocations(repo)
    included: list[tuple[Path, dict[str, Any]]] = []
    provenance_bundles = []
    seen: set[str] = set()
    all_generated: list[str] = []
    contribution_root = repo / "contributions/v1"
    for path in sorted(contribution_root.glob("*/*/*.json")):
        result = validate_bundle(path, root=repo, check_duplicates=False)
        bundle = result.bundle
        bundle_id = bundle["bundle_id"]
        if bundle_id in seen:
            raise ValidationError(f"duplicate bundle_id: {bundle_id}")
        seen.add(bundle_id)
        all_generated.append(bundle["generated_at"])
        relative = path.relative_to(repo)
        revoked = bundle_id in revocations
        provenance_bundles.append(
            {
                "bundle_id": bundle_id,
                "path": relative.as_posix(),
                "sha256": _sha256(path),
                "status": "revoked" if revoked else "included",
            }
        )
        if not revoked:
            included.append((relative, bundle))

    build_time = max(
        all_generated + [item["revoked_at"] for item in revocations.values()],
        default="1970-01-01T00:00:00Z",
    )
    summary = _aggregate(included)
    summary["build_time"] = build_time
    summary["bundle_count"] = len(included)
    (destination / "endpoint_summary.json").write_bytes(_canonical_json(summary))
    _write_sqlite(destination / "endpoint_evidence.sqlite", included, revocations)

    provenance = {
        "dataset_schema_version": 1,
        "source_commit": _source_commit(repo),
        "bundles": provenance_bundles,
        "revocations": [revocations[key] for key in sorted(revocations)],
    }
    (destination / "provenance.json").write_bytes(_canonical_json(provenance))

    hashed = {}
    for name in ARTIFACTS[:3]:
        artifact = destination / name
        hashed[name] = {"size": artifact.stat().st_size, "sha256": _sha256(artifact)}
    manifest = {
        "dataset_schema_version": 1,
        "source_commit": provenance["source_commit"],
        "build_time": build_time,
        "bundle_count": len(included),
        "row_count": sum(len(bundle["observations"]) for _, bundle in included),
        "artifacts": hashed,
    }
    (destination / "manifest.json").write_bytes(_canonical_json(manifest))
    checksum_names = (*ARTIFACTS,)
    checksums = "".join(f"{_sha256(destination / name)}  {name}\n" for name in checksum_names)
    (destination / "SHA256SUMS").write_text(checksums, encoding="ascii")
    return manifest
