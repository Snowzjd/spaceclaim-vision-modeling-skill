#!/usr/bin/env python3
"""Validate geometry-understanding output contracts and neutral fixtures.

This host tool checks JSON structure and deterministic cross-field invariants.
It does not inspect source pixels, judge geometric correctness, or run SpaceClaim.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
from pathlib import Path
from typing import Any

try:
    from jsonschema import Draft202012Validator
except ImportError as exc:  # pragma: no cover - exercised through CLI environments
    Draft202012Validator = None
    JSONSCHEMA_IMPORT_ERROR = exc
else:
    JSONSCHEMA_IMPORT_ERROR = None


REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_SCHEMA = REPO_ROOT / "spaceclaim-vision-modeling/references/geometry-understanding-output.schema.json"


def _reject_non_finite(value: str) -> None:
    raise ValueError("Non-finite JSON number is not allowed: %s" % value)


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"), parse_constant=_reject_non_finite)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def resolve_repo_path(repo_root: Path, value: Any) -> Path:
    if not isinstance(value, str) or not value:
        raise ValueError("Repository path must be a non-empty string.")
    raw = Path(value)
    if raw.is_absolute():
        raise ValueError("Absolute repository path is not allowed: %s" % value)
    resolved_root = repo_root.resolve()
    resolved = (resolved_root / raw).resolve()
    try:
        resolved.relative_to(resolved_root)
    except ValueError as exc:
        raise ValueError("Repository path escapes the repository root: %s" % value) from exc
    return resolved


def issue(code: str, path: str, message: str) -> dict[str, str]:
    return {"code": code, "path": path, "message": message}


def _all_item_ids(data: dict[str, Any]) -> list[tuple[str, str]]:
    result: list[tuple[str, str]] = []
    for field in (
        "observed_geometry",
        "bodies_and_features",
        "spatial_relations",
        "symmetry_and_repetition",
        "dimensions_with_provenance",
        "dimension_relations",
        "frame_assumptions",
        "unresolved_items",
    ):
        values = data.get(field, [])
        if not isinstance(values, list):
            continue
        for index, item in enumerate(values):
            if isinstance(item, dict) and isinstance(item.get("id"), str):
                result.append((item["id"], "$.%s[%d].id" % (field, index)))
    return result


def _dot(left: list[float], right: list[float]) -> float:
    return sum(a * b for a, b in zip(left, right))


def _norm(vector: list[float]) -> float:
    return math.sqrt(_dot(vector, vector))


def _determinant(x_axis: list[float], y_axis: list[float], z_axis: list[float]) -> float:
    return (
        x_axis[0] * (y_axis[1] * z_axis[2] - y_axis[2] * z_axis[1])
        - x_axis[1] * (y_axis[0] * z_axis[2] - y_axis[2] * z_axis[0])
        + x_axis[2] * (y_axis[0] * z_axis[1] - y_axis[1] * z_axis[0])
    )


def semantic_issues(data: dict[str, Any]) -> list[dict[str, str]]:
    issues: list[dict[str, str]] = []
    ids: dict[str, str] = {}
    for item_id, path in _all_item_ids(data):
        if item_id in ids:
            issues.append(issue("duplicate_item_id", path, "Item IDs must be unique across one operation output."))
        else:
            ids[item_id] = path

    unresolved = data.get("unresolved_items", [])
    if not isinstance(unresolved, list):
        unresolved = []
    blockers = [item for item in unresolved if isinstance(item, dict) and item.get("blocks_handoff") is True]
    handoff_status = data.get("handoff_status")
    if blockers and isinstance(handoff_status, str) and handoff_status in {"ready", "passed"}:
        issues.append(
            issue(
                "blocking_unresolved_requires_clarification",
                "$.handoff_status",
                "A ready or passed handoff cannot contain a blocking unresolved item.",
            )
        )

    operation_id = data.get("operation_id")
    if operation_id == "geometry_understanding.extract-geometry-observations":
        entity_ids = set()
        for field in ("observed_geometry", "bodies_and_features", "symmetry_and_repetition"):
            values = data.get(field, [])
            if isinstance(values, list):
                entity_ids.update(item.get("id") for item in values if isinstance(item, dict) and isinstance(item.get("id"), str))
        relations = data.get("spatial_relations", [])
        if isinstance(relations, list):
            for index, relation in enumerate(relations):
                if not isinstance(relation, dict):
                    continue
                participant_refs = relation.get("participant_refs", [])
                if not isinstance(participant_refs, list):
                    continue
                for ref in participant_refs:
                    if isinstance(ref, str) and ref not in entity_ids:
                        issues.append(issue("dangling_relation_ref", "$.spatial_relations[%d].participant_refs" % index, "Relation participants must reference an emitted observation, body, feature, symmetry, or repetition item."))
    if operation_id == "geometry_understanding.reconcile-dimensions":
        unresolved_links = set()
        for item in unresolved:
            if not isinstance(item, dict):
                continue
            related_refs = item.get("related_refs", [])
            if isinstance(related_refs, list):
                unresolved_links.update(ref for ref in related_refs if isinstance(ref, str))
        dimensions = data.get("dimensions_with_provenance", [])
        if not isinstance(dimensions, list):
            dimensions = []
        for index, dimension in enumerate(dimensions):
            if not isinstance(dimension, dict):
                continue
            path = "$.dimensions_with_provenance[%d]" % index
            disposition_value = dimension.get("disposition")
            disposition = disposition_value if isinstance(disposition_value, str) else None
            if disposition in {"accepted", "derived"}:
                if dimension.get("value") is None or not dimension.get("unit"):
                    issues.append(issue("resolved_dimension_missing_value_or_unit", path, "Accepted or derived dimensions require a numeric value and unit."))
            if disposition == "derived" and not dimension.get("derivation"):
                issues.append(issue("derived_dimension_missing_derivation", path, "A derived dimension requires an explicit derivation."))
            dimension_id = dimension.get("id")
            if disposition in {"conflicting", "unresolved"} and (not isinstance(dimension_id, str) or dimension_id not in unresolved_links):
                issues.append(issue("unresolved_dimension_missing_link", path, "Conflicting or unresolved dimensions must be referenced by an unresolved item."))

    if operation_id == "geometry_understanding.define-coordinate-frame":
        frame = data.get("coordinate_system", {})
        if not isinstance(frame, dict):
            return issues
        components = ("origin", "x_axis", "y_axis", "z_axis", "handedness", "unit_context")
        component_records = {
            name: frame.get(name) if isinstance(frame.get(name), dict) else {}
            for name in components
        }
        unresolved_components = [name for name in components if component_records[name].get("status") != "resolved"]
        if isinstance(handoff_status, str) and handoff_status in {"ready", "passed"} and unresolved_components:
            issues.append(issue("ready_frame_has_unresolved_component", "$.coordinate_system", "A ready or passed frame requires every core frame component to be resolved."))
        axes: dict[str, list[float]] = {}
        for name in ("x_axis", "y_axis", "z_axis"):
            component = component_records[name]
            value = component.get("value")
            if component.get("status") == "resolved":
                if not isinstance(value, list) or len(value) != 3 or not all(isinstance(item, (int, float)) and not isinstance(item, bool) and math.isfinite(item) for item in value):
                    issues.append(issue("resolved_axis_invalid_value", "$.coordinate_system.%s.value" % name, "A resolved axis requires three finite numeric components."))
                    continue
                if _norm(value) <= 1e-12:
                    issues.append(issue("zero_length_axis", "$.coordinate_system.%s.value" % name, "A resolved axis vector must be non-zero."))
                else:
                    axes[name] = [float(item) for item in value]
                    if abs(_norm(axes[name]) - 1.0) > 1e-6:
                        issues.append(issue("axis_not_normalized", "$.coordinate_system.%s.value" % name, "A resolved axis vector must be normalized."))
        for left, right in (("x_axis", "y_axis"), ("x_axis", "z_axis"), ("y_axis", "z_axis")):
            if left in axes and right in axes:
                cosine = abs(_dot(axes[left], axes[right]) / (_norm(axes[left]) * _norm(axes[right])))
                if cosine > 1e-6:
                    issues.append(issue("axes_not_orthogonal", "$.coordinate_system", "Resolved coordinate axes must be pairwise orthogonal."))
        if len(axes) == 3:
            handedness_value = component_records["handedness"].get("value")
            handedness = handedness_value if isinstance(handedness_value, str) else None
            determinant = _determinant(axes["x_axis"], axes["y_axis"], axes["z_axis"])
            if handedness == "right_handed" and determinant <= 0:
                issues.append(issue("handedness_mismatch", "$.coordinate_system.handedness.value", "Axis orientation does not match right_handed."))
            if handedness == "left_handed" and determinant >= 0:
                issues.append(issue("handedness_mismatch", "$.coordinate_system.handedness.value", "Axis orientation does not match left_handed."))
        handedness_component = component_records["handedness"]
        handedness_value = handedness_component.get("value")
        if handedness_component.get("status") == "resolved" and (not isinstance(handedness_value, str) or handedness_value not in {"right_handed", "left_handed"}):
            issues.append(issue("invalid_handedness", "$.coordinate_system.handedness.value", "Resolved handedness must be right_handed or left_handed."))
        unit_component = component_records["unit_context"]
        if unit_component.get("status") == "resolved" and not isinstance(unit_component.get("value"), str):
            issues.append(issue("invalid_unit_context", "$.coordinate_system.unit_context.value", "Resolved unit context must be a non-empty unit string."))
        if isinstance(handoff_status, str) and handoff_status in {"ready", "passed"} and not frame.get("source_view_mapping"):
            issues.append(issue("ready_frame_missing_view_mapping", "$.coordinate_system.source_view_mapping", "A ready or passed frame requires at least one source-view mapping."))
    return issues


def validate_output(data: Any, schema: dict[str, Any]) -> list[dict[str, str]]:
    if Draft202012Validator is None:
        raise RuntimeError("jsonschema is required: %s" % JSONSCHEMA_IMPORT_ERROR)
    issues = [
        issue("schema_violation", "$" + "".join("[%r]" % part for part in error.absolute_path), error.message)
        for error in sorted(Draft202012Validator(schema).iter_errors(data), key=lambda item: repr(list(item.absolute_path)))
    ]
    if isinstance(data, dict):
        issues.extend(semantic_issues(data))
    return issues


def evaluate_manifest(repo_root: Path, manifest_path: Path) -> dict[str, Any]:
    manifest = load_json(manifest_path)
    if not isinstance(manifest, dict) or manifest.get("fixture_manifest_version") != 1:
        raise ValueError("Unsupported or malformed fixture manifest.")
    versions = manifest.get("operation_template_versions")
    if not isinstance(versions, dict):
        raise ValueError("Fixture manifest must declare operation_template_versions.")
    fixtures = manifest.get("fixtures")
    if not isinstance(fixtures, list) or not fixtures:
        raise ValueError("Fixture manifest must contain at least one fixture.")
    schema_path = resolve_repo_path(repo_root, manifest["schema_path"])
    if sha256(schema_path) != manifest.get("schema_sha256"):
        raise ValueError("Fixture manifest schema_sha256 does not match the schema bytes.")
    schema = load_json(schema_path)
    results = []
    mismatches = 0
    seen_paths: set[str] = set()
    for fixture in fixtures:
        if not isinstance(fixture, dict) or not isinstance(fixture.get("expected_valid"), bool):
            raise ValueError("Each fixture entry must declare path and boolean expected_valid.")
        fixture_value = fixture.get("path")
        if not isinstance(fixture_value, str) or not fixture_value:
            raise ValueError("Fixture path must be a non-empty repository-relative string.")
        if fixture_value in seen_paths:
            raise ValueError("Duplicate fixture path: %s" % fixture_value)
        seen_paths.add(fixture_value)
        fixture_path = resolve_repo_path(repo_root, fixture_value)
        if sha256(fixture_path) != fixture.get("sha256"):
            raise ValueError("Fixture sha256 does not match: %s" % fixture_value)
        fixture_data = load_json(fixture_path)
        found = validate_output(fixture_data, schema)
        operation_value = fixture_data.get("operation_id") if isinstance(fixture_data, dict) else None
        operation_id = operation_value if isinstance(operation_value, str) else None
        expected_version = versions.get(operation_id) if operation_id is not None else None
        if expected_version is None or fixture_data.get("template_version") != expected_version:
            found.append(issue("fixture_template_version_mismatch", "$.template_version", "Fixture template_version must match its operation version in the manifest."))
        found_codes = sorted({item["code"] for item in found})
        expected_code_values = fixture.get("expected_issue_codes", [])
        if not isinstance(expected_code_values, list) or not all(isinstance(code, str) for code in expected_code_values):
            raise ValueError("Fixture expected_issue_codes must be an array of strings.")
        expected_codes = sorted(set(expected_code_values))
        actual_valid = not found
        expected_valid = fixture["expected_valid"]
        matched = actual_valid == expected_valid and found_codes == expected_codes
        if not matched:
            mismatches += 1
        results.append(
            {
                "fixture": fixture["path"],
                "expected_valid": expected_valid,
                "actual_valid": actual_valid,
                "expected_issue_codes": expected_codes,
                "actual_issue_codes": found_codes,
                "matched": matched,
            }
        )
    return {
        "status": "passed" if mismatches == 0 else "failed",
        "manifest": str(manifest_path),
        "fixtures_checked": len(results),
        "mismatches": mismatches,
        "issues": [],
        "results": results,
        "evidence_boundary": "Host-only contract and invariant checks; no source-interpretation accuracy or SpaceClaim behavior is evaluated.",
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--input", type=Path, help="Validate one output JSON document.")
    group.add_argument("--fixtures", type=Path, help="Run a repository-relative fixture manifest.")
    parser.add_argument("--schema", type=Path, default=DEFAULT_SCHEMA)
    args = parser.parse_args(argv)
    try:
        if args.fixtures:
            manifest_path = args.fixtures if args.fixtures.is_absolute() else REPO_ROOT / args.fixtures
            result = evaluate_manifest(REPO_ROOT, manifest_path)
            exit_code = 0 if result["mismatches"] == 0 else 1
        else:
            schema_path = args.schema if args.schema.is_absolute() else REPO_ROOT / args.schema
            input_path = args.input if args.input.is_absolute() else Path.cwd() / args.input
            issues = validate_output(load_json(input_path), load_json(schema_path))
            result = {
                "input": str(input_path),
                "valid": not issues,
                "issues": issues,
                "evidence_boundary": "Host-only contract and invariant checks; no source-interpretation accuracy or SpaceClaim behavior is evaluated.",
            }
            exit_code = 0 if not issues else 1
    except (OSError, ValueError, KeyError, RuntimeError, json.JSONDecodeError) as exc:
        result = {"valid": False, "issues": [issue("validation_error", "$", str(exc))]}
        exit_code = 2
    json.dump(result, sys.stdout, ensure_ascii=False, indent=2)
    sys.stdout.write("\n")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
