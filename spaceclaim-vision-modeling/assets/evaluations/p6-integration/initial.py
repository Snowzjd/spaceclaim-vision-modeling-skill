# Generated P6 generic-fallback V21/IronPython 2.7 source.
from __future__ import print_function

import datetime
import json
import math
import os
import traceback

MODEL_PATH = ""
REPORT_PATH = ""
if not os.path.isabs(MODEL_PATH) or not os.path.isabs(REPORT_PATH):
    raise ValueError("Configure explicit run-owned absolute output paths and repackage before execution")

from SpaceClaim.Api.V21 import *
from SpaceClaim.Api.V21.Geometry import CurveSegment, Plane, Profile
from SpaceClaim.Api.V21.Modeler import Body as ModelerBody
from System import Array


CASE_ID = "p6-request-A-right-triangular-prism"
BODY_NAME = "RightTriangularPrism"
PROFILE_VERTICES_MM = [[0.0, 0.0, 0.0], [19.0, 0.0, 0.0], [0.0, 13.0, 0.0]]
EXTRUSION_DISTANCE_MM = 7.0
TRANSLATION_MM = [4.0, -3.0, 2.0]
EXPECTED_BEFORE_BBOX_MM = [0.0, 0.0, 0.0, 19.0, 13.0, 7.0]
EXPECTED_AFTER_BBOX_MM = [4.0, -3.0, 2.0, 23.0, 10.0, 9.0]
EXPECTED_VOLUME_MM3 = 864.5
BBOX_TOLERANCE_MM = 0.001
VOLUME_TOLERANCE_MM3 = 0.001
MM_PER_M = 1000.0
MM3_PER_M3 = 1000000000.0


def near(left, right, tolerance):
    return abs(float(left) - float(right)) <= float(tolerance)


def point_m(values_mm):
    return Point.Create(
        float(values_mm[0]) / MM_PER_M,
        float(values_mm[1]) / MM_PER_M,
        float(values_mm[2]) / MM_PER_M,
    )


def point_mm(point):
    return [
        float(point.X) * MM_PER_M,
        float(point.Y) * MM_PER_M,
        float(point.Z) * MM_PER_M,
    ]


def shape_bbox_mm(shape):
    try:
        box = shape.GetBoundingBox(Matrix.Identity, True)
    except:
        box = shape.GetBoundingBox(Matrix.Identity)
    return tuple(point_mm(box.MinCorner) + point_mm(box.MaxCorner))


def body_volume_mm3(body):
    return float(body.Shape.Volume) * MM3_PER_M3


def current_bodies():
    return list(GetRootPart().GetAllBodies())


def bbox_matches(actual, expected):
    return all(
        near(actual[index], expected[index], BBOX_TOLERANCE_MM)
        for index in range(6)
    )


def write_report(path, report):
    if os.path.exists(path):
        raise ValueError("Refusing to overwrite an existing run report: %s" % path)
    directory = os.path.dirname(path)
    if directory and not os.path.isdir(directory):
        os.makedirs(directory)
    rendered = json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True)
    stream = open(path, "wb")
    try:
        stream.write((rendered + "\r\n").encode("utf-8"))
    finally:
        stream.close()
    print(rendered)


def stage(report, name, status, message=""):
    report["stages"].append({"name": name, "status": status, "message": message})


def body_row(body):
    bounds = shape_bbox_mm(body.Shape)
    return {
        "name": body.Name,
        "bbox_min_mm": list(bounds[:3]),
        "bbox_max_mm": list(bounds[3:]),
        "volume_mm3": body_volume_mm3(body),
        "face_count": len(list(body.Faces)),
        "edge_count": len(list(body.Edges)),
    }


def validate_body(body, expected_bbox):
    if not body.Shape.IsClosed or int(body.Shape.PieceCount) < 1:
        raise RuntimeError("Expected one nonempty closed solid")
    if not bbox_matches(shape_bbox_mm(body.Shape), expected_bbox):
        raise RuntimeError("Body bounding box does not match the accepted contract")
    if not near(body_volume_mm3(body), EXPECTED_VOLUME_MM3, VOLUME_TOLERANCE_MM3):
        raise RuntimeError("Body volume does not match the accepted contract")
    if len(list(body.Faces)) != 5 or len(list(body.Edges)) != 9:
        raise RuntimeError("Right triangular prism topology must be 5 faces and 9 edges")


def create_profile():
    plane = Plane.Create(
        Frame.Create(Point.Create(0.0, 0.0, 0.0), Direction.DirX, Direction.DirY)
    )
    curves = [
        CurveSegment.Create(
            point_m(PROFILE_VERTICES_MM[index]),
            point_m(PROFILE_VERTICES_MM[(index + 1) % len(PROFILE_VERTICES_MM)]),
        )
        for index in range(len(PROFILE_VERTICES_MM))
    ]
    return Profile(plane, Array[ITrimmedCurve](curves))


def translate_body(body):
    distance = math.sqrt(sum(value * value for value in TRANSLATION_MM))
    if distance <= 1.0e-12:
        raise ValueError("Translation vector must be nonzero")
    direction = Direction.Create(
        TRANSLATION_MM[0] / distance,
        TRANSLATION_MM[1] / distance,
        TRANSLATION_MM[2] / distance,
    )
    result = Move.Translate(
        BodySelection.Create(body), direction, distance / MM_PER_M, MoveOptions()
    )
    if result is not None and hasattr(result, "Success") and not result.Success:
        raise RuntimeError("Move.Translate reported failure")


def fresh_report():
    return {
        "schema_version": 1,
        "case_id": CASE_ID,
        "status": "failed",
        "target": {
            "spaceclaim_release": "2022 R1",
            "api_version": "V21",
            "python_runtime": "IronPython 2.7",
        },
        "stages": [],
        "bodies": [],
        "outputs": {"native_model_path": MODEL_PATH, "report_path": REPORT_PATH},
        "evidence_layers": {
            "static_archive": "not_tested",
            "spaceclaim_execution": "not_tested",
            "geometry_measurements": "not_tested",
            "native_save": "not_tested",
            "native_reopen": "not_tested",
            "visual_review": "not_tested",
            "requested_export": "not_tested",
        },
        "validation_boundary": (
            "This report would be emitted by an executed script. Preparation-only "
            "evaluation does not create this runtime report, reopen a model, review "
            "the viewport, or produce an export."
        ),
    }


def prepare_paths():
    model_path = os.path.abspath(MODEL_PATH).replace("\\", "/")
    report_path = os.path.abspath(REPORT_PATH).replace("\\", "/")
    if not model_path.lower().endswith(".scdoc"):
        raise ValueError("MODEL_PATH must end with .scdoc")
    if not report_path.lower().endswith(".json"):
        raise ValueError("REPORT_PATH must end with .json")
    if model_path.lower() == report_path.lower():
        raise ValueError("MODEL_PATH and REPORT_PATH must be different")
    for path in (model_path, report_path):
        if os.path.exists(path):
            raise ValueError("Refusing to overwrite existing run output: %s" % path)
        directory = os.path.dirname(path)
        if directory and not os.path.isdir(directory):
            os.makedirs(directory)
    return model_path, report_path


def run():
    report = fresh_report()
    execution_started = False
    save_attempted = False
    report_path = REPORT_PATH
    try:
        model_path, report_path = prepare_paths()
        report["outputs"] = {"native_model_path": model_path, "report_path": report_path}
        stage(report, "parameters_and_paths_validated", "passed")

        before = current_bodies()
        if before:
            raise RuntimeError("No-baseline run requires a new unsaved design with no bodies")
        stage(report, "clean_design_confirmed", "passed")
        execution_started = True

        profile = create_profile()
        transient = ModelerBody.ExtrudeProfile(
            profile, EXTRUSION_DISTANCE_MM / MM_PER_M
        )
        if transient is None or not transient.IsClosed:
            raise RuntimeError("ModelerBody.ExtrudeProfile did not produce a closed solid")
        stage(report, "profile_extruded", "passed")

        created = DesignBody.Create(GetRootPart(), BODY_NAME, transient)
        bodies = current_bodies()
        if len(bodies) != 1 or created not in bodies or created.Name != BODY_NAME:
            raise RuntimeError("DesignBody.Create did not produce the declared body")
        validate_body(created, EXPECTED_BEFORE_BBOX_MM)
        stage(report, "transient_body_attached", "passed")

        translate_body(created)
        bodies = current_bodies()
        matches = [
            body
            for body in bodies
            if body.Name == BODY_NAME
            and bbox_matches(shape_bbox_mm(body.Shape), EXPECTED_AFTER_BBOX_MM)
            and near(body_volume_mm3(body), EXPECTED_VOLUME_MM3, VOLUME_TOLERANCE_MM3)
        ]
        if len(matches) != 1:
            raise RuntimeError("Semantic post-translation selection expected one body")
        body = matches[0]
        validate_body(body, EXPECTED_AFTER_BBOX_MM)
        report["bodies"] = [body_row(body)]
        report["evidence_layers"]["spaceclaim_execution"] = "passed"
        report["evidence_layers"]["geometry_measurements"] = "passed"
        stage(report, "geometry_validated", "passed")

        save_attempted = True
        save_result = DocumentSave.Execute(model_path)
        if (
            save_result is None
            or not save_result.Success
            or not os.path.isfile(model_path)
            or os.path.getsize(model_path) == 0
        ):
            raise RuntimeError("DocumentSave.Execute did not produce the expected file")
        report["evidence_layers"]["native_save"] = "passed"
        stage(report, "native_model_saved", "passed")
        report["status"] = "passed"
        write_report(report_path, report)
    except Exception as exc:
        if execution_started and report["evidence_layers"]["spaceclaim_execution"] == "not_tested":
            report["evidence_layers"]["spaceclaim_execution"] = "failed"
        if save_attempted and report["evidence_layers"]["native_save"] == "not_tested":
            report["evidence_layers"]["native_save"] = "failed"
        report["error"] = {"type": exc.__class__.__name__, "message": str(exc)}
        stage(report, "failed", "failed", traceback.format_exc())
        try:
            write_report(report_path, report)
        except Exception:
            print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
        raise


run()
