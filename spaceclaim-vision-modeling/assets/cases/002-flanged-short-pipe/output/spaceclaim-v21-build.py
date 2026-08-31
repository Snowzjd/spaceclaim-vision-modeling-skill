# SpaceClaim 2022 R1 / API V21 candidate build script for case 002.
# IronPython 2.7 compatible. One controlled V21 runtime is documented in the case evidence.
# Set the paths for the current run. Start from a new unsaved blank design; the
# script saves the validated result directly to the run-owned native path.

from __future__ import print_function

import datetime
import json
import math
import os
import traceback

from System import Array
from SpaceClaim.Api.V21 import *
from SpaceClaim.Api.V21.Geometry import CircleProfile, Plane, PointUV
from SpaceClaim.Api.V21.Modeler import Body as ModelerBody


CASE_ID = "002-flanged-short-pipe"
SPACECLAIM_RELEASE = "2022 R1"
API_VERSION = "V21"
PYTHON_RUNTIME = "IronPython 2.7"

OUTPUT_MODEL_PATH = None  # Example: "C:/runs/002-flanged-short-pipe/model.scdoc"
REPORT_PATH = None  # Example: "C:/runs/002-flanged-short-pipe/runtime-report.json"

TOTAL_LENGTH_MM = 80.0
FLANGE_THICKNESS_MM = 10.0
MIDDLE_LENGTH_MM = 60.0
PIPE_OD_MM = 24.0
FLANGE_OD_MM = 48.0
BORE_DIAMETER_MM = 16.0
BOLT_DIAMETER_MM = 6.5
PCD_DIAMETER_MM = 36.0
BOLT_COUNT_PER_FLANGE = 4
CHAMFER_DISTANCE_MM = 1.0
CHAMFER_ANGLE_DEG = 45.0
JOINT_FILLET_RADIUS_MM = 1.5  # Explicit midpoint assumption within R1..R2.

BBOX_TOLERANCE_MM = 0.001
VOLUME_TOLERANCE_MM3 = 0.5
FEATURE_TOLERANCE_MM = 0.001
ANGLE_TOLERANCE_DEG = 0.01
# V21 geometry-kernel regression value after the R1.5 joint rounds and four
# 1 mm x 45 degree outside-edge chamfers. Feature dimensions are also checked
# independently below, so this value is not used as a substitute for them.
EXPECTED_VOLUME_MM3 = 44370.4398069

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
            "This report is emitted by the case 002 V21 build script. Native reopen "
            "and requested export layers require separate evidence."
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
    minimum = point_mm(box.MinCorner)
    maximum = point_mm(box.MaxCorner)
    return minimum + maximum


def body_volume_mm3(body):
    return float(body.Shape.Volume) * MM3_PER_M3


def current_bodies():
    return list(GetRootPart().GetAllBodies())


def current_groups():
    return list(WindowHelper.GetGroups())


def require_count(items, count, label):
    if len(items) != count:
        raise ValueError("Expected %d %s, found %d." % (count, label, len(items)))
    return items


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
    model_path = normalized_new_path(
        OUTPUT_MODEL_PATH, ".scdoc", "OUTPUT_MODEL_PATH"
    )
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
        2.0 * FLANGE_THICKNESS_MM + MIDDLE_LENGTH_MM,
        TOTAL_LENGTH_MM,
        FEATURE_TOLERANCE_MM,
    ):
        raise ValueError("Flange and middle lengths must sum to the total length.")
    if not (1.0 <= JOINT_FILLET_RADIUS_MM <= 2.0):
        raise ValueError("Joint fillet radius must remain inside the specified R1..R2 range.")
    if BOLT_COUNT_PER_FLANGE != 4:
        raise ValueError("Case 002 requires four bolt holes per flange.")
    if PCD_DIAMETER_MM / 2.0 + BOLT_DIAMETER_MM / 2.0 >= FLANGE_OD_MM / 2.0:
        raise ValueError("Bolt holes exceed the flange radial envelope.")
    if BORE_DIAMETER_MM >= PIPE_OD_MM:
        raise ValueError("The bore must be smaller than the pipe outside diameter.")


def transient_cylinder(x0, x1, center_y, center_z, radius, label):
    if x1 <= x0:
        raise ValueError("%s must have positive axial length." % label)
    plane = Plane.Create(
        Frame.Create(point_m(x0, center_y, center_z), Direction.DirX)
    )
    profile = CircleProfile(
        plane,
        mm(radius),
        PointUV.Create(0.0, 0.0),
        0.0,
    )
    body = ModelerBody.ExtrudeProfile(profile, mm(x1 - x0))
    if body is None or not body.IsClosed:
        raise RuntimeError("Transient cylinder creation failed: %s" % label)
    return body


def create_outer_solid_with_holes():
    # Construct and boolean the transient B-rep bodies before attaching a
    # single DesignBody to the document.  This avoids target-selection and
    # transaction ambiguity from ForceAdd/Combine on temporary document bodies.
    outer = transient_cylinder(
        0.0, TOTAL_LENGTH_MM, 0.0, 0.0, PIPE_OD_MM / 2.0, "pipe core"
    )
    left_flange = transient_cylinder(
        0.0, FLANGE_THICKNESS_MM, 0.0, 0.0, FLANGE_OD_MM / 2.0, "left flange"
    )
    right_flange = transient_cylinder(
        TOTAL_LENGTH_MM - FLANGE_THICKNESS_MM,
        TOTAL_LENGTH_MM,
        0.0,
        0.0,
        FLANGE_OD_MM / 2.0,
        "right flange",
    )
    outer.Unite(Array[ModelerBody]([left_flange, right_flange]))
    if not outer.IsClosed or outer.PieceCount != 1:
        raise RuntimeError("Transient outer union did not produce one closed piece.")

    cutter_extension = 1.0
    cutters = [
        transient_cylinder(
            -cutter_extension,
            TOTAL_LENGTH_MM + cutter_extension,
            0.0,
            0.0,
            BORE_DIAMETER_MM / 2.0,
            "central bore",
        )
    ]
    pcd_radius = PCD_DIAMETER_MM / 2.0
    for angle_index in range(BOLT_COUNT_PER_FLANGE):
        angle = 2.0 * math.pi * float(angle_index) / float(BOLT_COUNT_PER_FLANGE)
        center_y = pcd_radius * math.cos(angle)
        center_z = pcd_radius * math.sin(angle)
        cutters.append(
            transient_cylinder(
                -cutter_extension,
                FLANGE_THICKNESS_MM + cutter_extension,
                center_y,
                center_z,
                BOLT_DIAMETER_MM / 2.0,
                "left bolt hole %d" % (angle_index + 1),
            )
        )
        cutters.append(
            transient_cylinder(
                TOTAL_LENGTH_MM - FLANGE_THICKNESS_MM - cutter_extension,
                TOTAL_LENGTH_MM + cutter_extension,
                center_y,
                center_z,
                BOLT_DIAMETER_MM / 2.0,
                "right bolt hole %d" % (angle_index + 1),
            )
        )
    outer.Subtract(Array[ModelerBody](cutters))
    if not outer.IsClosed or outer.PieceCount != 1:
        raise RuntimeError("Transient cuts did not leave one closed piece.")

    created = DesignBody.Create(GetRootPart(), "FLANGED_PIPE_01", outer)
    body = require_count(current_bodies(), 1, "document bodies after attach")[0]
    if body != created or body.Name != "FLANGED_PIPE_01":
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
        require_count(local, 1, "%s at X %.9g radius %.9g" % (label, expected_x, expected_radius))
        matches.append(local[0])
    return matches


def apply_joint_fillets(body):
    signatures = (
        (FLANGE_THICKNESS_MM, PIPE_OD_MM / 2.0),
        (TOTAL_LENGTH_MM - FLANGE_THICKNESS_MM, PIPE_OD_MM / 2.0),
    )
    edges = find_circular_edges(body, signatures, "joint edge")
    result = ConstantRound.Execute(
        EdgeSelection.Create(*edges), mm(JOINT_FILLET_RADIUS_MM)
    )
    if not result.Success:
        raise RuntimeError("ConstantRound.Execute failed for the two joint edges.")
    return require_count(current_bodies(), 1, "bodies after joint fillets")[0]


def apply_outer_chamfers(body):
    signatures = (
        (0.0, FLANGE_OD_MM / 2.0),
        (FLANGE_THICKNESS_MM, FLANGE_OD_MM / 2.0),
        (TOTAL_LENGTH_MM - FLANGE_THICKNESS_MM, FLANGE_OD_MM / 2.0),
        (TOTAL_LENGTH_MM, FLANGE_OD_MM / 2.0),
    )
    edges = find_circular_edges(body, signatures, "flange outside edge")
    result = Chamfer.Execute(
        EdgeSelection.Create(*edges), mm(CHAMFER_DISTANCE_MM), False
    )
    if not result.Success:
        raise RuntimeError("Chamfer.Execute failed for the four flange outside edges.")
    return require_count(current_bodies(), 1, "bodies after outer chamfers")[0]


def face_record(face):
    geometry = face.Shape.Geometry
    kind = geometry.GetType().Name
    record = {"face": face, "kind": kind, "bbox": shape_bbox_mm(face.Shape)}
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
    chamfer_distances = []
    chamfer_angles = []
    for item in cones:
        chamfer_distances.append(item["bbox"][3] - item["bbox"][0])
        chamfer_angles.append(item["half_angle_deg"])
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


def validate_and_report_geometry(report, body):
    expected_bbox = [0.0, -24.0, -24.0, 80.0, 24.0, 24.0]
    bbox = shape_bbox_mm(body.Shape)
    if not all(
        near(bbox[index], expected_bbox[index], BBOX_TOLERANCE_MM)
        for index in range(6)
    ):
        raise ValueError("Final body bounding box does not match the contract: %r" % bbox)
    # Validate the requested geometric features before the aggregate volume so
    # a volume mismatch never hides which holes, rounds, or chamfers succeeded.
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
    # IronPython 2.7 text-mode files use the process code page. ASCII escaping
    # keeps reports writable even when a localized SpaceClaim exception is
    # included in the JSON payload.
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
        stage(report, "parameters_and_paths_validated", "passed")

        execution_started = True
        body = create_outer_solid_with_holes()
        stage(report, "outer_solid_and_holes_created", "passed")

        body = apply_joint_fillets(body)
        stage(report, "joint_fillets_created", "passed")

        body = apply_outer_chamfers(body)
        stage(report, "outer_chamfers_created", "passed")

        body = require_count(current_bodies(), 1, "final bodies")[0]
        if body.Name != "FLANGED_PIPE_01":
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
