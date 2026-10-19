from __future__ import annotations

import contextlib
import importlib.util
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "spaceclaim-vision-modeling" / "scripts"
MODULE_PATH = SCRIPTS / "compare_runtime_reports.py"
sys.path.insert(0, str(SCRIPTS))
SPEC = importlib.util.spec_from_file_location("compare_runtime_reports", MODULE_PATH)
assert SPEC and SPEC.loader
COMPARATOR = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(COMPARATOR)


def report(*, reopen: bool) -> dict:
    return {
        "schema_version": 1,
        "case_id": "synthetic-case",
        "status": "passed",
        "target": {
            "spaceclaim_release": "2022 R1",
            "api_version": "V21",
            "python_runtime": "IronPython 2.7",
        },
        "stages": [
            {
                "name": "reopened_geometry_validated" if reopen else "native_model_saved",
                "status": "passed",
            }
        ],
        "bodies": [
            {
                "name": "BODY_A",
                "bbox_min_mm": [0.0, 0.0, 0.0],
                "bbox_max_mm": [1.0, 2.0, 3.0],
                "volume_mm3": 6.0,
            }
        ],
        "named_face_groups": [{"name": "GROUP_A", "member_count": 1}],
        "features": [
            {"name": "holes", "count": 4, "measurements": {"diameter_mm": 6.5}}
        ],
        "outputs": {
            "native_model_path": "C:/runs/model.scdoc",
            "report_path": "C:/runs/%s.json" % ("reopen" if reopen else "forward"),
        },
        "evidence_layers": {
            "static_archive": "not_tested",
            "spaceclaim_execution": "passed",
            "geometry_measurements": "passed",
            "native_save": "not_tested" if reopen else "passed",
            "native_reopen": "passed" if reopen else "not_tested",
            "neutral_export": "not_tested",
        },
    }


class CompareRuntimeReportsTests(unittest.TestCase):
    def test_matching_forward_and_reopen_reports_pass(self) -> None:
        result = COMPARATOR.compare_reports(report(reopen=False), report(reopen=True))
        self.assertEqual("passed", result["status"])
        self.assertTrue(result["comparison"]["bodies_equal"])
        self.assertTrue(result["comparison"]["named_face_groups_equal"])
        self.assertTrue(result["comparison"]["features_equal"])

    def test_volume_change_fails(self) -> None:
        reopened = report(reopen=True)
        reopened["bodies"][0]["volume_mm3"] = 6.1
        result = COMPARATOR.compare_reports(report(reopen=False), reopened)
        self.assertEqual("failed", result["status"])
        self.assertIn("volume_persistence_mismatch", [item["code"] for item in result["issues"]])

    def test_group_change_fails(self) -> None:
        reopened = report(reopen=True)
        reopened["named_face_groups"][0]["member_count"] = 2
        result = COMPARATOR.compare_reports(report(reopen=False), reopened)
        self.assertEqual("failed", result["status"])
        self.assertIn("group_persistence_mismatch", [item["code"] for item in result["issues"]])

    def test_reopen_evidence_must_be_passed(self) -> None:
        reopened = report(reopen=True)
        reopened["evidence_layers"]["native_reopen"] = "not_tested"
        result = COMPARATOR.compare_reports(report(reopen=False), reopened)
        self.assertEqual("failed", result["status"])
        self.assertIn("reopen_not_passed", [item["code"] for item in result["issues"]])

    def test_forward_report_status_must_be_passed(self) -> None:
        forward = report(reopen=False)
        forward["status"] = "failed"
        forward["stages"][0]["status"] = "failed"
        result = COMPARATOR.compare_reports(forward, report(reopen=True))
        self.assertEqual("failed", result["status"])
        self.assertIn("forward_report_not_passed", [item["code"] for item in result["issues"]])

    def test_reopen_report_status_must_be_passed(self) -> None:
        reopened = report(reopen=True)
        reopened["status"] = "failed"
        reopened["stages"][0]["status"] = "failed"
        result = COMPARATOR.compare_reports(report(reopen=False), reopened)
        self.assertEqual("failed", result["status"])
        self.assertIn("reopen_report_not_passed", [item["code"] for item in result["issues"]])

    def test_feature_change_fails(self) -> None:
        reopened = report(reopen=True)
        reopened["features"][0]["measurements"]["diameter_mm"] = 6.6
        result = COMPARATOR.compare_reports(report(reopen=False), reopened)
        self.assertEqual("failed", result["status"])
        self.assertIn(
            "feature_measurement_persistence_mismatch",
            [item["code"] for item in result["issues"]],
        )

    def test_cli_returns_zero_and_emits_json(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            forward_path = Path(directory) / "forward.json"
            reopen_path = Path(directory) / "reopen.json"
            forward_path.write_text(json.dumps(report(reopen=False)), encoding="utf-8")
            reopen_path.write_text(json.dumps(report(reopen=True)), encoding="utf-8")
            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                exit_code = COMPARATOR.main([str(forward_path), str(reopen_path)])
            self.assertEqual(0, exit_code)
            self.assertEqual("passed", json.loads(stdout.getvalue())["status"])

    def test_cli_rejects_same_forward_and_reopen_path(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            report_path = Path(directory) / "same.json"
            report_path.write_text(json.dumps(report(reopen=False)), encoding="utf-8")
            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                exit_code = COMPARATOR.main([str(report_path), str(report_path)])
            result = json.loads(stdout.getvalue())
            self.assertEqual(2, exit_code)
            self.assertEqual("failed", result["status"])
            self.assertIn("same_report_path", [item["code"] for item in result["issues"]])


if __name__ == "__main__":
    unittest.main()
