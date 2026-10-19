from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = (
    ROOT
    / "spaceclaim-vision-modeling"
    / "scripts"
    / "validate_operation_registry.py"
)
SPEC = importlib.util.spec_from_file_location("validate_operation_registry", MODULE_PATH)
assert SPEC and SPEC.loader
VALIDATOR = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(VALIDATOR)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2), encoding="utf-8")


def evidence_record(status: str, path: str | None = None, digest: str | None = None) -> dict:
    refs = []
    if path is not None and digest is not None:
        refs.append({"path": path, "sha256": digest})
    return {"status": status, "evidence_refs": refs}


def build_fixture(repo: Path, *, status: str = "active", host_passed: bool = True) -> Path:
    package = repo / "spaceclaim-vision-modeling"
    references = package / "references"
    references.mkdir(parents=True, exist_ok=True)
    for name in (
        "operation-template.schema.json",
        "operation-registry.schema.json",
        "operation-evidence.schema.json",
    ):
        (references / name).write_text(
            (ROOT / "spaceclaim-vision-modeling" / "references" / name).read_text(
                encoding="utf-8"
            ),
            encoding="utf-8",
        )
    implementation = package / "scripts" / "tool.py"
    test_artifact = repo / "tests" / "test_tool.py"
    design_evidence = repo / "evidence" / "design.md"
    host_evidence = repo / "evidence" / "host-check.txt"
    for path, content in (
        (implementation, "print('tool')\n"),
        (test_artifact, "def test_tool():\n    assert True\n"),
        (design_evidence, "design review passed\n"),
        (host_evidence, "host checks passed\n"),
    ):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")

    layers = {
        "design_only": evidence_record(
            "passed", "evidence/design.md", sha256(design_evidence)
        ),
        "host_checked": evidence_record(
            "passed" if host_passed else "not_tested",
            "evidence/host-check.txt" if host_passed else None,
            sha256(host_evidence) if host_passed else None,
        ),
        "spaceclaim_execution": evidence_record("not_applicable"),
        "geometry_measurements": evidence_record("not_applicable"),
        "native_save": evidence_record("not_applicable"),
        "native_reopen": evidence_record("not_applicable"),
        "visual_review": evidence_record("not_applicable"),
        "requested_export": evidence_record("not_applicable"),
    }
    operation_id = "modeling_strategy_scripting.package-scscript"
    operation_evidence_relative = (
        "spaceclaim-vision-modeling/assets/operation-templates/evidence/host-check.json"
    )
    operation_evidence_path = repo / operation_evidence_relative
    if host_passed:
        write_json(
            operation_evidence_path,
            {
                "evidence_record_version": 1,
                "operation_id": operation_id,
                "template_version": "0.1.0",
                "recorded_on": "2026-09-03",
                "command": "python -m unittest tests.test_tool -q",
                "result": "passed",
                "exit_code": 0,
                "tests_run": 1,
                "tool": "spaceclaim-vision-modeling/scripts/tool.py",
                "test": "tests/test_tool.py",
                "tool_sha256": sha256(implementation),
                "test_sha256": sha256(test_artifact),
                "artifacts": [
                    {
                        "path": "spaceclaim-vision-modeling/scripts/tool.py",
                        "role": "tool",
                        "sha256": sha256(implementation),
                    },
                    {
                        "path": "tests/test_tool.py",
                        "role": "test",
                        "sha256": sha256(test_artifact),
                    },
                ],
                "evidence_boundary": {
                    layer: {"status": value["status"], "scope": "Fixture boundary."}
                    for layer, value in layers.items()
                },
                "notes": "Synthetic host-check fixture.",
            },
        )
    template = {
        "$schema": "../../references/operation-template.schema.json",
        "operation_id": operation_id,
        "template_version": "0.1.0",
        "contract_version": 1,
        "status": status,
        "stage": "modeling_strategy_scripting",
        "purpose": "Package a prepared source as a deterministic script archive.",
        "trigger": "A version-matched source must be packaged for SpaceClaim.",
        "inputs": [
            {
                "name": "source_path",
                "type": "path",
                "required": True,
                "description": "Prepared source path.",
                "provenance_required": True,
            }
        ],
        "preconditions": ["The source exists and target metadata is known."],
        "outputs": [
            {
                "name": "archive_path",
                "type": "path",
                "required": True,
                "description": "Packaged script archive path.",
            }
        ],
        "postconditions": ["The archive has the deterministic member structure."],
        "implementation": {
            "mode": "host_tool",
            "primary_artifact": "spaceclaim-vision-modeling/scripts/tool.py",
            "target_environment": "Host Python 3",
            "topology_effect": "none",
            "determinism": "deterministic",
        },
        "semantic_selection": {
            "required": False,
            "criteria": [],
            "ambiguity_checks": ["Geometry selection is not used."],
            "topology_refresh": "Not applicable.",
        },
        "failure_modes": [
            {
                "failure_id": "invalid_source",
                "condition": "The source is missing or empty.",
                "detection": "Validate input before packaging.",
                "safe_state": "No output is written.",
            }
        ],
        "recovery": [
            {
                "failure_id": "invalid_source",
                "action": "Repair the source and rerun packaging.",
                "clean_rerun_required": True,
            }
        ],
        "validation": [
            {
                "check": "Archive structure",
                "method": "Run the host test.",
                "expected": "Required members and bytes match.",
                "evidence_layer": "host_checked",
            }
        ],
        "dependencies": [],
        "evidence_level": {"template_version": "0.1.0", "layers": layers},
        "artifact_links": [
            {
                "path": "spaceclaim-vision-modeling/scripts/tool.py",
                "role": "implementation",
                "sha256": sha256(implementation),
            },
            {
                "path": "tests/test_tool.py",
                "role": "test",
                "sha256": sha256(test_artifact),
            },
            *(
                [
                    {
                        "path": operation_evidence_relative,
                        "role": "evidence",
                        "sha256": sha256(operation_evidence_path),
                    }
                ]
                if host_passed
                else []
            ),
        ],
    }
    template_relative = "assets/operation-templates/package-scscript.json"
    template_path = package / template_relative
    write_json(template_path, template)
    registry = {
        "registry_version": 1,
        "architecture_version": "0.3",
        "template_contract_version": 1,
        "stages": list(VALIDATOR.STAGES),
        "extension_points": [
            {
                "extension_id": "source.future-input-adapter",
                "status": "reserved",
                "purpose": "Reserve a future normalized source adapter.",
                "entry_from": "workflow_input",
                "input_contract": "future_source",
                "output_contract": "normalized_source_manifest",
                "reentry_stage": "geometry_understanding",
                "bypass_core_stages": False,
                "contract_path": None,
            }
        ],
        "fallback": {
            "enabled": True,
            "entrypoint": "SKILL.md",
            "conditions": ["No active template matches."],
        },
        "operations": [
            {
                "operation_id": operation_id,
                "stage": "modeling_strategy_scripting",
                "status": status,
                "template_version": "0.1.0",
                "template_path": template_relative,
                "template_sha256": sha256(template_path),
                "trigger_summary": "Package a prepared source.",
                "evidence_layers": [
                    "design_only",
                    *(["host_checked"] if host_passed else []),
                ],
            }
        ],
    }
    registry_path = package / "references" / "operation-registry.json"
    write_json(registry_path, registry)
    return registry_path


class OperationRegistryTests(unittest.TestCase):
    def test_public_registry_passes(self) -> None:
        result = VALIDATOR.validate_registry(ROOT)
        self.assertEqual("passed", result["status"])
        catalog = json.loads((ROOT / "spaceclaim-vision-modeling/references/operation-catalog.json").read_text(encoding="utf-8"))
        backed = [item for item in catalog["operations"] if item["registry_operation_id"] is not None]
        self.assertGreaterEqual(len(backed), 7)
        self.assertEqual(len(backed), result["operations_checked"])
        self.assertEqual(2, result["extensions_checked"])

    def test_malformed_registry_fails_schema_validation(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repo = Path(directory)
            registry = build_fixture(repo)
            write_json(registry, {"operations": []})
            result = VALIDATOR.validate_registry(repo, registry)
        self.assertEqual("failed", result["status"])
        self.assertIn("registry_schema_violation", [item["code"] for item in result["issues"]])

    def test_valid_active_template_passes(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repo = Path(directory)
            registry = build_fixture(repo)
            result = VALIDATOR.validate_registry(repo, registry)
        self.assertEqual([], result["issues"])
        self.assertEqual("passed", result["status"])

    def test_valid_candidate_template_passes_without_host_claim(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repo = Path(directory)
            registry = build_fixture(repo, status="candidate", host_passed=False)
            result = VALIDATOR.validate_registry(repo, registry)
        self.assertEqual("passed", result["status"])

    def test_evidence_version_mismatch_fails(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repo = Path(directory)
            registry = build_fixture(repo)
            registry_data = json.loads(registry.read_text(encoding="utf-8"))
            template_path = repo / "spaceclaim-vision-modeling" / registry_data["operations"][0]["template_path"]
            template = json.loads(template_path.read_text(encoding="utf-8"))
            template["evidence_level"]["template_version"] = "0.0.9"
            write_json(template_path, template)
            result = VALIDATOR.validate_registry(repo, registry)
        self.assertIn("evidence_version_mismatch", [item["code"] for item in result["issues"]])

    def test_template_byte_drift_invalidates_registry_identity(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repo = Path(directory)
            registry = build_fixture(repo)
            registry_data = json.loads(registry.read_text(encoding="utf-8"))
            template_path = repo / "spaceclaim-vision-modeling" / registry_data["operations"][0]["template_path"]
            template = json.loads(template_path.read_text(encoding="utf-8"))
            template["postconditions"].append("A material contract edit changes the template bytes.")
            write_json(template_path, template)
            result = VALIDATOR.validate_registry(repo, registry)
        self.assertIn("template_sha256_mismatch", [item["code"] for item in result["issues"]])

    def test_operation_evidence_identity_must_match_template(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repo = Path(directory)
            registry = build_fixture(repo)
            registry_data = json.loads(registry.read_text(encoding="utf-8"))
            template_path = repo / "spaceclaim-vision-modeling" / registry_data["operations"][0]["template_path"]
            template = json.loads(template_path.read_text(encoding="utf-8"))
            evidence_link = next(
                item for item in template["artifact_links"] if item["role"] == "evidence"
            )
            evidence_path = repo / evidence_link["path"]
            evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
            evidence["operation_id"] = "modeling_strategy_scripting.audit-scscript"
            write_json(evidence_path, evidence)
            evidence_link["sha256"] = sha256(evidence_path)
            write_json(template_path, template)
            registry_data["operations"][0]["template_sha256"] = sha256(template_path)
            write_json(registry, registry_data)
            result = VALIDATOR.validate_registry(repo, registry)
        self.assertIn("evidence_operation_mismatch", [item["code"] for item in result["issues"]])

    def test_layer_cannot_redirect_to_unvalidated_operation_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repo = Path(directory)
            registry = build_fixture(repo)
            registry_data = json.loads(registry.read_text(encoding="utf-8"))
            template_path = repo / "spaceclaim-vision-modeling" / registry_data["operations"][0]["template_path"]
            template = json.loads(template_path.read_text(encoding="utf-8"))
            valid_link = next(
                item for item in template["artifact_links"] if item["role"] == "evidence"
            )
            valid_evidence = json.loads((repo / valid_link["path"]).read_text(encoding="utf-8"))
            valid_evidence["operation_id"] = "modeling_strategy_scripting.audit-scscript"
            wrong_path = repo / "spaceclaim-vision-modeling/assets/operation-templates/evidence/wrong-host-check.json"
            write_json(wrong_path, valid_evidence)
            template["evidence_level"]["layers"]["host_checked"]["evidence_refs"] = [
                {
                    "path": "spaceclaim-vision-modeling/assets/operation-templates/evidence/wrong-host-check.json",
                    "sha256": sha256(wrong_path),
                }
            ]
            write_json(template_path, template)
            registry_data["operations"][0]["template_sha256"] = sha256(template_path)
            write_json(registry, registry_data)
            result = VALIDATOR.validate_registry(repo, registry)
        self.assertIn(
            "unregistered_operation_evidence_ref",
            [item["code"] for item in result["issues"]],
        )

    def test_operation_evidence_artifacts_must_match_template_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repo = Path(directory)
            registry = build_fixture(repo)
            other_tool = repo / "spaceclaim-vision-modeling/scripts/other.py"
            other_test = repo / "tests/test_other.py"
            other_tool.write_text("print('other')\n", encoding="utf-8")
            other_test.write_text("def test_other():\n    assert True\n", encoding="utf-8")
            registry_data = json.loads(registry.read_text(encoding="utf-8"))
            template_path = repo / "spaceclaim-vision-modeling" / registry_data["operations"][0]["template_path"]
            template = json.loads(template_path.read_text(encoding="utf-8"))
            evidence_link = next(
                item for item in template["artifact_links"] if item["role"] == "evidence"
            )
            evidence_path = repo / evidence_link["path"]
            evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
            evidence["tool"] = "spaceclaim-vision-modeling/scripts/other.py"
            evidence["test"] = "tests/test_other.py"
            evidence["tool_sha256"] = sha256(other_tool)
            evidence["test_sha256"] = sha256(other_test)
            evidence["artifacts"] = [
                {
                    "path": evidence["tool"],
                    "role": "tool",
                    "sha256": evidence["tool_sha256"],
                },
                {
                    "path": evidence["test"],
                    "role": "test",
                    "sha256": evidence["test_sha256"],
                },
            ]
            write_json(evidence_path, evidence)
            evidence_link["sha256"] = sha256(evidence_path)
            write_json(template_path, template)
            registry_data["operations"][0]["template_sha256"] = sha256(template_path)
            write_json(registry, registry_data)
            result = VALIDATOR.validate_registry(repo, registry)
        codes = [item["code"] for item in result["issues"]]
        self.assertIn("evidence_primary_artifact_mismatch", codes)
        self.assertIn("evidence_template_artifact_mismatch", codes)

    def test_schema_invalid_template_type_fails(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repo = Path(directory)
            registry = build_fixture(repo)
            registry_data = json.loads(registry.read_text(encoding="utf-8"))
            template_path = repo / "spaceclaim-vision-modeling" / registry_data["operations"][0]["template_path"]
            template = json.loads(template_path.read_text(encoding="utf-8"))
            template["inputs"] = "not-an-array"
            write_json(template_path, template)
            result = VALIDATOR.validate_registry(repo, registry)
        self.assertIn("template_schema_violation", [item["code"] for item in result["issues"]])

    def test_passed_evidence_requires_reference_and_matching_hash(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repo = Path(directory)
            registry = build_fixture(repo)
            registry_data = json.loads(registry.read_text(encoding="utf-8"))
            template_path = repo / "spaceclaim-vision-modeling" / registry_data["operations"][0]["template_path"]
            template = json.loads(template_path.read_text(encoding="utf-8"))
            template["evidence_level"]["layers"]["host_checked"]["evidence_refs"] = []
            write_json(template_path, template)
            unbound = VALIDATOR.validate_registry(repo, registry)
            template["evidence_level"]["layers"]["host_checked"]["evidence_refs"] = [
                {"path": "evidence/host-check.txt", "sha256": "0" * 64}
            ]
            write_json(template_path, template)
            mismatched = VALIDATOR.validate_registry(repo, registry)
        self.assertIn("unbound_evidence", [item["code"] for item in unbound["issues"]])
        self.assertIn("template_schema_violation", [item["code"] for item in unbound["issues"]])
        self.assertIn("sha256_mismatch", [item["code"] for item in mismatched["issues"]])

    def test_duplicate_and_missing_dependency_fail(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repo = Path(directory)
            registry = build_fixture(repo)
            data = json.loads(registry.read_text(encoding="utf-8"))
            data["operations"].append(copy.deepcopy(data["operations"][0]))
            write_json(registry, data)
            duplicate = VALIDATOR.validate_registry(repo, registry)
            data["operations"] = data["operations"][:1]
            template_path = repo / "spaceclaim-vision-modeling" / data["operations"][0]["template_path"]
            template = json.loads(template_path.read_text(encoding="utf-8"))
            template["dependencies"] = ["geometry_understanding.missing-operation"]
            write_json(template_path, template)
            write_json(registry, data)
            missing = VALIDATOR.validate_registry(repo, registry)
        self.assertIn("duplicate_operation_id", [item["code"] for item in duplicate["issues"]])
        self.assertIn("missing_dependency", [item["code"] for item in missing["issues"]])

    def test_null_primary_artifact_requires_reason(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repo = Path(directory)
            registry = build_fixture(repo)
            data = json.loads(registry.read_text(encoding="utf-8"))
            template_path = repo / "spaceclaim-vision-modeling" / data["operations"][0]["template_path"]
            template = json.loads(template_path.read_text(encoding="utf-8"))
            template["implementation"]["primary_artifact"] = None
            write_json(template_path, template)
            result = VALIDATOR.validate_registry(repo, registry)
        self.assertIn("missing_primary_artifact_reason", [item["code"] for item in result["issues"]])
        self.assertIn("template_schema_violation", [item["code"] for item in result["issues"]])

    def test_dependency_cycle_is_rejected(self) -> None:
        issues = []
        VALIDATOR.find_dependency_cycles(
            {
                "geometry_understanding.first": ["geometry_understanding.second"],
                "geometry_understanding.second": ["geometry_understanding.first"],
            },
            issues,
        )
        self.assertIn("dependency_cycle", [item["code"] for item in issues])

    def test_stage_mismatch_and_missing_artifact_fail(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repo = Path(directory)
            registry = build_fixture(repo)
            data = json.loads(registry.read_text(encoding="utf-8"))
            template_path = repo / "spaceclaim-vision-modeling" / data["operations"][0]["template_path"]
            template = json.loads(template_path.read_text(encoding="utf-8"))
            template["stage"] = "validation_visual_review"
            template["artifact_links"][0]["path"] = "spaceclaim-vision-modeling/scripts/missing.py"
            template["artifact_links"][0].pop("sha256", None)
            write_json(template_path, template)
            result = VALIDATOR.validate_registry(repo, registry)
        codes = [item["code"] for item in result["issues"]]
        self.assertIn("registry_template_mismatch", codes)
        self.assertIn("operation_stage_mismatch", codes)
        self.assertIn("missing_artifact", codes)

    def test_absolute_path_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            issues = []
            resolved = VALIDATOR.resolve_repo_path(
                Path(directory), "C:/outside/file.json", "$.path", issues
            )
        self.assertIsNone(resolved)
        self.assertIn("absolute_path", [item["code"] for item in issues])

    def test_duplicate_extension_id_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repo = Path(directory)
            registry = build_fixture(repo)
            data = json.loads(registry.read_text(encoding="utf-8"))
            data["extension_points"].append(copy.deepcopy(data["extension_points"][0]))
            write_json(registry, data)
            result = VALIDATOR.validate_registry(repo, registry)
        self.assertIn("duplicate_extension_id", [item["code"] for item in result["issues"]])


if __name__ == "__main__":
    unittest.main()
