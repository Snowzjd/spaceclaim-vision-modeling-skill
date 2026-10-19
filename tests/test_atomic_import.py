from __future__ import annotations

import ast
import hashlib
import math
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ACTION = (
    ROOT
    / "spaceclaim-vision-modeling"
    / "assets"
    / "operation-templates"
    / "modeling-strategy-scripting"
    / "actions"
    / "ma-35.action.py"
)


class DescendantSelector:
    def __init__(self, owner):
        self.owner = owner

    def __getitem__(self, item_type):
        return lambda: [item for item in self.owner.descendants if isinstance(item, item_type)]


class FakePart:
    def __init__(self, parent=None):
        self.Parent = parent
        self.descendants = []
        self.GetDescendants = DescendantSelector(self)

    @property
    def Bodies(self):
        return [item for item in self.descendants if isinstance(item, FakeBody)]

    @property
    def Components(self):
        return [item for item in self.descendants if isinstance(item, FakeComponent)]


class FakeOccurrenceShape:
    """World-space volume only; no kernel topology on the occurrence shape."""

    def __init__(self, volume):
        self.volume_mm3 = float(volume)


class FakeMaster:
    def __init__(self, volume):
        self.volume_mm3 = float(volume)
        self.closed = True


class FakeBody:
    def __init__(self, bbox_mm, volume_mm3, parent=None):
        self.bbox_mm = list(bbox_mm)
        self.volume_mm3 = float(volume_mm3)
        self.Parent = parent
        self.Shape = FakeOccurrenceShape(volume_mm3)
        self.Master = FakeMaster(volume_mm3)


class FakeImportOptions:
    create_calls = 0

    @classmethod
    def Create(cls):
        cls.create_calls += 1
        return object()


class FakeComponent(FakePart):
    create_calls = []
    root = None
    source_mutation = None
    content_factory = None

    @classmethod
    def CreateFromFile(cls, parent, path, options):
        cls.create_calls.append((parent, path, options))
        content = cls.content_factory(parent)
        component = cls(parent=parent)
        component.Content = content
        component.descendants = list(content.descendants)
        parent.descendants.append(component)
        if cls.source_mutation is not None:
            cls.source_mutation(path)
        return None


class FakeContext:
    def __init__(self, root):
        self.ActivePart = root


class FakeActiveWindow:
    def __init__(self, root):
        self.ActiveContext = FakeContext(root)


class FakeWindow:
    ActiveWindow = None


def finite(value, label):
    if isinstance(value, bool):
        raise ValueError(label + " must be numeric, not boolean")
    value = float(value)
    if math.isnan(value) or math.isinf(value):
        raise ValueError(label + " must be finite")
    return value


def tolerance(value):
    value = finite(value, "tolerance")
    if value < 0:
        raise ValueError("Tolerance cannot be negative")
    return value


def near(actual, expected, tol):
    return abs(float(actual) - float(expected)) <= tolerance(tol)


def bounds_mm(body):
    return list(body.bbox_mm)


def volume_mm3(body):
    return body.volume_mm3


def assert_closed(body):
    if not body.closed or body.volume_mm3 <= 0:
        raise ValueError("Expected a nonempty closed solid")
    return body


def bbox_matches(actual, expected, tol):
    return len(actual) == 6 and all(near(actual[index], expected[index], tol) for index in range(6))


def one(items, label):
    values = list(items)
    if len(values) != 1:
        raise ValueError("Expected one " + label + ", found " + str(len(values)))
    return values[0]


def load_operation(root, content_factory):
    FakeComponent.root = root
    FakeComponent.content_factory = content_factory
    FakeComponent.create_calls = []
    FakeComponent.source_mutation = None
    FakeImportOptions.create_calls = 0
    FakeWindow.ActiveWindow = FakeActiveWindow(root)
    namespace = {
        "basestring": str,
        "Component": FakeComponent,
        "DesignBody": FakeBody,
        "ImportOptions": FakeImportOptions,
        "Window": FakeWindow,
        "GetRootPart": lambda: root,
        "finite": finite,
        "tolerance": tolerance,
        "near": near,
        "bounds_mm": bounds_mm,
        "volume_mm3": volume_mm3,
        "assert_closed": assert_closed,
        "bbox_matches": bbox_matches,
        "one": one,
    }
    source = ACTION.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(ACTION))
    assert [node.name for node in tree.body if isinstance(node, ast.FunctionDef)] == ["operation"]
    exec(compile(source, str(ACTION), "exec"), namespace)
    return namespace["operation"]


class AtomicImportActionTests(unittest.TestCase):
    def test_source_is_one_action_and_uses_only_controlled_import_entry_point(self):
        source = ACTION.read_text(encoding="utf-8")
        tree = ast.parse(source, filename=str(ACTION))
        self.assertEqual([node.name for node in tree.body if isinstance(node, ast.FunctionDef)], ["operation"])
        self.assertIn("Component.CreateFromFile", source)
        self.assertIn("ImportOptions.Create", source)
        for forbidden in ("Document.Open", "DocumentSave", "ReplaceFromFile", "Save(", "RenameObject"):
            self.assertNotIn(forbidden, source)

    def test_valid_import_matches_signatures_without_relying_on_body_order(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "native-fixture.scdoc"
            payload = b"native scdoc fixture"
            path.write_bytes(payload)
            root = FakePart()
            body_a = FakeBody([0.0, 0.0, 0.0, 10.0, 5.0, 2.0], 100.0)
            body_b = FakeBody([20.0, -2.0, 1.0, 24.0, 4.0, 7.0], 120.0)
            operation = load_operation(root, lambda parent: FakePart(parent))

            def content(parent):
                part = FakePart(parent)
                part.descendants.extend([body_b, body_a])
                body_a.Parent = part
                body_b.Parent = part
                return part

            FakeComponent.content_factory = content
            result = operation(
                {
                    "source_path": str(path),
                    "source_sha256": hashlib.sha256(payload).hexdigest().upper(),
                    "expected_body_count": 2,
                    "expected_body_signatures": [
                        {"bbox_mm": body_a.bbox_mm, "volume_mm3": body_a.volume_mm3},
                        {"bbox_mm": body_b.bbox_mm, "volume_mm3": body_b.volume_mm3},
                    ],
                    "bbox_tolerance_mm": 0.001,
                    "volume_tolerance_mm3": 0.001,
                }
            )
            self.assertEqual(1, len(FakeComponent.create_calls))
            self.assertIs(root, FakeComponent.create_calls[0][0])
            self.assertEqual(str(path), FakeComponent.create_calls[0][1])
            self.assertEqual([body_b, body_a], result["bodies"])
            self.assertIsNotNone(result["component"])
            self.assertEqual(hashlib.sha256(payload).hexdigest(), result["source_sha256"])
            self.assertEqual([body_b.bbox_mm, body_a.bbox_mm], [item["bbox_mm"] for item in result["measurements"]])
            self.assertEqual([120.0, 100.0], [item["volume_mm3"] for item in result["measurements"]])

    def test_hash_or_extension_guard_precedes_import(self):
        with tempfile.TemporaryDirectory() as directory:
            native = Path(directory) / "native.scdoc"
            native.write_bytes(b"fixture")
            foreign = Path(directory) / "foreign.step"
            foreign.write_bytes(b"fixture")
            root = FakePart()
            operation = load_operation(root, lambda parent: FakePart(parent))
            base = {
                "source_path": str(native),
                "source_sha256": "0" * 64,
                "expected_body_count": 1,
                "expected_body_signatures": [{"bbox_mm": [0, 0, 0, 1, 1, 1], "volume_mm3": 1}],
                "bbox_tolerance_mm": 0.001,
                "volume_tolerance_mm3": 0.001,
            }
            with self.assertRaises(ValueError):
                operation(base)
            self.assertEqual([], FakeComponent.create_calls)
            invalid_extension = dict(base, source_path=str(foreign), source_sha256=hashlib.sha256(b"fixture").hexdigest())
            with self.assertRaises(ValueError):
                operation(invalid_extension)
            self.assertEqual([], FakeComponent.create_calls)
            unsupported_override = dict(base, source_sha256=hashlib.sha256(b"fixture").hexdigest(), units="mm")
            with self.assertRaises(ValueError):
                operation(unsupported_override)
            self.assertEqual([], FakeComponent.create_calls)

    def test_geometry_guards_precede_import(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "native.scdoc"
            payload = b"fixture"
            path.write_bytes(payload)
            root = FakePart()
            operation = load_operation(root, lambda parent: FakePart(parent))
            base = {
                "source_path": str(path),
                "source_sha256": hashlib.sha256(payload).hexdigest(),
                "expected_body_count": 1,
                "expected_body_signatures": [{"bbox_mm": [0, 0, 0, 1, 1, 1], "volume_mm3": 1}],
                "bbox_tolerance_mm": 0.001,
                "volume_tolerance_mm3": 0.001,
            }
            invalid_cases = (
                {"expected_body_count": True},
                {"expected_body_count": 0},
                {"expected_body_count": 2},
                {"bbox_tolerance_mm": -1.0},
                {"volume_tolerance_mm3": float("nan")},
            )
            for override in invalid_cases:
                with self.subTest(override=override):
                    params = dict(base)
                    params.update(override)
                    with self.assertRaises((ValueError, RuntimeError)):
                        operation(params)
                    self.assertEqual([], FakeComponent.create_calls)

    def test_source_change_during_import_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "native.scdoc"
            payload = b"fixture"
            path.write_bytes(payload)
            root = FakePart()
            body = FakeBody([0, 0, 0, 1, 1, 1], 1.0)

            def content(parent):
                part = FakePart(parent)
                body.Parent = part
                part.descendants.append(body)
                return part

            operation = load_operation(root, content)
            FakeComponent.source_mutation = lambda current_path: Path(current_path).write_bytes(b"changed")
            with self.assertRaises(RuntimeError):
                operation(
                    {
                        "source_path": str(path),
                        "source_sha256": hashlib.sha256(payload).hexdigest(),
                        "expected_body_count": 1,
                        "expected_body_signatures": [{"bbox_mm": body.bbox_mm, "volume_mm3": 1.0}],
                        "bbox_tolerance_mm": 0.001,
                        "volume_tolerance_mm3": 0.001,
                    }
                )
            FakeComponent.source_mutation = None

    def test_nested_source_is_rejected_after_component_creation(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "nested.scdoc"
            payload = b"fixture"
            path.write_bytes(payload)
            root = FakePart()

            def content(parent):
                part = FakePart(parent)
                part.descendants.append(FakeComponent(parent=part))
                return part

            operation = load_operation(root, content)
            with self.assertRaises(RuntimeError):
                operation(
                    {
                        "source_path": str(path),
                        "source_sha256": hashlib.sha256(payload).hexdigest(),
                        "expected_body_count": 1,
                        "expected_body_signatures": [{"bbox_mm": [0, 0, 0, 1, 1, 1], "volume_mm3": 1.0}],
                        "bbox_tolerance_mm": 0.001,
                        "volume_tolerance_mm3": 0.001,
                    }
                )


if __name__ == "__main__":
    unittest.main()
