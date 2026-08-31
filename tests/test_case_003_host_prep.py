from __future__ import annotations

import ast
import importlib.util
import json
import re
import tempfile
import unittest
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


if __name__ == "__main__":
    unittest.main()
