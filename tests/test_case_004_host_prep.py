from __future__ import annotations

import ast
import hashlib
import importlib.util
import json
import re
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CASE_ROOT = (
    ROOT
    / "spaceclaim-vision-modeling"
    / "assets"
    / "cases"
    / "004-rounded-plate-support"
)
BUILD_PATH = CASE_ROOT / "output" / "spaceclaim-v21-build.py"
REOPEN_PATH = CASE_ROOT / "output" / "spaceclaim-v21-reopen-audit.py"
BUILD_SCSCRIPT_PATH = CASE_ROOT / "output" / "spaceclaim-v21-build.scscript"
REOPEN_SCSCRIPT_PATH = CASE_ROOT / "output" / "spaceclaim-v21-reopen-audit.scscript"
CONTRACT_PATH = CASE_ROOT / "validation" / "validation-contract.json"
EVIDENCE_PATH = CASE_ROOT / "validation" / "runtime-evidence.md"
FORWARD_REPORT_PATH = CASE_ROOT / "validation" / "forward-runtime-report.json"
REOPEN_REPORT_PATH = CASE_ROOT / "validation" / "reopen-runtime-report.json"
AUDITOR_PATH = ROOT / "spaceclaim-vision-modeling" / "scripts" / "audit_scscript.py"
AUDITOR_SPEC = importlib.util.spec_from_file_location("case_004_auditor", AUDITOR_PATH)
assert AUDITOR_SPEC and AUDITOR_SPEC.loader
AUDITOR = importlib.util.module_from_spec(AUDITOR_SPEC)
AUDITOR_SPEC.loader.exec_module(AUDITOR)
PACKAGER_PATH = ROOT / "spaceclaim-vision-modeling" / "scripts" / "package_scscript.py"
PACKAGER_SPEC = importlib.util.spec_from_file_location("case_004_packager", PACKAGER_PATH)
assert PACKAGER_SPEC and PACKAGER_SPEC.loader
PACKAGER = importlib.util.module_from_spec(PACKAGER_SPEC)
PACKAGER_SPEC.loader.exec_module(PACKAGER)
SCRIPTS_PATH = ROOT / "spaceclaim-vision-modeling" / "scripts"
if str(SCRIPTS_PATH) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_PATH))
VALIDATOR_PATH = SCRIPTS_PATH / "validate_runtime_report.py"
VALIDATOR_SPEC = importlib.util.spec_from_file_location("case_004_runtime_validator", VALIDATOR_PATH)
assert VALIDATOR_SPEC and VALIDATOR_SPEC.loader
VALIDATOR = importlib.util.module_from_spec(VALIDATOR_SPEC)
VALIDATOR_SPEC.loader.exec_module(VALIDATOR)
COMPARATOR_PATH = SCRIPTS_PATH / "compare_runtime_reports.py"
COMPARATOR_SPEC = importlib.util.spec_from_file_location("case_004_runtime_comparator", COMPARATOR_PATH)
assert COMPARATOR_SPEC and COMPARATOR_SPEC.loader
COMPARATOR = importlib.util.module_from_spec(COMPARATOR_SPEC)
COMPARATOR_SPEC.loader.exec_module(COMPARATOR)


class Case004HostPrepTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.build_source = BUILD_PATH.read_text(encoding="utf-8")
        cls.reopen_source = REOPEN_PATH.read_text(encoding="utf-8")
        cls.contract = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))

    def test_both_v21_sources_are_python_ast_parseable(self) -> None:
        ast.parse(self.build_source, filename=str(BUILD_PATH))
        ast.parse(self.reopen_source, filename=str(REOPEN_PATH))
        for source in (self.build_source, self.reopen_source):
            self.assertIn("from SpaceClaim.Api.V21 import *", source)

    def test_formal_build_archive_passes_v21_operation_audit(self) -> None:
        result = AUDITOR.audit_archive(
            BUILD_SCSCRIPT_PATH,
            require_api="21",
            forbid_numbered_aliases=True,
            required_operations=(
                "ModelerBody.ExtrudeProfile",
                "plate.Unite",
                "plate.Subtract",
                "ConstantRound.Execute",
                "DocumentSave.Execute",
            ),
        )
        self.assertEqual("passed", result["status"])
        self.assertEqual([], result["numbered_aliases"])

    def test_reopen_archive_is_read_only_and_passes_v21_operation_audit(self) -> None:
        result = AUDITOR.audit_archive(
            REOPEN_SCSCRIPT_PATH,
            require_api="21",
            forbid_numbered_aliases=True,
            forbidden_operations=(
                "DesignBody.Create",
                "ConstantRound.Execute",
                "Chamfer.Execute",
                "DocumentSave.Execute",
            ),
        )
        self.assertEqual("passed", result["status"])
        self.assertEqual([], result["numbered_aliases"])
        self.assertNotIn("DesignBody.Create", result["operation_counts"])
        self.assertNotIn("DocumentSave.Execute", result["operation_counts"])

    def test_reopen_source_has_no_mutating_model_operations(self) -> None:
        source = self.reopen_source
        self.assertIn("NATIVE_MODEL_PATH = None", source)
        self.assertIn("REPORT_PATH = None", source)
        self.assertIn("normalized_path(REPORT_PATH, \".json\", \"REPORT_PATH\", False)", source)
        self.assertIn("refusing to overwrite", source)
        self.assertIn('"native_reopen"] = "passed"', source)
        for forbidden in (
            "DesignBody.Create(",
            "ConstantRound.Execute(",
            "Chamfer.Execute(",
            "DocumentSave.Execute(",
            "RenameObject.Execute(",
            "NamedSelection.Create(",
        ):
            self.assertNotIn(forbidden, source)

    def test_reopen_validates_contract_geometry_and_features(self) -> None:
        source = self.reopen_source
        self.assertIn("[0.0, 0.0, 0.0, 120.0, 80.0, 60.0]", source)
        self.assertIn("EXPECTED_VOLUME_MM3 = 128473.8907081775", source)
        self.assertIn("R10 corner cylinder faces", source)
        self.assertIn("central support cylinder faces", source)
        self.assertIn("mounting-hole cylinder faces", source)
        self.assertIn("body.Name != \"ROUNDED_PLATE_SUPPORT_01\"", source)
        self.assertIn("validate_and_report_geometry(report, body)", source)
        self.assertLess(
            source.index("validate_and_report_geometry(report, body)"),
            source.index("write_report(report_path, report)"),
        )

    def test_contract_covers_case004_geometry(self) -> None:
        self.assertEqual(1, self.contract["schema_version"])
        self.assertEqual("004-rounded-plate-support", self.contract["case_id"])
        self.assertEqual("V21", self.contract["target"]["api_version"])
        self.assertEqual(
            {
                "name": "ROUNDED_PLATE_SUPPORT_01",
                "bbox_min_mm": [0.0, 0.0, 0.0],
                "bbox_max_mm": [120.0, 80.0, 60.0],
                "volume_mm3": 128473.8907081775,
            },
            self.contract["bodies"][0],
        )
        features = {item["name"]: item for item in self.contract["features"]}
        self.assertEqual(
            {"rounded_base_plate", "central_support", "mounting_holes"},
            set(features),
        )
        self.assertEqual(10.0, features["rounded_base_plate"]["measurements"]["corner_radius_mm"])
        self.assertEqual(30.0, features["central_support"]["measurements"]["diameter_mm"])
        self.assertEqual(50.0, features["central_support"]["measurements"]["height_mm"])
        self.assertEqual(4, features["mounting_holes"]["count"])
        self.assertEqual(8.0, features["mounting_holes"]["measurements"]["diameter_mm"])

    def test_build_reenumerates_after_union_subtract_and_round(self) -> None:
        source = self.build_source
        union_index = source.index("plate.Unite(")
        subtract_index = source.index("plate.Subtract(", union_index)
        attach_index = source.index("DesignBody.Create(", subtract_index)
        attach_reenumeration = source.index("current_bodies()", attach_index)
        round_index = source.index("ConstantRound.Execute")
        round_reenumeration = source.index("current_bodies()", round_index)
        self.assertLess(union_index, subtract_index)
        self.assertLess(subtract_index, attach_index)
        self.assertLess(attach_index, attach_reenumeration)
        self.assertLess(round_index, round_reenumeration)
        self.assertIn("bodies after plate corner rounds", source[round_reenumeration : round_reenumeration + 140])

    def test_build_validates_before_its_only_native_save(self) -> None:
        self.assertEqual(1, self.build_source.count("DocumentSave.Execute("))
        self.assertLess(
            self.build_source.index("validate_and_report_geometry(report, body)"),
            self.build_source.index("DocumentSave.Execute("),
        )
        self.assertIsNone(re.search(r"\b(?:Body|Face|Edge)\d+\b", self.build_source))
        self.assertIsNone(re.search(r"\b(?:Body|Face|Edge)\d+\b", self.reopen_source))

    def test_case_bundle_contains_no_private_paths(self) -> None:
        private_path_patterns = (
            re.compile(r"(?i)[A-Za-z]:[/\\]+Users[/\\]+"),
            re.compile(r"(?i)[A-Za-z]:[/\\]+(?:ai|SN2)(?:[/\\]|$)"),
            re.compile(r"(?i)\\\\[^\\\r\n]+\\[^\\\r\n]+"),
        )
        violations = []
        for path in sorted(item for item in CASE_ROOT.rglob("*") if item.is_file()):
            try:
                text = path.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                continue
            for pattern in private_path_patterns:
                match = pattern.search(text)
                if match:
                    violations.append("%s: private path %r" % (path.relative_to(CASE_ROOT), match.group(0)))
        self.assertEqual([], violations)

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

    def test_submitted_scscript_embeds_exact_utf8_neighboring_sources(self) -> None:
        for archive_path, source_path in (
            (BUILD_SCSCRIPT_PATH, BUILD_PATH),
            (REOPEN_SCSCRIPT_PATH, REOPEN_PATH),
        ):
            source_bytes = source_path.read_bytes()
            try:
                source_bytes.decode("utf-8")
            except UnicodeDecodeError as exc:
                self.fail("Neighboring source is not UTF-8: %s" % exc)
            self.assertTrue(archive_path.is_file(), "Missing submitted archive: %s" % archive_path)
            with zipfile.ZipFile(archive_path) as archive:
                self.assertIn("_script", archive.namelist())
                self.assertEqual(
                    source_bytes,
                    archive.read("_script"),
                    "_script bytes differ from %s" % source_path,
                )

    def test_runtime_evidence_records_current_public_artifact_hashes(self) -> None:
        self.assertTrue(EVIDENCE_PATH.is_file(), "Missing runtime evidence: %s" % EVIDENCE_PATH)
        evidence_lines = EVIDENCE_PATH.read_text(encoding="utf-8").splitlines()
        artifacts = (
            ("Public parameterized build package", BUILD_SCSCRIPT_PATH),
            ("Public parameterized reopen package", REOPEN_SCSCRIPT_PATH),
            ("Public sanitized forward report", FORWARD_REPORT_PATH),
            ("Public sanitized native-reopen report", REOPEN_REPORT_PATH),
        )
        for label, artifact_path in artifacts:
            digest = hashlib.sha256(artifact_path.read_bytes()).hexdigest().upper()
            matching_lines = [line.upper() for line in evidence_lines if label.upper() in line.upper()]
            self.assertTrue(matching_lines, "Evidence does not name %s" % label)
            self.assertTrue(
                any(digest in line for line in matching_lines),
                "Evidence hash for %s is not current (%s)" % (label, digest),
            )

    def test_failure_state_machine_only_downgrades_untested_evidence(self) -> None:
        for source, evidence_names in (
            (self.build_source, ("spaceclaim_execution", "native_save")),
            (self.reopen_source, ("spaceclaim_execution", "native_reopen")),
        ):
            self.assertIn("execution_started", source)
            except_start = source.rfind("except Exception as exc:")
            self.assertGreaterEqual(except_start, 0)
            except_source = source[except_start:]
            for evidence_name in evidence_names:
                pattern = (
                    r"if[\s\S]*report\[\"evidence_layers\"\]\[\"%s\"\]"
                    r"\s*==\s*\"not_tested\"[\s\S]*report\[\"evidence_layers\"\]"
                    r"\[\"%s\"\]\s*=\s*\"failed\""
                ) % (evidence_name, evidence_name)
                self.assertRegex(except_source, pattern)

    def test_visual_evidence_heading_and_each_screenshot_record(self) -> None:
        evidence = EVIDENCE_PATH.read_text(encoding="utf-8")
        self.assertIn("## Visual review evidence", evidence)
        self.assertIn(
            "| Model/run | View | Selection state | Expected visible features | "
            "Observed agreement or discrepancy | Occluded/unresolved | External capture path / SHA-256 |",
            evidence,
        )
        for screenshot_name in (
            "visual-home.png",
            "visual-front-z.png",
            "visual-side-x.png",
        ):
            self.assertRegex(
                evidence,
                r"`%s`[^\r\n]*?`[0-9A-Fa-f]{64}`" % re.escape(screenshot_name),
            )


if __name__ == "__main__":
    unittest.main()
