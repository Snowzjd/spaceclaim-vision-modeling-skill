# Generated V21/IronPython 2.7 rectangular-prism script.
from __future__ import print_function

import datetime
import json
import os
import traceback

from SpaceClaim.Api.V21 import *


CASE_ID = "v03-atomic-rectangular-prism"
BODY_NAME = "ATOMIC_PRISM"
MINIMUM_CORNER_MM = [10.0,-5.0,2.0]
SIZE_MM = [40.0,30.0,12.0]
EXPECTED_BBOX_MM = [10.0,-5.0,2.0,50.0,25.0,14.0]
EXPECTED_VOLUME_MM3 = 14400.0
MODEL_PATH = "C:/Users/Public/Documents/SpaceClaimVisionModeling/v03-atomic-rectangular-prism/run-001/rectangular-prism.scdoc"
REPORT_PATH = "C:/Users/Public/Documents/SpaceClaimVisionModeling/v03-atomic-rectangular-prism/run-001/validation-runtime-report.json"
BBOX_TOLERANCE_MM = 0.001
VOLUME_TOLERANCE_MM3 = 0.001
MM_PER_M = 1000.0
MM3_PER_M3 = 1.0e9


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


def bbox_matches(actual):
    return all(
        near(actual[index], EXPECTED_BBOX_MM[index], BBOX_TOLERANCE_MM)
        for index in range(6)
    )


def write_report(path, report):
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


def body_row(body):
    bbox = shape_bbox_mm(body.Shape)
    return {
        "name": body.Name,
        "bbox_min_mm": list(bbox[:3]),
        "bbox_max_mm": list(bbox[3:]),
        "volume_mm3": body_volume_mm3(body),
    }


def validate_body(body):
    bbox = shape_bbox_mm(body.Shape)
    if not bbox_matches(bbox):
        raise ValueError("Body bounding box does not match the accepted contract: %r" % (bbox,))
    volume = body_volume_mm3(body)
    if not near(volume, EXPECTED_VOLUME_MM3, VOLUME_TOLERANCE_MM3):
        raise ValueError("Body volume %.12g mm3 does not match %.12g mm3." % (volume, EXPECTED_VOLUME_MM3))
    if len(list(body.Faces)) != 6:
        raise ValueError("A rectangular prism must have exactly 6 faces.")
    if len(list(body.Edges)) != 12:
        raise ValueError("A rectangular prism must have exactly 12 edges.")


def run():
    report = {
        "schema_version": 1,
        "case_id": CASE_ID,
        "status": "failed",
        "generated_at_utc": datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "target": {"spaceclaim_release": "2022 R1", "api_version": "V21", "python_runtime": "IronPython 2.7"},
        "stages": [],
        "bodies": [],
        "named_face_groups": [],
        "features": [],
        "outputs": {"native_model_path": MODEL_PATH, "report_path": REPORT_PATH},
        "evidence_layers": {
            "static_archive": "not_tested",
            "spaceclaim_execution": "not_tested",
            "geometry_measurements": "not_tested",
            "native_save": "not_tested",
            "native_reopen": "not_tested",
            "neutral_export": "not_tested",
        },
        "validation_boundary": "This read-only report checks the currently open model. Save, reopen, and visual-review status must be recorded independently.",
    }
    try:
        report_path = os.path.abspath(REPORT_PATH).replace("\\", "/")
        if os.path.exists(report_path):
            raise ValueError("Refusing to overwrite existing validation report: %s" % report_path)
        bodies = current_bodies()
        if len(bodies) != 1:
            raise ValueError("Expected exactly one body, found %d." % len(bodies))
        body = bodies[0]
        if body.Name != BODY_NAME:
            raise ValueError("Body name does not match the accepted contract.")
        validate_body(body)
        report["bodies"] = [body_row(body)]
        report["evidence_layers"]["spaceclaim_execution"] = "passed"
        report["evidence_layers"]["geometry_measurements"] = "passed"
        report["stages"].append({"name": "read_only_geometry_validated", "status": "passed", "message": ""})
        report["status"] = "passed"
        write_report(report_path, report)
    except Exception as exc:
        if report["evidence_layers"]["spaceclaim_execution"] == "not_tested":
            report["evidence_layers"]["spaceclaim_execution"] = "failed"
        report["error"] = {"type": exc.__class__.__name__, "message": str(exc)}
        report["stages"].append({"name": "failed", "status": "failed", "message": traceback.format_exc()})
        try:
            write_report(REPORT_PATH, report)
        except:
            print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
        raise


run()
