from __future__ import annotations

import ast
import importlib.util
import json
import math
import re
import tempfile
import unittest
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "spaceclaim-vision-modeling"
SCRIPTS = PACKAGE / "scripts"
ACTIONS = PACKAGE / "assets" / "operation-templates" / "validation-visual-review" / "actions"


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


BUILDER = load_module("validation_script_builder", SCRIPTS / "build_validation_scripts.py")
AUDITOR = load_module("validation_script_auditor", SCRIPTS / "audit_scscript.py")


class ValidationActionTests(unittest.TestCase):
    def test_all_catalog_actions_have_independent_sources_and_archives(self) -> None:
        ids = ["VA-%02d" % number for number in range(4, 19)]
        self.assertEqual(tuple(ids), BUILDER.ACTION_IDS)
        for ident in ids:
            with self.subTest(ident=ident):
                source_path = ACTIONS / (ident.lower() + ".action.py")
                editable_path = ACTIONS / (ident.lower() + ".py")
                archive_path = ACTIONS / (ident.lower() + ".scscript")
                self.assertTrue(source_path.is_file())
                self.assertTrue(editable_path.is_file())
                self.assertTrue(archive_path.is_file())
                source = editable_path.read_text(encoding="utf-8")
                ast.parse(source, filename=str(editable_path))
                self.assertEqual(1, source.count("def operation("))
                self.assertIn('ACTION_ID = "' + ident + '"', source)
                self.assertIn("ATOMIC_INPUT", source)
                with zipfile.ZipFile(archive_path) as archive:
                    self.assertEqual(source.encode("utf-8"), archive.read("_script"))
                    self.assertEqual(b"21", archive.read("_apiVersion"))
                    self.assertEqual(
                        ["_script", "_apiVersion", "_smartVariableVersion", "[Content_Types].xml"],
                        archive.namelist(),
                    )

    def test_generated_actions_are_read_only_and_case_neutral(self) -> None:
        forbidden = (
            "DocumentSave.Execute",
            "RenameObject.Execute",
            "NamedSelection.Create",
            "Move.Translate",
            "Move.Rotate",
            "Combine.Merge",
            "BlockBody.Create",
            "ConstantRound.Execute",
            "Chamfer.Execute",
            "Selection.Create",
        )
        for archive_path in sorted(ACTIONS.glob("va-*.scscript")):
            with self.subTest(archive=archive_path.name):
                result = AUDITOR.audit_archive(
                    archive_path,
                    require_api="21",
                    forbid_numbered_aliases=True,
                    forbidden_operations=forbidden,
                )
                self.assertEqual("passed", result["status"], result["issues"])
                source = zipfile.ZipFile(archive_path).read("_script").decode("utf-8")
                self.assertNotRegex(source, r"\b(?:Body|Face|Edge)\d+\b")
                self.assertNotIn("import os", source)
                self.assertNotIn("import subprocess", source)

    def test_builder_rebuilds_exactly_selected_archive_without_spaceclaim(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            # The builder writes only its checked-in action directory; this
            # smoke check uses a temporary copy of one source to verify the
            # assembly contract without starting SpaceClaim.
            source = ACTIONS / "va-04.action.py"
            assembled = BUILDER.assembled_source(source)
            self.assertIn("from SpaceClaim.Api.V21 import *", assembled)
            self.assertIn("Supply one explicit ATOMIC_INPUT", assembled)
            ast.parse(assembled)
            output = Path(directory) / "assembled.py"
            output.write_text(assembled, encoding="utf-8")
            self.assertEqual(assembled, output.read_text(encoding="utf-8"))

    def test_finite_guards_reject_nan_inf_bool_and_bad_vectors(self) -> None:
        common = ast.parse((ACTIONS / "common.py").read_text(encoding="utf-8"))
        wanted = {"finite", "nonnegative", "positive", "vector3", "normalize"}
        module = ast.Module(
            body=[node for node in common.body if isinstance(node, ast.FunctionDef) and node.name in wanted],
            type_ignores=[],
        )
        namespace = {"math": __import__("math")}
        exec(compile(module, "validation-common", "exec"), namespace, namespace)
        for value in (float("nan"), float("inf"), True):
            with self.assertRaises(ValueError):
                namespace["finite"](value, "number")
        with self.assertRaises(ValueError):
            namespace["nonnegative"](-1, "tolerance")
        with self.assertRaises(ValueError):
            namespace["vector3"]([1, 2], "point")
        with self.assertRaises(ValueError):
            namespace["normalize"]([0, 0, 0], "axis")

    def test_unknown_cone_and_torus_boundaries_are_explicit(self) -> None:
        cone = (ACTIONS / "va-14.action.py").read_text(encoding="utf-8")
        torus = (ACTIONS / "va-15.action.py").read_text(encoding="utf-8")
        self.assertIn("needs_manual_review", cone)
        self.assertIn("HalfAngle", cone)
        self.assertIn("needs_manual_review", torus)
        self.assertIn("MinorRadius", torus)
        self.assertIn("association", torus)
        self.assertNotIn("Cone.Create", cone)
        self.assertNotIn("Torus.Create", torus)

    def test_manual_review_is_not_presented_as_runtime_success(self) -> None:
        common = (ACTIONS / "common.py").read_text(encoding="utf-8")
        self.assertIn('"runtime_claim": False', common)
        self.assertIn('"geometry_modified": False', common)
        self.assertIn('"gui_interaction": False', common)
        for path in sorted(ACTIONS.glob("va-*.py")):
            self.assertNotIn('"runtime_success": True', path.read_text(encoding="utf-8"))

    def test_repeated_placement_uses_one_length_unit_and_finite_count_errors(self) -> None:
        namespace = {
            "active_root": lambda mapping: mapping["expected_root"],
            "required": lambda mapping, *names: next(mapping[name] for name in names if name in mapping),
            "optional": lambda mapping, default, *names: next(
                (mapping[name] for name in names if name in mapping), default
            ),
            "vector3": lambda value, label: [float(item) for item in value],
            "finite": lambda value, label: float(value),
            "nonnegative": lambda value, label: float(value),
            "positive": lambda value, label: float(value),
            "normalize": lambda value, label: [float(item) / math.sqrt(sum(float(item) ** 2 for item in value)) for item in value],
            "subtract": lambda left, right: [left[index] - right[index] for index in range(3)],
            "dot": lambda left, right: sum(left[index] * right[index] for index in range(3)),
            "norm": lambda value, label: math.sqrt(sum(item * item for item in value)),
            "angle_wrap_degrees": lambda value: ((value + 180.0) % 360.0) - 180.0,
            "passed": lambda action_id, **values: dict(action_id=action_id, status="passed", **values),
            "manual_review": lambda action_id, reason, **values: dict(action_id=action_id, status="needs_manual_review", reason=reason, **values),
            "math": math,
            "PI": math.pi,
            "_STRING_TYPES": (str,),
        }
        source = (ACTIONS / "va-16.action.py").read_text(encoding="utf-8")
        exec(compile(source, "va-16.action.py", "exec"), namespace, namespace)
        result = namespace["operation"](
            {
                "positions_mm": [[0, 0, 0], [1, 0, 0]],
                "expected_root": object(),
                "tolerance_mm": 0.01,
                "expected_rule": {"mode": "linear", "step_mm": [1, 0, 0], "count": 3},
            }
        )
        self.assertEqual("failed", result["status"])
        self.assertFalse(result["count_matches"])
        self.assertTrue(math.isfinite(result["max_error"]))
        circular = namespace["operation"](
            {
                "positions_mm": [[1, 0, 0], [0, 1, 0]],
                "expected_root": object(),
                "tolerance_mm": 0.001,
                "expected_rule": {
                    "mode": "circular",
                    "center_mm": [0, 0, 0],
                    "axis": [0, 0, 1],
                    "pitch_radius_mm": 1,
                    "angle_step_deg": 90,
                    "count": 2,
                },
            }
        )
        self.assertEqual("passed", circular["status"])
        self.assertEqual([0.0, 0.0], circular["angular_errors_deg"])
        self.assertEqual([0.0, 0.0], circular["angular_errors_mm"])
        self.assertEqual("circular", circular["rule"]["mode"])
        self.assertEqual(90.0, circular["rule"]["angle_step_deg"])
        self.assertEqual(2, circular["rule"]["count"])

        # Angular error is converted to a chord length before comparison with
        # the one millimetre tolerance.  A 10-degree error on a unit circle is
        # therefore about 0.1743 mm, not 10 (mixed units).
        circular_mismatch = namespace["operation"](
            {
                "positions_mm": [[1, 0, 0], [math.cos(math.radians(100)), math.sin(math.radians(100)), 0]],
                "expected_root": object(),
                "tolerance_mm": 0.1,
                "expected_rule": {
                    "mode": "circular",
                    "center_mm": [0, 0, 0],
                    "axis": [0, 0, 1],
                    "pitch_radius_mm": 1,
                    "angle_step_deg": 90,
                },
            }
        )
        self.assertEqual("failed", circular_mismatch["status"])
        self.assertAlmostEqual(10.0, circular_mismatch["angular_errors_deg"][1], places=8)
        self.assertAlmostEqual(
            2.0 * math.sin(math.radians(5.0)),
            circular_mismatch["angular_errors_mm"][1],
            places=8,
        )
        self.assertAlmostEqual(circular_mismatch["angular_errors_mm"][1], circular_mismatch["max_error"], places=8)

        # Count mismatch is a boolean result dimension; it must not encode
        # failure by placing infinity into a JSON result.
        circular_count_mismatch = namespace["operation"](
            {
                "positions_mm": [[1, 0, 0], [0, 1, 0]],
                "expected_root": object(),
                "tolerance_mm": 0.001,
                "expected_rule": {
                    "mode": "circular",
                    "center_mm": [0, 0, 0],
                    "axis": [0, 0, 1],
                    "pitch_radius_mm": 1,
                    "angle_step_deg": 90,
                    "count": 3,
                },
            }
        )
        self.assertEqual("failed", circular_count_mismatch["status"])
        self.assertFalse(circular_count_mismatch["count_matches"])
        self.assertTrue(math.isfinite(circular_count_mismatch["max_error"]))
        json.dumps(circular_count_mismatch, allow_nan=False)

    def test_count_action_rejects_duplicate_and_mixed_inferred_objects(self) -> None:
        class FakeObject:
            pass

        root = FakeObject()
        body = FakeObject()
        other_body = FakeObject()
        face = FakeObject()

        def require(mapping, *names):
            for name in names:
                if name in mapping:
                    return mapping[name]
            raise ValueError("missing")

        namespace = {
            "active_root": lambda mapping: root,
            "required": require,
            "optional": lambda mapping, default, *names: next((mapping[name] for name in names if name in mapping), default),
            "finite": lambda value, label: float(value),
            "root_bodies": lambda supplied: [body, other_body],
            "contains_object": lambda items, target: any(item is target for item in items),
            "groups_for_root": lambda supplied: [],
            "same_object": lambda left, right: left is right,
        }
        # The candidate bodies expose empty topology for the inference pass.
        body.Faces = []
        body.Edges = []
        other_body.Faces = [face]
        other_body.Edges = []
        namespace["operation"] = None
        source = (ACTIONS / "va-07.action.py").read_text(encoding="utf-8")
        exec(compile(source, "va-07.action.py", "exec"), namespace, namespace)
        with self.assertRaises(ValueError):
            namespace["operation"]({"objects": [body, body], "expected_count": 2})
        with self.assertRaises(ValueError):
            namespace["operation"](
                {"objects": [body, body], "expected_count": 2, "object_kind": "body"}
            )
        with self.assertRaises(ValueError):
            namespace["operation"]({"objects": [body, face], "expected_count": 2})

    def test_name_check_is_unicode_safe_and_owner_body_is_context_only(self) -> None:
        common_tree = ast.parse((ACTIONS / "common.py").read_text(encoding="utf-8"))
        common_nodes = [node for node in common_tree.body if isinstance(node, ast.FunctionDef)]
        common_namespace = {"_STRING_TYPES": (str,)}
        exec(
            compile(ast.Module(body=common_nodes, type_ignores=[]), "validation-common", "exec"),
            common_namespace,
            common_namespace,
        )

        class FakeObject:
            def __init__(self, **values):
                self.__dict__.update(values)

        root = FakeObject()
        face = FakeObject()
        body = FakeObject(Parent=root, Faces=[face], Edges=[])
        common_namespace["root_bodies"] = lambda supplied: [body]
        common_namespace["same_object"] = lambda left, right: left is right
        target, kind = common_namespace["object_identity"]({"body": body, "face": face}, root)
        self.assertIs(face, target)
        self.assertEqual("face", kind)
        target, kind = common_namespace["object_identity"]({"body": body}, root)
        self.assertIs(body, target)
        self.assertEqual("body", kind)
        with self.assertRaises(ValueError):
            common_namespace["object_identity"]({"body": body, "face": face, "edge": face}, root)

        named = FakeObject(Name="测量体-α")
        self.assertEqual("测量体-α", common_namespace["safe_name"](named))

        action_tree = ast.parse((ACTIONS / "va-17.action.py").read_text(encoding="utf-8"))
        operation = next(node for node in action_tree.body if isinstance(node, ast.FunctionDef) and node.name == "operation")
        action_namespace = {
            "ACTION_ID": "VA-17",
            "active_root": lambda mapping: mapping["expected_root"],
            "object_identity": lambda mapping, supplied: (named, "body"),
            "required": lambda mapping, *names: next(mapping[name] for name in names if name in mapping),
            "safe_name": common_namespace["safe_name"],
            "text": common_namespace["text"],
            "passed": lambda action_id, **values: dict(action_id=action_id, status="passed", **values),
            "_STRING_TYPES": (str,),
        }
        exec(compile(ast.Module(body=[operation], type_ignores=[]), "va-17.action.py", "exec"), action_namespace, action_namespace)
        result = action_namespace["operation"](
            {"expected_root": root, "body": named, "expected_name": "测量体-α"}
        )
        self.assertEqual("passed", result["status"])
        self.assertEqual("测量体-α", result["expected_name"])
        self.assertNotIn("str(expected)", (ACTIONS / "va-17.action.py").read_text(encoding="utf-8"))

    def test_named_group_uses_active_window_scope_and_rejects_stale_members(self) -> None:
        class FakeObject:
            def __init__(self, parent=None, **values):
                self.Parent = parent
                self.__dict__.update(values)

        root = FakeObject()
        document_parent = FakeObject()
        body = FakeObject(root, Faces=[], Edges=[])
        face = FakeObject(body)
        body.Faces = [face]
        group = FakeObject(document_parent, Members=[face])

        class FakeWindowHelper:
            groups = [group]

            @classmethod
            def GetGroups(cls):
                return cls.groups

        def required(mapping, *names):
            for name in names:
                if name in mapping:
                    return mapping[name]
            raise ValueError("missing")

        def contains(items, target):
            return any(item is target for item in items)

        def compare(actual, expected):
            return len(actual) == len(expected) and all(item is wanted for item, wanted in zip(actual, expected))

        namespace = {
            "ACTION_ID": "VA-18",
            "WindowHelper": FakeWindowHelper,
            "active_root": lambda mapping: mapping["root"],
            "required": required,
            "contains_object": contains,
            "root_bodies": lambda supplied: [body],
            "group_members": lambda supplied: list(supplied.Members),
            "compare_identity_sets": compare,
            "passed": lambda action_id, **values: dict(action_id=action_id, status="passed", **values),
        }
        source = (ACTIONS / "va-18.action.py").read_text(encoding="utf-8")
        exec(compile(source, "va-18.action.py", "exec"), namespace, namespace)

        result = namespace["operation"]({"root": root, "group": group, "expected_members": [face]})
        self.assertEqual("passed", result["status"])

        stale_group = FakeObject(document_parent, Members=[face])
        with self.assertRaisesRegex(ValueError, "current active window"):
            namespace["operation"]({"root": root, "group": stale_group, "expected_members": [face]})

        stale_face = FakeObject(body)
        stale_group = FakeObject(document_parent, Members=[stale_face])
        FakeWindowHelper.groups = [stale_group]
        with self.assertRaisesRegex(ValueError, "stale or outside"):
            namespace["operation"](
                {"root": root, "group": stale_group, "expected_members": [stale_face]}
            )

        occurrence_body = FakeObject(FakeObject(), Faces=[], Edges=[])
        occurrence_face = FakeObject(occurrence_body)
        occurrence_group = FakeObject(document_parent, Members=[occurrence_face])
        FakeWindowHelper.groups = [occurrence_group]
        with self.assertRaisesRegex(ValueError, "stale or outside"):
            namespace["operation"](
                {"root": root, "group": occurrence_group, "expected_members": [occurrence_face]}
            )


if __name__ == "__main__":
    unittest.main()
