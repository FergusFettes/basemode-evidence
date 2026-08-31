"""Defensive validation for contribution bundles and contribution-only PRs."""

from __future__ import annotations

import json
import math
import re
import subprocess
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from importlib import resources
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker

MAX_FILE_BYTES = 1_000_000
MAX_WINDOW = timedelta(days=31)
MAX_FUTURE_SKEW = timedelta(hours=24)
CONTRIBUTION_PATH = re.compile(
    r"^contributions/v1/(?P<year>\d{4})/(?P<month>0[1-9]|1[0-2])/(?P<id>[0-9a-f-]{36})\.json$"
)
SUSPICIOUS_KEY = re.compile(
    r"(?:prompt|response|message|content|body|secret|api.?key|authorization|account|user.?id|"
    r"install|hostname|path|document.?id|tree.?id|node.?id|request.?params?)",
    re.IGNORECASE,
)
URL_OR_PATH = re.compile(r"(?:https?://|file://|(?:^|\s)/(?:Users|home|tmp|var|etc)/|[A-Za-z]:\\)")
TOKEN_LIKE = re.compile(r"(?:sk-[A-Za-z0-9_-]{16,}|Bearer\s+[A-Za-z0-9._-]{12,})")
NATURAL_LANGUAGE = re.compile(r"(?:[A-Za-z]{2,}\s+){7,}[A-Za-z]{2,}")


@dataclass(frozen=True)
class ValidationResult:
    """A validated bundle and its human-readable summary."""

    path: Path
    bundle: dict[str, Any]
    summary: str


class ValidationError(ValueError):
    """Raised when evidence fails schema, semantic, privacy, or PR validation."""


def repository_root(start: Path | None = None) -> Path:
    """Return the nearest parent containing the pinned schema."""
    current = (start or Path.cwd()).resolve()
    if current.is_file():
        current = current.parent
    for candidate in (current, *current.parents):
        if (candidate / "schemas/contribution-v1.schema.json").is_file():
            return candidate
    raise ValidationError("could not locate schemas/contribution-v1.schema.json")


def _load_json(path: Path, *, max_bytes: int = MAX_FILE_BYTES) -> Any:
    try:
        size = path.stat().st_size
    except OSError as exc:
        raise ValidationError(f"cannot read {path}: {exc}") from exc
    if size > max_bytes:
        raise ValidationError(f"file exceeds {max_bytes} byte limit")
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except UnicodeDecodeError as exc:
        raise ValidationError("bundle must be UTF-8") from exc
    except json.JSONDecodeError as exc:
        raise ValidationError(f"invalid JSON: {exc}") from exc


def _load_schema(repo: Path, name: str) -> Any:
    source_schema = repo / "schemas" / name
    if source_schema.is_file():
        return _load_json(source_schema)
    try:
        packaged = resources.files("basemode_evidence").joinpath("schemas", name)
        return json.loads(packaged.read_text(encoding="utf-8"))
    except (FileNotFoundError, ModuleNotFoundError, json.JSONDecodeError) as exc:
        raise ValidationError(f"could not locate pinned schema {name}") from exc


def _utc(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def _scan(value: Any, location: str = "$") -> list[str]:
    errors: list[str] = []
    if isinstance(value, dict):
        for key, child in value.items():
            if SUSPICIOUS_KEY.search(key) and key not in {
                "content_filter",
                "empty_response",
                "input_tokens",
                "output_tokens",
            }:
                errors.append(f"{location}.{key}: suspicious key")
            errors.extend(_scan(child, f"{location}.{key}"))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            errors.extend(_scan(child, f"{location}[{index}]"))
    elif isinstance(value, str):
        if TOKEN_LIKE.search(value):
            errors.append(f"{location}: token-like value")
        if URL_OR_PATH.search(value):
            errors.append(f"{location}: URL or filesystem path")
        if len(value) > 160 or NATURAL_LANGUAGE.search(value):
            errors.append(f"{location}: content-like string")
    return errors


def _semantic_errors(
    bundle: dict[str, Any], *, now: datetime | None = None, check_clock: bool = True
) -> list[str]:
    errors: list[str] = []
    start = _utc(bundle["window_start"])
    end = _utc(bundle["window_end"])
    generated = _utc(bundle["generated_at"])
    current = now or datetime.now(UTC)
    if start >= end:
        errors.append("window_start must be before window_end")
    if end - start > MAX_WINDOW:
        errors.append(f"aggregation window exceeds {MAX_WINDOW.days} days")
    if generated < end:
        errors.append("generated_at must not precede window_end")
    if check_clock and generated > current + MAX_FUTURE_SKEW:
        errors.append("generated_at is too far in the future")

    dimensions: set[tuple[str, str, str, str | None]] = set()
    for index, row in enumerate(bundle["observations"]):
        prefix = f"observations[{index}]"
        checks = (
            ("successful_operations", "operations"),
            ("recovered_operations", "successful_operations"),
            ("successful_initial_attempts", "initial_attempts"),
            ("initial_attempts", "attempts"),
        )
        for smaller, larger in checks:
            if row[smaller] > row[larger]:
                errors.append(f"{prefix}.{smaller} must not exceed {larger}")
        if sum(row["failures"].values()) > row["attempts"]:
            errors.append(f"{prefix}: summed failures must not exceed attempts")
        metrics = (
            ("latency_ms", "successful_operations"),
            ("ttft_ms", "successful_operations"),
        )
        for metric, population in metrics:
            if metric not in row:
                continue
            if row[metric]["count"] > row[population]:
                errors.append(f"{prefix}.{metric}.count must not exceed {population}")
            if row[metric]["p50"] > row[metric]["p95"]:
                errors.append(f"{prefix}.{metric}.p50 must not exceed p95")
            if not all(math.isfinite(row[metric][key]) for key in ("p50", "p95")):
                errors.append(f"{prefix}.{metric}: percentiles must be finite")
        if "cost_usd" in row and not math.isfinite(row["cost_usd"]):
            errors.append(f"{prefix}.cost_usd must be finite")
        dimension = (row["endpoint"], row["strategy"], row["source"], row.get("source_version"))
        if dimension in dimensions:
            errors.append(f"{prefix}: duplicate observation dimensions")
        dimensions.add(dimension)
    return errors


def _summary(bundle: dict[str, Any]) -> str:
    rows = bundle["observations"]
    failures = sum(sum(row["failures"].values()) for row in rows)
    endpoints = ", ".join(sorted({row["endpoint"] for row in rows}))
    return (
        f"schema v{bundle['schema_version']}; window {bundle['window_start']} to "
        f"{bundle['window_end']}; endpoints: {endpoints}; "
        f"operations: {sum(row['operations'] for row in rows)}; "
        f"attempts: {sum(row['attempts'] for row in rows)}; failures: {failures}; "
        "no content-bearing fields accepted"
    )


def validate_bundle(
    path: str | Path,
    *,
    root: str | Path | None = None,
    enforce_path: bool = True,
    check_duplicates: bool = True,
    now: datetime | None = None,
    check_clock: bool = True,
) -> ValidationResult:
    """Validate one contribution against the pinned schema and semantic rules."""
    bundle_path = Path(path).resolve()
    if root:
        repo = Path(root).resolve()
    else:
        try:
            repo = repository_root(bundle_path)
        except ValidationError:
            repo = Path.cwd().resolve()
    bundle = _load_json(bundle_path)
    schema = _load_schema(repo, "contribution-v1.schema.json")
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    schema_errors = sorted(validator.iter_errors(bundle), key=lambda error: list(error.path))
    if schema_errors:
        rendered = "; ".join(
            f"{'/'.join(map(str, error.path)) or '$'}: {error.message}" for error in schema_errors
        )
        raise ValidationError(f"schema validation failed: {rendered}")

    errors = _semantic_errors(bundle, now=now, check_clock=check_clock) + _scan(bundle)
    try:
        relative = bundle_path.relative_to(repo).as_posix()
    except ValueError:
        relative = bundle_path.name
    if enforce_path:
        match = CONTRIBUTION_PATH.fullmatch(relative)
        if not match:
            errors.append("path must be contributions/v1/YYYY/MM/<bundle-id>.json")
        else:
            if match["id"] != bundle["bundle_id"]:
                errors.append("filename stem must equal bundle_id")
            end = _utc(bundle["window_end"])
            if (match["year"], match["month"]) != (f"{end.year:04d}", f"{end.month:02d}"):
                errors.append("path year/month must agree with window_end")
    if check_duplicates:
        matches = list((repo / "contributions/v1").glob(f"*/*/{bundle['bundle_id']}.json"))
        if any(candidate.resolve() != bundle_path for candidate in matches):
            errors.append("bundle_id already exists")
    if errors:
        raise ValidationError("; ".join(errors))
    return ValidationResult(bundle_path, bundle, _summary(bundle))


def _git(repo: Path, *args: str) -> str:
    result = subprocess.run(["git", *args], cwd=repo, text=True, capture_output=True, check=False)
    if result.returncode:
        raise ValidationError(result.stderr.strip() or f"git {' '.join(args)} failed")
    return result.stdout


def validate_pr(base: str, head: str, *, root: str | Path | None = None) -> ValidationResult:
    """Validate that a revision range adds exactly one valid contribution file."""
    repo = Path(root).resolve() if root else repository_root()
    changes = _git(repo, "diff", "--name-status", "--no-renames", base, head).splitlines()
    if len(changes) != 1:
        raise ValidationError("PR must change exactly one file")
    parts = changes[0].split("\t")
    if len(parts) != 2 or parts[0] != "A" or not CONTRIBUTION_PATH.fullmatch(parts[1]):
        raise ValidationError("PR must only add one contributions/v1/YYYY/MM/<bundle-id>.json file")
    bundle_id = Path(parts[1]).stem
    historical_paths = _git(
        repo, "log", base, "--name-only", "--pretty=format:", "--", "contributions/v1"
    ).splitlines()
    if any(Path(path).stem == bundle_id for path in historical_paths if path):
        raise ValidationError("bundle_id already exists in repository history")
    return validate_bundle(repo / parts[1], root=repo)
