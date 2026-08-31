#!/usr/bin/env python3
"""Validate a structured SpaceClaim report without claiming application runtime.

This host-side tool checks JSON structure and an optional case contract.  It
does not launch SpaceClaim and cannot independently prove execution, geometry,
native save/reopen, or requested export evidence declared by a report.
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
)
EVIDENCE_STATES = ("passed", "failed", "not_tested")
MAX_JSON_BYTES = 16 * 1024 * 1024


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
        stage_names: list[str] = []
        for index, stage in enumerate(stages):
            path = "$.stages[%d]" % index
            if not isinstance(stage, dict):
                add_issue(issues, "invalid_object", path, "Expected an object.")
                continue
            if not isinstance(stage.get("name"), str) or not stage["name"].strip():
                add_issue(issues, "invalid_string", path + ".name", "Expected a non-empty string.")
            else:
                stage_names.append(stage["name"])
            if stage.get("status") not in EVIDENCE_STATES:
                add_issue(issues, "invalid_stage_status", path + ".status", "Invalid stage status.")
        if len(stage_names) != len(set(stage_names)):
            add_issue(issues, "duplicate_stage_name", "$.stages", "Stage names must be unique.")

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
            bbox_min = body.get("bbox_min_mm")
            bbox_max = body.get("bbox_max_mm")
            if (
                isinstance(bbox_min, list)
                and isinstance(bbox_max, list)
                and len(bbox_min) == 3
                and len(bbox_max) == 3
                and all(is_number(item) for item in bbox_min + bbox_max)
                and any(bbox_min[axis] > bbox_max[axis] for axis in range(3))
            ):
                add_issue(
                    issues,
                    "invalid_bbox_order",
                    path,
                    "Each bounding-box minimum must be less than or equal to its maximum.",
                )
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

    features = report.get("features", [])
    if not isinstance(features, list):
        add_issue(issues, "invalid_array", "$.features", "Expected an array when provided.")
    else:
        feature_names: list[str] = []
        for index, feature in enumerate(features):
            path = "$.features[%d]" % index
            if not isinstance(feature, dict):
                add_issue(issues, "invalid_object", path, "Expected an object.")
                continue
            name = feature.get("name")
            if not isinstance(name, str) or not name.strip():
                add_issue(issues, "invalid_string", path + ".name", "Expected a non-empty string.")
            else:
                feature_names.append(name)
            count = feature.get("count")
            if not isinstance(count, int) or isinstance(count, bool) or count < 0:
                add_issue(issues, "invalid_integer", path + ".count", "Expected a non-negative integer.")
            measurements = feature.get("measurements")
            if not isinstance(measurements, dict):
                add_issue(issues, "invalid_object", path + ".measurements", "Expected an object.")
            else:
                for key, value in measurements.items():
                    if not isinstance(key, str) or not key.strip() or not is_number(value):
                        add_issue(
                            issues,
                            "invalid_feature_measurement",
                            path + ".measurements",
                            "Measurement names must be non-empty strings and values must be finite numbers.",
                        )
        if len(feature_names) != len(set(feature_names)):
            add_issue(issues, "duplicate_feature_name", "$.features", "Feature names must be unique.")

    outputs = report["outputs"]
    if not isinstance(outputs, dict):
        add_issue(issues, "invalid_object", "$.outputs", "Expected an object.")
    else:
        output_values: list[str] = []
        for key in ("native_model_path", "report_path"):
            value = outputs.get(key)
            if not isinstance(value, str) or not value.strip():
                add_issue(issues, "invalid_string", "$.outputs.%s" % key, "Expected a non-empty string.")
            else:
                output_values.append(value)
        if len(output_values) == 2 and output_values[0] == output_values[1]:
            add_issue(
                issues,
                "output_path_collision",
                "$.outputs",
                "Native-model and report paths must be different.",
            )

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

    failed_stage = isinstance(stages, list) and any(
        isinstance(stage, dict) and stage.get("status") == "failed"
        for stage in stages
    )
    failed_evidence = isinstance(evidence, dict) and any(
        evidence.get(key) == "failed" for key in EVIDENCE_KEYS
    )

    if report["status"] == "passed":
        if failed_stage:
            add_issue(
                issues,
                "inconsistent_report_status",
                "$.status",
                "A passed report cannot contain a failed stage.",
            )
        if failed_evidence:
            add_issue(
                issues,
                "inconsistent_report_status",
                "$.status",
                "A passed report cannot contain a failed evidence layer.",
            )
    elif report["status"] == "failed" and not (failed_stage or failed_evidence):
        add_issue(
            issues,
            "inconsistent_report_status",
            "$.status",
            "A failed report must contain at least one failed stage or evidence layer.",
        )
    return issues


def validate_contract_structure(contract: Any) -> list[dict[str, str]]:
    issues: list[dict[str, str]] = []
    if not isinstance(contract, dict):
        add_issue(issues, "invalid_contract_type", "$", "The contract must be a JSON object.")
        return issues

    if contract.get("schema_version") != 1:
        add_issue(issues, "invalid_contract", "$.schema_version", "Contract schema version must be 1.")
    if not isinstance(contract.get("case_id"), str) or not contract["case_id"].strip():
        add_issue(issues, "invalid_contract", "$.case_id", "Contract case_id must be a non-empty string.")
    if contract.get("expected_report_status") not in (None, "passed", "failed"):
        add_issue(
            issues,
            "invalid_contract",
            "$.expected_report_status",
            "Expected passed, failed, or omission.",
        )

    target = contract.get("target", {})
    if not isinstance(target, dict):
        add_issue(issues, "invalid_contract", "$.target", "Contract target must be an object.")
    else:
        for key, value in target.items():
            if key not in ("spaceclaim_release", "api_version", "python_runtime"):
                add_issue(issues, "invalid_contract", "$.target.%s" % key, "Unsupported target key.")
            elif not isinstance(value, str) or not value.strip():
                add_issue(issues, "invalid_contract", "$.target.%s" % key, "Expected a non-empty string.")

    tolerances = contract.get("tolerances", {})
    if not isinstance(tolerances, dict):
        add_issue(issues, "invalid_contract", "$.tolerances", "Contract tolerances must be an object.")
    else:
        for key in ("bbox_mm", "volume_mm3", "feature_mm", "angle_deg"):
            value = tolerances.get(key, 0.0)
            if not is_number(value) or value < 0:
                add_issue(
                    issues,
                    "invalid_contract",
                    "$.tolerances.%s" % key,
                    "Tolerance must be a non-negative finite number.",
                )

    bodies = contract.get("bodies")
    if not isinstance(bodies, list):
        add_issue(issues, "invalid_contract", "$.bodies", "Contract bodies must be an array.")
    else:
        body_names: list[str] = []
        for index, body in enumerate(bodies):
            path = "$.bodies[%d]" % index
            if not isinstance(body, dict):
                add_issue(issues, "invalid_contract", path, "Expected an object.")
                continue
            name = body.get("name")
            if not isinstance(name, str) or not name.strip():
                add_issue(issues, "invalid_contract", path + ".name", "Expected a non-empty string.")
            else:
                body_names.append(name)
            for field in ("bbox_min_mm", "bbox_max_mm"):
                value = body.get(field)
                if not isinstance(value, list) or len(value) != 3 or not all(is_number(item) for item in value):
                    add_issue(issues, "invalid_contract", path + "." + field, "Expected three finite numbers.")
            if not is_number(body.get("volume_mm3")) or body["volume_mm3"] < 0:
                add_issue(issues, "invalid_contract", path + ".volume_mm3", "Expected a non-negative finite number.")
        if len(body_names) != len(set(body_names)):
            add_issue(issues, "invalid_contract", "$.bodies", "Contract body names must be unique.")

    groups = contract.get("named_face_groups")
    if not isinstance(groups, list):
        add_issue(issues, "invalid_contract", "$.named_face_groups", "Contract groups must be an array.")
    else:
        group_names: list[str] = []
        for index, group in enumerate(groups):
            path = "$.named_face_groups[%d]" % index
            if not isinstance(group, dict):
                add_issue(issues, "invalid_contract", path, "Expected an object.")
                continue
            name = group.get("name")
            if not isinstance(name, str) or not name.strip():
                add_issue(issues, "invalid_contract", path + ".name", "Expected a non-empty string.")
            else:
                group_names.append(name)
            count = group.get("member_count")
            if not isinstance(count, int) or isinstance(count, bool) or count < 0:
                add_issue(issues, "invalid_contract", path + ".member_count", "Expected a non-negative integer.")
        if len(group_names) != len(set(group_names)):
            add_issue(issues, "invalid_contract", "$.named_face_groups", "Contract group names must be unique.")

    features = contract.get("features", [])
    if not isinstance(features, list):
        add_issue(issues, "invalid_contract", "$.features", "Contract features must be an array when provided.")
    else:
        feature_names: list[str] = []
        for index, feature in enumerate(features):
            path = "$.features[%d]" % index
            if not isinstance(feature, dict):
                add_issue(issues, "invalid_contract", path, "Expected an object.")
                continue
            name = feature.get("name")
            if not isinstance(name, str) or not name.strip():
                add_issue(issues, "invalid_contract", path + ".name", "Expected a non-empty string.")
            else:
                feature_names.append(name)
            count = feature.get("count")
            if not isinstance(count, int) or isinstance(count, bool) or count < 0:
                add_issue(issues, "invalid_contract", path + ".count", "Expected a non-negative integer.")
            measurements = feature.get("measurements")
            if not isinstance(measurements, dict):
                add_issue(issues, "invalid_contract", path + ".measurements", "Expected an object.")
            else:
                for key, value in measurements.items():
                    if not isinstance(key, str) or not key.strip() or not is_number(value):
                        add_issue(issues, "invalid_contract", path + ".measurements", "Expected finite numeric measurements.")
        if len(feature_names) != len(set(feature_names)):
            add_issue(issues, "invalid_contract", "$.features", "Contract feature names must be unique.")

    evidence = contract.get("evidence_layers", {})
    if not isinstance(evidence, dict):
        add_issue(issues, "invalid_contract", "$.evidence_layers", "Contract evidence_layers must be an object.")
    else:
        for key, allowed in evidence.items():
            if key not in EVIDENCE_KEYS:
                add_issue(issues, "invalid_contract", "$.evidence_layers.%s" % key, "Unsupported evidence layer.")
                continue
            allowed_values = allowed if isinstance(allowed, list) else [allowed]
            if not allowed_values or any(value not in EVIDENCE_STATES for value in allowed_values):
                add_issue(
                    issues,
                    "invalid_contract",
                    "$.evidence_layers.%s" % key,
                    "Allowed values must be passed, failed, or not_tested.",
                )
    return issues


def close_enough(actual: float, expected: float, tolerance: float) -> bool:
    return abs(float(actual) - float(expected)) <= float(tolerance)


def compare_contract(
    report: dict[str, Any], contract: dict[str, Any]
) -> list[dict[str, str]]:
    issues: list[dict[str, str]] = []
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

    if "features" in contract:
        actual_features = {
            item.get("name"): item
            for item in report.get("features", [])
            if isinstance(item, dict)
        }
        expected_features = {item["name"]: item for item in contract["features"]}
        if set(actual_features) != set(expected_features):
            add_issue(
                issues,
                "feature_name_set_mismatch",
                "$.features",
                "Expected %s, found %s."
                % (sorted(expected_features), sorted(actual_features)),
            )
        feature_tolerance = float(tolerances.get("feature_mm", 0.0))
        angle_tolerance = float(tolerances.get("angle_deg", 0.0))
        for name in sorted(set(actual_features) & set(expected_features)):
            actual = actual_features[name]
            expected = expected_features[name]
            if actual.get("count") != expected["count"]:
                add_issue(
                    issues,
                    "feature_count_mismatch",
                    "$.features[%s].count" % name,
                    "Expected %d." % expected["count"],
                )
            actual_measurements = actual.get("measurements", {})
            expected_measurements = expected["measurements"]
            if set(actual_measurements) != set(expected_measurements):
                add_issue(
                    issues,
                    "feature_measurement_set_mismatch",
                    "$.features[%s].measurements" % name,
                    "Expected %s, found %s."
                    % (sorted(expected_measurements), sorted(actual_measurements)),
                )
            for key in sorted(set(actual_measurements) & set(expected_measurements)):
                tolerance = angle_tolerance if key.endswith("_deg") else feature_tolerance
                if not close_enough(actual_measurements[key], expected_measurements[key], tolerance):
                    add_issue(
                        issues,
                        "feature_measurement_mismatch",
                        "$.features[%s].measurements.%s" % (name, key),
                        "Outside %.9g tolerance." % tolerance,
                    )

    for key, allowed in contract.get("evidence_layers", {}).items():
        allowed_values = allowed if isinstance(allowed, list) else [allowed]
        actual = report.get("evidence_layers", {}).get(key)
        if actual not in allowed_values:
            add_issue(issues, "evidence_boundary_mismatch", "$.evidence_layers.%s" % key, "Expected one of %s, found %r." % (allowed_values, actual))
    return issues


def load_json(path: Path) -> Any:
    if path.stat().st_size > MAX_JSON_BYTES:
        raise ValueError("JSON input exceeds the %d byte safety limit: %s" % (MAX_JSON_BYTES, path))
    return json.loads(path.read_text(encoding="utf-8"))


def validate_report(report: Any, contract: Any | None = None) -> dict[str, Any]:
    issues = validate_structure(report)
    if not issues and contract is not None:
        contract_issues = validate_contract_structure(contract)
        issues.extend(contract_issues)
        if not contract_issues:
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
    except (OSError, UnicodeError, ValueError, json.JSONDecodeError) as exc:
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
