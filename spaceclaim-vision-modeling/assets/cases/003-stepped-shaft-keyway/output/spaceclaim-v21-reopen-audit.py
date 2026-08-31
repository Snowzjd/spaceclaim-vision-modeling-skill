# SpaceClaim 2022 R1 / API V21 read-only native-reopen audit for case 003.
# IronPython 2.7 compatible. This script never edits or saves the active model.

from __future__ import print_function

import datetime
import json
import math
import os
import traceback

from SpaceClaim.Api.V21 import *


CASE_ID = "003-stepped-shaft-keyway"
SPACECLAIM_RELEASE = "2022 R1"
API_VERSION = "V21"
PYTHON_RUNTIME = "IronPython 2.7"

NATIVE_MODEL_PATH = None
REPORT_PATH = None

TOTAL_LENGTH_MM = 100.0
LEFT_LENGTH_MM = 25.0
MIDDLE_LENGTH_MM = 40.0
RIGHT_LENGTH_MM = 35.0
LEFT_DIAMETER_MM = 20.0
MIDDLE_DIAMETER_MM = 38.0
RIGHT_DIAMETER_MM = 28.0
BORE_DIAMETER_MM = 10.0
KEYWAY_LENGTH_MM = 8.0
KEYWAY_WIDTH_MM = 8.0
KEYWAY_DEPTH_MM = 3.0
KEYWAY_X_START_MM = 41.0
KEYWAY_X_END_MM = 49.0
SHOULDER_FILLET_RADIUS_MM = 1.0
CHAMFER_DISTANCE_MM = 1.0
CHAMFER_ANGLE_DEG = 45.0
EXPECTED_VOLUME_MM3 = 66659.1160764

BBOX_TOLERANCE_MM = 0.001
VOLUME_TOLERANCE_MM3 = 5.0
FEATURE_TOLERANCE_MM = 0.001
ANGLE_TOLERANCE_DEG = 0.01
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
        "drawing_metadata": {
            "material_note": "45 steel",
            "material_assignment": "not_performed",
            "keyway_axial_location": "centered_assumption_x_41_to_49_mm",
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
            "Read-only audit of the active reopened case 003 native document. "
            "It does not modify or save the model."
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


def face_record(face):
    geometry = face.Shape.Geometry
    kind = geometry.GetType().Name
    record = {"kind": kind, "bbox": shape_bbox_mm(face.Shape)}
    if kind in ("Cylinder", "Cone"):
        record["radius_mm"] = abs(float(geometry.Radius)) * MM_PER_M
    if kind == "Cone":
        record["half_angle_deg"] = abs(float(geometry.HalfAngle)) * 180.0 / math.pi
    if kind == "Torus":
        record["major_radius_mm"] = abs(float(geometry.MajorRadius)) * MM_PER_M
        record["minor_radius_mm"] = abs(float(geometry.MinorRadius)) * MM_PER_M
    return record


def unique_cylinder(records, expected_radius, label):
    matches = [
        item
        for item in records
        if item["kind"] == "Cylinder"
        and near(item["radius_mm"], expected_radius, FEATURE_TOLERANCE_MM)
    ]
    return require_count(matches, 1, label)[0]


def validate_features(body):
    records = [face_record(face) for face in list(body.Faces)]
    left = unique_cylinder(records, LEFT_DIAMETER_MM / 2.0, "left outer cylinders")
    middle = unique_cylinder(records, MIDDLE_DIAMETER_MM / 2.0, "middle outer cylinders")
    right = unique_cylinder(records, RIGHT_DIAMETER_MM / 2.0, "right outer cylinders")
    bore = unique_cylinder(records, BORE_DIAMETER_MM / 2.0, "through-bore cylinders")

    tori = [item for item in records if item["kind"] == "Torus"]
    require_count(tori, 2, "toroidal shoulder fillet faces")
    tori.sort(key=lambda item: 0.5 * (item["bbox"][0] + item["bbox"][3]))
    fillet_radii = [item["minor_radius_mm"] for item in tori]
    if any(
        not near(value, SHOULDER_FILLET_RADIUS_MM, FEATURE_TOLERANCE_MM)
        for value in fillet_radii
    ):
        raise ValueError("A reopened shoulder fillet does not match R1.")
    left_shoulder_x = tori[0]["bbox"][3]
    right_shoulder_x = tori[1]["bbox"][0]
    segment_lengths = (
        left_shoulder_x,
        right_shoulder_x - left_shoulder_x,
        TOTAL_LENGTH_MM - right_shoulder_x,
    )
    for actual, expected in zip(
        segment_lengths, (LEFT_LENGTH_MM, MIDDLE_LENGTH_MM, RIGHT_LENGTH_MM)
    ):
        if not near(actual, expected, FEATURE_TOLERANCE_MM):
            raise ValueError("A reopened shaft segment length does not match the drawing.")

    bore_bbox = bore["bbox"]
    if not near(
        bore_bbox[3] - bore_bbox[0],
        TOTAL_LENGTH_MM - 2.0 * CHAMFER_DISTANCE_MM,
        FEATURE_TOLERANCE_MM,
    ):
        raise ValueError("The reopened straight bore span is incorrect.")

    middle_radius = MIDDLE_DIAMETER_MM / 2.0
    keyway_floor_z = middle_radius - KEYWAY_DEPTH_MM
    expected_floor_bbox = [
        KEYWAY_X_START_MM,
        -KEYWAY_WIDTH_MM / 2.0,
        keyway_floor_z,
        KEYWAY_X_END_MM,
        KEYWAY_WIDTH_MM / 2.0,
        keyway_floor_z,
    ]
    floor_faces = [
        item
        for item in records
        if item["kind"] == "Plane"
        and all(
            near(item["bbox"][index], expected_floor_bbox[index], FEATURE_TOLERANCE_MM)
            for index in range(6)
        )
    ]
    floor = require_count(floor_faces, 1, "reopened keyway floor faces")[0]
    floor_bbox = floor["bbox"]

    cones = [item for item in records if item["kind"] == "Cone"]
    require_count(cones, 4, "reopened conical chamfer faces")
    chamfer_distances = [item["bbox"][3] - item["bbox"][0] for item in cones]
    chamfer_angles = [item["half_angle_deg"] for item in cones]
    if any(
        not near(value, CHAMFER_DISTANCE_MM, FEATURE_TOLERANCE_MM)
        for value in chamfer_distances
    ):
        raise ValueError("A reopened chamfer does not have 1 mm axial span.")
    if any(
        not near(value, CHAMFER_ANGLE_DEG, ANGLE_TOLERANCE_DEG)
        for value in chamfer_angles
    ):
        raise ValueError("A reopened chamfer is not 45 degrees.")

    return [
        {
            "name": "stepped_outer_segments",
            "count": 3,
            "measurements": {
                "left_diameter_mm": 2.0 * left["radius_mm"],
                "middle_diameter_mm": 2.0 * middle["radius_mm"],
                "right_diameter_mm": 2.0 * right["radius_mm"],
                "left_length_mm": segment_lengths[0],
                "middle_length_mm": segment_lengths[1],
                "right_length_mm": segment_lengths[2],
            },
        },
        {
            "name": "through_bore",
            "count": 1,
            "measurements": {
                "diameter_mm": 2.0 * bore["radius_mm"],
                "through_length_mm": TOTAL_LENGTH_MM,
            },
        },
        {
            "name": "keyway",
            "count": 1,
            "measurements": {
                "length_mm": floor_bbox[3] - floor_bbox[0],
                "width_mm": floor_bbox[4] - floor_bbox[1],
                "depth_mm": middle_radius - floor_bbox[2],
                "x_start_mm": floor_bbox[0],
                "x_end_mm": floor_bbox[3],
            },
        },
        {
            "name": "end_and_bore_chamfers",
            "count": len(cones),
            "measurements": {
                "distance_mm": sum(chamfer_distances) / len(chamfer_distances),
                "angle_deg": sum(chamfer_angles) / len(chamfer_angles),
            },
        },
        {
            "name": "shoulder_fillets",
            "count": len(tori),
            "measurements": {
                "radius_mm": sum(fillet_radii) / len(fillet_radii),
            },
        },
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
        model_path = normalized_path(NATIVE_MODEL_PATH, ".scdoc", "NATIVE_MODEL_PATH", True)
        report_path = normalized_path(REPORT_PATH, ".json", "REPORT_PATH", False)
        if model_path.lower() == report_path.lower():
            raise ValueError("Model and report paths must be different.")
        report["outputs"]["native_model_path"] = model_path
        report["outputs"]["report_path"] = report_path

        body = require_count(list(GetRootPart().GetAllBodies()), 1, "reopened bodies")[0]
        if body.Name != "STEPPED_SHAFT_KEYWAY_01":
            raise ValueError("Reopened body name does not match the case contract.")

        bbox = shape_bbox_mm(body.Shape)
        expected_bbox = [0.0, -19.0, -19.0, 100.0, 19.0, 19.0]
        if not all(
            near(bbox[index], expected_bbox[index], BBOX_TOLERANCE_MM)
            for index in range(6)
        ):
            raise ValueError("Reopened body bounding box does not match the contract.")
        report["features"] = validate_features(body)
        volume = body_volume_mm3(body)
        if not near(volume, EXPECTED_VOLUME_MM3, VOLUME_TOLERANCE_MM3):
            raise ValueError("Reopened body volume does not match the contract.")

        report["bodies"] = [
            {
                "name": body.Name,
                "bbox_min_mm": bbox[:3],
                "bbox_max_mm": bbox[3:],
                "volume_mm3": volume,
                "face_count": len(list(body.Faces)),
            }
        ]
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
