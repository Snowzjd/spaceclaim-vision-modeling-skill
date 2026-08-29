from __future__ import annotations

import ast
import importlib.util
import json
import re
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
    / "001-offset-block-array"
)
SCRIPT_PATH = CASE_ROOT / "output" / "spaceclaim-v21-build.py"
CONTRACT_PATH = CASE_ROOT / "validation-contract.json"
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


class Case001HostPreparationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.source = SCRIPT_PATH.read_text(encoding="utf-8")
        cls.contract = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))

    def test_candidate_script_is_host_parseable_and_runtime_pending(self) -> None:
        ast.parse(self.source)
        self.assertIn("runtime_pending", self.source)
        self.assertIn('from SpaceClaim.Api.V21 import *', self.source)

    def test_candidate_requires_explicit_new_output_paths(self) -> None:
        self.assertIn("OUTPUT_MODEL_PATH = None", self.source)
        self.assertIn("REPORT_PATH = None", self.source)
        self.assertIn("refusing to overwrite", self.source)

    def test_geometry_validation_precedes_the_only_native_save(self) -> None:
        self.assertEqual(1, self.source.count("DocumentSave.Execute("))
        self.assertLess(
            self.source.index("validate_and_report_geometry(report, named_bodies)"),
            self.source.index("DocumentSave.Execute("),
        )
        self.assertIsNone(re.search(r"\b(?:Body|Face|Edge)\d+\b", self.source))

    def test_candidate_source_passes_static_archive_rules(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            archive_path = Path(directory) / "case-001-candidate.scscript"
            with zipfile.ZipFile(archive_path, "w") as archive:
                archive.writestr("_script", self.source.encode("utf-8"))
                archive.writestr("_apiVersion", b"21")
                archive.writestr("_smartVariableVersion", b"1")
                archive.writestr("_userScriptObjects", b"")
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
        self.assertEqual({"INLET", "OUTLET"}, {item["name"] for item in self.contract["named_face_groups"]})
        self.assertIn("evidence_layers", schema["required"])


if __name__ == "__main__":
    unittest.main()
