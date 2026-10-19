from __future__ import annotations

import json
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "spaceclaim-vision-modeling"
REFERENCES = PACKAGE / "references"


class V03ArchitectureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.skill = (PACKAGE / "SKILL.md").read_text(encoding="utf-8")
        cls.architecture = (REFERENCES / "architecture.md").read_text(encoding="utf-8")
        cls.contract = (REFERENCES / "operation-template-contract.md").read_text(
            encoding="utf-8"
        )
        cls.template_schema = json.loads(
            (REFERENCES / "operation-template.schema.json").read_text(encoding="utf-8")
        )
        cls.registry_schema = json.loads(
            (REFERENCES / "operation-registry.schema.json").read_text(encoding="utf-8")
        )
        cls.evidence_schema = json.loads(
            (REFERENCES / "operation-evidence.schema.json").read_text(encoding="utf-8")
        )
        cls.registry = json.loads(
            (REFERENCES / "operation-registry.json").read_text(encoding="utf-8")
        )

    def test_four_stages_are_frozen_in_order(self) -> None:
        expected = [
            "geometry_understanding",
            "modeling_strategy_scripting",
            "execution_recovery",
            "validation_visual_review",
        ]
        self.assertEqual(expected, self.registry["stages"])
        for heading in (
            "Geometry understanding",
            "Modeling strategy and scripting",
            "Execution and recovery",
            "Validation and visual review",
        ):
            self.assertIn(heading, self.architecture)

    def test_extension_hooks_do_not_change_the_four_core_stages(self) -> None:
        extensions = self.registry["extension_points"]
        self.assertEqual(
            {
                "source.video-temporal-observation",
                "learning.demonstrated-modeling-candidate",
            },
            {item["extension_id"] for item in extensions},
        )
        for item in extensions:
            self.assertEqual("reserved", item["status"])
            self.assertFalse(item["bypass_core_stages"])
            self.assertEqual("geometry_understanding", item["reentry_stage"])
        self.assertIn("video or screen recording", self.architecture)
        self.assertIn("## Extension-stage protocol", self.architecture)

    def test_skill_routes_to_architecture_and_atomic_contract(self) -> None:
        for path in (
            "references/architecture.md",
            "references/operation-template-contract.md",
            "references/operation-template.schema.json",
            "references/operation-registry.json",
            "references/operation-registry.schema.json",
            "references/operation-evidence.schema.json",
        ):
            self.assertIn(path, self.skill)

    def test_skill_routes_directly_to_each_stage_library(self) -> None:
        for path in (
            "references/geometry-understanding-operations.md",
            "references/modeling-strategy-scripting-operations.md",
            "references/execution-recovery-operations.md",
            "references/validation-visual-review-operations.md",
        ):
            self.assertIn(path, self.skill)
            self.assertTrue((PACKAGE / path).exists())

    def test_skill_exposes_four_stage_workflow_in_order(self) -> None:
        headings = (
            "### 1. Geometry understanding",
            "### 2. Modeling strategy and scripting",
            "### 3. Execution and recovery",
            "### 4. Validation and visual review",
        )
        positions = [self.skill.index(heading) for heading in headings]
        self.assertEqual(positions, sorted(positions))
        self.assertNotIn("### 5.", self.skill)

    def test_initial_active_set_is_host_only(self) -> None:
        operations = [
            item for item in self.registry["operations"] if item["status"] == "active"
        ]
        self.assertEqual(
            {
                "modeling_strategy_scripting.package-scscript",
                "modeling_strategy_scripting.audit-scscript",
                "validation_visual_review.validate-runtime-report-schema",
                "validation_visual_review.compare-runtime-report-to-contract",
                "validation_visual_review.compare-runtime-reports",
            },
            {item["operation_id"] for item in operations},
        )
        for item in operations:
            self.assertEqual("active", item["status"])
            self.assertEqual(["design_only", "host_checked"], item["evidence_layers"])

    def test_broad_migration_drafts_are_not_registered(self) -> None:
        draft_ids = {
            "geometry_understanding.extract-geometry-observations",
            "geometry_understanding.reconcile-dimensions",
            "execution_recovery.execute-script-in-clean-design",
        }
        operation_ids = {item["operation_id"] for item in self.registry["operations"]}
        self.assertTrue(draft_ids.isdisjoint(operation_ids))
        retained_paths = (
            "assets/operation-templates/geometry-understanding/extract-geometry-observations.json",
            "assets/operation-templates/geometry-understanding/reconcile-dimensions.json",
            "assets/operation-templates/geometry-understanding/define-coordinate-frame.json",
            "assets/operation-templates/execution-recovery/execute-script-in-clean-design.json",
        )
        for path in retained_paths:
            self.assertTrue((PACKAGE / path).exists())
        self.assertIn("unregistered migration", self.architecture.lower())

    def test_frame_replacement_does_not_reuse_legacy_draft(self) -> None:
        entry = next(item for item in self.registry["operations"] if item["operation_id"] == "geometry_understanding.define-coordinate-frame")
        self.assertEqual("0.3.1", entry["template_version"])
        self.assertIn("/atoms/", entry["template_path"])
        template = json.loads((PACKAGE / entry["template_path"]).read_text(encoding="utf-8"))
        self.assertEqual(1, len(template["outputs"]))
        self.assertNotIn("geometry-understanding-output.schema.json", template["output_schema"]["path"])

    def test_runtime_report_validation_is_two_atomic_operations(self) -> None:
        by_id = {item["operation_id"]: item for item in self.registry["operations"]}
        schema_id = "validation_visual_review.validate-runtime-report-schema"
        contract_id = "validation_visual_review.compare-runtime-report-to-contract"
        self.assertTrue({schema_id, contract_id}.issubset(by_id))
        schema_template = json.loads(
            (PACKAGE / by_id[schema_id]["template_path"]).read_text(encoding="utf-8")
        )
        contract_template = json.loads(
            (PACKAGE / by_id[contract_id]["template_path"]).read_text(encoding="utf-8")
        )
        self.assertEqual([], schema_template["dependencies"])
        self.assertEqual([schema_id], contract_template["dependencies"])
        self.assertEqual(1, len(schema_template["outputs"]))
        self.assertEqual(1, len(contract_template["outputs"]))

    def test_first_modeling_atoms_are_independent_action_candidates(self) -> None:
        expected = [
            "modeling_strategy_scripting.extrude-planar-profile",
            "modeling_strategy_scripting.translate-body",
        ]
        by_id = {item["operation_id"]: item for item in self.registry["operations"]}
        self.assertTrue(set(expected).issubset(by_id))
        for operation_id in expected:
            self.assertEqual("candidate", by_id[operation_id]["status"])
            self.assertEqual(
                "modeling_strategy_scripting", by_id[operation_id]["stage"]
            )

        templates = {
            operation_id: json.loads(
                (PACKAGE / by_id[operation_id]["template_path"]).read_text(encoding="utf-8")
            )
            for operation_id in expected
        }
        for template in templates.values():
            self.assertEqual([], template["dependencies"])
            self.assertEqual("spaceclaim_scscript", template["implementation"]["mode"])
            self.assertTrue(template["implementation"]["primary_artifact"].endswith(".scscript"))
            self.assertEqual(
                "passed",
                template["evidence_level"]["layers"]["spaceclaim_execution"]["status"],
            )
            self.assertTrue(template["evidence_level"]["layers"]["spaceclaim_execution"]["evidence_refs"])

        self.assertEqual(
            {"profile", "distance_mm"},
            {field["name"] for field in templates[expected[0]]["inputs"]},
        )
        self.assertIn("delta_mm", {field["name"] for field in templates[expected[1]]["inputs"]})

    def test_case_shaped_operations_are_not_registered(self) -> None:
        operation_ids = {item["operation_id"] for item in self.registry["operations"]}
        self.assertTrue(
            {
                "geometry_understanding.interpret-rectangular-prism",
                "modeling_strategy_scripting.create-rectangular-prism-scscript",
                "validation_visual_review.validate-rectangular-prism",
            }.isdisjoint(operation_ids)
        )

    def test_full_workflow_remains_the_fallback(self) -> None:
        self.assertTrue(self.registry["fallback"]["enabled"])
        self.assertEqual("SKILL.md", self.registry["fallback"]["entrypoint"])
        self.assertIn("v0.2 workflow", self.architecture)
        self.assertIn("generic v0.2 workflow", self.architecture)
        self.assertIn("keep this full workflow as the fallback", self.skill)

    def test_template_contract_requires_normative_fields(self) -> None:
        required = set(self.template_schema["required"])
        expected = {
            "operation_id",
            "stage",
            "purpose",
            "trigger",
            "inputs",
            "preconditions",
            "outputs",
            "postconditions",
            "implementation",
            "semantic_selection",
            "failure_modes",
            "recovery",
            "validation",
            "dependencies",
            "evidence_level",
            "artifact_links",
        }
        self.assertTrue(expected.issubset(required))
        for field in expected:
            self.assertRegex(self.contract, r"(?m)^- `?%s`?" % re.escape(field))

    def test_registry_has_no_case_specific_operations(self) -> None:
        registry = json.loads(json.dumps(self.registry))
        for operation in registry["operations"]:
            operation.pop("template_sha256", None)
        text = json.dumps(registry, ensure_ascii=False)
        for token in (
            "001",
            "002",
            "003",
            "004",
            "INLET",
            "OUTLET",
            "rectangular-prism",
            "flanged-short-pipe",
            "stepped-shaft",
            "rounded-plate",
        ):
            self.assertNotIn(token, text)

    def test_registry_schema_requires_fallback_and_operations(self) -> None:
        required = set(self.registry_schema["required"])
        self.assertTrue(
            {"stages", "extension_points", "fallback", "operations"}.issubset(required)
        )
        operation_required = set(
            self.registry_schema["properties"]["operations"]["items"]["required"]
        )
        self.assertIn("template_sha256", operation_required)

    def test_host_evidence_schema_tracks_identity_and_all_layers(self) -> None:
        required = set(self.evidence_schema["required"])
        self.assertTrue(
            {
                "operation_id",
                "template_version",
                "tool_sha256",
                "test_sha256",
                "evidence_boundary",
            }.issubset(required)
        )
        boundary = self.evidence_schema["properties"]["evidence_boundary"]
        self.assertEqual(
            {
                "design_only",
                "host_checked",
                "spaceclaim_execution",
                "geometry_measurements",
                "native_save",
                "native_reopen",
                "visual_review",
                "requested_export",
            },
            set(boundary["required"]),
        )

    def test_template_evidence_tracks_every_layer_separately(self) -> None:
        layers = self.template_schema["$defs"]["evidence_level"]["properties"][
            "layers"
        ]
        self.assertEqual(
            {
                "design_only",
                "host_checked",
                "spaceclaim_execution",
                "geometry_measurements",
                "native_save",
                "native_reopen",
                "visual_review",
                "requested_export",
            },
            set(layers["required"]),
        )
        record = self.template_schema["$defs"]["evidence_record"]
        self.assertIn("allOf", record)
        self.assertEqual(
            {"path", "sha256"},
            set(self.template_schema["$defs"]["evidence_ref"]["required"]),
        )

    def test_v02_evidence_mapping_is_explicit(self) -> None:
        self.assertIn("## Evidence taxonomy compatibility", self.architecture)
        for token in ("static_archive", "neutral_export", "visual_review"):
            self.assertIn(token, self.architecture)

    def test_operation_id_contract_rejects_recorded_alias_terms(self) -> None:
        pattern = self.template_schema["properties"]["operation_id"]["pattern"]
        self.assertIsNone(re.fullmatch(pattern, "modeling_strategy_scripting.Face12"))
        self.assertIsNotNone(
            re.fullmatch(pattern, "modeling_strategy_scripting.select-semantically")
        )


if __name__ == "__main__":
    unittest.main()
