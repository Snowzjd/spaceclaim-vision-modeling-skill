#!/usr/bin/env python3
"""Generate a V21 rectangular-prism build or read-only validation ``.scscript``.

The input geometry contract is checked before any output is written. The
generated IronPython 2.7 source centralizes all case values and the companion
``.scscript`` is the formal SpaceClaim executable artifact.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
import sys
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent


def _load_sibling(module_name: str, filename: str):
    spec = importlib.util.spec_from_file_location(module_name, SCRIPT_DIR / filename)
    if spec is None or spec.loader is None:
        raise RuntimeError("could not load %s" % filename)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


CONTRACT_VALIDATOR = _load_sibling(
    "rectangular_prism_contract_validator", "validate_rectangular_prism_contract.py"
)
PACKAGER = _load_sibling("rectangular_prism_packager", "package_scscript.py")


COMMON_SOURCE = r'''# Generated V21/IronPython 2.7 rectangular-prism script.
from __future__ import print_function

import datetime
import json
import os
import traceback

from SpaceClaim.Api.V21 import *


CASE_ID = @@CASE_ID@@
BODY_NAME = @@BODY_NAME@@
MINIMUM_CORNER_MM = @@MINIMUM_CORNER_MM@@
SIZE_MM = @@SIZE_MM@@
EXPECTED_BBOX_MM = @@EXPECTED_BBOX_MM@@
EXPECTED_VOLUME_MM3 = @@EXPECTED_VOLUME_MM3@@
MODEL_PATH = @@MODEL_PATH@@
REPORT_PATH = @@REPORT_PATH@@
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
'''


BUILD_SOURCE = COMMON_SOURCE + r'''

def fresh_report():
    return {
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
        "validation_boundary": "The build report is emitted by the executed script; native reopen and visual review require independent evidence.",
    }


def stage(report, name, status, message=""):
    report["stages"].append({"name": name, "status": status, "message": message})


def prepare_paths():
    model_path = os.path.abspath(MODEL_PATH).replace("\\", "/")
    report_path = os.path.abspath(REPORT_PATH).replace("\\", "/")
    if not model_path.lower().endswith(".scdoc"):
        raise ValueError("MODEL_PATH must end with .scdoc")
    if not report_path.lower().endswith(".json"):
        raise ValueError("REPORT_PATH must end with .json")
    if model_path.lower() == report_path.lower():
        raise ValueError("Model and report paths must be different")
    for path in (model_path, report_path):
        if os.path.exists(path):
            raise ValueError("Refusing to overwrite existing run output: %s" % path)
        directory = os.path.dirname(path)
        if directory and not os.path.isdir(directory):
            os.makedirs(directory)
    return model_path, report_path


def run():
    report = fresh_report()
    report_path = REPORT_PATH
    execution_started = False
    save_attempted = False
    try:
        model_path, report_path = prepare_paths()
        report["outputs"]["native_model_path"] = model_path
        report["outputs"]["report_path"] = report_path
        stage(report, "parameters_and_paths_validated", "passed")

        if current_bodies():
            raise ValueError("The build must start from a clean design with no bodies.")
        stage(report, "clean_design_confirmed", "passed")

        execution_started = True
        maximum = [MINIMUM_CORNER_MM[index] + SIZE_MM[index] for index in range(3)]
        result = BlockBody.Create(
            point_m(MINIMUM_CORNER_MM),
            point_m(maximum),
            ExtrudeType.ForceIndependent,
        )
        if not result.Success or result.CreatedBody is None:
            raise RuntimeError("BlockBody.Create did not create a body.")

        bodies = current_bodies()
        if len(bodies) != 1:
            raise ValueError("Expected one body after creation, found %d." % len(bodies))
        body = bodies[0]
        validate_body(body)
        rename_result = RenameObject.Execute(BodySelection.Create(body), BODY_NAME)
        if not rename_result.Success:
            raise RuntimeError("Body rename failed.")

        bodies = current_bodies()
        if len(bodies) != 1 or bodies[0].Name != BODY_NAME:
            raise ValueError("Final body identity does not match the contract.")
        validate_body(bodies[0])
        report["bodies"] = [body_row(bodies[0])]
        report["evidence_layers"]["spaceclaim_execution"] = "passed"
        report["evidence_layers"]["geometry_measurements"] = "passed"
        stage(report, "geometry_validated", "passed")

        save_attempted = True
        save_result = DocumentSave.Execute(model_path)
        if not save_result.Success or not os.path.isfile(model_path):
            raise RuntimeError("Native save did not produce the expected file.")
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
        except:
            print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
        raise


run()
'''


VALIDATION_SOURCE = COMMON_SOURCE + r'''

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
'''


def _literal(value: Any) -> str:
    return json.dumps(value, ensure_ascii=True, separators=(",", ":"))


def render_source(contract: dict[str, Any], mode: str, run_directory: Path) -> str:
    result = CONTRACT_VALIDATOR.validate_contract(contract)
    if result["status"] != "passed":
        raise ValueError("invalid rectangular-prism contract: %s" % result["issues"])
    if contract["handoff_status"] != "ready":
        raise ValueError("geometry contract must have handoff_status ready")

    primitive = contract["primitive"]
    expected = contract["expected_geometry"]
    model_path = run_directory / "rectangular-prism.scdoc"
    report_name = "forward-runtime-report.json" if mode == "build" else "validation-runtime-report.json"
    replacements = {
        "@@CASE_ID@@": _literal("v03-atomic-rectangular-prism"),
        "@@BODY_NAME@@": _literal(primitive["body_name"]),
        "@@MINIMUM_CORNER_MM@@": _literal(primitive["minimum_corner_mm"]),
        "@@SIZE_MM@@": _literal(primitive["size_mm"]),
        "@@EXPECTED_BBOX_MM@@": _literal(expected["bbox_min_mm"] + expected["bbox_max_mm"]),
        "@@EXPECTED_VOLUME_MM3@@": _literal(expected["volume_mm3"]),
        "@@MODEL_PATH@@": _literal(model_path.as_posix()),
        "@@REPORT_PATH@@": _literal((run_directory / report_name).as_posix()),
    }
    source = BUILD_SOURCE if mode == "build" else VALIDATION_SOURCE
    for token, value in replacements.items():
        source = source.replace(token, value)
    if "@@" in source:
        raise RuntimeError("unresolved source placeholder")
    return source


def generate(
    contract_path: Path,
    mode: str,
    source_output: Path,
    scscript_output: Path,
    run_directory: Path,
    *,
    force: bool = False,
) -> tuple[Path, Path]:
    if mode not in {"build", "validate"}:
        raise ValueError("mode must be build or validate")
    if source_output.resolve() == scscript_output.resolve():
        raise ValueError("source and .scscript outputs must be different")
    for output in (source_output, scscript_output):
        if output.exists() and not force:
            raise FileExistsError("refusing to overwrite existing output: %s" % output)

    contract = json.loads(contract_path.read_text(encoding="utf-8"))
    if not isinstance(contract, dict):
        raise ValueError("contract JSON root must be an object")
    source = render_source(contract, mode, run_directory.resolve())
    source_output.parent.mkdir(parents=True, exist_ok=True)
    write_mode = "w" if force else "x"
    with source_output.open(write_mode, encoding="utf-8", newline="\n") as stream:
        stream.write(source)
    try:
        PACKAGER.package_scscript(
            source_output,
            scscript_output,
            api_version="21",
            smart_variable_version="2",
            force=force,
        )
    except Exception:
        if not force:
            source_output.unlink(missing_ok=True)
        raise
    return source_output, scscript_output


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("contract", type=Path)
    parser.add_argument("--mode", choices=("build", "validate"), required=True)
    parser.add_argument("--source-output", type=Path, required=True)
    parser.add_argument("--scscript-output", type=Path, required=True)
    parser.add_argument("--run-directory", type=Path, required=True)
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args(argv)
    try:
        outputs = generate(
            args.contract,
            args.mode,
            args.source_output,
            args.scscript_output,
            args.run_directory,
            force=args.force,
        )
    except (OSError, ValueError, RuntimeError, json.JSONDecodeError) as exc:
        print("error: %s" % exc, file=sys.stderr)
        return 2
    print(json.dumps({"source": str(outputs[0]), "scscript": str(outputs[1])}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
