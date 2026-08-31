# SpaceClaim 2022 R1 / API V21 candidate build script for case 001.
# IronPython 2.7 compatible. Historical controlled evidence and the current
# package difference are recorded in runtime-evidence.md.
# Start from a new unsaved design. Both run-owned output paths must not exist.

from __future__ import print_function

import datetime
import json
import os
import traceback

from SpaceClaim.Api.V21 import *


CASE_ID = "001-offset-block-array"
SPACECLAIM_RELEASE = "2022 R1"
API_VERSION = "V21"
PYTHON_RUNTIME = "IronPython 2.7"

OUTPUT_MODEL_PATH = None  # Example: "C:/runs/001-offset-block-array/model.scdoc"
REPORT_PATH = None  # Example: "C:/runs/001-offset-block-array/runtime-report.json"

LENGTH_MM = 20.0
WIDTH_MM = 8.0
HEIGHT_MM = 4.0
BBOX_TOLERANCE_MM = 0.001
VOLUME_TOLERANCE_MM3 = 0.001
NORMAL_TOLERANCE = 1.0e-6

EXPECTED_BODIES = (
    ("BLOCK_01", (0.0, 0.0, 0.0, 20.0, 8.0, 4.0)),
    ("BLOCK_02", (30.0, 3.0, 0.0, 50.0, 11.0, 4.0)),
    ("BLOCK_03", (60.0, 0.0, 0.0, 80.0, 8.0, 4.0)),
)

MM_PER_M = 1000.0
MM3_PER_M3 = 1.0e9


def fresh_report():
    return {
        "schema_version": 1,
        "case_id": CASE_ID,
        "status": "failed",
        "generated_at_utc": datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "target": {
            "spaceclaim_release": SPACECLAIM_RELEASE,
            "api_version": API_VERSION,
            "python_runtime": PYTHON_RUNTIME,
        },
        "stages": [],
        "bodies": [],
        "named_face_groups": [],
        "outputs": {
            "native_model_path": OUTPUT_MODEL_PATH or "<unset>",
            "report_path": REPORT_PATH or "<unset>",
        },
        "evidence_layers": {
            "static_archive": "not_tested",
            "spaceclaim_execution": "not_tested",
            "geometry_measurements": "not_tested",
            "native_save": "not_tested",
            "native_reopen": "not_tested",
            "neutral_export": "not_tested",
        },
        "validation_boundary": (
            "This report is emitted by the case 001 V21 build script. Native reopen "
            "and requested export layers require separate evidence."
        ),
    }


def stage(report, name, status, message=""):
    report["stages"].append({"name": name, "status": status, "message": message})


def near(left, right, tolerance):
    return abs(float(left) - float(right)) <= float(tolerance)


def point_m(x_mm, y_mm, z_mm):
    return Point.Create(x_mm / MM_PER_M, y_mm / MM_PER_M, z_mm / MM_PER_M)


def point_mm(point):
    return [float(point.X) * MM_PER_M, float(point.Y) * MM_PER_M, float(point.Z) * MM_PER_M]


def shape_bbox_mm(shape):
    try:
        box = shape.GetBoundingBox(Matrix.Identity, True)
    except:
        box = shape.GetBoundingBox(Matrix.Identity)
    return tuple(point_mm(box.MinCorner) + point_mm(box.MaxCorner))


def bbox_near(actual, expected):
    return all(
        near(actual[index], expected[index], BBOX_TOLERANCE_MM)
        for index in range(6)
    )


def body_volume_mm3(body):
    return float(body.Shape.Volume) * MM3_PER_M3


def current_bodies():
    return list(GetRootPart().GetAllBodies())


def current_groups():
    return list(WindowHelper.GetGroups())


def require_unique(items, predicate, label):
    matches = [item for item in items if predicate(item)]
    if len(matches) != 1:
        raise ValueError("Expected one %s, found %d" % (label, len(matches)))
    return matches[0]


def validate_parameters():
    if not near(LENGTH_MM * WIDTH_MM * HEIGHT_MM, 640.0, VOLUME_TOLERANCE_MM3):
        raise ValueError("Block parameter volume must be 640 mm3.")
    if BBOX_TOLERANCE_MM <= 0 or VOLUME_TOLERANCE_MM3 <= 0:
        raise ValueError("Validation tolerances must be positive.")
    if len(set(item[0] for item in EXPECTED_BODIES)) != len(EXPECTED_BODIES):
        raise ValueError("Expected body names must be unique.")


def normalized_new_path(value, suffix, label, allow_existing=False):
    if not value or not isinstance(value, basestring):
        raise ValueError("%s must be set before the authorized run." % label)
    path = os.path.abspath(value)
    if not path.lower().endswith(suffix):
        raise ValueError("%s must end with %s." % (label, suffix))
    if os.path.exists(path) and not allow_existing:
        raise ValueError("%s already exists; refusing to overwrite: %s" % (label, path))
    return path.replace("\\", "/")


def prepare_output_paths(report):
    model_path = normalized_new_path(OUTPUT_MODEL_PATH, ".scdoc", "OUTPUT_MODEL_PATH")
    report_path = normalized_new_path(REPORT_PATH, ".json", "REPORT_PATH")
    if model_path.lower() == report_path.lower():
        raise ValueError("Model and report paths must be different.")
    for path in (model_path, report_path):
        directory = os.path.dirname(path)
        if directory and not os.path.isdir(directory):
            os.makedirs(directory)
    report["outputs"]["native_model_path"] = model_path
    report["outputs"]["report_path"] = report_path
    return model_path, report_path


def create_independent_blocks():
    for unused_name, bbox in EXPECTED_BODIES:
        result = BlockBody.Create(
            point_m(bbox[0], bbox[1], bbox[2]),
            point_m(bbox[3], bbox[4], bbox[5]),
            ExtrudeType.ForceIndependent,
        )
        if not result.Success or result.CreatedBody is None:
            raise RuntimeError("BlockBody.Create failed for bbox %r" % (bbox,))


def identify_and_name_bodies():
    bodies = current_bodies()
    if len(bodies) != len(EXPECTED_BODIES):
        raise ValueError("Expected 3 bodies, found %d." % len(bodies))
    named = {}
    for expected_name, expected_bbox in EXPECTED_BODIES:
        body = require_unique(
            bodies,
            lambda candidate, box=expected_bbox: bbox_near(
                shape_bbox_mm(candidate.Shape), box
            ),
            "body at bbox %r" % (expected_bbox,),
        )
        volume = body_volume_mm3(body)
        if not near(volume, 640.0, VOLUME_TOLERANCE_MM3):
            raise ValueError("%s volume %.9g mm3 does not match 640 mm3." % (expected_name, volume))
        rename_result = RenameObject.Execute(BodySelection.Create(body), expected_name)
        if not rename_result.Success:
            raise RuntimeError("Body rename failed: %s" % expected_name)
        named[expected_name] = body
    if sorted(body.Name for body in current_bodies()) != sorted(named):
        raise ValueError("Final body names do not match the naming contract.")
    return named


def outward_normal(face):
    geometry = face.Shape.Geometry
    if geometry.GetType().Name != "Plane":
        raise ValueError("Expected a planar end face.")
    direction = geometry.Frame.DirZ
    sign = -1.0 if face.Shape.IsReversed else 1.0
    return (sign * float(direction.X), sign * float(direction.Y), sign * float(direction.Z))


def find_end_face(body, x_mm, expected_normal_x, label):
    def matches(face):
        bbox = shape_bbox_mm(face.Shape)
        if not near(bbox[0], x_mm, BBOX_TOLERANCE_MM):
            return False
        if not near(bbox[3], x_mm, BBOX_TOLERANCE_MM):
            return False
        try:
            normal = outward_normal(face)
        except:
            return False
        return (
            near(normal[0], expected_normal_x, NORMAL_TOLERANCE)
            and near(normal[1], 0.0, NORMAL_TOLERANCE)
            and near(normal[2], 0.0, NORMAL_TOLERANCE)
        )

    return require_unique(list(body.Faces), matches, label)


def create_named_face_group(face, final_name):
    result = NamedSelection.Create(FaceSelection.Create(face), Selection.Empty())
    if not result.Success or result.CreatedNamedSelection is None:
        raise RuntimeError("Named selection creation failed: %s" % final_name)
    created = result.CreatedNamedSelection
    rename_result = NamedSelection.Rename(created.Name, final_name)
    if not rename_result.Success:
        raise RuntimeError("Named selection rename failed: %s" % final_name)
    return created


def validate_and_report_geometry(report, named_bodies):
    body_rows = []
    for name in sorted(named_bodies):
        body = named_bodies[name]
        bbox = shape_bbox_mm(body.Shape)
        body_rows.append(
            {
                "name": name,
                "bbox_min_mm": list(bbox[:3]),
                "bbox_max_mm": list(bbox[3:]),
                "volume_mm3": body_volume_mm3(body),
            }
        )
    report["bodies"] = body_rows

    groups_by_name = dict((group.Name, group) for group in current_groups())
    if set(groups_by_name) != set(("INLET", "OUTLET")):
        raise ValueError("Final named face groups must be exactly INLET and OUTLET.")
    group_rows = []
    for name in ("INLET", "OUTLET"):
        count = int(groups_by_name[name].Members.Count)
        if count != 1:
            raise ValueError("%s expected one member, found %d." % (name, count))
        group_rows.append({"name": name, "member_count": count})
    report["named_face_groups"] = group_rows


def write_report(path, report):
    rendered = json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True)
    stream = open(path, "wb")
    try:
        stream.write((rendered + "\r\n").encode("utf-8"))
    finally:
        stream.close()
    print(rendered)


def run():
    report = fresh_report()
    report_path = None
    save_attempted = False
    execution_started = False
    try:
        validate_parameters()
        model_path, report_path = prepare_output_paths(report)
        stage(report, "parameters_and_paths_validated", "passed")

        execution_started = True
        if current_bodies() or current_groups():
            raise ValueError("Case 001 must start from a clean model with no bodies or groups.")
        stage(report, "clean_model_confirmed", "passed")

        create_independent_blocks()
        named_bodies = identify_and_name_bodies()
        stage(report, "bodies_created_and_named", "passed")

        inlet_face = find_end_face(named_bodies["BLOCK_01"], 0.0, -1.0, "INLET face")
        outlet_face = find_end_face(named_bodies["BLOCK_03"], 80.0, 1.0, "OUTLET face")
        create_named_face_group(inlet_face, "INLET")
        create_named_face_group(outlet_face, "OUTLET")
        validate_and_report_geometry(report, named_bodies)
        report["evidence_layers"]["spaceclaim_execution"] = "passed"
        report["evidence_layers"]["geometry_measurements"] = "passed"
        stage(report, "geometry_and_groups_validated", "passed")

        save_attempted = True
        save_result = DocumentSave.Execute(model_path)
        if not save_result.Success or not os.path.isfile(model_path):
            raise RuntimeError("Native save did not produce the expected .scdoc file.")
        report["evidence_layers"]["native_save"] = "passed"
        stage(report, "native_model_saved", "passed")

        report["status"] = "passed"
        write_report(report_path, report)
        return report
    except Exception as exc:
        report["status"] = "failed"
        if (
            execution_started
            and report["evidence_layers"]["spaceclaim_execution"] == "not_tested"
        ):
            report["evidence_layers"]["spaceclaim_execution"] = "failed"
        if (
            save_attempted
            and report["evidence_layers"]["native_save"] == "not_tested"
        ):
            report["evidence_layers"]["native_save"] = "failed"
        report["error"] = {"type": exc.__class__.__name__, "message": str(exc)}
        stage(report, "failed", "failed", traceback.format_exc())
        if report_path:
            try:
                write_report(report_path, report)
            except:
                print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
        else:
            print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
        raise


run()
