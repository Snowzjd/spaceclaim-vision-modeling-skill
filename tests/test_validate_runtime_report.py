from __future__ import annotations

import contextlib
import copy
import importlib.util
import io
import json
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "spaceclaim-vision-modeling" / "scripts" / "validate_runtime_report.py"
CONTRACT_PATH = (
    ROOT
    / "spaceclaim-vision-modeling"
    / "assets"
    / "cases"
    / "001-offset-block-array"
    / "validation-contract.json"
)
SPEC = importlib.util.spec_from_file_location("validate_runtime_report", MODULE_PATH)
assert SPEC and SPEC.loader
VALIDATOR = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(VALIDATOR)


def passing_report() -> dict:
    contract = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
    return {
        "schema_version": 1,
        "case_id": contract["case_id"],
        "status": "passed",
        "target": {
            "spaceclaim_release": "2022 R1",
            "api_version": "V21",
            "python_runtime": "IronPython 2.7"
        },
        "stages": [
            {"name": "parameters_validated", "status": "passed"},
            {"name": "geometry_validated", "status": "passed"},
            {"name": "native_saved", "status": "passed"}
        ],
        "bodies": copy.deepcopy(contract["bodies"]),
        "named_face_groups": copy.deepcopy(contract["named_face_groups"]),
        "features": [],
        "outputs": {
            "native_model_path": "C:/runs/001/model.scdoc",
            "report_path": "C:/runs/001/runtime-report.json"
        },
        "evidence_layers": {
            "static_archive": "not_tested",
            "spaceclaim_execution": "passed",
            "geometry_measurements": "passed",
            "native_save": "passed",
            "native_reopen": "not_tested",
            "neutral_export": "not_tested"
        }
    }


class ValidateRuntimeReportTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.contract = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))

    def validate(self, report: dict) -> dict:
        return VALIDATOR.validate_report(report, self.contract)

    def test_matching_report_passes(self) -> None:
        self.assertEqual("passed", self.validate(passing_report())["status"])

    def test_missing_required_field_fails(self) -> None:
        report = passing_report()
        del report["outputs"]
        result = self.validate(report)
        self.assertEqual("failed", result["status"])
        self.assertIn("missing_field", [issue["code"] for issue in result["issues"]])

    def test_invalid_evidence_state_fails(self) -> None:
        report = passing_report()
        report["evidence_layers"]["neutral_export"] = "unknown"
        result = self.validate(report)
        self.assertIn("invalid_evidence_state", [issue["code"] for issue in result["issues"]])

    def test_passed_report_cannot_contain_failed_stage(self) -> None:
        report = passing_report()
        report["stages"][1]["status"] = "failed"
        result = self.validate(report)
        self.assertIn("inconsistent_report_status", [issue["code"] for issue in result["issues"]])

    def test_bbox_minimum_cannot_exceed_maximum(self) -> None:
        report = passing_report()
        report["bodies"][0]["bbox_min_mm"][0] = 21.0
        result = self.validate(report)
        self.assertIn("invalid_bbox_order", [issue["code"] for issue in result["issues"]])

    def test_output_paths_must_be_distinct(self) -> None:
        report = passing_report()
        report["outputs"]["report_path"] = report["outputs"]["native_model_path"]
        result = self.validate(report)
        self.assertIn("output_path_collision", [issue["code"] for issue in result["issues"]])

    def test_body_name_set_mismatch_fails(self) -> None:
        report = passing_report()
        report["bodies"][0]["name"] = "WRONG"
        result = self.validate(report)
        self.assertIn("body_name_set_mismatch", [issue["code"] for issue in result["issues"]])

    def test_bbox_mismatch_fails(self) -> None:
        report = passing_report()
        report["bodies"][1]["bbox_max_mm"][1] = 12.0
        result = self.validate(report)
        self.assertIn("bbox_mismatch", [issue["code"] for issue in result["issues"]])

    def test_volume_mismatch_fails(self) -> None:
        report = passing_report()
        report["bodies"][2]["volume_mm3"] = 641.0
        result = self.validate(report)
        self.assertIn("volume_mismatch", [issue["code"] for issue in result["issues"]])

    def test_group_member_count_mismatch_fails(self) -> None:
        report = passing_report()
        report["named_face_groups"][0]["member_count"] = 2
        result = self.validate(report)
        self.assertIn("group_member_count_mismatch", [issue["code"] for issue in result["issues"]])

    def test_unperformed_export_claim_fails_contract(self) -> None:
        report = passing_report()
        report["evidence_layers"]["neutral_export"] = "passed"
        result = self.validate(report)
        self.assertIn("evidence_boundary_mismatch", [issue["code"] for issue in result["issues"]])

    def test_target_api_mismatch_fails(self) -> None:
        report = passing_report()
        report["target"]["api_version"] = "V22"
        result = self.validate(report)
        self.assertIn("target_mismatch", [issue["code"] for issue in result["issues"]])

    def test_negative_contract_tolerance_fails_without_exception(self) -> None:
        contract = copy.deepcopy(self.contract)
        contract["tolerances"]["bbox_mm"] = -0.001
        result = VALIDATOR.validate_report(passing_report(), contract)
        self.assertEqual("failed", result["status"])
        self.assertIn("invalid_contract", [issue["code"] for issue in result["issues"]])

    def test_feature_contract_is_compared(self) -> None:
        report = passing_report()
        report["features"] = [
            {"name": "holes", "count": 4, "measurements": {"diameter_mm": 6.5}}
        ]
        contract = copy.deepcopy(self.contract)
        contract["tolerances"]["feature_mm"] = 0.001
        contract["features"] = [
            {"name": "holes", "count": 4, "measurements": {"diameter_mm": 6.5}}
        ]
        self.assertEqual("passed", VALIDATOR.validate_report(report, contract)["status"])
        report["features"][0]["count"] = 3
        result = VALIDATOR.validate_report(report, contract)
        self.assertIn("feature_count_mismatch", [issue["code"] for issue in result["issues"]])

    def test_invalid_feature_measurement_fails(self) -> None:
        report = passing_report()
        report["features"] = [
            {"name": "holes", "count": 4, "measurements": {"diameter_mm": "6.5"}}
        ]
        result = self.validate(report)
        self.assertIn("invalid_feature_measurement", [issue["code"] for issue in result["issues"]])

    def test_duplicate_contract_body_name_fails_without_exception(self) -> None:
        contract = copy.deepcopy(self.contract)
        contract["bodies"][1]["name"] = contract["bodies"][0]["name"]
        result = VALIDATOR.validate_report(passing_report(), contract)
        self.assertEqual("failed", result["status"])
        self.assertIn("invalid_contract", [issue["code"] for issue in result["issues"]])

    def test_cli_returns_zero_for_matching_report(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            report_path = Path(directory) / "report.json"
            report_path.write_text(json.dumps(passing_report()), encoding="utf-8")
            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                exit_code = VALIDATOR.main(
                    [str(report_path), "--contract", str(CONTRACT_PATH)]
                )
            self.assertEqual(0, exit_code)
            self.assertEqual("passed", json.loads(stdout.getvalue())["status"])


if __name__ == "__main__":
    unittest.main()
