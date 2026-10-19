from __future__ import annotations

import ast
import copy
import hashlib
import importlib.util
import json
import tempfile
import unittest
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "spaceclaim-vision-modeling"
CASE = PACKAGE / "assets" / "atomic-cases" / "001-rectangular-prism"
CONTRACT = CASE / "stages" / "01-geometry-understanding" / "geometry-contract.json"
BUILD_SOURCE = CASE / "stages" / "02-modeling-strategy-scripting" / "output" / "create-rectangular-prism.py"
BUILD_SCSCRIPT = BUILD_SOURCE.with_suffix(".scscript")
VALIDATION_SOURCE = CASE / "stages" / "04-validation-visual-review" / "output" / "validate-rectangular-prism.py"
VALIDATION_SCSCRIPT = VALIDATION_SOURCE.with_suffix(".scscript")
VALIDATION_CONTRACT = CASE / "validation-contract.json"
FORWARD_REPORT = CASE / "stages" / "04-validation-visual-review" / "evidence" / "forward-runtime-report.json"
VALIDATION_REPORT = CASE / "stages" / "04-validation-visual-review" / "evidence" / "validation-runtime-report.json"
RUNTIME_EVIDENCE = CASE / "stages" / "04-validation-visual-review" / "evidence" / "runtime-evidence.json"


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


CONTRACT_VALIDATOR = load_module(
    "atomic_rectangular_contract_validator",
    PACKAGE / "scripts" / "validate_rectangular_prism_contract.py",
)
GENERATOR = load_module(
    "atomic_rectangular_generator",
    PACKAGE / "scripts" / "generate_rectangular_prism_scscript.py",
)
AUDITOR = load_module(
    "atomic_rectangular_auditor", PACKAGE / "scripts" / "audit_scscript.py"
)
RUNTIME_VALIDATOR = load_module(
    "atomic_rectangular_runtime_validator",
    PACKAGE / "scripts" / "validate_runtime_report.py",
)


class AtomicRectangularPrismTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
        cls.build_source = BUILD_SOURCE.read_text(encoding="utf-8")
        cls.validation_source = VALIDATION_SOURCE.read_text(encoding="utf-8")

    def test_geometry_contract_passes_schema_source_and_derived_checks(self) -> None:
        result = CONTRACT_VALIDATOR.validate_contract(self.contract)
        self.assertEqual("passed", result["status"], result["issues"])
        self.assertEqual([50.0, 25.0, 14.0], result["derived"]["bbox_max_mm"])
        self.assertEqual(14400.0, result["derived"]["volume_mm3"])

    def test_geometry_contract_rejects_non_positive_size(self) -> None:
        contract = copy.deepcopy(self.contract)
        contract["primitive"]["size_mm"][1] = 0.0
        result = CONTRACT_VALIDATOR.validate_contract(contract, verify_sources=False)
        self.assertEqual("failed", result["status"])
        self.assertIn("schema_violation", {item["code"] for item in result["issues"]})

    def test_geometry_contract_rejects_mismatched_bbox_and_volume(self) -> None:
        contract = copy.deepcopy(self.contract)
        contract["expected_geometry"]["bbox_max_mm"][0] += 1.0
        contract["expected_geometry"]["volume_mm3"] += 1.0
        result = CONTRACT_VALIDATOR.validate_contract(contract, verify_sources=False)
        codes = {item["code"] for item in result["issues"]}
        self.assertIn("bbox_max_mismatch", codes)
        self.assertIn("volume_mismatch", codes)

    def test_geometry_contract_rejects_unknown_provenance_source(self) -> None:
        contract = copy.deepcopy(self.contract)
        contract["primitive"]["provenance"]["size_mm"]["source_ids"] = ["missing-source"]
        result = CONTRACT_VALIDATOR.validate_contract(contract, verify_sources=False)
        self.assertIn("unknown_source_id", {item["code"] for item in result["issues"]})

    def test_case_source_hash_is_bound_and_current(self) -> None:
        source = self.contract["source_manifest"][0]
        source_path = ROOT / source["path"]
        self.assertEqual(source["sha256"], hashlib.sha256(source_path.read_bytes()).hexdigest())

    def test_committed_sources_are_ironpython_parseable_and_centralized(self) -> None:
        for source in (self.build_source, self.validation_source):
            ast.parse(source)
            self.assertIn("from SpaceClaim.Api.V21 import *", source)
            self.assertEqual(1, source.count("BODY_NAME = "))
            self.assertEqual(1, source.count("MINIMUM_CORNER_MM = "))
            self.assertEqual(1, source.count("SIZE_MM = "))
            self.assertNotRegex(source, r"\b(?:Body|Face|Edge)\d+\b")

    def test_build_source_reenumerates_and_validates_before_save(self) -> None:
        self.assertIn("BlockBody.Create", self.build_source)
        self.assertGreaterEqual(self.build_source.count("bodies = current_bodies()"), 2)
        self.assertEqual(1, self.build_source.count("DocumentSave.Execute("))
        self.assertLess(
            self.build_source.index("validate_body(bodies[0])"),
            self.build_source.index("DocumentSave.Execute("),
        )

    def test_validation_source_is_read_only(self) -> None:
        for forbidden in (
            "BlockBody.Create",
            "RenameObject.Execute",
            "DocumentSave.Execute",
            "NamedSelection.Create",
        ):
            self.assertNotIn(forbidden, self.validation_source)
        self.assertIn("validate_body(body)", self.validation_source)

    def test_committed_scscript_packages_embed_exact_neighbor_sources(self) -> None:
        for source_path, archive_path in (
            (BUILD_SOURCE, BUILD_SCSCRIPT),
            (VALIDATION_SOURCE, VALIDATION_SCSCRIPT),
        ):
            with zipfile.ZipFile(archive_path) as archive:
                self.assertEqual(source_path.read_bytes(), archive.read("_script"))
                self.assertEqual(b"21", archive.read("_apiVersion"))

    def test_build_and_validation_packages_pass_bounded_static_audit(self) -> None:
        build = AUDITOR.audit_archive(
            BUILD_SCSCRIPT,
            require_api="21",
            forbid_numbered_aliases=True,
            required_operations=("BlockBody.Create", "DocumentSave.Execute"),
        )
        validation = AUDITOR.audit_archive(
            VALIDATION_SCSCRIPT,
            require_api="21",
            forbid_numbered_aliases=True,
            forbidden_operations=("BlockBody.Create", "DocumentSave.Execute"),
        )
        self.assertEqual("passed", build["status"], build["issues"])
        self.assertEqual("passed", validation["status"], validation["issues"])

    def test_generator_can_replace_case_values_without_template_edits(self) -> None:
        contract = copy.deepcopy(self.contract)
        contract["primitive"]["body_name"] = "SECOND_PRISM"
        contract["primitive"]["minimum_corner_mm"] = [-3.0, 4.0, 5.0]
        contract["primitive"]["size_mm"] = [7.0, 8.0, 9.0]
        contract["expected_geometry"] = {
            "body_count": 1,
            "bbox_min_mm": [-3.0, 4.0, 5.0],
            "bbox_max_mm": [4.0, 12.0, 14.0],
            "volume_mm3": 504.0,
        }
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            contract_path = root / "contract.json"
            contract_path.write_text(json.dumps(contract), encoding="utf-8")
            source_path = root / "build.py"
            archive_path = root / "build.scscript"
            GENERATOR.generate(
                contract_path,
                "build",
                source_path,
                archive_path,
                root / "run",
            )
            source = source_path.read_text(encoding="utf-8")
            self.assertIn('BODY_NAME = "SECOND_PRISM"', source)
            self.assertIn("MINIMUM_CORNER_MM = [-3.0,4.0,5.0]", source)
            self.assertIn("SIZE_MM = [7.0,8.0,9.0]", source)
            self.assertTrue(archive_path.is_file())

    def test_generator_refuses_output_collision(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "same.scscript"
            output.write_bytes(b"existing")
            with self.assertRaises(FileExistsError):
                GENERATOR.generate(CONTRACT, "build", Path(directory) / "source.py", output, Path(directory) / "run")
            self.assertEqual(b"existing", output.read_bytes())

    def test_validation_contract_is_single_body_and_case_only(self) -> None:
        contract = json.loads(VALIDATION_CONTRACT.read_text(encoding="utf-8"))
        self.assertEqual(1, len(contract["bodies"]))
        self.assertEqual([], contract["named_face_groups"])
        self.assertEqual([], contract["features"])
        self.assertNotIn("INLET", json.dumps(contract))
        self.assertNotIn("OUTLET", json.dumps(contract))

    def test_stage_three_and_four_record_completed_runtime(self) -> None:
        execution = json.loads(
            (CASE / "stages" / "03-execution-recovery" / "execution-contract.json").read_text(encoding="utf-8")
        )
        acceptance = json.loads(
            (CASE / "stages" / "04-validation-visual-review" / "acceptance-contract.json").read_text(encoding="utf-8")
        )
        evidence = json.loads(RUNTIME_EVIDENCE.read_text(encoding="utf-8"))
        self.assertEqual("passed", execution["handoff_status"])
        self.assertEqual(1, execution["executed_artifact_identity"]["run_count"])
        self.assertEqual(
            hashlib.sha256(BUILD_SCSCRIPT.read_bytes()).hexdigest(),
            execution["executed_artifact_identity"]["sha256"],
        )
        self.assertEqual("passed", execution["save_state"])
        self.assertEqual("passed", acceptance["overall_status"])
        self.assertEqual("passed", acceptance["native_reopen_result"])
        self.assertEqual("passed", acceptance["visual_agreement"])
        self.assertEqual(
            {
                "spaceclaim_execution": "passed",
                "geometry_measurements": "passed",
                "native_save": "passed",
                "native_reopen": "passed",
                "visual_review": "passed",
                "requested_export": "not_applicable",
            },
            evidence["evidence_layers"],
        )

    def test_sanitized_forward_and_reopen_reports_pass_case_contract(self) -> None:
        contract = RUNTIME_VALIDATOR.load_json(VALIDATION_CONTRACT)
        for path in (FORWARD_REPORT, VALIDATION_REPORT):
            report = RUNTIME_VALIDATOR.load_json(path)
            result = RUNTIME_VALIDATOR.validate_report(report, contract=contract)
            self.assertEqual("passed", result["status"], result["issues"])
            self.assertEqual(path.name, report["outputs"]["report_path"])
            self.assertNotRegex(json.dumps(report), r"[A-Za-z]:[/\\]")

    def test_runtime_evidence_binds_exact_external_artifact_hashes_without_absolute_paths(self) -> None:
        evidence = json.loads(RUNTIME_EVIDENCE.read_text(encoding="utf-8"))
        self.assertEqual(
            hashlib.sha256(BUILD_SCSCRIPT.read_bytes()).hexdigest(),
            evidence["exact_artifacts"]["build_scscript"]["sha256"],
        )
        self.assertEqual(
            hashlib.sha256(VALIDATION_SCSCRIPT.read_bytes()).hexdigest(),
            evidence["exact_artifacts"]["validation_scscript"]["sha256"],
        )
        self.assertFalse(evidence["exact_artifacts"]["native_model"]["repository_bundled"])
        self.assertNotRegex(json.dumps(evidence), r"[A-Za-z]:[/\\]")


if __name__ == "__main__":
    unittest.main()
