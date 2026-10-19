from __future__ import annotations

import ast
import importlib.util
import unittest
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "spaceclaim-vision-modeling"
TEMPLATES = PACKAGE / "assets" / "operation-templates" / "modeling-strategy-scripting"
EXTRUDE_SOURCE = TEMPLATES / "extrude-planar-profile.py"
TRANSLATE_SOURCE = TEMPLATES / "translate-body.py"
EXTRUDE_SCSCRIPT = EXTRUDE_SOURCE.with_suffix(".scscript")
TRANSLATE_SCSCRIPT = TRANSLATE_SOURCE.with_suffix(".scscript")


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


AUDITOR = load_module("atomic_action_auditor", PACKAGE / "scripts" / "audit_scscript.py")


class AtomicModelingActionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.extrude = EXTRUDE_SOURCE.read_text(encoding="utf-8")
        cls.translate = TRANSLATE_SOURCE.read_text(encoding="utf-8")

    def test_sources_are_v21_ironpython_parseable_and_case_neutral(self) -> None:
        for source in (self.extrude, self.translate):
            ast.parse(source)
            self.assertIn("from SpaceClaim.Api.V21 import *", source)
            self.assertNotRegex(source, r"\b(?:Body|Face|Edge)\d+\b")
            for token in (
                "case-001",
                "case-002",
                "case-003",
                "case-004",
                "rectangular-prism",
            ):
                self.assertNotIn(token, source)

    def test_extrude_template_contains_only_the_target_modeling_action(self) -> None:
        self.assertIn("ModelerBody.ExtrudeProfile", self.extrude)
        self.assertIn("DesignBody.Create", self.extrude)
        for forbidden in (
            "Move.Translate",
            "Move.Rotate",
            "Combine.",
            "DocumentSave.Execute",
            "Copy.Execute",
        ):
            self.assertNotIn(forbidden, self.extrude)
        self.assertIn("PROFILE_KIND = None", self.extrude)
        self.assertIn("EXTRUSION_DISTANCE_MM = None", self.extrude)

    def test_translate_template_contains_only_the_target_modeling_action(self) -> None:
        self.assertEqual(1, self.translate.count("Move.Translate("))
        for forbidden in (
            "ExtrudeProfile",
            "DesignBody.Create",
            "Move.Rotate",
            "Combine.",
            "DocumentSave.Execute",
            "Copy.Execute",
        ):
            self.assertNotIn(forbidden, self.translate)
        self.assertIn("TRANSLATION_DISTANCE_MM = None", self.translate)
        self.assertIn("EXPECTED_BEFORE_BBOX_MM = None", self.translate)

    def test_translate_reenumerates_and_checks_observable_postconditions(self) -> None:
        operation_index = self.translate.index("Move.Translate(")
        reselect_index = self.translate.index(
            "moved = resolve_unique_body(expected_after_bbox())", operation_index
        )
        self.assertLess(operation_index, reselect_index)
        self.assertIn("Translation changed the target body volume", self.translate)

    def test_packages_embed_exact_sources_and_v21_metadata(self) -> None:
        for source_path, archive_path in (
            (EXTRUDE_SOURCE, EXTRUDE_SCSCRIPT),
            (TRANSLATE_SOURCE, TRANSLATE_SCSCRIPT),
        ):
            with zipfile.ZipFile(archive_path) as archive:
                self.assertEqual(source_path.read_bytes(), archive.read("_script"))
                self.assertEqual(b"21", archive.read("_apiVersion"))

    def test_packages_pass_action_specific_static_audit(self) -> None:
        extrude = AUDITOR.audit_archive(
            EXTRUDE_SCSCRIPT,
            require_api="21",
            forbid_numbered_aliases=True,
            required_operations=("ModelerBody.ExtrudeProfile",),
            forbidden_operations=("Move.Translate", "Move.Rotate", "Combine.Merge"),
        )
        translate = AUDITOR.audit_archive(
            TRANSLATE_SCSCRIPT,
            require_api="21",
            forbid_numbered_aliases=True,
            required_operations=("Move.Translate",),
            forbidden_operations=("ModelerBody.ExtrudeProfile", "Move.Rotate", "Combine.Merge"),
        )
        self.assertEqual("passed", extrude["status"], extrude["issues"])
        self.assertEqual("passed", translate["status"], translate["issues"])


if __name__ == "__main__":
    unittest.main()
