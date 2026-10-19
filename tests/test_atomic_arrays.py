from __future__ import annotations

import ast
import math
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ACTIONS = (
    ROOT
    / "spaceclaim-vision-modeling"
    / "assets"
    / "operation-templates"
    / "modeling-strategy-scripting"
    / "actions"
)


class FakeDirection:
    def __init__(self, values):
        self.X, self.Y, self.Z = values


class FakePoint:
    def __init__(self, values):
        self.values = tuple(values)


class FakeVector:
    def __init__(self, values):
        self.values = tuple(values)


class FakeVectorFactory:
    @staticmethod
    def Create(*values):
        return FakeVector(values)


class FakeMatrix:
    def __init__(self, kind, value):
        self.kind = kind
        self.value = value


class FakeMatrixFactory:
    @staticmethod
    def CreateTranslation(vector):
        return FakeMatrix("translation", vector)

    @staticmethod
    def CreateRotation(axis, angle):
        return FakeMatrix("rotation", (axis, angle))


class FakeLine:
    @staticmethod
    def Create(origin, direction):
        return (origin, direction)


class FakeBody:
    def __init__(self, volume=125.0):
        self.volume = volume
        self.copy_calls = 0
        self.transforms = []
        self.is_transient = True
        self.closed = True

    def Copy(self):
        self.copy_calls += 1
        return FakeBody(self.volume)

    def Transform(self, matrix):
        self.transforms.append(matrix)


def finite(value, label):
    if isinstance(value, bool):
        raise ValueError(label + " must be numeric, not boolean")
    value = float(value)
    if math.isnan(value) or math.isinf(value):
        raise ValueError(label + " must be finite")
    return value


def vector3(values, label):
    if not isinstance(values, (list, tuple)) or len(values) != 3:
        raise ValueError(label + " requires three coordinates")
    return [finite(value, label) for value in values]


def point_mm(values):
    return FakePoint([value / 1000.0 for value in vector3(values, "point_mm")])


def direction(values):
    values = vector3(values, "direction")
    length = math.sqrt(sum(value * value for value in values))
    if length <= 1e-12:
        raise ValueError("Direction must be nonzero")
    return FakeDirection([value / length for value in values])


def positive(value, label):
    value = finite(value, label)
    if value <= 0:
        raise ValueError(label + " must be positive")
    return value


def tolerance(value):
    value = finite(value, "tolerance")
    if value < 0:
        raise ValueError("Tolerance cannot be negative")
    return value


def near(actual, expected, tol):
    return abs(float(actual) - float(expected)) <= tolerance(tol)


def require_transient(body):
    if not getattr(body, "is_transient", False):
        raise ValueError("This operation variant requires a transient Modeler Body")
    if not body.closed or body.volume <= 0:
        raise ValueError("Expected a nonempty closed solid")
    return body


def volume_mm3(body):
    return body.volume


def assert_closed(body):
    return require_transient(body)


def load_operation(filename):
    namespace = {
        "math": math,
        "Vector": FakeVectorFactory,
        "Matrix": FakeMatrixFactory,
        "Line": FakeLine,
        "finite": finite,
        "vector3": vector3,
        "point_mm": point_mm,
        "direction": direction,
        "positive": positive,
        "tolerance": tolerance,
        "near": near,
        "require_transient": require_transient,
        "volume_mm3": volume_mm3,
        "assert_closed": assert_closed,
    }
    source = (ACTIONS / filename).read_text(encoding="utf-8")
    ast.parse(source, filename=str(ACTIONS / filename))
    exec(compile(source, str(ACTIONS / filename), "exec"), namespace)
    return namespace["operation"]


class AtomicArrayActionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.linear = staticmethod(load_operation("ma-18.action.py"))
        cls.circular = staticmethod(load_operation("ma-19.action.py"))

    def test_sources_are_single_v21_action_functions(self):
        for name in ("ma-18.action.py", "ma-19.action.py"):
            tree = ast.parse((ACTIONS / name).read_text(encoding="utf-8"))
            self.assertEqual([node.name for node in tree.body if isinstance(node, ast.FunctionDef)], ["operation"])
            self.assertEqual("operation", tree.body[0].name)
            self.assertNotRegex((ACTIONS / name).read_text(encoding="utf-8"), r"Body\d+|Face\d+|Edge\d+")

    def test_linear_uses_independent_copies_and_meter_translation(self):
        source = FakeBody()
        result = self.linear(
            {
                "body": source,
                "direction": [1.0, 2.0, 2.0],
                "spacing_mm": 5.0,
                "count": 3,
                "volume_tolerance_mm3": 0.0,
            }
        )
        self.assertEqual(3, source.copy_calls)
        self.assertEqual([], source.transforms)
        self.assertEqual(3, len(result["instances"]))
        expected_offsets = [
            [0.0, 0.0, 0.0],
            [5.0 / 3.0, 10.0 / 3.0, 10.0 / 3.0],
            [10.0 / 3.0, 20.0 / 3.0, 20.0 / 3.0],
        ]
        for actual, expected in zip(result["offsets_mm"], expected_offsets):
            for actual_component, expected_component in zip(actual, expected):
                self.assertAlmostEqual(expected_component, actual_component)
        self.assertEqual("preserved", result["source_policy"])
        self.assertEqual("independent", result["association"])
        for actual, expected in zip(
            (result["instances"][1].transforms[0].value.values, result["instances"][2].transforms[0].value.values),
            ((5.0 / 3000.0, 10.0 / 3000.0, 10.0 / 3000.0), (10.0 / 3000.0, 20.0 / 3000.0, 20.0 / 3000.0)),
        ):
            for actual_component, expected_component in zip(actual, expected):
                self.assertAlmostEqual(expected_component, actual_component)
        self.assertEqual(3, len({id(instance) for instance in result["instances"]}))
        self.assertNotIn(source, result["instances"])

    def test_circular_uses_independent_copies_and_signed_radians(self):
        source = FakeBody()
        result = self.circular(
            {
                "body": source,
                "axis_origin_mm": [10.0, 20.0, 30.0],
                "axis_direction": [0.0, 0.0, 2.0],
                "count": 4,
                "step_angle_degrees": -90.0,
                "volume_tolerance_mm3": 0.0,
            }
        )
        self.assertEqual(4, source.copy_calls)
        self.assertEqual([], source.transforms)
        self.assertEqual([0.0, -90.0, -180.0, -270.0], result["angles_degrees"])
        self.assertEqual("preserved", result["source_policy"])
        self.assertEqual("independent", result["association"])
        axis, angle = result["instances"][2].transforms[0].value
        self.assertEqual((0.01, 0.02, 0.03), axis[0].values)
        self.assertEqual((0.0, 0.0, 1.0), (axis[1].X, axis[1].Y, axis[1].Z))
        self.assertAlmostEqual(-math.pi, angle)

    def test_linear_guards_run_before_any_copy(self):
        cases = (
            {"count": True},
            {"count": 1},
            {"count": 2.5},
            {"spacing_mm": 0.0},
            {"spacing_mm": float("nan")},
            {"direction": [0.0, 0.0, 0.0]},
            {"volume_tolerance_mm3": -1.0},
        )
        base = {
            "body": None,
            "direction": [1.0, 0.0, 0.0],
            "spacing_mm": 1.0,
            "count": 2,
            "volume_tolerance_mm3": 0.0,
        }
        for override in cases:
            source = FakeBody()
            params = dict(base, body=source)
            params.update(override)
            with self.assertRaises(ValueError):
                self.linear(params)
            self.assertEqual(0, source.copy_calls, override)
            self.assertEqual([], source.transforms, override)

    def test_circular_rejects_periodic_duplicates_before_any_copy(self):
        cases = (
            {"step_angle_degrees": 0.0, "count": 2},
            {"step_angle_degrees": 360.0, "count": 2},
            {"step_angle_degrees": 180.0, "count": 3},
            {"step_angle_degrees": 450.0, "count": 5},
            {"step_angle_degrees": float("inf"), "count": 2},
            {"axis_direction": [0.0, 0.0, 0.0], "step_angle_degrees": 90.0, "count": 2},
        )
        base = {
            "body": None,
            "axis_origin_mm": [0.0, 0.0, 0.0],
            "axis_direction": [0.0, 0.0, 1.0],
            "count": 4,
            "step_angle_degrees": 90.0,
            "volume_tolerance_mm3": 0.0,
        }
        for override in cases:
            source = FakeBody()
            params = dict(base, body=source)
            params.update(override)
            with self.assertRaises(ValueError):
                self.circular(params)
            self.assertEqual(0, source.copy_calls, override)
            self.assertEqual([], source.transforms, override)


if __name__ == "__main__":
    unittest.main()
