from __future__ import annotations
import copy
import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("atomic_reasoning", ROOT / "spaceclaim-vision-modeling/scripts/validate_atomic_reasoning.py")
module = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(module)


class AtomicReasoningTests(unittest.TestCase):
    def setUp(self):
        self.manifest = {"sources": [{"id": "text-1", "kind": "text", "locator": "clause 1"}]}
        self.specs = {"GU-11": {"result_fields": [{"name": "value", "type": "number"}, {"name": "unit", "type": "string"}]}}
        self.result = {"contract_version": 1, "catalog_id": "GU-11", "instance_id": "d1", "status": "resolved",
                       "data": {"value": 6.5, "unit": "mm"}, "provenance": [{"fields": ["value", "unit"], "kind": "user", "source_refs": ["text-1"], "rationale": "Quoted requirement"}], "unresolved": []}

    def check(self, result=None):
        return module.validate(result or self.result, self.manifest, self.specs)

    def test_supported_result(self):
        self.assertEqual([], self.check())

    def test_unknown_is_not_ready(self):
        self.result["data"]["value"] = None
        self.assertTrue(self.check())
        self.result["unresolved"] = [{"field": "value", "reason": "Not dimensioned", "blocking": True, "needed": "Supply diameter"}]
        self.assertTrue(self.check())
        self.result["status"] = "requires_clarification"
        self.assertEqual([], self.check())

    def test_unbacked_source_and_duplicate_provenance(self):
        self.result["provenance"][0]["source_refs"] = ["invented"]
        self.assertTrue(self.check())
        self.result["provenance"][0]["source_refs"] = ["text-1"]
        self.result["provenance"].append(copy.deepcopy(self.result["provenance"][0]))
        self.assertTrue(self.check())

    def test_bool_nan_and_extra_fields_rejected(self):
        for invalid in (True, float("nan"), float("inf")):
            self.result["data"]["value"] = invalid
            self.assertTrue(self.check())
        self.result["data"]["value"] = 6.5
        self.result["data"]["recipe"] = "build whole part"
        self.assertTrue(self.check())

    def test_malformed_envelope(self):
        for malformed in ([], None, {"contract_version": True}):
            self.assertTrue(module.validate(malformed, self.manifest, self.specs))

    def test_unit_conversion_and_quantity(self):
        data = dict(original_value=0.75, original_unit="in", value=19.05, unit="mm", quantity_kind="length")
        self.assertEqual([], module.numeric_checks("GU-12", data))
        data["value"] = 0.75
        self.assertTrue(module.numeric_checks("GU-12", data))
        data["unit"] = "mm2"
        self.assertTrue(module.numeric_checks("GU-12", data))

    def test_bounded_arithmetic(self):
        self.assertEqual(17, module.arithmetic("total - 2 * end", {"total": 35, "end": 9}))
        self.assertEqual(17, module.arithmetic("total - 2 * end", {"total": {"value": 35, "unit": "mm"}, "end": {"value": 9, "unit": "mm"}}))
        for expression in ("__import__('os')", "x.real", "10 ** 1000000", "x[0]", "True", "missing"):
            with self.assertRaises((ValueError, SyntaxError)):
                module.arithmetic(expression, {"x": 1})

    def test_inapplicable_cannot_hide_missing_dimension(self):
        self.result["data"]["value"] = None
        self.result["not_applicable"] = [{"field": "value", "reason": "Missing in source"}]
        self.assertTrue(self.check())

    def test_wrong_derived_value(self):
        data = dict(expression="length * width * height", bindings=dict(length=11, width=7, height=3), value=231)
        self.assertEqual([], module.numeric_checks("GU-19", data))
        data["value"] = 230
        self.assertTrue(module.numeric_checks("GU-19", data))

    def test_conflict_finding_does_not_authorize_build(self):
        item = {"instance_id": "length-check", "catalog_id": "GU-14", "status": "resolved", "data": {"verdict": "conflict"}}
        self.assertTrue(module.handoff_blockers([item]))
        item["data"]["verdict"] = "consistent"
        self.assertEqual([], module.handoff_blockers([item]))

    def test_dependency_cycle_blocks_case_handoff(self):
        items = [{"instance_id": str(i), "catalog_id": "MS-04", "status": "resolved", "data": {"dependency_edge": {"upstream_id": a, "downstream_id": b}}} for i, (a, b) in enumerate((("profile", "extrusion"), ("extrusion", "profile")))]
        self.assertIn("Cyclic operation dependency", module.handoff_blockers(items))

    def test_strategy_empty_payload_and_wrong_comparison(self):
        self.assertTrue(module.strategy_checks("MS-01", {"parameter_declaration": {}}))
        data = {"constraint_result": dict(parameter_name="width", value=-1, operator=">", operand=0, unit="mm", verdict="passed", violation_reason="")}
        self.assertTrue(module.strategy_checks("MS-02", data))

    def test_documented_locator_and_verdict_variants(self):
        for locator in ("text clause", {"path": "request.txt", "region": "clause 1"}):
            self.manifest["sources"][0]["locator"] = locator
            self.assertEqual([], self.check())
        for verdict in ("pass", "passed"):
            data = {"constraint_result": dict(parameter_name="width", value=4, operator=">", operand=0, unit="mm", verdict=verdict, violation_reason=None)}
            self.assertEqual([], module.strategy_checks("MS-02", data))
        data["constraint_result"].update(operator="in", operand=[2, 4, 8])
        self.assertEqual([], module.strategy_checks("MS-02", data))
        data["constraint_result"]["operand"] = [2, 8]
        self.assertTrue(module.strategy_checks("MS-02", data))

    def test_case_can_exclude_optional_camera_not_required_dimension(self):
        items = [{"instance_id": "camera", "catalog_id": "GU-03", "status": "requires_clarification", "data": {}}, {"instance_id": "length", "catalog_id": "GU-14", "status": "resolved", "data": {"verdict": "consistent"}}]
        self.assertEqual([], module.handoff_blockers(items, ["length"]))
        items[1]["data"]["verdict"] = "conflict"
        self.assertTrue(module.handoff_blockers(items, ["length"]))
        self.assertTrue(module.handoff_blockers(items, ["missing"]))

    def test_relation_failure_is_detected_not_fixed(self):
        data = dict(lhs=65, rhs=64, tolerance=0.01, relation="eq", verdict="conflict")
        self.assertEqual([], module.numeric_checks("GU-14", data))
        data["verdict"] = "consistent"
        self.assertTrue(module.numeric_checks("GU-14", data))

    def test_frame_alias_and_geometric_invariant(self):
        data = dict(origin=[2, -3, 1], axes=[[1, 0, 0], [0, 1, 0], [0, 0, 1]], handedness="right_handed")
        self.assertEqual([], module.numeric_checks("GU-15", data))
        data["axes"][2] = [0, 0, -1]
        self.assertTrue(module.numeric_checks("GU-15", data))
        data["handedness"] = "left-handed"
        self.assertEqual([], module.numeric_checks("GU-15", data))

    def test_guidance_coverage_and_action_specific_fields(self):
        specs = module.specifications()
        expected = {"GU-%02d" % n for n in range(1, 21)} | {"MS-%02d" % n for n in range(1, 10)}
        self.assertEqual(expected, set(specs))
        for op in specs.values():
            self.assertTrue(op["input_fields"])
            self.assertTrue(op["result_fields"])
            self.assertGreaterEqual(len(op["procedure"]), 3)
            self.assertTrue(op["rejection_rules"])
            for fields in (op["input_fields"], op["result_fields"]):
                self.assertEqual(len(fields), len({field["name"] for field in fields}))
                self.assertTrue(all(field["type"] in module.TYPES for field in fields))


if __name__ == "__main__":
    unittest.main()
