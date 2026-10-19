from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "spaceclaim-vision-modeling"
SCRIPT = PACKAGE / "scripts" / "validate_geometry_understanding_outputs.py"
SCHEMA = PACKAGE / "references" / "geometry-understanding-output.schema.json"
MANIFEST = PACKAGE / "assets" / "operation-templates" / "evaluation-fixtures" / "geometry-understanding" / "fixture-manifest.json"

SPEC = importlib.util.spec_from_file_location("validate_geometry_understanding_outputs", SCRIPT)
VALIDATOR = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(VALIDATOR)


class GeometryUnderstandingOutputTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.schema = json.loads(SCHEMA.read_text(encoding="utf-8"))

    def test_case_neutral_fixture_manifest_matches_expected_results(self) -> None:
        result = VALIDATOR.evaluate_manifest(ROOT, MANIFEST)
        self.assertEqual(9, result["fixtures_checked"])
        self.assertEqual(0, result["mismatches"], result)
        self.assertIn("no source-interpretation accuracy", result["evidence_boundary"])

    def test_duplicate_ids_are_rejected(self) -> None:
        data = json.loads((MANIFEST.parent / "extract-ready.json").read_text(encoding="utf-8"))
        data["bodies_and_features"][0]["id"] = data["observed_geometry"][0]["id"]
        codes = {item["code"] for item in VALIDATOR.validate_output(data, self.schema)}
        self.assertIn("duplicate_item_id", codes)

    def test_ready_frame_requires_resolved_components(self) -> None:
        data = json.loads((MANIFEST.parent / "frame-underdetermined.json").read_text(encoding="utf-8"))
        data["handoff_status"] = "ready"
        codes = {item["code"] for item in VALIDATOR.validate_output(data, self.schema)}
        self.assertIn("ready_frame_has_unresolved_component", codes)
        self.assertIn("blocking_unresolved_requires_clarification", codes)

    def test_operation_outputs_cannot_mix_atomic_payloads(self) -> None:
        data = json.loads((MANIFEST.parent / "extract-ready.json").read_text(encoding="utf-8"))
        data["dimension_relations"] = []
        codes = {item["code"] for item in VALIDATOR.validate_output(data, self.schema)}
        self.assertIn("schema_violation", codes)

    def test_schema_invalid_nested_types_report_issues_without_crashing(self) -> None:
        data = json.loads((MANIFEST.parent / "frame-ready.json").read_text(encoding="utf-8"))
        data["coordinate_system"]["x_axis"] = "invalid"
        issues = VALIDATOR.validate_output(data, self.schema)
        self.assertIn("schema_violation", {item["code"] for item in issues})

        dimension_data = json.loads((MANIFEST.parent / "dimensions-conflict.json").read_text(encoding="utf-8"))
        dimension_data["dimensions_with_provenance"][0]["id"] = []
        dimension_data["dimensions_with_provenance"][0]["disposition"] = []
        issues = VALIDATOR.validate_output(dimension_data, self.schema)
        self.assertIn("schema_violation", {item["code"] for item in issues})

        extract_data = json.loads((MANIFEST.parent / "extract-ready.json").read_text(encoding="utf-8"))
        extract_data["spatial_relations"][0]["participant_refs"] = None
        issues = VALIDATOR.validate_output(extract_data, self.schema)
        self.assertIn("schema_violation", {item["code"] for item in issues})

        dimension_data = json.loads((MANIFEST.parent / "dimensions-conflict.json").read_text(encoding="utf-8"))
        dimension_data["unresolved_items"][0]["related_refs"] = None
        issues = VALIDATOR.validate_output(dimension_data, self.schema)
        self.assertIn("schema_violation", {item["code"] for item in issues})

    def test_dangling_relation_reference_is_rejected(self) -> None:
        data = json.loads((MANIFEST.parent / "extract-ready.json").read_text(encoding="utf-8"))
        data["spatial_relations"][0]["participant_refs"][1] = "missing-feature"
        codes = {item["code"] for item in VALIDATOR.validate_output(data, self.schema)}
        self.assertIn("dangling_relation_ref", codes)

    def test_manifest_path_escape_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
            manifest["schema_path"] = "../outside.json"
            path = Path(directory) / "manifest.json"
            path.write_text(json.dumps(manifest), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "escapes"):
                VALIDATOR.evaluate_manifest(ROOT, path)

    def test_cli_validates_one_output_and_reports_host_boundary(self) -> None:
        fixture = MANIFEST.parent / "dimensions-ready.json"
        completed = subprocess.run([sys.executable, str(SCRIPT), "--input", str(fixture)], cwd=ROOT, capture_output=True, text=True, check=False)
        self.assertEqual(0, completed.returncode, completed.stderr)
        result = json.loads(completed.stdout)
        self.assertTrue(result["valid"])
        self.assertIn("Host-only", result["evidence_boundary"])

    def test_cli_rejects_invalid_json_document(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "invalid.json"
            path.write_text("{", encoding="utf-8")
            completed = subprocess.run([sys.executable, str(SCRIPT), "--input", str(path)], cwd=ROOT, capture_output=True, text=True, check=False)
        self.assertEqual(2, completed.returncode)
        result = json.loads(completed.stdout)
        self.assertEqual("validation_error", result["issues"][0]["code"])


if __name__ == "__main__":
    unittest.main()
