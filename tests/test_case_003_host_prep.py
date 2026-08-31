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
    / "003-stepped-shaft-keyway"
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
AUDITOR_SPEC = importlib.util.spec_from_file_location("case_003_auditor", AUDITOR_PATH)
assert AUDITOR_SPEC and AUDITOR_SPEC.loader
AUDITOR = importlib.util.module_from_spec(AUDITOR_SPEC)
AUDITOR_SPEC.loader.exec_module(AUDITOR)
PACKAGER_PATH = ROOT / "spaceclaim-vision-modeling" / "scripts" / "package_scscript.py"
PACKAGER_SPEC = importlib.util.spec_from_file_location("case_003_packager", PACKAGER_PATH)
assert PACKAGER_SPEC and PACKAGER_SPEC.loader
PACKAGER = importlib.util.module_from_spec(PACKAGER_SPEC)
PACKAGER_SPEC.loader.exec_module(PACKAGER)
SCRIPTS_PATH = ROOT / "spaceclaim-vision-modeling" / "scripts"
if str(SCRIPTS_PATH) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_PATH))
VALIDATOR_PATH = SCRIPTS_PATH / "validate_runtime_report.py"
VALIDATOR_SPEC = importlib.util.spec_from_file_location("case_003_runtime_validator", VALIDATOR_PATH)
assert VALIDATOR_SPEC and VALIDATOR_SPEC.loader
VALIDATOR = importlib.util.module_from_spec(VALIDATOR_SPEC)
VALIDATOR_SPEC.loader.exec_module(VALIDATOR)
COMPARATOR_PATH = SCRIPTS_PATH / "compare_runtime_reports.py"
COMPARATOR_SPEC = importlib.util.spec_from_file_location("case_003_runtime_comparator", COMPARATOR_PATH)
assert COMPARATOR_SPEC and COMPARATOR_SPEC.loader
COMPARATOR = importlib.util.module_from_spec(COMPARATOR_SPEC)
COMPARATOR_SPEC.loader.exec_module(COMPARATOR)


class Case003HostPrepTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.build_source = BUILD_PATH.read_text(encoding="utf-8")
        cls.reopen_source = REOPEN_PATH.read_text(encoding="utf-8")
        cls.contract = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))

    def test_both_v21_sources_are_ast_parseable(self) -> None:
        ast.parse(self.build_source, filename=str(BUILD_PATH))
        ast.parse(self.reopen_source, filename=str(REOPEN_PATH))
        for source in (self.build_source, self.reopen_source):
            self.assertIn("from SpaceClaim.Api.V21 import *", source)

    def test_build_source_packages_and_passes_static_audit(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            archive_path = Path(directory) / "case-003-build.scscript"
            PACKAGER.package_scscript(BUILD_PATH, archive_path)
            result = AUDITOR.audit_archive(
                archive_path,
                require_api="21",
                forbid_numbered_aliases=True,
                required_operations=(
                    "ModelerBody.ExtrudeProfile",
                    "outer.Unite",
                    "outer.Subtract",
                    "ConstantRound.Execute",
                    "Chamfer.Execute",
                    "DocumentSave.Execute",
                ),
            )
            self.assertEqual("passed", result["status"])
            self.assertEqual([], result["numbered_aliases"])

    def test_formal_scscript_assets_pass_bounded_audits(self) -> None:
        build_result = AUDITOR.audit_archive(
            BUILD_SCSCRIPT_PATH,
            require_api="21",
            forbid_numbered_aliases=True,
            required_operations=(
                "ModelerBody.ExtrudeProfile",
                "outer.Unite",
                "outer.Subtract",
                "ConstantRound.Execute",
                "Chamfer.Execute",
                "DocumentSave.Execute",
            ),
        )
        self.assertEqual("passed", build_result["status"])

        reopen_result = AUDITOR.audit_archive(
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
        self.assertEqual("passed", reopen_result["status"])

    def test_contract_covers_drawing_geometry_and_assumptions(self) -> None:
        self.assertEqual("003-stepped-shaft-keyway", self.contract["case_id"])
        self.assertEqual("V21", self.contract["target"]["api_version"])
        self.assertEqual("STEPPED_SHAFT_KEYWAY_01", self.contract["bodies"][0]["name"])
        self.assertEqual([0.0, -19.0, -19.0], self.contract["bodies"][0]["bbox_min_mm"])
        self.assertEqual([100.0, 19.0, 19.0], self.contract["bodies"][0]["bbox_max_mm"])

        features = {item["name"]: item for item in self.contract["features"]}
        self.assertEqual(
            {
                "stepped_outer_segments",
                "through_bore",
                "keyway",
                "end_and_bore_chamfers",
                "shoulder_fillets",
            },
            set(features),
        )
        self.assertEqual(8.0, features["keyway"]["measurements"]["length_mm"])
        self.assertEqual(8.0, features["keyway"]["measurements"]["width_mm"])
        self.assertEqual(3.0, features["keyway"]["measurements"]["depth_mm"])
        self.assertEqual(41.0, features["keyway"]["measurements"]["x_start_mm"])
        self.assertEqual(49.0, features["keyway"]["measurements"]["x_end_mm"])

    def test_v21_profiles_are_imported_from_geometry_namespace(self) -> None:
        self.assertIn(
            "from SpaceClaim.Api.V21.Geometry import CircleProfile, Plane, PointUV, RectangleProfile",
            self.build_source,
        )
        self.assertIn("CircleProfile(plane, mm(radius), PointUV.Create(0.0, 0.0), 0.0)", self.build_source)
        self.assertIn("profile = RectangleProfile(", self.build_source)
        self.assertEqual(2, self.build_source.count("ModelerBody.ExtrudeProfile(profile,"))

    def test_topology_changes_are_followed_by_reenumeration(self) -> None:
        source = self.build_source
        subtract_index = source.index("outer.Subtract(")
        attach_index = source.index("DesignBody.Create(", subtract_index)
        attach_reenumeration = source.index("current_bodies()", attach_index)
        self.assertLess(subtract_index, attach_index)
        self.assertLess(attach_index, attach_reenumeration)
        for operation, marker in (
            ("ConstantRound.Execute", "bodies after shoulder fillets"),
            ("Chamfer.Execute", "bodies after end chamfers"),
        ):
            operation_index = source.index(operation)
            reenumeration_index = source.index("current_bodies()", operation_index)
            self.assertIn(marker, source[reenumeration_index : reenumeration_index + 140])

    def test_clean_document_and_validation_precede_only_save(self) -> None:
        self.assertIn('require_count(current_bodies(), 0, "initial document bodies")', self.build_source)
        self.assertEqual(1, self.build_source.count("DocumentSave.Execute("))
        self.assertLess(
            self.build_source.index("validate_and_report_geometry(report, body)"),
            self.build_source.index("DocumentSave.Execute("),
        )
        self.assertIsNone(re.search(r"\b(?:Body|Face|Edge)\d+\b", self.build_source))

    def test_model_and_report_paths_are_run_owned(self) -> None:
        self.assertIn("OUTPUT_MODEL_PATH = None", self.build_source)
        self.assertIn("REPORT_PATH = None", self.build_source)
        self.assertIn("refusing to overwrite", self.build_source)
        self.assertIn("NATIVE_MODEL_PATH = None", self.reopen_source)
        self.assertIn("refusing to overwrite", self.reopen_source)

    def test_drawing_is_not_redistributed_and_case_has_no_private_paths(self) -> None:
        image_suffixes = {".png", ".jpg", ".jpeg", ".bmp", ".tif", ".tiff"}
        self.assertEqual(
            [],
            [path for path in CASE_ROOT.rglob("*") if path.suffix.lower() in image_suffixes],
        )
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

    def test_submitted_scscript_embeds_exact_neighboring_python_sources(self) -> None:
        for archive_path, source_path in (
            (BUILD_SCSCRIPT_PATH, BUILD_PATH),
            (REOPEN_SCSCRIPT_PATH, REOPEN_PATH),
        ):
            self.assertTrue(archive_path.is_file(), "Missing submitted archive: %s" % archive_path)
            self.assertTrue(source_path.is_file(), "Missing neighboring source: %s" % source_path)
            with zipfile.ZipFile(archive_path) as archive:
                self.assertIn("_script", archive.namelist())
                self.assertEqual(
                    source_path.read_bytes(),
                    archive.read("_script"),
                    "_script bytes differ from %s" % source_path,
                )

    def test_runtime_evidence_records_current_public_artifact_hashes(self) -> None:
        self.assertTrue(EVIDENCE_PATH.is_file(), "Missing runtime evidence: %s" % EVIDENCE_PATH)
        evidence_lines = EVIDENCE_PATH.read_text(encoding="utf-8").splitlines()
        artifacts = (
            ("../output/spaceclaim-v21-build.scscript", BUILD_SCSCRIPT_PATH),
            ("../output/spaceclaim-v21-reopen-audit.scscript", REOPEN_SCSCRIPT_PATH),
            ("forward-runtime-report.json", FORWARD_REPORT_PATH),
            ("reopen-runtime-report.json", REOPEN_REPORT_PATH),
        )
        for public_name, artifact_path in artifacts:
            digest = hashlib.sha256(artifact_path.read_bytes()).hexdigest().upper()
            matching_lines = [line.upper() for line in evidence_lines if public_name in line]
            self.assertTrue(matching_lines, "Evidence does not name %s" % public_name)
            self.assertTrue(
                any(digest in line for line in matching_lines),
                "Evidence hash for %s is not current (%s)" % (public_name, digest),
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


if __name__ == "__main__":
    unittest.main()
