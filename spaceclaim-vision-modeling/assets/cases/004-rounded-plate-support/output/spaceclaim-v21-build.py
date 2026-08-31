# SpaceClaim 2022 R1 / API V21 candidate build script for case 004.
# IronPython 2.7 compatible. One controlled V21 runtime is documented in the case evidence.
# Start from a new unsaved design. Set the two run-owned output paths before
# packaging the execution copy; the formal public source keeps them unset.

from __future__ import print_function

import datetime
import json
import math
import os
import traceback

from System import Array
from SpaceClaim.Api.V21 import *
from SpaceClaim.Api.V21.Geometry import CircleProfile, Plane, PointUV, RectangleProfile
from SpaceClaim.Api.V21.Modeler import Body as ModelerBody


CASE_ID = "004-rounded-plate-support"
SPACECLAIM_RELEASE = "2022 R1"
API_VERSION = "V21"
PYTHON_RUNTIME = "IronPython 2.7"

OUTPUT_MODEL_PATH = None  # Example: "C:/runs/004-rounded-plate-support/model.scdoc"
REPORT_PATH = None  # Example: "C:/runs/004-rounded-plate-support/forward-report.json"

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
BOOLEAN_OVERLAP_MM = 0.1
CUTTER_EXTENSION_MM = 1.0

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
            "This report is emitted by the case 004 V21 build script. Native "
            "reopen requires a separate read-only audit. The support-height "
            "interpretation and omitted unspecified features remain explicit."
        ),
    }


def stage(report, name, status, message=""):
    report["stages"].append({"name": name, "status": status, "message": message})


def mm(value):
    return float(value) / MM_PER_M


def near(left, right, tolerance):
    return abs(float(left) - float(right)) <= float(tolerance)


def point_m(x_mm, y_mm, z_mm):
    return Point.Create(mm(x_mm), mm(y_mm), mm(z_mm))


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


def current_bodies():
    return list(GetRootPart().GetAllBodies())


def require_count(items, count, label):
    if len(items) != count:
        raise ValueError("Expected %d %s, found %d." % (count, label, len(items)))
    return items


def assert_bbox(actual, expected, tolerance, label):
    if not all(near(actual[index], expected[index], tolerance) for index in range(6)):
        raise ValueError("%s bounding box mismatch: %r" % (label, actual))


def normalized_new_path(value, suffix, label):
    if not value or not isinstance(value, basestring):
        raise ValueError("%s must be set before the authorized run." % label)
    path = os.path.abspath(value)
    if not path.lower().endswith(suffix):
        raise ValueError("%s must end with %s." % (label, suffix))
    if os.path.exists(path):
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


def hole_centers():
    return [
        (HOLE_EDGE_OFFSET_MM, HOLE_EDGE_OFFSET_MM),
        (PLATE_LENGTH_MM - HOLE_EDGE_OFFSET_MM, HOLE_EDGE_OFFSET_MM),
        (HOLE_EDGE_OFFSET_MM, PLATE_WIDTH_MM - HOLE_EDGE_OFFSET_MM),
        (PLATE_LENGTH_MM - HOLE_EDGE_OFFSET_MM, PLATE_WIDTH_MM - HOLE_EDGE_OFFSET_MM),
    ]


def validate_parameters():
    if min(PLATE_LENGTH_MM, PLATE_WIDTH_MM, PLATE_THICKNESS_MM) <= 0.0:
        raise ValueError("Plate dimensions must be positive.")
    if CORNER_RADIUS_MM <= 0.0 or 2.0 * CORNER_RADIUS_MM > min(PLATE_LENGTH_MM, PLATE_WIDTH_MM):
        raise ValueError("Corner radius is invalid for the plate footprint.")
    if SUPPORT_DIAMETER_MM <= 0.0 or SUPPORT_HEIGHT_MM <= 0.0:
        raise ValueError("Support dimensions must be positive.")
    if SUPPORT_DIAMETER_MM >= min(PLATE_LENGTH_MM, PLATE_WIDTH_MM):
        raise ValueError("Support diameter exceeds the plate footprint.")
    if HOLE_DIAMETER_MM <= 0.0:
        raise ValueError("Hole diameter must be positive.")
    if HOLE_EDGE_OFFSET_MM <= HOLE_DIAMETER_MM / 2.0:
        raise ValueError("Hole edge offset does not leave positive edge ligament.")
    if HOLE_EDGE_OFFSET_MM >= min(PLATE_LENGTH_MM, PLATE_WIDTH_MM) / 2.0:
        raise ValueError("Hole edge offset crosses the plate centerline.")


def xy_plane(center_x, center_y, z0):
    frame = Frame.Create(
        point_m(center_x, center_y, z0), Direction.DirX, Direction.DirY
    )
    return Plane.Create(frame)


def transient_rectangle_z(center_x, center_y, z0, length, width, height, label):
    profile = RectangleProfile(
        xy_plane(center_x, center_y, z0),
        mm(length),
        mm(width),
        PointUV.Create(0.0, 0.0),
        0.0,
    )
    body = ModelerBody.ExtrudeProfile(profile, mm(height))
    if body is None or not body.IsClosed:
        raise RuntimeError("Transient rectangular prism creation failed: %s" % label)
    return body


def transient_cylinder_z(center_x, center_y, z0, z1, radius, label):
    if z1 <= z0:
        raise ValueError("%s must have positive height." % label)
    profile = CircleProfile(
        xy_plane(center_x, center_y, z0),
        mm(radius),
        PointUV.Create(0.0, 0.0),
        0.0,
    )
    body = ModelerBody.ExtrudeProfile(profile, mm(z1 - z0))
    if body is None or not body.IsClosed:
        raise RuntimeError("Transient cylinder creation failed: %s" % label)
    return body


def create_plate_support_and_holes():
    plate = transient_rectangle_z(
        SUPPORT_CENTER_X_MM,
        SUPPORT_CENTER_Y_MM,
        0.0,
        PLATE_LENGTH_MM,
        PLATE_WIDTH_MM,
        PLATE_THICKNESS_MM,
        "base plate",
    )
    assert_bbox(
        shape_bbox_mm(plate),
        [0.0, 0.0, 0.0, PLATE_LENGTH_MM, PLATE_WIDTH_MM, PLATE_THICKNESS_MM],
        BBOX_TOLERANCE_MM,
        "transient base plate",
    )

    support = transient_cylinder_z(
        SUPPORT_CENTER_X_MM,
        SUPPORT_CENTER_Y_MM,
        PLATE_THICKNESS_MM - BOOLEAN_OVERLAP_MM,
        PLATE_THICKNESS_MM + SUPPORT_HEIGHT_MM,
        SUPPORT_DIAMETER_MM / 2.0,
        "central support",
    )
    plate.Unite(Array[ModelerBody]([support]))
    if not plate.IsClosed or plate.PieceCount != 1:
        raise RuntimeError("Plate and support union did not produce one closed piece.")

    cutters = []
    for index, center in enumerate(hole_centers()):
        cutters.append(
            transient_cylinder_z(
                center[0],
                center[1],
                -CUTTER_EXTENSION_MM,
                PLATE_THICKNESS_MM + CUTTER_EXTENSION_MM,
                HOLE_DIAMETER_MM / 2.0,
                "mounting hole %d" % (index + 1),
            )
        )
    plate.Subtract(Array[ModelerBody](cutters))
    if not plate.IsClosed or plate.PieceCount != 1:
        raise RuntimeError("Mounting-hole subtraction did not leave one closed piece.")

    created = DesignBody.Create(GetRootPart(), "ROUNDED_PLATE_SUPPORT_01", plate)
    body = require_count(current_bodies(), 1, "document bodies after attach")[0]
    if body != created or body.Name != "ROUNDED_PLATE_SUPPORT_01":
        raise RuntimeError("The transient result was not attached with the required name.")
    return body


def vertical_corner_edge(body, x_value, y_value):
    matches = []
    for edge in list(body.Edges):
        bbox = shape_bbox_mm(edge.Shape)
        if (
            near(bbox[0], x_value, FEATURE_TOLERANCE_MM)
            and near(bbox[3], x_value, FEATURE_TOLERANCE_MM)
            and near(bbox[1], y_value, FEATURE_TOLERANCE_MM)
            and near(bbox[4], y_value, FEATURE_TOLERANCE_MM)
            and near(bbox[2], 0.0, FEATURE_TOLERANCE_MM)
            and near(bbox[5], PLATE_THICKNESS_MM, FEATURE_TOLERANCE_MM)
        ):
            matches.append(edge)
    return require_count(
        matches,
        1,
        "vertical corner edges at X %.9g Y %.9g" % (x_value, y_value),
    )[0]


def apply_plate_corner_rounds(body):
    edges = [
        vertical_corner_edge(body, 0.0, 0.0),
        vertical_corner_edge(body, PLATE_LENGTH_MM, 0.0),
        vertical_corner_edge(body, 0.0, PLATE_WIDTH_MM),
        vertical_corner_edge(body, PLATE_LENGTH_MM, PLATE_WIDTH_MM),
    ]
    result = ConstantRound.Execute(
        EdgeSelection.Create(*edges), mm(CORNER_RADIUS_MM)
    )
    if not result.Success:
        raise RuntimeError("ConstantRound.Execute failed for the four plate corners.")
    return require_count(current_bodies(), 1, "bodies after plate corner rounds")[0]


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
        [(round(bbox_center_xy(item["bbox"])[0], 6), round(bbox_center_xy(item["bbox"])[1], 6)) for item in holes]
    )
    expected_centers = sorted([(round(item[0], 6), round(item[1], 6)) for item in hole_centers()])
    if measured_centers != expected_centers:
        raise ValueError("Mounting-hole centers do not match the edge-offset contract: %r" % measured_centers)
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
                "corner_radius_mm": sum(item["radius_mm"] for item in corner_faces) / 4.0,
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
    assert_bbox(bbox, expected_bbox, BBOX_TOLERANCE_MM, "final body")
    report["features"] = validate_features(body)
    volume = body_volume_mm3(body)
    if not near(volume, EXPECTED_VOLUME_MM3, VOLUME_TOLERANCE_MM3):
        raise ValueError(
            "Final volume %.12g mm3 does not match %.12g mm3 within tolerance."
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
    save_attempted = False
    try:
        validate_parameters()
        model_path, report_path = prepare_output_paths(report)
        require_count(current_bodies(), 0, "initial document bodies")
        stage(report, "parameters_paths_and_clean_document_validated", "passed")

        body = create_plate_support_and_holes()
        stage(report, "plate_support_and_holes_created", "passed")

        body = apply_plate_corner_rounds(body)
        stage(report, "plate_corner_rounds_created", "passed")

        body = require_count(current_bodies(), 1, "final bodies")[0]
        if body.Name != "ROUNDED_PLATE_SUPPORT_01":
            raise ValueError("Final body name does not match the case contract.")
        stage(report, "body_named", "passed")

        validate_and_report_geometry(report, body)
        report["evidence_layers"]["spaceclaim_execution"] = "passed"
        report["evidence_layers"]["geometry_measurements"] = "passed"
        stage(report, "geometry_and_features_validated", "passed")

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
        report["evidence_layers"]["spaceclaim_execution"] = "failed"
        if save_attempted:
            report["evidence_layers"]["native_save"] = "failed"
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
