import ast
import importlib.util
from pathlib import Path
import sys
import unittest
import zipfile

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "spaceclaim-vision-modeling"
sys.path.insert(0, str(PACKAGE / "scripts"))
import build_atomic_scripts as builder
from audit_scscript import audit_archive


class IsolatedGeometryScriptTests(unittest.TestCase):
    def test_each_package_contains_one_exact_action_and_common_helpers(self):
        paths = sorted(builder.ACTIONS.glob("ma-*.action.py"))
        self.assertGreaterEqual(len(paths), 9)
        for path in paths:
            with self.subTest(path=path.name):
                source = builder.assembled_source(path)
                ast.parse(source)
                archive = path.with_name(path.name.replace(".action.py", ".scscript"))
                with zipfile.ZipFile(archive) as package:
                    self.assertEqual(source.encode("utf-8"), package.read("_script"))
                    self.assertEqual(b"21", package.read("_apiVersion"))
                self.assertEqual(1, source.count("def operation("))
                self.assertNotIn("DocumentSave.Execute", source)
                self.assertNotRegex(source, r"\b(?:Face|Body|Edge)\d+\b")

    def test_actions_pass_static_archive_policy(self):
        for path in builder.ACTIONS.glob("ma-*.scscript"):
            with self.subTest(path=path.name):
                result = audit_archive(path, require_api="21", forbid_numbered_aliases=True)
                self.assertEqual("passed", result["status"], result["issues"])

    def test_extrusion_no_longer_implicitly_creates_profile_or_attaches(self):
        source = (builder.ACTIONS / "ma-06.action.py").read_text(encoding="utf-8")
        self.assertIn('p["profile"]', source)
        self.assertNotIn("DesignBody.Create", source)
        self.assertNotIn("RectangleProfile", source)
        self.assertNotIn("CircleProfile", source)

    def test_numeric_guards_reject_non_finite_boolean_and_zero(self):
        common = ast.parse((builder.ACTIONS / "common.py").read_text(encoding="utf-8"))
        pure = ast.Module(body=[node for node in common.body if isinstance(node, ast.FunctionDef) and node.name in {"finite", "positive", "vector3", "tolerance"}], type_ignores=[])
        import math
        scope = {"math": math}
        exec(compile(pure, "guards", "exec"), scope)
        for value in (float("inf"), float("nan"), True):
            with self.assertRaises(ValueError): scope["finite"](value, "number")
        with self.assertRaises(ValueError): scope["positive"](0, "length")
        with self.assertRaises(ValueError): scope["vector3"]([1, 2], "point")
        with self.assertRaises(ValueError): scope["tolerance"](-1)

    def action(self, ident, **helpers):
        scope = dict(helpers)
        exec(compile((builder.ACTIONS / (ident + '.action.py')).read_text(encoding='utf-8'), ident, 'exec'), scope)
        return scope['operation']

    def test_body_selector_rejects_unknown_predicate_before_enumeration(self):
        action = self.action('ma-28')
        with self.assertRaisesRegex(ValueError, 'Unsupported'):
            action({'criteria': {'bbox_mm': [0]*6, 'material': 'steel'}})

    def test_negative_tolerance_does_not_create_or_move_geometry(self):
        def reject(value):
            if value < 0:
                raise ValueError('negative tolerance')
        import math
        create = self.action('ma-05', vector3=lambda v, label: v, tolerance=reject)
        move = self.action('ma-14', require_live_body=lambda b: b,
                           vector3=lambda v, label: v, tolerance=reject, math=math)
        # No API mutator is available: reaching it instead of early rejection fails.
        with self.assertRaisesRegex(ValueError, 'negative tolerance'):
            create({'min_mm': [0,0,0], 'max_mm': [1,2,3], 'bbox_tolerance_mm': -1})
        with self.assertRaisesRegex(ValueError, 'negative tolerance'):
            move({'body': object(), 'delta_mm': [1,0,0], 'bbox_tolerance_mm': -1,
                  'volume_tolerance_mm3': .001})

    def test_face_selector_does_not_silently_ignore_unsupported_normal_variant(self):
        action = self.action('ma-29', require_live_body=lambda b: b)
        with self.assertRaisesRegex(ValueError, 'Unsupported'):
            action({'body': object(), 'criteria': {'curvature': 1}})

    def test_sweep_rejects_empty_path_before_kernel_call(self):
        action = self.action('ma-09')
        with self.assertRaisesRegex(ValueError, 'nonempty'):
            action({'path': []})


if __name__ == "__main__":
    unittest.main()
