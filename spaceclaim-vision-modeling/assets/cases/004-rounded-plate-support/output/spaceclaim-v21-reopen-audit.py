# SpaceClaim 2022 R1 / API V21 read-only native-reopen audit for case 004.
# IronPython 2.7 compatible. This script never edits or saves the active model.
# Set NATIVE_MODEL_PATH and REPORT_PATH only in a run-owned execution copy.

from __future__ import print_function

import datetime
import json
import os
import traceback

from SpaceClaim.Api.V21 import *


CASE_ID = "004-rounded-plate-support"
SPACECLAIM_RELEASE = "2022 R1"
API_VERSION = "V21"
PYTHON_RUNTIME = "IronPython 2.7"

NATIVE_MODEL_PATH = None  # Example: "C:/runs/004-rounded-plate-support/model.scdoc"
REPORT_PATH = None  # Example: "C:/runs/004-rounded-plate-support/reopen-runtime-report.json"

PLATE_LENGTH_MM = 120.0
PLATE_WIDTH_MM = 80.0
PLATE_THICKNESS_MM = 10.0
CORNER_RADIUS_MM = 10.0
SUPPORT_DIAMETER_MM = 30.0
SUPPORT_HEIGHT_MM = 50.0
HOLE_DIAMETER_MM = 8.0
HOLE_EDGE_OFFSET_MM = 15.0
SUPPORT_CENTER_X_MM = PLATE_LENGTH_MM / 2.0
SUPPORT_CENTER_Y_MM = PLATE_WIDTH_MM / 2.0

BBOX_TOLERANCE_MM = 0.001
VOLUME_TOLERANCE_MM3 = 5.0
FEATURE_TOLERANCE_MM = 0.001
EXPECTED_VOLUME_MM3 = 128473.8907081775

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
        "features": [],
        "interpretation_metadata": {
            "input_type": "text_description_in_image",
            "source_label": "case_3",
            "repository_case_id": CASE_ID,
            "support_height_interpretation": "50_mm_above_plate_top_total_height_60_mm",
            "support_and_plate": "united_single_body",
            "unspecified_edge_treatments": "not_added",
        },
        "outputs": {
            "native_model_path": NATIVE_MODEL_PATH or "<unset>",
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
            "Read-only audit of the active reopened case 004 native document. "
            "It does not modify or save the model. The support-height "
            "interpretation and omitted unspecified features remain explicit."
        ),
    }


def stage(report, name, status, message=""):
    report["stages"].append({"name": name, "status": status, "message": message})


def near(left, right, tolerance):
    return abs(float(left) - float(right)) <= float(tolerance)


def point_mm(point):
    return [
        float(point.X) * MM_PER_M,
        float(point.Y) * MM_PER_M,
        float(point.Z) * MM_PER_M,
    ]


def shape_bbox_mm(shape):
    box = shape.GetBoundingBox(Matrix.Identity)
    return point_mm(box.MinCorner) + point_mm(box.MaxCorner)


def body_volume_mm3(body):
    return float(body.Shape.Volume) * MM3_PER_M3


def require_count(items, count, label):
    if len(items) != count:
        raise ValueError("Expected %d %s, found %d." % (count, label, len(items)))
    return items


def assert_bbox(actual, expected, tolerance, label):
    if not all(near(actual[index], expected[index], tolerance) for index in range(6)):
        raise ValueError("%s bounding box mismatch: %r" % (label, actual))


def normalized_path(value, suffix, label, must_exist):
    if not value or not isinstance(value, basestring):
        raise ValueError("%s must be set before the reopen audit." % label)
    path = os.path.abspath(value)
    if not path.lower().endswith(suffix):
        raise ValueError("%s must end with %s." % (label, suffix))
    if must_exist and not os.path.isfile(path):
        raise ValueError("%s does not exist: %s" % (label, path))
    if not must_exist and os.path.exists(path):
        raise ValueError("%s already exists; refusing to overwrite: %s" % (label, path))
    return path.replace("\\", "/")


def hole_centers():
    return [
        (HOLE_EDGE_OFFSET_MM, HOLE_EDGE_OFFSET_MM),
        (PLATE_LENGTH_MM - HOLE_EDGE_OFFSET_MM, HOLE_EDGE_OFFSET_MM),
        (HOLE_EDGE_OFFSET_MM, PLATE_WIDTH_MM - HOLE_EDGE_OFFSET_MM),
        (
            PLATE_LENGTH_MM - HOLE_EDGE_OFFSET_MM,
            PLATE_WIDTH_MM - HOLE_EDGE_OFFSET_MM,
        ),
    ]


def face_record(face):
    geometry = face.Shape.Geometry
    kind = geometry.GetType().Name
    record = {"kind": kind, "bbox": shape_bbox_mm(face.Shape)}
    if kind == "Cylinder":
        record["radius_mm"] = abs(float(geometry.Radius)) * MM_PER_M
    return record


def cylinder_records(records, expected_radius):
    return [
        item
        for item in records
        if item["kind"] == "Cylinder"
        and near(item["radius_mm"], expected_radius, FEATURE_TOLERANCE_MM)
    ]


def bbox_center_xy(bbox):
    return (0.5 * (bbox[0] + bbox[3]), 0.5 * (bbox[1] + bbox[4]))


def validate_features(body):
    records = [face_record(face) for face in list(body.Faces)]

    corner_faces = cylinder_records(records, CORNER_RADIUS_MM)
    require_count(corner_faces, 4, "R10 corner cylinder faces")
    expected_corner_bboxes = [
        [0.0, 0.0, 0.0, 10.0, 10.0, 10.0],
        [110.0, 0.0, 0.0, 120.0, 10.0, 10.0],
        [0.0, 70.0, 0.0, 10.0, 80.0, 10.0],
        [110.0, 70.0, 0.0, 120.0, 80.0, 10.0],
    ]
    unmatched = list(corner_faces)
    for expected in expected_corner_bboxes:
        local = [
            item
            for item in unmatched
            if all(
                near(item["bbox"][index], expected[index], FEATURE_TOLERANCE_MM)
                for index in range(6)
            )
        ]
        match = require_count(local, 1, "rounded-corner faces at %r" % expected)[0]
        unmatched.remove(match)

    support_faces = cylinder_records(records, SUPPORT_DIAMETER_MM / 2.0)
    support = require_count(support_faces, 1, "central support cylinder faces")[0]
    support_bbox = support["bbox"]
    assert_bbox(
        support_bbox,
        [
            SUPPORT_CENTER_X_MM - SUPPORT_DIAMETER_MM / 2.0,
            SUPPORT_CENTER_Y_MM - SUPPORT_DIAMETER_MM / 2.0,
            PLATE_THICKNESS_MM,
            SUPPORT_CENTER_X_MM + SUPPORT_DIAMETER_MM / 2.0,
            SUPPORT_CENTER_Y_MM + SUPPORT_DIAMETER_MM / 2.0,
            PLATE_THICKNESS_MM + SUPPORT_HEIGHT_MM,
        ],
        FEATURE_TOLERANCE_MM,
        "central support cylinder",
    )

    holes = cylinder_records(records, HOLE_DIAMETER_MM / 2.0)
    require_count(holes, 4, "mounting-hole cylinder faces")
    measured_centers = sorted(
        [
            (
                round(bbox_center_xy(item["bbox"])[0], 6),
                round(bbox_center_xy(item["bbox"])[1], 6),
            )
            for item in holes
        ]
    )
    expected_centers = sorted(
        [(round(item[0], 6), round(item[1], 6)) for item in hole_centers()]
    )
    if measured_centers != expected_centers:
        raise ValueError(
            "Mounting-hole centers do not match the edge-offset contract: %r"
            % measured_centers
        )
    for item in holes:
        bbox = item["bbox"]
        if not near(bbox[2], 0.0, FEATURE_TOLERANCE_MM) or not near(
            bbox[5], PLATE_THICKNESS_MM, FEATURE_TOLERANCE_MM
        ):
            raise ValueError("A mounting hole does not span the plate thickness.")

    return [
        {
            "name": "rounded_base_plate",
            "count": 1,
            "measurements": {
                "length_mm": PLATE_LENGTH_MM,
                "width_mm": PLATE_WIDTH_MM,
                "thickness_mm": PLATE_THICKNESS_MM,
                "corner_radius_mm": sum(item["radius_mm"] for item in corner_faces)
                / 4.0,
            },
        },
        {
            "name": "central_support",
            "count": 1,
            "measurements": {
                "diameter_mm": 2.0 * support["radius_mm"],
                "height_mm": support_bbox[5] - support_bbox[2],
                "center_x_mm": bbox_center_xy(support_bbox)[0],
                "center_y_mm": bbox_center_xy(support_bbox)[1],
            },
        },
        {
            "name": "mounting_holes",
            "count": 4,
            "measurements": {
                "diameter_mm": 2.0 * sum(item["radius_mm"] for item in holes) / 4.0,
                "edge_offset_x_mm": HOLE_EDGE_OFFSET_MM,
                "edge_offset_y_mm": HOLE_EDGE_OFFSET_MM,
                "through_length_mm": PLATE_THICKNESS_MM,
            },
        },
    ]


def validate_and_report_geometry(report, body):
    expected_bbox = [0.0, 0.0, 0.0, 120.0, 80.0, 60.0]
    bbox = shape_bbox_mm(body.Shape)
    assert_bbox(bbox, expected_bbox, BBOX_TOLERANCE_MM, "reopened body")
    report["features"] = validate_features(body)
    volume = body_volume_mm3(body)
    if not near(volume, EXPECTED_VOLUME_MM3, VOLUME_TOLERANCE_MM3):
        raise ValueError(
            "Reopened volume %.12g mm3 does not match %.12g mm3 within tolerance."
            % (volume, EXPECTED_VOLUME_MM3)
        )
    report["bodies"] = [
        {
            "name": body.Name,
            "bbox_min_mm": bbox[:3],
            "bbox_max_mm": bbox[3:],
            "volume_mm3": volume,
            "face_count": len(list(body.Faces)),
        }
    ]


def write_report(path, report):
    text = json.dumps(report, ensure_ascii=True, indent=2, sort_keys=True)
    with open(path, "w") as handle:
        handle.write(text)
        handle.write("\n")


def run():
    report = fresh_report()
    report_path = None
    try:
        model_path = normalized_path(
            NATIVE_MODEL_PATH, ".scdoc", "NATIVE_MODEL_PATH", True
        )
        report_path = normalized_path(REPORT_PATH, ".json", "REPORT_PATH", False)
        if model_path.lower() == report_path.lower():
            raise ValueError("Model and report paths must be different.")
        report["outputs"]["native_model_path"] = model_path
        report["outputs"]["report_path"] = report_path

        bodies = list(GetRootPart().GetAllBodies())
        body = require_count(bodies, 1, "reopened bodies")[0]
        if body.Name != "ROUNDED_PLATE_SUPPORT_01":
            raise ValueError("Reopened body name does not match the case contract.")

        validate_and_report_geometry(report, body)
        report["evidence_layers"]["spaceclaim_execution"] = "passed"
        report["evidence_layers"]["geometry_measurements"] = "passed"
        report["evidence_layers"]["native_reopen"] = "passed"
        stage(report, "reopened_geometry_and_features_validated", "passed")
        report["status"] = "passed"
        write_report(report_path, report)
        return report
    except Exception as exc:
        report["status"] = "failed"
        report["evidence_layers"]["spaceclaim_execution"] = "failed"
        report["evidence_layers"]["native_reopen"] = "failed"
        report["error"] = {"type": exc.__class__.__name__, "message": str(exc)}
        stage(report, "failed", "failed", traceback.format_exc())
        if report_path:
            try:
                write_report(report_path, report)
            except:
                print(json.dumps(report, ensure_ascii=True, indent=2, sort_keys=True))
        else:
            print(json.dumps(report, ensure_ascii=True, indent=2, sort_keys=True))
        raise


run()
