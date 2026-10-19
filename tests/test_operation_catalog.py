from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "spaceclaim-vision-modeling" / "scripts" / "validate_operation_catalog.py"
SPEC = importlib.util.spec_from_file_location("validate_operation_catalog", MODULE_PATH)
assert SPEC and SPEC.loader
VALIDATOR = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(VALIDATOR)


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")


def expected_ids() -> list[str]:
    ranges = {"GU": 20, "MS": 11, "MA": 35, "EX": 14, "ER": 12, "VA": 25, "VI": 22}
    return [
        "%s-%02d" % (prefix, number)
        for prefix, count in ranges.items()
        for number in range(1, count + 1)
    ]


def fixture_catalog() -> dict:
    operations = []
    for operation_id in expected_ids():
        prefix = operation_id[:2]
        stage = VALIDATOR.PREFIX_TO_STAGE[prefix]
        operation = {
            "id": operation_id,
            "stage": stage,
            "name": "测试动作%s" % operation_id,
            "operation": "catalog-operation-%s" % operation_id.lower(),
            "inputs": ["输入契约"],
            "output": "输出契约",
            "preconditions": ["前置条件已满足"],
            "postcondition": "后置条件可检查",
            "topology_effect": "none",
            "required_evidence": ["interpretation_evaluation"],
            "lifecycle": "catalogued",
            "registry_operation_id": None,
            "implementation_scope": "仅声明目录范围，不执行主机操作。",
        }
        operations.append(operation)

    # Back these two entries so tests exercise lifecycle/registry matching in
    # the passing fixture without depending on real template names or hashes.
    operations[0]["lifecycle"] = "active"
    operations[0]["registry_operation_id"] = "geometry_understanding.gu-01"
    operations[20]["lifecycle"] = "candidate"
    operations[20]["registry_operation_id"] = "modeling_strategy_scripting.ms-01"
    return {
        "catalog_version": 1,
        "architecture_version": "0.3",
        "stages": list(VALIDATOR.STAGES),
        "operations": operations,
    }


def fixture_registry() -> dict:
    return {
        "stages": list(VALIDATOR.STAGES),
        "operations": [
            {
                "operation_id": "geometry_understanding.gu-01",
                "stage": "geometry_understanding",
                "status": "active",
            },
            {
                "operation_id": "modeling_strategy_scripting.ms-01",
                "stage": "modeling_strategy_scripting",
                "status": "candidate",
            },
        ],
    }


class OperationCatalogValidationTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tempdir = tempfile.TemporaryDirectory()
        self.repo = Path(self._tempdir.name)
        self.catalog_path = self.repo / "spaceclaim-vision-modeling" / "references" / "operation-catalog.json"
        write_json(self.catalog_path, fixture_catalog())
        write_json(self.repo / "spaceclaim-vision-modeling" / "references" / "operation-registry.json", fixture_registry())

    def tearDown(self) -> None:
        self._tempdir.cleanup()

    def validate(self, catalog: dict | None = None) -> dict:
        if catalog is not None:
            write_json(self.catalog_path, catalog)
        return VALIDATOR.validate_catalog(self.repo, self.catalog_path)

    def test_complete_fixture_passes(self) -> None:
        result = self.validate()
        self.assertEqual("passed", result["status"], result["issues"])
        self.assertEqual(139, result["counts"]["operations"])
        self.assertEqual(2, result["counts"]["registry_operations"])

    def test_duplicate_and_missing_ids_fail(self) -> None:
        catalog = fixture_catalog()
        catalog["operations"][1]["id"] = catalog["operations"][0]["id"]
        result = self.validate(catalog)
        codes = [item["code"] for item in result["issues"]]
        self.assertIn("duplicate_operation_id", codes)
        self.assertIn("missing_operation_id", codes)

    def test_stage_drift_fails(self) -> None:
        catalog = fixture_catalog()
        catalog["operations"][0]["stage"] = "execution_recovery"
        result = self.validate(catalog)
        self.assertIn("operation_stage_mismatch", [item["code"] for item in result["issues"]])

    def test_active_without_registry_backing_fails(self) -> None:
        catalog = fixture_catalog()
        catalog["operations"][0]["registry_operation_id"] = None
        result = self.validate(catalog)
        codes = [item["code"] for item in result["issues"]]
        self.assertIn("lifecycle_missing_registry_binding", codes)
        self.assertIn("registry_operation_unaccounted", codes)

    def test_registry_entry_must_be_accounted_for(self) -> None:
        registry = fixture_registry()
        registry["operations"].append(
            {
                "operation_id": "execution_recovery.extra",
                "stage": "execution_recovery",
                "status": "active",
            }
        )
        write_json(self.repo / "spaceclaim-vision-modeling" / "references" / "operation-registry.json", registry)
        result = self.validate()
        self.assertIn("registry_operation_unaccounted", [item["code"] for item in result["issues"]])

    def test_invalid_field_types_and_boolean_version_fail(self) -> None:
        catalog = fixture_catalog()
        catalog["catalog_version"] = True
        catalog["operations"][0]["inputs"] = "not-an-array"
        catalog["operations"][1]["required_evidence"] = ["host_checked", 3]
        result = self.validate(catalog)
        codes = [item["code"] for item in result["issues"]]
        self.assertIn("invalid_catalog_version", codes)
        self.assertIn("invalid_field_type", codes)

    def test_empty_required_evidence_fails(self) -> None:
        catalog = fixture_catalog()
        catalog["operations"][0]["required_evidence"] = []
        result = self.validate(catalog)
        self.assertIn("empty_required_evidence", [item["code"] for item in result["issues"]])

    def test_unhashable_lifecycle_reports_error_without_crash(self) -> None:
        catalog = fixture_catalog()
        catalog["operations"][0]["lifecycle"] = []
        result = self.validate(catalog)
        self.assertEqual("failed", result["status"])
        self.assertIn("invalid_field_type", [item["code"] for item in result["issues"]])

    def test_malformed_and_unreadable_catalog_fail_cleanly(self) -> None:
        self.catalog_path.write_text("{not-json", encoding="utf-8")
        malformed = VALIDATOR.validate_catalog(self.repo, self.catalog_path)
        self.assertEqual("failed", malformed["status"])
        self.assertIn("catalog_load_failed", [item["code"] for item in malformed["issues"]])

        self.catalog_path.unlink()
        unreadable = VALIDATOR.validate_catalog(self.repo, self.catalog_path)
        self.assertEqual("failed", unreadable["status"])
        self.assertIn("catalog_load_failed", [item["code"] for item in unreadable["issues"]])

    def test_catalogued_operation_cannot_bind_registry(self) -> None:
        catalog = fixture_catalog()
        catalog["operations"][2]["registry_operation_id"] = "geometry_understanding.gu-01"
        result = self.validate(catalog)
        self.assertIn("catalogued_registry_binding", [item["code"] for item in result["issues"]])

    def test_real_catalog_passes_when_present(self) -> None:
        catalog_path = ROOT / "spaceclaim-vision-modeling" / "references" / "operation-catalog.json"
        if not catalog_path.is_file():
            self.skipTest("The P1 catalog is being prepared by the catalog owner.")
        result = VALIDATOR.validate_catalog(ROOT)
        self.assertEqual("passed", result["status"], result["issues"])


if __name__ == "__main__":
    unittest.main()
