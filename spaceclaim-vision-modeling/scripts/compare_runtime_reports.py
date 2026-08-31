#!/usr/bin/env python3
"""Compare forward and native-reopen SpaceClaim reports on the host.

The comparison checks persisted body geometry and named-group membership declared
by two structured reports.  It does not launch SpaceClaim or independently prove
that either report came from an application run.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path
from typing import Any

from validate_runtime_report import load_json, validate_report


def add_issue(issues: list[dict[str, str]], code: str, path: str, message: str) -> None:
    issues.append({"code": code, "path": path, "message": message})


def close_enough(actual: Any, expected: Any, tolerance: float) -> bool:
    return (
        isinstance(actual, (int, float))
        and not isinstance(actual, bool)
        and isinstance(expected, (int, float))
        and not isinstance(expected, bool)
        and math.isfinite(actual)
        and math.isfinite(expected)
        and abs(float(actual) - float(expected)) <= tolerance
    )


def compare_reports(
    forward: Any,
    reopened: Any,
    *,
    bbox_tolerance_mm: float = 1.0e-9,
    volume_tolerance_mm3: float = 1.0e-9,
    feature_tolerance: float = 1.0e-9,
) -> dict[str, Any]:
    issues: list[dict[str, str]] = []
    if not math.isfinite(bbox_tolerance_mm) or bbox_tolerance_mm < 0:
        add_issue(issues, "invalid_tolerance", "$.bbox_tolerance_mm", "Expected a non-negative finite number.")
    if not math.isfinite(volume_tolerance_mm3) or volume_tolerance_mm3 < 0:
        add_issue(issues, "invalid_tolerance", "$.volume_tolerance_mm3", "Expected a non-negative finite number.")
    if not math.isfinite(feature_tolerance) or feature_tolerance < 0:
        add_issue(issues, "invalid_tolerance", "$.feature_tolerance", "Expected a non-negative finite number.")

    forward_validation = validate_report(forward)
    reopen_validation = validate_report(reopened)
    if forward_validation["status"] != "passed":
        add_issue(issues, "invalid_forward_report", "$forward", "Forward report structure is invalid.")
    if reopen_validation["status"] != "passed":
        add_issue(issues, "invalid_reopen_report", "$reopened", "Reopen report structure is invalid.")
    # A comparison is only meaningful for reports that themselves claim a
    # successful forward/reopen run.  The structure validator deliberately
    # accepts well-formed failed reports so they can be inspected, therefore
    # reject those reports explicitly here before comparing their geometry.
    if not isinstance(forward, dict) or forward.get("status") != "passed":
        add_issue(
            issues,
            "forward_report_not_passed",
            "$forward.status",
            "Forward report status must be passed for comparison.",
        )
    if not isinstance(reopened, dict) or reopened.get("status") != "passed":
        add_issue(
            issues,
            "reopen_report_not_passed",
            "$reopened.status",
            "Reopen report status must be passed for comparison.",
        )

    result: dict[str, Any] = {
        "schema_version": 1,
        "evidence_level": "host_report_comparison_only",
        "status": "failed",
        "comparison": {
            "case_and_target_equal": False,
            "bodies_equal": False,
            "named_face_groups_equal": False,
            "features_equal": False,
        },
        "issues": issues,
    }
    if issues:
        return result

    case_and_target_equal = (
        forward["case_id"] == reopened["case_id"]
        and forward["target"] == reopened["target"]
    )
    result["comparison"]["case_and_target_equal"] = case_and_target_equal
    if not case_and_target_equal:
        add_issue(
            issues,
            "case_or_target_mismatch",
            "$",
            "Forward and reopen reports must describe the same case and target runtime.",
        )

    if forward["evidence_layers"]["native_save"] != "passed":
        add_issue(
            issues,
            "forward_save_not_passed",
            "$forward.evidence_layers.native_save",
            "Forward report must declare native_save as passed.",
        )
    if reopened["evidence_layers"]["native_reopen"] != "passed":
        add_issue(
            issues,
            "reopen_not_passed",
            "$reopened.evidence_layers.native_reopen",
            "Reopen report must declare native_reopen as passed.",
        )

    forward_bodies = {item["name"]: item for item in forward["bodies"]}
    reopen_bodies = {item["name"]: item for item in reopened["bodies"]}
    bodies_equal = set(forward_bodies) == set(reopen_bodies)
    if not bodies_equal:
        add_issue(
            issues,
            "body_name_set_mismatch",
            "$.bodies",
            "Forward and reopen body-name sets differ.",
        )
    for name in sorted(set(forward_bodies) & set(reopen_bodies)):
        before = forward_bodies[name]
        after = reopen_bodies[name]
        for field in ("bbox_min_mm", "bbox_max_mm"):
            if any(
                not close_enough(before[field][axis], after[field][axis], bbox_tolerance_mm)
                for axis in range(3)
            ):
                bodies_equal = False
                add_issue(
                    issues,
                    "bbox_persistence_mismatch",
                    "$.bodies[%s].%s" % (name, field),
                    "Forward and reopen values differ beyond tolerance.",
                )
        if not close_enough(
            before["volume_mm3"], after["volume_mm3"], volume_tolerance_mm3
        ):
            bodies_equal = False
            add_issue(
                issues,
                "volume_persistence_mismatch",
                "$.bodies[%s].volume_mm3" % name,
                "Forward and reopen values differ beyond tolerance.",
            )
    result["comparison"]["bodies_equal"] = bodies_equal

    forward_groups = {
        item["name"]: item["member_count"] for item in forward["named_face_groups"]
    }
    reopen_groups = {
        item["name"]: item["member_count"] for item in reopened["named_face_groups"]
    }
    groups_equal = forward_groups == reopen_groups
    result["comparison"]["named_face_groups_equal"] = groups_equal
    if not groups_equal:
        add_issue(
            issues,
            "group_persistence_mismatch",
            "$.named_face_groups",
            "Forward and reopen group names or member counts differ.",
        )

    forward_features = {item["name"]: item for item in forward.get("features", [])}
    reopen_features = {item["name"]: item for item in reopened.get("features", [])}
    features_equal = set(forward_features) == set(reopen_features)
    if not features_equal:
        add_issue(
            issues,
            "feature_name_set_mismatch",
            "$.features",
            "Forward and reopen feature-name sets differ.",
        )
    for name in sorted(set(forward_features) & set(reopen_features)):
        before = forward_features[name]
        after = reopen_features[name]
        if before["count"] != after["count"]:
            features_equal = False
            add_issue(
                issues,
                "feature_count_persistence_mismatch",
                "$.features[%s].count" % name,
                "Forward and reopen feature counts differ.",
            )
        before_measurements = before["measurements"]
        after_measurements = after["measurements"]
        if set(before_measurements) != set(after_measurements):
            features_equal = False
            add_issue(
                issues,
                "feature_measurement_set_mismatch",
                "$.features[%s].measurements" % name,
                "Forward and reopen feature measurement names differ.",
            )
        for key in sorted(set(before_measurements) & set(after_measurements)):
            if not close_enough(before_measurements[key], after_measurements[key], feature_tolerance):
                features_equal = False
                add_issue(
                    issues,
                    "feature_measurement_persistence_mismatch",
                    "$.features[%s].measurements.%s" % (name, key),
                    "Forward and reopen feature measurements differ beyond tolerance.",
                )
    result["comparison"]["features_equal"] = features_equal

    result["status"] = "failed" if issues else "passed"
    return result


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("forward_report", type=Path)
    parser.add_argument("reopen_report", type=Path)
    parser.add_argument("--bbox-tolerance-mm", type=float, default=1.0e-9)
    parser.add_argument("--volume-tolerance-mm3", type=float, default=1.0e-9)
    parser.add_argument("--feature-tolerance", type=float, default=1.0e-9)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        result = compare_reports(
            load_json(args.forward_report),
            load_json(args.reopen_report),
            bbox_tolerance_mm=args.bbox_tolerance_mm,
            volume_tolerance_mm3=args.volume_tolerance_mm3,
            feature_tolerance=args.feature_tolerance,
        )
    except (OSError, UnicodeError, ValueError, json.JSONDecodeError) as exc:
        result = {
            "schema_version": 1,
            "evidence_level": "host_report_comparison_only",
            "status": "failed",
            "comparison": {
                "case_and_target_equal": False,
                "bodies_equal": False,
                "named_face_groups_equal": False,
                "features_equal": False,
            },
            "issues": [{"code": "input_read_error", "path": "$", "message": str(exc)}],
        }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["status"] == "passed" else 2


if __name__ == "__main__":
    sys.exit(main())
