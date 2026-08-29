#!/usr/bin/env python3
"""Validate a structured SpaceClaim report without claiming application runtime.

This host-side tool checks JSON structure and an optional case contract.  It
does not launch SpaceClaim and cannot independently prove execution, geometry,
native save/reopen, export, meshing, or solver evidence declared by a report.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path
from typing import Any


REPORT_REQUIRED = (
    "schema_version",
    "case_id",
    "status",
    "target",
    "stages",
    "bodies",
    "named_face_groups",
    "outputs",
    "evidence_layers",
)
EVIDENCE_KEYS = (
    "static_archive",
    "spaceclaim_execution",
    "geometry_measurements",
    "native_save",
    "native_reopen",
    "neutral_export",
    "mesh",
    "solver",
)
EVIDENCE_STATES = ("passed", "failed", "not_tested")


def add_issue(issues: list[dict[str, str]], code: str, path: str, message: str) -> None:
    issues.append({"code": code, "path": path, "message": message})


def is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def validate_vector3(
    value: Any, path: str, issues: list[dict[str, str]]
) -> None:
    if not isinstance(value, list) or len(value) != 3 or not all(is_number(item) for item in value):
        add_issue(issues, "invalid_vector3", path, "Expected an array of three finite numbers.")


def validate_structure(report: Any) -> list[dict[str, str]]:
    issues: list[dict[str, str]] = []
    if not isinstance(report, dict):
        add_issue(issues, "invalid_report_type", "$", "The report must be a JSON object.")
        return issues

    for key in REPORT_REQUIRED:
        if key not in report:
            add_issue(issues, "missing_field", "$.%s" % key, "Required field is missing.")

    if issues:
        return issues

    if report["schema_version"] != 1:
        add_issue(issues, "unsupported_schema_version", "$.schema_version", "Expected schema version 1.")
    if not isinstance(report["case_id"], str) or not report["case_id"].strip():
        add_issue(issues, "invalid_string", "$.case_id", "Expected a non-empty string.")
    if report["status"] not in ("passed", "failed"):
        add_issue(issues, "invalid_report_status", "$.status", "Expected passed or failed.")

    target = report["target"]
    if not isinstance(target, dict):
        add_issue(issues, "invalid_object", "$.target", "Expected an object.")
    else:
        for key in ("spaceclaim_release", "api_version", "python_runtime"):
            value = target.get(key)
            if not isinstance(value, str) or not value.strip():
                add_issue(issues, "invalid_string", "$.target.%s" % key, "Expected a non-empty string.")

    stages = report["stages"]
    if not isinstance(stages, list) or not stages:
        add_issue(issues, "invalid_stages", "$.stages", "Expected at least one stage marker.")
    else:
        for index, stage in enumerate(stages):
            path = "$.stages[%d]" % index
            if not isinstance(stage, dict):
                add_issue(issues, "invalid_object", path, "Expected an object.")
                continue
            if not isinstance(stage.get("name"), str) or not stage["name"].strip():
                add_issue(issues, "invalid_string", path + ".name", "Expected a non-empty string.")
            if stage.get("status") not in EVIDENCE_STATES:
                add_issue(issues, "invalid_stage_status", path + ".status", "Invalid stage status.")

    bodies = report["bodies"]
    if not isinstance(bodies, list):
        add_issue(issues, "invalid_array", "$.bodies", "Expected an array.")
    else:
        names: list[str] = []
        for index, body in enumerate(bodies):
            path = "$.bodies[%d]" % index
            if not isinstance(body, dict):
                add_issue(issues, "invalid_object", path, "Expected an object.")
                continue
            name = body.get("name")
            if not isinstance(name, str) or not name.strip():
                add_issue(issues, "invalid_string", path + ".name", "Expected a non-empty string.")
            else:
                names.append(name)
            validate_vector3(body.get("bbox_min_mm"), path + ".bbox_min_mm", issues)
            validate_vector3(body.get("bbox_max_mm"), path + ".bbox_max_mm", issues)
            if not is_number(body.get("volume_mm3")) or body["volume_mm3"] < 0:
                add_issue(issues, "invalid_number", path + ".volume_mm3", "Expected a non-negative finite number.")
        if len(names) != len(set(names)):
            add_issue(issues, "duplicate_body_name", "$.bodies", "Body names must be unique.")

    groups = report["named_face_groups"]
    if not isinstance(groups, list):
        add_issue(issues, "invalid_array", "$.named_face_groups", "Expected an array.")
    else:
        names = []
        for index, group in enumerate(groups):
            path = "$.named_face_groups[%d]" % index
            if not isinstance(group, dict):
                add_issue(issues, "invalid_object", path, "Expected an object.")
                continue
            name = group.get("name")
            if not isinstance(name, str) or not name.strip():
                add_issue(issues, "invalid_string", path + ".name", "Expected a non-empty string.")
            else:
                names.append(name)
            count = group.get("member_count")
            if not isinstance(count, int) or isinstance(count, bool) or count < 0:
                add_issue(issues, "invalid_integer", path + ".member_count", "Expected a non-negative integer.")
        if len(names) != len(set(names)):
            add_issue(issues, "duplicate_group_name", "$.named_face_groups", "Group names must be unique.")

    outputs = report["outputs"]
    if not isinstance(outputs, dict):
        add_issue(issues, "invalid_object", "$.outputs", "Expected an object.")
    else:
        for key in ("native_model_path", "report_path"):
            value = outputs.get(key)
            if not isinstance(value, str) or not value.strip():
                add_issue(issues, "invalid_string", "$.outputs.%s" % key, "Expected a non-empty string.")

    evidence = report["evidence_layers"]
    if not isinstance(evidence, dict):
        add_issue(issues, "invalid_object", "$.evidence_layers", "Expected an object.")
    else:
        for key in EVIDENCE_KEYS:
            if evidence.get(key) not in EVIDENCE_STATES:
                add_issue(
                    issues,
                    "invalid_evidence_state",
                    "$.evidence_layers.%s" % key,
                    "Expected passed, failed, or not_tested.",
                )
        extras = sorted(set(evidence) - set(EVIDENCE_KEYS))
        if extras:
            add_issue(issues, "unexpected_evidence_layer", "$.evidence_layers", "Unexpected keys: %s" % ", ".join(extras))
    return issues


def close_enough(actual: float, expected: float, tolerance: float) -> bool:
    return abs(float(actual) - float(expected)) <= float(tolerance)


def compare_contract(
    report: dict[str, Any], contract: dict[str, Any]
) -> list[dict[str, str]]:
    issues: list[dict[str, str]] = []
    if contract.get("schema_version") != 1:
        add_issue(issues, "invalid_contract", "$.schema_version", "Contract schema version must be 1.")
        return issues

    if report.get("case_id") != contract.get("case_id"):
        add_issue(issues, "case_id_mismatch", "$.case_id", "Report and contract case IDs differ.")
    expected_status = contract.get("expected_report_status")
    if expected_status and report.get("status") != expected_status:
        add_issue(issues, "report_status_mismatch", "$.status", "Expected %s." % expected_status)

    for key, expected in contract.get("target", {}).items():
        actual = report.get("target", {}).get(key)
        if actual != expected:
            add_issue(issues, "target_mismatch", "$.target.%s" % key, "Expected %r, found %r." % (expected, actual))

    tolerances = contract.get("tolerances", {})
    bbox_tolerance = float(tolerances.get("bbox_mm", 0.0))
    volume_tolerance = float(tolerances.get("volume_mm3", 0.0))
    actual_bodies = {item.get("name"): item for item in report.get("bodies", []) if isinstance(item, dict)}
    expected_bodies = {item["name"]: item for item in contract.get("bodies", [])}
    if set(actual_bodies) != set(expected_bodies):
        add_issue(
            issues,
            "body_name_set_mismatch",
            "$.bodies",
            "Expected %s, found %s." % (sorted(expected_bodies), sorted(actual_bodies)),
        )
    for name in sorted(set(actual_bodies) & set(expected_bodies)):
        actual = actual_bodies[name]
        expected = expected_bodies[name]
        for field in ("bbox_min_mm", "bbox_max_mm"):
            actual_vector = actual.get(field, [])
            expected_vector = expected[field]
            if len(actual_vector) == 3 and any(
                not close_enough(actual_vector[index], expected_vector[index], bbox_tolerance)
                for index in range(3)
            ):
                add_issue(issues, "bbox_mismatch", "$.bodies[%s].%s" % (name, field), "Outside %.9g mm tolerance." % bbox_tolerance)
        if is_number(actual.get("volume_mm3")) and not close_enough(
            actual["volume_mm3"], expected["volume_mm3"], volume_tolerance
        ):
            add_issue(issues, "volume_mismatch", "$.bodies[%s].volume_mm3" % name, "Outside %.9g mm3 tolerance." % volume_tolerance)

    actual_groups = {item.get("name"): item for item in report.get("named_face_groups", []) if isinstance(item, dict)}
    expected_groups = {item["name"]: item for item in contract.get("named_face_groups", [])}
    if set(actual_groups) != set(expected_groups):
        add_issue(issues, "group_name_set_mismatch", "$.named_face_groups", "Expected %s, found %s." % (sorted(expected_groups), sorted(actual_groups)))
    for name in sorted(set(actual_groups) & set(expected_groups)):
        if actual_groups[name].get("member_count") != expected_groups[name]["member_count"]:
            add_issue(issues, "group_member_count_mismatch", "$.named_face_groups[%s].member_count" % name, "Expected %d." % expected_groups[name]["member_count"])

    for key, allowed in contract.get("evidence_layers", {}).items():
        allowed_values = allowed if isinstance(allowed, list) else [allowed]
        actual = report.get("evidence_layers", {}).get(key)
        if actual not in allowed_values:
            add_issue(issues, "evidence_boundary_mismatch", "$.evidence_layers.%s" % key, "Expected one of %s, found %r." % (allowed_values, actual))
    return issues


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def validate_report(report: Any, contract: Any | None = None) -> dict[str, Any]:
    issues = validate_structure(report)
    if not issues and contract is not None:
        if not isinstance(contract, dict):
            add_issue(issues, "invalid_contract_type", "$", "The contract must be a JSON object.")
        else:
            issues.extend(compare_contract(report, contract))
    return {
        "schema_version": 1,
        "evidence_level": "host_report_structure_and_contract_only",
        "status": "failed" if issues else "passed",
        "issues": issues,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("report", type=Path, help="SpaceClaim runtime report JSON")
    parser.add_argument("--contract", type=Path, help="Optional case validation contract JSON")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        report = load_json(args.report)
        contract = load_json(args.contract) if args.contract else None
        result = validate_report(report, contract)
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        result = {
            "schema_version": 1,
            "evidence_level": "host_report_structure_and_contract_only",
            "status": "failed",
            "issues": [{"code": "input_read_error", "path": "$", "message": str(exc)}],
        }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["status"] == "passed" else 2


if __name__ == "__main__":
    sys.exit(main())
