# Python Script, API Version = V21
# Bounded MA-35 import harness.  ACTION_DIR, REPORT, IMPORT_SOURCE,
# IMPORT_SHA256, expected body signatures, and tolerances are supplied by the
# host builder.  No source path or fixture digest is embedded in this asset.
from SpaceClaim.Api.V21 import *
from SpaceClaim.Api.V21.Geometry import *
import hashlib
import json
import math
import os
import traceback
import zipfile


ACTION_DIR = globals().get("ACTION_DIR")
REPORT = globals().get("REPORT")
IMPORT_SOURCE = globals().get("IMPORT_SOURCE")
IMPORT_SHA256 = globals().get("IMPORT_SHA256")
IMPORT_EXPECTED_BODY_SIGNATURES = globals().get("IMPORT_EXPECTED_BODY_SIGNATURES")
if IMPORT_EXPECTED_BODY_SIGNATURES is None:
    IMPORT_EXPECTED_BODY_SIGNATURES = globals().get("IMPORT_EXPECTED_SIGNATURES")
if IMPORT_EXPECTED_BODY_SIGNATURES is None:
    expected_bbox = globals().get("IMPORT_EXPECTED_BBOX_MM")
    expected_volume = globals().get("IMPORT_EXPECTED_VOLUME_MM3")
    if expected_bbox is not None and expected_volume is not None:
        IMPORT_EXPECTED_BODY_SIGNATURES = [
            {"bbox_mm": expected_bbox, "volume_mm3": expected_volume}
        ]
IMPORT_BBOX_TOLERANCE_MM = globals().get("IMPORT_BBOX_TOLERANCE_MM")
IMPORT_VOLUME_TOLERANCE_MM3 = globals().get("IMPORT_VOLUME_TOLERANCE_MM3")

events = []
tests = []
report = {
    "schema_version": 1,
    "suite_id": "p3-actions-import",
    "status": "failed",
    "tests": tests,
    "events": events,
}


def _finite(value, label):
    value = float(value)
    if math.isnan(value) or math.isinf(value):
        raise AssertionError(label + " must be finite")
    return value


def _close(actual, expected, tolerance, label):
    actual = _finite(actual, label + " actual")
    expected = _finite(expected, label + " expected")
    tolerance = _finite(tolerance, label + " tolerance")
    if tolerance < 0 or abs(actual - expected) > tolerance:
        raise AssertionError(label + " mismatch: " + str((actual, expected, tolerance)))


def _shape(item):
    return item.Shape if hasattr(item, "Shape") else item


def _bounds(item):
    box = _shape(item).GetBoundingBox(Matrix.Identity)
    return [
        float(box.MinCorner.X) * 1000.0,
        float(box.MinCorner.Y) * 1000.0,
        float(box.MinCorner.Z) * 1000.0,
        float(box.MaxCorner.X) * 1000.0,
        float(box.MaxCorner.Y) * 1000.0,
        float(box.MaxCorner.Z) * 1000.0,
    ]


def _volume(item):
    return float(_shape(item).Volume) * 1e9


def _bbox_matches(actual, expected, tolerance):
    if len(actual) != 6 or len(expected) != 6:
        return False
    for index in range(6):
        try:
            _close(actual[index], expected[index], tolerance, "bbox[" + str(index) + "]")
        except AssertionError:
            return False
    return True


def _assert_solid(item, label):
    shape = item.Master.Shape
    if not shape.IsClosed or not shape.IsManifold or int(shape.PieceCount) != 1:
        raise AssertionError(label + " is not a single closed manifold solid")
    volume = _finite(_volume(item), label + " volume")
    if volume <= 0:
        raise AssertionError(label + " has nonpositive volume")
    return volume


def _measure(item, label):
    return {"bbox_mm": _bounds(item), "volume_mm3": _assert_solid(item, label)}


def _one(values, label):
    values = list(values)
    if len(values) != 1:
        raise AssertionError("Expected one " + label + ", found " + str(len(values)))
    return values[0]


def _sha256(path):
    stream = open(path, "rb")
    try:
        return hashlib.sha256(stream.read()).hexdigest().lower()
    finally:
        stream.close()


def _direct_components(root):
    return [component for component in root.GetDescendants[Component]() if component.Parent == root]


def _direct_bodies(root):
    return [body for body in root.GetDescendants[DesignBody]() if body.Parent == root]


def _read_action(ident):
    if not isinstance(ACTION_DIR, basestring) or not ACTION_DIR.strip():
        raise ValueError("ACTION_DIR must be supplied by the host")
    path = os.path.join(ACTION_DIR, ident.lower() + ".scscript")
    stream = open(path, "rb")
    try:
        archive_bytes = stream.read()
    finally:
        stream.close()
    archive_hash = hashlib.sha256(archive_bytes).hexdigest()
    archive = zipfile.ZipFile(path, "r")
    try:
        source = archive.read("_script")
    finally:
        archive.close()
    return source, archive_hash


def _call(ident, params, expect_rejection=False):
    source, archive_hash = _read_action(ident)
    event = {
        "id": ident,
        "source_sha256": hashlib.sha256(source).hexdigest(),
        "archive_sha256": archive_hash,
        "status": "failed",
    }
    events.append(event)
    scope = dict(globals())
    scope["ATOMIC_INPUT"] = params
    try:
        code = compile(source, ident + "::_script", "exec")
        exec(code, scope, scope)
        if "ATOMIC_OUTPUT" not in scope:
            raise RuntimeError("Atomic script did not publish ATOMIC_OUTPUT")
    except ValueError:
        if expect_rejection:
            event["status"] = "rejected"
            event["reason"] = str(traceback.format_exc())
            return None
        event["status"] = "failed"
        event["reason"] = traceback.format_exc()
        raise
    except:
        event["status"] = "failed"
        event["reason"] = traceback.format_exc()
        raise
    if expect_rejection:
        event["status"] = "failed"
        event["reason"] = "Expected the atomic action to reject its input"
        raise AssertionError("Expected rejection: " + ident)
    event["status"] = "executed"
    return scope["ATOMIC_OUTPUT"]


def _group(group_id, action_ids, function):
    result = {"id": group_id, "actions": list(action_ids), "status": "failed"}
    tests.append(result)
    try:
        checks = function()
        if checks is None:
            checks = {}
        if not isinstance(checks, dict):
            checks = {"result": checks}
        result["status"] = "passed"
        result["checks"] = checks
    except:
        result["error"] = traceback.format_exc()
    return result


def _validate_configuration():
    if not isinstance(IMPORT_SOURCE, basestring) or not IMPORT_SOURCE.strip():
        raise ValueError("IMPORT_SOURCE must be supplied by the host")
    if not isinstance(IMPORT_SHA256, basestring) or len(IMPORT_SHA256) != 64:
        raise ValueError("IMPORT_SHA256 must be a 64-character hexadecimal digest")
    if any(character not in "0123456789abcdefABCDEF" for character in IMPORT_SHA256):
        raise ValueError("IMPORT_SHA256 must be hexadecimal")
    if not isinstance(IMPORT_EXPECTED_BODY_SIGNATURES, (list, tuple)) or not IMPORT_EXPECTED_BODY_SIGNATURES:
        raise ValueError("Expected body signatures must be supplied by the host")
    _finite(IMPORT_BBOX_TOLERANCE_MM, "IMPORT_BBOX_TOLERANCE_MM")
    _finite(IMPORT_VOLUME_TOLERANCE_MM3, "IMPORT_VOLUME_TOLERANCE_MM3")
    if float(IMPORT_BBOX_TOLERANCE_MM) < 0 or float(IMPORT_VOLUME_TOLERANCE_MM3) < 0:
        raise ValueError("Import tolerances must be nonnegative")
    for signature in IMPORT_EXPECTED_BODY_SIGNATURES:
        if not isinstance(signature, dict) or "bbox_mm" not in signature or "volume_mm3" not in signature:
            raise ValueError("Each expected body signature requires bbox_mm and volume_mm3")
        if len(signature["bbox_mm"]) != 6:
            raise ValueError("Expected bbox_mm requires six coordinates")
        for value in signature["bbox_mm"]:
            _finite(value, "expected bbox_mm")
        if _finite(signature["volume_mm3"], "expected volume_mm3") <= 0:
            raise ValueError("Expected volume_mm3 must be positive")


def _base_params(source_path, source_sha256):
    return {
        "source_path": source_path,
        "source_sha256": source_sha256,
        "expected_body_count": len(IMPORT_EXPECTED_BODY_SIGNATURES),
        "expected_body_signatures": IMPORT_EXPECTED_BODY_SIGNATURES,
        "bbox_tolerance_mm": IMPORT_BBOX_TOLERANCE_MM,
        "volume_tolerance_mm3": IMPORT_VOLUME_TOLERANCE_MM3,
    }


def _assert_empty_root(root, label):
    components = _direct_components(root)
    bodies = _direct_bodies(root)
    if components or bodies:
        raise AssertionError(label + " requires a fresh empty root")
    return {"component_count": len(components), "body_count": len(bodies)}


def _test_negative_hash():
    root = GetRootPart()
    _assert_empty_root(root, "negative hash test")
    actual_hash = _sha256(IMPORT_SOURCE)
    wrong_hash = "0" * 64 if actual_hash != "0" * 64 else "1" * 64
    _call("MA-35", _base_params(IMPORT_SOURCE, wrong_hash), True)
    _assert_empty_root(root, "negative hash postcondition")
    return {"hash_rejected": True, "component_count_unchanged": True}


def _test_negative_extension():
    root = GetRootPart()
    _assert_empty_root(root, "negative extension test")
    invalid_path = IMPORT_SOURCE + ".step"
    _call("MA-35", _base_params(invalid_path, IMPORT_SHA256), True)
    _assert_empty_root(root, "negative extension postcondition")
    return {"extension_rejected": True, "component_count_unchanged": True}


def _test_positive_import():
    root = GetRootPart()
    _assert_empty_root(root, "positive import test")
    source_before = _sha256(IMPORT_SOURCE)
    if source_before != IMPORT_SHA256.lower():
        raise AssertionError("Injected source digest does not match the source before import")
    before_components = _direct_components(root)
    output = _call("MA-35", _base_params(IMPORT_SOURCE, IMPORT_SHA256))
    after_components = _direct_components(root)
    new_components = [component for component in after_components if component not in before_components]
    if len(new_components) != 1:
        raise AssertionError("Expected one new direct-root imported component")
    component = new_components[0]
    if component.Parent != root:
        raise AssertionError("Imported component is not a direct child of the root")
    if output.get("component") not in new_components:
        raise AssertionError("Action output component is not the new direct-root component")
    if list(component.Content.Components):
        raise AssertionError("Imported fixture contains nested components")

    bodies = list(component.Content.Bodies)
    if len(bodies) != len(IMPORT_EXPECTED_BODY_SIGNATURES):
        raise AssertionError("Imported body count differs from injected expectations")
    measurements = [_measure(body, "imported body") for body in bodies]
    remaining = list(range(len(measurements)))
    for signature in IMPORT_EXPECTED_BODY_SIGNATURES:
        matches = [
            index for index in remaining
            if _bbox_matches(
                measurements[index]["bbox_mm"],
                signature["bbox_mm"],
                float(IMPORT_BBOX_TOLERANCE_MM),
            )
            and abs(measurements[index]["volume_mm3"] - float(signature["volume_mm3"]))
            <= float(IMPORT_VOLUME_TOLERANCE_MM3)
        ]
        if len(matches) != 1:
            raise AssertionError("Expected body signature did not resolve uniquely")
        remaining.remove(matches[0])
    if remaining:
        raise AssertionError("Imported body measurements did not cover every expectation")

    source_after = _sha256(IMPORT_SOURCE)
    if source_after != source_before or source_after != IMPORT_SHA256.lower():
        raise AssertionError("Import source changed during the positive test")
    return {
        "source_sha256": source_after,
        "new_component_count": len(new_components),
        "component_count_after": len(after_components),
        "body_count": len(bodies),
        "measurements": measurements,
    }


def _run_suite():
    _group("negative-source-hash", ["MA-35"], _test_negative_hash)
    _group("negative-source-extension", ["MA-35"], _test_negative_extension)
    _group("positive-native-import", ["MA-35"], _test_positive_import)


try:
    if not isinstance(REPORT, basestring) or not REPORT.strip():
        raise ValueError("REPORT must be supplied by the host")
    _validate_configuration()
    _run_suite()
except:
    report["error"] = traceback.format_exc()
finally:
    report["status"] = "passed" if tests and not report.get("error") else "failed"
    for test in tests:
        if test.get("status") != "passed":
            report["status"] = "failed"
            break
    try:
        stream = open(REPORT, "wb")
        try:
            stream.write(json.dumps(report, indent=2).encode("utf-8"))
        finally:
            stream.close()
    except:
        report["status"] = "failed"
        report["error"] = traceback.format_exc()
    print(json.dumps(report))
