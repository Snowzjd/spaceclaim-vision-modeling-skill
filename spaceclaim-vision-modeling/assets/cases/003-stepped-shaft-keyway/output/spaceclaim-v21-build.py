# SpaceClaim 2022 R1 / API V21 candidate build script for case 003.
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


CASE_ID = "003-stepped-shaft-keyway"
SPACECLAIM_RELEASE = "2022 R1"
API_VERSION = "V21"
PYTHON_RUNTIME = "IronPython 2.7"

OUTPUT_MODEL_PATH = None  # Example: "C:/runs/003-stepped-shaft-keyway/model.scdoc"
REPORT_PATH = None  # Example: "C:/runs/003-stepped-shaft-keyway/forward-report.json"

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
KEYWAY_X_START_MM = 41.0  # Explicit centered-location assumption.
KEYWAY_X_END_MM = 49.0

SHOULDER_FILLET_RADIUS_MM = 1.0
CHAMFER_DISTANCE_MM = 1.0
CHAMFER_ANGLE_DEG = 45.0
BOOLEAN_OVERLAP_MM = 0.1
CUTTER_EXTENSION_MM = 1.0

BBOX_TOLERANCE_MM = 0.001
VOLUME_TOLERANCE_MM3 = 5.0
FEATURE_TOLERANCE_MM = 0.001
ANGLE_TOLERANCE_DEG = 0.01
# Analytic preflight value for the interpreted geometry. Keep the wider first-
# run tolerance until a V21 kernel measurement and independent feature checks
# have passed; then tighten the regression contract if appropriate.
EXPECTED_VOLUME_MM3 = 66659.1160764

MM_PER_M = 1000.0
MM2_PER_M2 = 1.0e6
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
            "This report is emitted by the case 003 V21 build script. Native "
            "reopen requires a separate read-only audit. Material assignment and "
            "any unperformed export are not claimed."
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


def validate_parameters():
    if not near(
        LEFT_LENGTH_MM + MIDDLE_LENGTH_MM + RIGHT_LENGTH_MM,
        TOTAL_LENGTH_MM,
        FEATURE_TOLERANCE_MM,
    ):
        raise ValueError("The three segment lengths must sum to the total length.")
    if KEYWAY_X_START_MM < LEFT_LENGTH_MM:
        raise ValueError("The keyway must start inside the middle segment.")
    if KEYWAY_X_END_MM > LEFT_LENGTH_MM + MIDDLE_LENGTH_MM:
        raise ValueError("The keyway must end inside the middle segment.")
    if not near(
        KEYWAY_X_END_MM - KEYWAY_X_START_MM,
        KEYWAY_LENGTH_MM,
        FEATURE_TOLERANCE_MM,
    ):
        raise ValueError("The keyway X interval must match its axial length.")
    if KEYWAY_DEPTH_MM <= 0.0 or KEYWAY_DEPTH_MM >= MIDDLE_DIAMETER_MM / 2.0:
        raise ValueError("The keyway depth is outside the middle-cylinder radius.")
    if KEYWAY_WIDTH_MM >= MIDDLE_DIAMETER_MM:
        raise ValueError("The keyway width exceeds the middle-cylinder diameter.")
    if BORE_DIAMETER_MM >= min(LEFT_DIAMETER_MM, RIGHT_DIAMETER_MM):
        raise ValueError("The bore must be smaller than both end segments.")
    if SHOULDER_FILLET_RADIUS_MM <= 0.0:
        raise ValueError("The shoulder fillet radius must be positive.")


def transient_cylinder(x0, x1, radius, label):
    if x1 <= x0:
        raise ValueError("%s must have positive axial length." % label)
    plane = Plane.Create(Frame.Create(point_m(x0, 0.0, 0.0), Direction.DirX))
    profile = CircleProfile(plane, mm(radius), PointUV.Create(0.0, 0.0), 0.0)
    body = ModelerBody.ExtrudeProfile(profile, mm(x1 - x0))
    if body is None or not body.IsClosed:
        raise RuntimeError("Transient cylinder creation failed: %s" % label)
    return body


def transient_rectangular_prism(x0, x1, center_y, center_z, width, height, label):
    if x1 <= x0 or width <= 0.0 or height <= 0.0:
        raise ValueError("%s dimensions must be positive." % label)
    plane = Plane.Create(
        Frame.Create(point_m(x0, center_y, center_z), Direction.DirX)
    )
    profile = RectangleProfile(
        plane,
        mm(width),
        mm(height),
        PointUV.Create(0.0, 0.0),
        0.0,
    )
    body = ModelerBody.ExtrudeProfile(profile, mm(x1 - x0))
    if body is None or not body.IsClosed:
        raise RuntimeError("Transient rectangular prism creation failed: %s" % label)
    return body


def create_outer_solid_with_cuts():
    left_shoulder_x = LEFT_LENGTH_MM
    right_shoulder_x = LEFT_LENGTH_MM + MIDDLE_LENGTH_MM

    outer = transient_cylinder(
        0.0,
        left_shoulder_x + BOOLEAN_OVERLAP_MM,
        LEFT_DIAMETER_MM / 2.0,
        "left step",
    )
    middle = transient_cylinder(
        left_shoulder_x,
        right_shoulder_x,
        MIDDLE_DIAMETER_MM / 2.0,
        "middle step",
    )
    right = transient_cylinder(
        right_shoulder_x - BOOLEAN_OVERLAP_MM,
        TOTAL_LENGTH_MM,
        RIGHT_DIAMETER_MM / 2.0,
        "right step",
    )
    outer.Unite(Array[ModelerBody]([middle, right]))
    if not outer.IsClosed or outer.PieceCount != 1:
        raise RuntimeError("Transient stepped-shaft union did not produce one closed piece.")

    bore = transient_cylinder(
        -CUTTER_EXTENSION_MM,
        TOTAL_LENGTH_MM + CUTTER_EXTENSION_MM,
        BORE_DIAMETER_MM / 2.0,
        "through bore",
    )
    middle_radius = MIDDLE_DIAMETER_MM / 2.0
    keyway_floor_z = middle_radius - KEYWAY_DEPTH_MM
    keyway_top_z = middle_radius + CUTTER_EXTENSION_MM
    keyway = transient_rectangular_prism(
        KEYWAY_X_START_MM,
        KEYWAY_X_END_MM,
        0.0,
        0.5 * (keyway_floor_z + keyway_top_z),
        KEYWAY_WIDTH_MM,
        keyway_top_z - keyway_floor_z,
        "middle keyway",
    )
    outer.Subtract(Array[ModelerBody]([bore, keyway]))
    if not outer.IsClosed or outer.PieceCount != 1:
        raise RuntimeError("Transient bore and keyway cuts did not leave one closed piece.")

    created = DesignBody.Create(GetRootPart(), "STEPPED_SHAFT_KEYWAY_01", outer)
    body = require_count(current_bodies(), 1, "document bodies after attach")[0]
    if body != created or body.Name != "STEPPED_SHAFT_KEYWAY_01":
        raise RuntimeError("The transient result was not attached with the required name.")
    return body


def edge_matches_circle(edge, expected_x_mm, expected_radius_mm):
    bbox = shape_bbox_mm(edge.Shape)
    expected_bbox = [
        expected_x_mm,
        -expected_radius_mm,
        -expected_radius_mm,
        expected_x_mm,
        expected_radius_mm,
        expected_radius_mm,
    ]
    return all(
        near(bbox[index], expected_bbox[index], FEATURE_TOLERANCE_MM)
        for index in range(6)
    )


def find_circular_edges(body, signatures, label):
    matches = []
    for expected_x, expected_radius in signatures:
        local = [
            edge
            for edge in list(body.Edges)
            if edge_matches_circle(edge, expected_x, expected_radius)
        ]
        require_count(
            local,
            1,
            "%s at X %.9g radius %.9g" % (label, expected_x, expected_radius),
        )
        matches.append(local[0])
    return matches


def apply_shoulder_fillets(body):
    signatures = (
        (LEFT_LENGTH_MM, LEFT_DIAMETER_MM / 2.0),
        (LEFT_LENGTH_MM + MIDDLE_LENGTH_MM, RIGHT_DIAMETER_MM / 2.0),
    )
    edges = find_circular_edges(body, signatures, "shoulder edge")
    result = ConstantRound.Execute(
        EdgeSelection.Create(*edges), mm(SHOULDER_FILLET_RADIUS_MM)
    )
    if not result.Success:
        raise RuntimeError("ConstantRound.Execute failed for the two shoulder edges.")
    return require_count(current_bodies(), 1, "bodies after shoulder fillets")[0]


def apply_end_and_bore_chamfers(body):
    signatures = (
        (0.0, LEFT_DIAMETER_MM / 2.0),
        (TOTAL_LENGTH_MM, RIGHT_DIAMETER_MM / 2.0),
        (0.0, BORE_DIAMETER_MM / 2.0),
        (TOTAL_LENGTH_MM, BORE_DIAMETER_MM / 2.0),
    )
    edges = find_circular_edges(body, signatures, "end or bore-mouth edge")
    result = Chamfer.Execute(
        EdgeSelection.Create(*edges), mm(CHAMFER_DISTANCE_MM), False
    )
    if not result.Success:
        raise RuntimeError("Chamfer.Execute failed for the four end and bore-mouth edges.")
    return require_count(current_bodies(), 1, "bodies after end chamfers")[0]


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
        raise ValueError("A shoulder fillet does not match R1.")
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
            raise ValueError("A measured shaft segment length does not match the drawing.")

    bore_bbox = bore["bbox"]
    expected_straight_bore_span = TOTAL_LENGTH_MM - 2.0 * CHAMFER_DISTANCE_MM
    if not near(
        bore_bbox[3] - bore_bbox[0],
        expected_straight_bore_span,
        FEATURE_TOLERANCE_MM,
    ):
        raise ValueError("The straight bore span does not match the two mouth chamfers.")

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
    floor = require_count(floor_faces, 1, "keyway floor faces")[0]
    floor_bbox = floor["bbox"]

    cones = [item for item in records if item["kind"] == "Cone"]
    require_count(cones, 4, "conical end and bore-mouth chamfer faces")
    chamfer_distances = [item["bbox"][3] - item["bbox"][0] for item in cones]
    chamfer_angles = [item["half_angle_deg"] for item in cones]
    if any(
        not near(value, CHAMFER_DISTANCE_MM, FEATURE_TOLERANCE_MM)
        for value in chamfer_distances
    ):
        raise ValueError("A chamfer does not have 1 mm axial span.")
    if any(
        not near(value, CHAMFER_ANGLE_DEG, ANGLE_TOLERANCE_DEG)
        for value in chamfer_angles
    ):
        raise ValueError("A chamfer is not 45 degrees.")

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


def validate_and_report_geometry(report, body):
    expected_bbox = [0.0, -19.0, -19.0, 100.0, 19.0, 19.0]
    bbox = shape_bbox_mm(body.Shape)
    if not all(
        near(bbox[index], expected_bbox[index], BBOX_TOLERANCE_MM)
        for index in range(6)
    ):
        raise ValueError("Final body bounding box does not match the contract: %r" % bbox)
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
    execution_started = False
    try:
        validate_parameters()
        model_path, report_path = prepare_output_paths(report)
        execution_started = True
        require_count(current_bodies(), 0, "initial document bodies")
        stage(report, "parameters_paths_and_clean_document_validated", "passed")

        body = create_outer_solid_with_cuts()
        stage(report, "stepped_solid_bore_and_keyway_created", "passed")

        body = apply_shoulder_fillets(body)
        stage(report, "shoulder_fillets_created", "passed")

        body = apply_end_and_bore_chamfers(body)
        stage(report, "end_and_bore_chamfers_created", "passed")

        body = require_count(current_bodies(), 1, "final bodies")[0]
        if body.Name != "STEPPED_SHAFT_KEYWAY_01":
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
                print(json.dumps(report, ensure_ascii=True, indent=2, sort_keys=True))
        else:
            print(json.dumps(report, ensure_ascii=True, indent=2, sort_keys=True))
        raise


run()
