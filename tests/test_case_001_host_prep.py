from __future__ import annotations

import ast
import importlib.util
import json
import re
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CASE_ROOT = (
    ROOT
    / "spaceclaim-vision-modeling"
    / "assets"
    / "cases"
    / "001-offset-block-array"
)
SCRIPT_PATH = CASE_ROOT / "output" / "spaceclaim-v21-build.py"
CONTRACT_PATH = CASE_ROOT / "validation-contract.json"
EVIDENCE_PATH = CASE_ROOT / "runtime-evidence.md"
FORWARD_REPORT_PATH = CASE_ROOT / "forward-runtime-report.json"
REOPEN_REPORT_PATH = CASE_ROOT / "reopen-runtime-report.json"
SCHEMA_PATH = (
    ROOT
    / "spaceclaim-vision-modeling"
    / "references"
    / "spaceclaim-validation-report.schema.json"
)
AUDITOR_PATH = ROOT / "spaceclaim-vision-modeling" / "scripts" / "audit_scscript.py"
AUDITOR_SPEC = importlib.util.spec_from_file_location("case_001_auditor", AUDITOR_PATH)
assert AUDITOR_SPEC and AUDITOR_SPEC.loader
AUDITOR = importlib.util.module_from_spec(AUDITOR_SPEC)
AUDITOR_SPEC.loader.exec_module(AUDITOR)
PACKAGER_PATH = ROOT / "spaceclaim-vision-modeling" / "scripts" / "package_scscript.py"
PACKAGER_SPEC = importlib.util.spec_from_file_location("case_001_packager", PACKAGER_PATH)
assert PACKAGER_SPEC and PACKAGER_SPEC.loader
PACKAGER = importlib.util.module_from_spec(PACKAGER_SPEC)
PACKAGER_SPEC.loader.exec_module(PACKAGER)
SCRIPTS_PATH = ROOT / "spaceclaim-vision-modeling" / "scripts"
if str(SCRIPTS_PATH) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_PATH))
VALIDATOR_PATH = SCRIPTS_PATH / "validate_runtime_report.py"
VALIDATOR_SPEC = importlib.util.spec_from_file_location("case_001_runtime_validator", VALIDATOR_PATH)
assert VALIDATOR_SPEC and VALIDATOR_SPEC.loader
VALIDATOR = importlib.util.module_from_spec(VALIDATOR_SPEC)
VALIDATOR_SPEC.loader.exec_module(VALIDATOR)
COMPARATOR_PATH = SCRIPTS_PATH / "compare_runtime_reports.py"
COMPARATOR_SPEC = importlib.util.spec_from_file_location("case_001_runtime_comparator", COMPARATOR_PATH)
assert COMPARATOR_SPEC and COMPARATOR_SPEC.loader
COMPARATOR = importlib.util.module_from_spec(COMPARATOR_SPEC)
COMPARATOR_SPEC.loader.exec_module(COMPARATOR)


class Case001Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.source = SCRIPT_PATH.read_text(encoding="utf-8")
        cls.contract = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))

    def test_candidate_script_is_host_parseable_and_forward_tested(self) -> None:
        ast.parse(self.source)
        self.assertIn("forward-tested", self.source)
        self.assertNotIn("runtime" + "_pending", self.source)
        self.assertIn('from SpaceClaim.Api.V21 import *', self.source)

    def test_runtime_evidence_records_forward_and_reopen_boundaries(self) -> None:
        evidence = EVIDENCE_PATH.read_text(encoding="utf-8")
        self.assertIn("SpaceClaim 2022 R1", evidence)
        self.assertIn("Scripting API: V21", evidence)
        self.assertIn("Native persistence result", evidence)
        self.assertIn("Evidence boundary", evidence)

    def test_script_allows_run_owned_model_but_protects_report(self) -> None:
        self.assertIn("OUTPUT_MODEL_PATH = None", self.source)
        self.assertIn("REPORT_PATH = None", self.source)
        self.assertIn('"OUTPUT_MODEL_PATH", allow_existing=True', self.source)
        self.assertIn('normalized_new_path(REPORT_PATH, ".json", "REPORT_PATH")', self.source)
        self.assertIn("refusing to overwrite", self.source)

    def test_geometry_validation_precedes_the_only_native_save(self) -> None:
        self.assertEqual(1, self.source.count("DocumentSave.Execute("))
        self.assertLess(
            self.source.index("validate_and_report_geometry(report, named_bodies)"),
            self.source.index("DocumentSave.Execute("),
        )
        self.assertIsNone(re.search(r"\b(?:Body|Face|Edge)\d+\b", self.source))

    def test_forward_source_passes_static_archive_rules(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            archive_path = Path(directory) / "case-001-candidate.scscript"
            PACKAGER.package_scscript(SCRIPT_PATH, archive_path)
            result = AUDITOR.audit_archive(
                archive_path,
                require_api="21",
                forbid_numbered_aliases=True,
                required_operations=(
                    "BlockBody.Create",
                    "NamedSelection.Create",
                    "DocumentSave.Execute",
                ),
            )
            self.assertEqual("passed", result["status"])

    def test_contract_and_report_schema_cover_case_001(self) -> None:
        schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
        self.assertEqual(1, self.contract["schema_version"])
        self.assertEqual("001-offset-block-array", self.contract["case_id"])
        self.assertEqual(3, len(self.contract["bodies"]))
        group_names = [item["name"] for item in self.contract["named_face_groups"]]
        self.assertEqual(2, len(group_names))
        self.assertEqual(len(group_names), len(set(group_names)))
        self.assertIn("evidence_layers", schema["required"])

    def _load_public_runtime_report(self, report_path: Path) -> dict:
        self.assertTrue(report_path.is_file(), "Missing public runtime report: %s" % report_path)
        report = VALIDATOR.load_json(report_path)
        result = VALIDATOR.validate_report(report, self.contract)
        self.assertEqual(
            "passed",
            result["status"],
            "%s failed contract validation: %s" % (report_path, result["issues"]),
        )
        self.assertEqual(report_path.name, report["outputs"]["report_path"])
        return report

    def test_public_runtime_reports_exist_and_pass_contract(self) -> None:
        self._load_public_runtime_report(FORWARD_REPORT_PATH)
        self._load_public_runtime_report(REOPEN_REPORT_PATH)

    def test_public_runtime_reports_compare_as_passed(self) -> None:
        forward = self._load_public_runtime_report(FORWARD_REPORT_PATH)
        reopened = self._load_public_runtime_report(REOPEN_REPORT_PATH)
        tolerances = self.contract.get("tolerances", {})
        result = COMPARATOR.compare_reports(
            forward,
            reopened,
            bbox_tolerance_mm=float(tolerances.get("bbox_mm", 0.0)),
            volume_tolerance_mm3=float(tolerances.get("volume_mm3", 0.0)),
            feature_tolerance=float(tolerances.get("feature_mm", 0.0)),
        )
        self.assertEqual(
            "passed",
            result["status"],
            "Forward/reopen comparison failed: %s" % result["issues"],
        )
        self.assertTrue(all(result["comparison"].values()), result["comparison"])


if __name__ == "__main__":
    unittest.main()
