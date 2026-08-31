# SpaceClaim 2022 R1 / API V21 read-only native-reopen audit for case 002.
# IronPython 2.7 compatible. This script never edits or saves the active model.

from __future__ import print_function

import datetime
import json
import math
import os
import traceback

from SpaceClaim.Api.V21 import *


CASE_ID = "002-flanged-short-pipe"
SPACECLAIM_RELEASE = "2022 R1"
API_VERSION = "V21"
PYTHON_RUNTIME = "IronPython 2.7"

NATIVE_MODEL_PATH = None
REPORT_PATH = None

TOTAL_LENGTH_MM = 80.0
FLANGE_THICKNESS_MM = 10.0
BORE_DIAMETER_MM = 16.0
BOLT_DIAMETER_MM = 6.5
PCD_DIAMETER_MM = 36.0
BOLT_COUNT_PER_FLANGE = 4
CHAMFER_DISTANCE_MM = 1.0
CHAMFER_ANGLE_DEG = 45.0
JOINT_FILLET_RADIUS_MM = 1.5
EXPECTED_VOLUME_MM3 = 44370.4398069

BBOX_TOLERANCE_MM = 0.001
VOLUME_TOLERANCE_MM3 = 0.5
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
            "Read-only audit of the active reopened case 002 native document. "
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


def validate_features(body):
    records = [face_record(face) for face in list(body.Faces)]
    cylinders = [item for item in records if item["kind"] == "Cylinder"]
    cones = [item for item in records if item["kind"] == "Cone"]
    tori = [item for item in records if item["kind"] == "Torus"]

    central = [
        item
        for item in cylinders
        if near(item["radius_mm"], BORE_DIAMETER_MM / 2.0, FEATURE_TOLERANCE_MM)
    ]
    require_count(central, 1, "central bore cylindrical faces")
    central_span = central[0]["bbox"][3] - central[0]["bbox"][0]
    if not near(central_span, TOTAL_LENGTH_MM, FEATURE_TOLERANCE_MM):
        raise ValueError("Central bore axial span does not match the total length.")

    bolts = [
        item
        for item in cylinders
        if near(item["radius_mm"], BOLT_DIAMETER_MM / 2.0, FEATURE_TOLERANCE_MM)
    ]
    require_count(bolts, 2 * BOLT_COUNT_PER_FLANGE, "bolt-hole cylindrical faces")
    left_count = 0
    right_count = 0
    pcd_diameters = []
    for item in bolts:
        bbox = item["bbox"]
        axial_mid = 0.5 * (bbox[0] + bbox[3])
        center_y = 0.5 * (bbox[1] + bbox[4])
        center_z = 0.5 * (bbox[2] + bbox[5])
        pcd_diameters.append(2.0 * math.sqrt(center_y * center_y + center_z * center_z))
        if axial_mid < TOTAL_LENGTH_MM / 2.0:
            left_count += 1
        else:
            right_count += 1
        if not near(bbox[3] - bbox[0], FLANGE_THICKNESS_MM, FEATURE_TOLERANCE_MM):
            raise ValueError("A bolt-hole face does not span one flange thickness.")
    if left_count != BOLT_COUNT_PER_FLANGE or right_count != BOLT_COUNT_PER_FLANGE:
        raise ValueError("Bolt-hole distribution is not four per flange.")
    if any(
        not near(value, PCD_DIAMETER_MM, FEATURE_TOLERANCE_MM)
        for value in pcd_diameters
    ):
        raise ValueError("A bolt-hole center is outside the required PCD.")

    require_count(cones, 4, "conical chamfer faces")
    chamfer_distances = [item["bbox"][3] - item["bbox"][0] for item in cones]
    chamfer_angles = [item["half_angle_deg"] for item in cones]
    if any(
        not near(value, CHAMFER_DISTANCE_MM, FEATURE_TOLERANCE_MM)
        for value in chamfer_distances
    ):
        raise ValueError("A flange outside chamfer does not have 1 mm axial span.")
    if any(
        not near(value, CHAMFER_ANGLE_DEG, ANGLE_TOLERANCE_DEG)
        for value in chamfer_angles
    ):
        raise ValueError("A flange outside chamfer is not 45 degrees.")

    require_count(tori, 2, "toroidal joint fillet faces")
    fillet_radii = [item["minor_radius_mm"] for item in tori]
    if any(
        not near(value, JOINT_FILLET_RADIUS_MM, FEATURE_TOLERANCE_MM)
        for value in fillet_radii
    ):
        raise ValueError("A joint fillet does not match the configured radius.")

    return [
        {
            "name": "central_bore",
            "count": len(central),
            "measurements": {
                "diameter_mm": 2.0 * central[0]["radius_mm"],
                "axial_span_mm": central_span,
            },
        },
        {
            "name": "bolt_holes",
            "count": len(bolts),
            "measurements": {
                "diameter_mm": 2.0 * sum(item["radius_mm"] for item in bolts) / len(bolts),
                "pcd_diameter_mm": sum(pcd_diameters) / len(pcd_diameters),
            },
        },
        {
            "name": "outer_chamfers",
            "count": len(cones),
            "measurements": {
                "distance_mm": sum(chamfer_distances) / len(chamfer_distances),
                "angle_deg": sum(chamfer_angles) / len(chamfer_angles),
            },
        },
        {
            "name": "joint_fillets",
            "count": len(tori),
            "measurements": {
                "radius_mm": sum(fillet_radii) / len(fillet_radii),
            },
        },
    ]


def write_report(path, report):
    # Keep localized V21 exception text writable under IronPython 2.7.
    text = json.dumps(report, ensure_ascii=True, indent=2, sort_keys=True)
    with open(path, "w") as handle:
        handle.write(text)
        handle.write("\n")


def run():
    report = fresh_report()
    report_path = None
    execution_started = False
    try:
        model_path = normalized_path(NATIVE_MODEL_PATH, ".scdoc", "NATIVE_MODEL_PATH", True)
        report_path = normalized_path(REPORT_PATH, ".json", "REPORT_PATH", False)
        if model_path.lower() == report_path.lower():
            raise ValueError("Model and report paths must be different.")
        report["outputs"]["native_model_path"] = model_path
        report["outputs"]["report_path"] = report_path

        execution_started = True
        body = require_count(list(GetRootPart().GetAllBodies()), 1, "reopened bodies")[0]
        if body.Name != "FLANGED_PIPE_01":
            raise ValueError("Reopened body name does not match the case contract.")

        bbox = shape_bbox_mm(body.Shape)
        expected_bbox = [0.0, -24.0, -24.0, 80.0, 24.0, 24.0]
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
        if execution_started:
            if report["evidence_layers"]["spaceclaim_execution"] == "not_tested":
                report["evidence_layers"]["spaceclaim_execution"] = "failed"
            if report["evidence_layers"]["native_reopen"] == "not_tested":
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
