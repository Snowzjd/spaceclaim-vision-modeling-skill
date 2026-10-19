#!/usr/bin/env python3
"""Validate an axis-aligned rectangular-prism geometry contract on the host.

This checker validates structure, provenance references, and derived numeric
invariants. It does not interpret source material or run SpaceClaim.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
from pathlib import Path
from typing import Any

try:
    from jsonschema import Draft202012Validator
except ImportError:  # pragma: no cover - exercised by CLI environments only
    Draft202012Validator = None


PACKAGE_ROOT = Path(__file__).resolve().parents[1]
REPOSITORY_ROOT = PACKAGE_ROOT.parent
SCHEMA_PATH = PACKAGE_ROOT / "references" / "rectangular-prism-geometry-contract.schema.json"


def _issue(code: str, path: str, message: str) -> dict[str, str]:
    return {"code": code, "path": path, "message": message}


def _near(left: float, right: float, tolerance: float = 1.0e-9) -> bool:
    return math.isclose(float(left), float(right), rel_tol=0.0, abs_tol=tolerance)


def _load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("JSON root must be an object")
    return value


def validate_contract(
    contract: dict[str, Any],
    *,
    repository_root: Path = REPOSITORY_ROOT,
    verify_sources: bool = True,
) -> dict[str, Any]:
    issues: list[dict[str, str]] = []
    if Draft202012Validator is None:
        issues.append(_issue("jsonschema_unavailable", "$", "jsonschema is required"))
        return {"status": "failed", "evidence_level": "host_contract_validation_only", "issues": issues}

    schema = _load_json(SCHEMA_PATH)
    validator = Draft202012Validator(schema)
    for error in sorted(validator.iter_errors(contract), key=lambda item: list(item.path)):
        location = "$" + "".join("[%r]" % part for part in error.path)
        issues.append(_issue("schema_violation", location, error.message))
    if issues:
        return {"status": "failed", "evidence_level": "host_contract_validation_only", "issues": issues}

    sources = {item["source_id"]: item for item in contract["source_manifest"]}
    for field, provenance in contract["primitive"]["provenance"].items():
        for source_id in provenance["source_ids"]:
            if source_id not in sources:
                issues.append(
                    _issue(
                        "unknown_source_id",
                        "$.primitive.provenance.%s.source_ids" % field,
                        "Unknown source_id: %s" % source_id,
                    )
                )

    if verify_sources:
        root = repository_root.resolve()
        for index, source in enumerate(contract["source_manifest"]):
            path = (repository_root / source["path"]).resolve()
            try:
                path.relative_to(root)
            except ValueError:
                issues.append(_issue("source_path_escape", "$.source_manifest[%d].path" % index, "Source path escapes the repository"))
                continue
            if not path.is_file():
                issues.append(_issue("source_missing", "$.source_manifest[%d].path" % index, "Source file does not exist"))
                continue
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            if digest.lower() != source["sha256"].lower():
                issues.append(_issue("source_hash_mismatch", "$.source_manifest[%d].sha256" % index, "Source SHA-256 does not match"))

    primitive = contract["primitive"]
    minimum = [float(value) for value in primitive["minimum_corner_mm"]]
    size = [float(value) for value in primitive["size_mm"]]
    expected = contract["expected_geometry"]
    maximum = [minimum[index] + size[index] for index in range(3)]
    volume = size[0] * size[1] * size[2]
    for index, actual in enumerate(expected["bbox_min_mm"]):
        if not _near(actual, minimum[index]):
            issues.append(_issue("bbox_min_mismatch", "$.expected_geometry.bbox_min_mm[%d]" % index, "Expected minimum does not match primitive minimum"))
    for index, actual in enumerate(expected["bbox_max_mm"]):
        if not _near(actual, maximum[index]):
            issues.append(_issue("bbox_max_mismatch", "$.expected_geometry.bbox_max_mm[%d]" % index, "Expected maximum does not equal minimum plus size"))
    if not _near(expected["volume_mm3"], volume):
        issues.append(_issue("volume_mismatch", "$.expected_geometry.volume_mm3", "Expected volume does not equal the product of the three sizes"))

    return {
        "status": "failed" if issues else "passed",
        "evidence_level": "host_contract_validation_only",
        "issues": issues,
        "derived": {"bbox_min_mm": minimum, "bbox_max_mm": maximum, "volume_mm3": volume},
        "boundary": "This result checks declared structure and invariants only; it does not prove source interpretation or SpaceClaim geometry.",
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("contract", type=Path)
    parser.add_argument("--skip-source-files", action="store_true")
    args = parser.parse_args(argv)
    try:
        contract = _load_json(args.contract)
        result = validate_contract(contract, verify_sources=not args.skip_source_files)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        result = {
            "status": "failed",
            "evidence_level": "host_contract_validation_only",
            "issues": [_issue("load_failed", "$", str(exc))],
        }
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if result["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
