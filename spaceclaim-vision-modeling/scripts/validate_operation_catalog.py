#!/usr/bin/env python3
"""Validate the host-side v0.3 operation catalog.

This validator checks the catalog's JSON shape and its relationship with the
operation registry.  It deliberately does not inspect operation templates,
template hashes, dependency graphs, or SpaceClaim behavior.  In particular,
``required_evidence`` is a declaration of the evidence layer needed by an
operation; this tool does not claim that the evidence has been produced.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any


PACKAGE_RELATIVE_CATALOG = Path("spaceclaim-vision-modeling/references/operation-catalog.json")
PACKAGE_RELATIVE_REGISTRY = Path("spaceclaim-vision-modeling/references/operation-registry.json")

CATALOG_FIELDS = frozenset({"catalog_version", "architecture_version", "stages", "operations"})
OPERATION_FIELDS = frozenset(
    {
        "id",
        "stage",
        "name",
        "operation",
        "inputs",
        "output",
        "preconditions",
        "postcondition",
        "topology_effect",
        "required_evidence",
        "lifecycle",
        "registry_operation_id",
        "implementation_scope",
    }
)

STAGES = (
    "geometry_understanding",
    "modeling_strategy_scripting",
    "execution_recovery",
    "validation_visual_review",
)

# These are the catalog's public identifiers, not registry operation names.
# The registry remains the source of truth for the actual IDs used by backed
# active/candidate/deprecated operations.
PREFIX_TO_STAGE = {
    "GU": "geometry_understanding",
    "MS": "modeling_strategy_scripting",
    "MA": "modeling_strategy_scripting",
    "EX": "execution_recovery",
    "ER": "execution_recovery",
    "VA": "validation_visual_review",
    "VI": "validation_visual_review",
}
ID_RANGES = {
    "GU": 20,
    "MS": 11,
    "MA": 35,
    "EX": 14,
    "ER": 12,
    "VA": 25,
    "VI": 22,
}
EXPECTED_OPERATION_IDS = frozenset(
    "%s-%02d" % (prefix, number)
    for prefix, count in ID_RANGES.items()
    for number in range(1, count + 1)
)

TOPOLOGY_EFFECTS = frozenset({"none", "creates", "modifies", "deletes", "conditional"})
LIFECYCLES = frozenset({"catalogued", "candidate", "active", "deprecated"})
REGISTRY_STATUSES = frozenset({"candidate", "active", "deprecated"})
EVIDENCE_LAYERS = frozenset(
    {
        "interpretation_evaluation",
        "host_checked",
        "spaceclaim_execution",
        "geometry_measurements",
        "native_save",
        "native_reopen",
        "visual_review",
        "requested_export",
    }
)
OPERATION_ID_RE = re.compile(r"^(?P<prefix>[A-Z]{2})-(?P<number>\d{2})$")
KEBAB_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
HAN_RE = re.compile(r"[\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff]")


def _issue(issues: list[dict[str, str]], code: str, path: str, message: str) -> None:
    issues.append({"code": code, "path": path, "message": message})


def _reject_non_finite(value: str) -> None:
    raise ValueError("Non-finite JSON number is not allowed: %s" % value)


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"), parse_constant=_reject_non_finite)


def _is_nonempty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _validate_nonempty_string(
    value: Any,
    path: str,
    field: str,
    issues: list[dict[str, str]],
) -> None:
    if not isinstance(value, str):
        _issue(issues, "invalid_field_type", path, "%s must be a string." % field)
    elif not value.strip():
        _issue(issues, "empty_string", path, "%s must not be blank." % field)


def _validate_string_array(
    value: Any,
    path: str,
    field: str,
    issues: list[dict[str, str]],
) -> None:
    if not isinstance(value, list):
        _issue(issues, "invalid_field_type", path, "%s must be an array of strings." % field)
        return
    if not value:
        _issue(issues, "empty_array", path, "%s must contain at least one string." % field)
    for index, item in enumerate(value):
        if not isinstance(item, str):
            _issue(
                issues,
                "invalid_field_type",
                "%s[%d]" % (path, index),
                "%s entries must be strings." % field,
            )
        elif not item.strip():
            _issue(
                issues,
                "empty_string",
                "%s[%d]" % (path, index),
                "%s entries must not be blank." % field,
            )


def _expected_id(id_value: str) -> bool:
    return id_value in EXPECTED_OPERATION_IDS


def _validate_catalog_operation(
    operation: Any,
    index: int,
    catalog_stages: set[str],
    issues: list[dict[str, str]],
    operation_ids: list[str],
    operation_names: dict[tuple[str, str], str],
) -> None:
    path = "$.operations[%d]" % index
    if not isinstance(operation, dict):
        _issue(issues, "invalid_operation_type", path, "Each operation must be an object.")
        return

    unknown = sorted(set(operation) - OPERATION_FIELDS)
    for field in unknown:
        _issue(issues, "unknown_operation_field", path + "." + str(field), "Unknown operation field.")
    for field in sorted(OPERATION_FIELDS - set(operation)):
        _issue(issues, "missing_operation_field", path + "." + field, "Required operation field is missing.")

    id_value = operation.get("id")
    if not isinstance(id_value, str):
        _issue(issues, "invalid_field_type", path + ".id", "id must be a string.")
    elif not id_value.strip():
        _issue(issues, "empty_string", path + ".id", "id must not be blank.")
    else:
        operation_ids.append(id_value)
        if operation_ids.count(id_value) > 1:
            _issue(issues, "duplicate_operation_id", path + ".id", "Operation IDs must be unique.")
        if not _expected_id(id_value):
            _issue(issues, "unexpected_operation_id", path + ".id", "Operation ID is outside the required catalog coverage.")

        match = OPERATION_ID_RE.fullmatch(id_value)
        if match is None or match.group("prefix") not in PREFIX_TO_STAGE:
            _issue(issues, "invalid_operation_id", path + ".id", "Operation ID must use a required two-letter prefix and two-digit number.")
        elif id_value not in EXPECTED_OPERATION_IDS:
            # Keep the coverage issue above as the primary signal; this detail
            # is useful when the prefix is known but its number is out of range.
            _issue(issues, "operation_number_out_of_range", path + ".id", "Operation number is outside the required range for its prefix.")

    stage_value = operation.get("stage")
    if not isinstance(stage_value, str):
        _issue(issues, "invalid_field_type", path + ".stage", "stage must be a string.")
    elif stage_value not in catalog_stages:
        _issue(issues, "invalid_stage", path + ".stage", "stage must be one of the catalog stages.")

    if isinstance(id_value, str) and isinstance(stage_value, str):
        match = OPERATION_ID_RE.fullmatch(id_value)
        if match and match.group("prefix") in PREFIX_TO_STAGE:
            expected_stage = PREFIX_TO_STAGE[match.group("prefix")]
            if stage_value != expected_stage:
                _issue(
                    issues,
                    "operation_stage_mismatch",
                    path + ".stage",
                    "Operation ID prefix %s belongs to stage %s." % (match.group("prefix"), expected_stage),
                )

    name_value = operation.get("name")
    if not isinstance(name_value, str):
        _issue(issues, "invalid_field_type", path + ".name", "name must be a string.")
    elif not name_value.strip():
        _issue(issues, "empty_string", path + ".name", "name must not be blank.")
    elif not HAN_RE.search(name_value):
        _issue(issues, "name_not_chinese", path + ".name", "name must contain a Chinese descriptive action.")

    operation_name = operation.get("operation")
    if not isinstance(operation_name, str):
        _issue(issues, "invalid_field_type", path + ".operation", "operation must be a string.")
    elif not operation_name.strip():
        _issue(issues, "empty_string", path + ".operation", "operation must not be blank.")
    elif KEBAB_RE.fullmatch(operation_name) is None:
        _issue(issues, "invalid_operation_name", path + ".operation", "operation must be lowercase kebab-case.")
    elif isinstance(stage_value, str):
        key = (stage_value, operation_name)
        if key in operation_names:
            _issue(
                issues,
                "duplicate_operation_name",
                path + ".operation",
                "operation must be unique within its stage; first seen at %s." % operation_names[key],
            )
        else:
            operation_names[key] = path + ".operation"

    _validate_string_array(operation.get("inputs"), path + ".inputs", "inputs", issues)
    _validate_nonempty_string(operation.get("output"), path + ".output", "output", issues)
    _validate_string_array(operation.get("preconditions"), path + ".preconditions", "preconditions", issues)
    _validate_nonempty_string(operation.get("postcondition"), path + ".postcondition", "postcondition", issues)

    topology = operation.get("topology_effect")
    if not isinstance(topology, str):
        _issue(issues, "invalid_field_type", path + ".topology_effect", "topology_effect must be a string.")
    elif topology not in TOPOLOGY_EFFECTS:
        _issue(issues, "invalid_topology_effect", path + ".topology_effect", "Unknown topology effect.")

    evidence = operation.get("required_evidence")
    if not isinstance(evidence, list):
        _issue(issues, "invalid_field_type", path + ".required_evidence", "required_evidence must be an array of strings.")
    elif not evidence:
        _issue(issues, "empty_required_evidence", path + ".required_evidence", "required_evidence must contain at least one layer.")
    else:
        seen_evidence: set[str] = set()
        for evidence_index, layer in enumerate(evidence):
            evidence_path = "%s.required_evidence[%d]" % (path, evidence_index)
            if not isinstance(layer, str):
                _issue(issues, "invalid_field_type", evidence_path, "Evidence layers must be strings.")
                continue
            if not layer.strip():
                _issue(issues, "empty_string", evidence_path, "Evidence layer names must not be blank.")
            if layer not in EVIDENCE_LAYERS:
                _issue(issues, "invalid_required_evidence", evidence_path, "Unknown required evidence layer.")
            if layer in seen_evidence:
                _issue(issues, "duplicate_required_evidence", evidence_path, "required_evidence entries must be unique.")
            seen_evidence.add(layer)

    lifecycle = operation.get("lifecycle")
    if not isinstance(lifecycle, str):
        _issue(issues, "invalid_field_type", path + ".lifecycle", "lifecycle must be a string.")
    elif lifecycle not in LIFECYCLES:
        _issue(issues, "invalid_lifecycle", path + ".lifecycle", "Unknown lifecycle value.")

    registry_id = operation.get("registry_operation_id")
    if registry_id is not None and not isinstance(registry_id, str):
        _issue(issues, "invalid_field_type", path + ".registry_operation_id", "registry_operation_id must be a string or null.")
    elif isinstance(registry_id, str) and not registry_id.strip():
        _issue(issues, "empty_string", path + ".registry_operation_id", "registry_operation_id must not be blank when provided.")

    _validate_nonempty_string(
        operation.get("implementation_scope"),
        path + ".implementation_scope",
        "implementation_scope",
        issues,
    )


def _load_registry(
    registry_path: Path,
    issues: list[dict[str, str]],
) -> tuple[list[str] | None, list[dict[str, Any]] | None]:
    try:
        registry = _load_json(registry_path)
    except (OSError, UnicodeError, ValueError, json.JSONDecodeError) as exc:
        _issue(issues, "registry_load_failed", "$", "Could not read operation registry: %s" % exc)
        return None, None

    if not isinstance(registry, dict):
        _issue(issues, "invalid_registry_root", "$", "Operation registry must be an object.")
        return None, None

    stages_value = registry.get("stages")
    registry_stages: list[str] | None
    if not isinstance(stages_value, list):
        _issue(issues, "invalid_registry_stages", "$.registry.stages", "Registry stages must be an array.")
        registry_stages = None
    else:
        registry_stages = []
        for index, stage in enumerate(stages_value):
            if not isinstance(stage, str) or not stage.strip():
                _issue(issues, "invalid_registry_stage", "$.registry.stages[%d]" % index, "Registry stage IDs must be non-empty strings.")
            else:
                registry_stages.append(stage)
        if len(stages_value) != len(STAGES):
            _issue(issues, "invalid_registry_stage_count", "$.registry.stages", "Registry must declare four workflow stages.")
        if len(set(registry_stages)) != len(registry_stages):
            _issue(issues, "duplicate_registry_stage", "$.registry.stages", "Registry stage IDs must be unique.")

    operations_value = registry.get("operations")
    if not isinstance(operations_value, list):
        _issue(issues, "invalid_registry_operations", "$.registry.operations", "Registry operations must be an array.")
        return registry_stages, None

    registry_operations: list[dict[str, Any]] = []
    registry_ids: set[str] = set()
    for index, entry in enumerate(operations_value):
        path = "$.registry.operations[%d]" % index
        if not isinstance(entry, dict):
            _issue(issues, "invalid_registry_operation", path, "Registry operation entries must be objects.")
            continue
        operation_id = entry.get("operation_id")
        stage = entry.get("stage")
        status = entry.get("status")
        if not isinstance(operation_id, str) or not operation_id.strip():
            _issue(issues, "invalid_registry_operation_id", path + ".operation_id", "Registry operation_id must be a non-empty string.")
        elif operation_id in registry_ids:
            _issue(issues, "duplicate_registry_operation_id", path + ".operation_id", "Registry operation IDs must be unique.")
        else:
            registry_ids.add(operation_id)
        if not isinstance(stage, str) or not stage.strip():
            _issue(issues, "invalid_registry_operation_stage", path + ".stage", "Registry operation stage must be a non-empty string.")
        if not isinstance(status, str) or status not in REGISTRY_STATUSES:
            _issue(issues, "invalid_registry_operation_status", path + ".status", "Registry operation status is invalid.")
        registry_operations.append(
            {
                "operation_id": operation_id,
                "stage": stage,
                "status": status,
                "path": path,
            }
        )
    return registry_stages, registry_operations


def _validate_registry_bindings(
    catalog_operations: list[Any],
    registry_operations: list[dict[str, Any]] | None,
    issues: list[dict[str, str]],
) -> None:
    if registry_operations is None:
        return

    registry_by_id: dict[str, dict[str, Any]] = {}
    for entry in registry_operations:
        operation_id = entry.get("operation_id")
        if isinstance(operation_id, str) and operation_id not in registry_by_id:
            registry_by_id[operation_id] = entry

    bound_registry_ids: dict[str, str] = {}
    for index, operation in enumerate(catalog_operations):
        if not isinstance(operation, dict):
            continue
        path = "$.operations[%d]" % index
        lifecycle = operation.get("lifecycle")
        registry_id = operation.get("registry_operation_id")
        if lifecycle == "catalogued":
            if registry_id is not None:
                _issue(
                    issues,
                    "catalogued_registry_binding",
                    path + ".registry_operation_id",
                    "catalogued operations must have registry_operation_id set to null.",
                )
            continue

        if isinstance(lifecycle, str) and lifecycle in {"candidate", "active", "deprecated"}:
            if registry_id is None:
                _issue(
                    issues,
                    "lifecycle_missing_registry_binding",
                    path + ".registry_operation_id",
                    "Non-catalogued operations must bind one registry operation.",
                )
                continue
            if not isinstance(registry_id, str) or not registry_id.strip():
                continue
            if registry_id in bound_registry_ids:
                _issue(
                    issues,
                    "registry_binding_not_one_to_one",
                    path + ".registry_operation_id",
                    "A registry operation may be bound to only one catalog operation; first seen at %s."
                    % bound_registry_ids[registry_id],
                )
            else:
                bound_registry_ids[registry_id] = path + ".registry_operation_id"

            registry_entry = registry_by_id.get(registry_id)
            if registry_entry is None:
                _issue(
                    issues,
                    "registry_operation_missing",
                    path + ".registry_operation_id",
                    "registry_operation_id does not exist in the operation registry.",
                )
                continue

            if operation.get("stage") != registry_entry.get("stage"):
                _issue(
                    issues,
                    "registry_stage_mismatch",
                    path + ".stage",
                    "Catalog stage must equal the bound registry operation stage.",
                )
            if lifecycle != registry_entry.get("status"):
                _issue(
                    issues,
                    "registry_status_mismatch",
                    path + ".lifecycle",
                    "Catalog lifecycle must equal the bound registry operation status.",
                )

    for operation_id, entry in registry_by_id.items():
        if operation_id not in bound_registry_ids:
            _issue(
                issues,
                "registry_operation_unaccounted",
                entry.get("path", "$.registry.operations") + ".operation_id",
                "Every existing registry operation must be accounted for by one catalog operation.",
            )


def _resolve_catalog_path(repo_root: Path, catalog_path: Path | None) -> Path:
    if catalog_path is None:
        return repo_root / PACKAGE_RELATIVE_CATALOG
    candidate = Path(catalog_path)
    return candidate if candidate.is_absolute() else repo_root / candidate


def _report(
    catalog_path: Path,
    registry_path: Path,
    issues: list[dict[str, str]],
    operations_checked: int,
    registry_operations_checked: int,
) -> dict[str, Any]:
    expected_count = len(EXPECTED_OPERATION_IDS)
    counts = {
        "operations": operations_checked,
        "operations_checked": operations_checked,
        "expected_operations": expected_count,
        "registry_operations": registry_operations_checked,
        "registry_operations_checked": registry_operations_checked,
        "issues": len(issues),
    }
    return {
        "schema_version": 1,
        "catalog": str(catalog_path),
        "registry": str(registry_path),
        "status": "failed" if issues else "passed",
        "counts": counts,
        "operations_checked": operations_checked,
        "registry_operations_checked": registry_operations_checked,
        "issues": issues,
        "evidence_boundary": "Host-only catalog type, coverage, and registry-synchronization checks; no template, SpaceClaim, or evidence-result claim is made.",
    }


def validate_catalog(repo_root: Path, catalog_path: Path | None = None) -> dict[str, Any]:
    """Validate a catalog and its operation-registry synchronization.

    ``catalog_path`` may be absolute or repository-relative.  When omitted,
    the package-relative catalog path is used.  All expected input failures
    are returned in the report rather than escaping as exceptions.
    """

    issues: list[dict[str, str]] = []
    try:
        root = Path(repo_root).resolve()
    except (OSError, TypeError, ValueError) as exc:
        fallback_catalog = Path(catalog_path) if catalog_path is not None else PACKAGE_RELATIVE_CATALOG
        return _report(fallback_catalog, PACKAGE_RELATIVE_REGISTRY, [{"code": "invalid_repo_root", "path": "$", "message": str(exc)}], 0, 0)

    catalog_file = _resolve_catalog_path(root, catalog_path)
    registry_file = root / PACKAGE_RELATIVE_REGISTRY
    operations_checked = 0
    registry_operations_checked = 0

    try:
        catalog = _load_json(catalog_file)
    except (OSError, UnicodeError, ValueError, json.JSONDecodeError) as exc:
        _issue(issues, "catalog_load_failed", "$", "Could not read operation catalog: %s" % exc)
        return _report(catalog_file, registry_file, issues, 0, 0)

    registry_stages, registry_operations = _load_registry(registry_file, issues)
    if registry_operations is not None:
        registry_operations_checked = len(registry_operations)

    if not isinstance(catalog, dict):
        _issue(issues, "invalid_catalog_root", "$", "Operation catalog must be an object.")
        return _report(catalog_file, registry_file, issues, 0, registry_operations_checked)

    unknown = sorted(set(catalog) - CATALOG_FIELDS)
    for field in unknown:
        _issue(issues, "unknown_catalog_field", "$." + str(field), "Unknown catalog field.")
    for field in sorted(CATALOG_FIELDS - set(catalog)):
        _issue(issues, "missing_catalog_field", "$." + field, "Required catalog field is missing.")

    catalog_version = catalog.get("catalog_version")
    if type(catalog_version) is not int or catalog_version != 1:
        _issue(issues, "invalid_catalog_version", "$.catalog_version", "catalog_version must be integer 1 (boolean values are not accepted).")

    architecture_version = catalog.get("architecture_version")
    if not isinstance(architecture_version, str) or architecture_version != "0.3":
        _issue(issues, "invalid_architecture_version", "$.architecture_version", "architecture_version must be the string '0.3'.")

    catalog_stages_value = catalog.get("stages")
    catalog_stages: set[str] = set()
    if not isinstance(catalog_stages_value, list):
        _issue(issues, "invalid_stages_type", "$.stages", "stages must be an array of four stage IDs.")
    else:
        for index, stage in enumerate(catalog_stages_value):
            if not isinstance(stage, str) or not stage.strip():
                _issue(issues, "invalid_stage", "$.stages[%d]" % index, "Stage IDs must be non-empty strings.")
            else:
                catalog_stages.add(stage)
        if len(catalog_stages_value) != len(STAGES):
            _issue(issues, "invalid_stage_count", "$.stages", "Catalog must declare exactly four workflow stages.")
        if len(catalog_stages) != len(catalog_stages_value):
            _issue(issues, "duplicate_stage", "$.stages", "Catalog stage IDs must be unique.")
        if tuple(catalog_stages_value) != STAGES:
            _issue(issues, "invalid_stage_ids", "$.stages", "Catalog stages must be the four established workflow stage IDs in registry order.")
        if registry_stages is not None and catalog_stages_value != registry_stages:
            _issue(issues, "catalog_registry_stage_mismatch", "$.stages", "Catalog stages must equal the registry stages.")

    operations_value = catalog.get("operations")
    if not isinstance(operations_value, list):
        _issue(issues, "invalid_operations_type", "$.operations", "operations must be an array.")
        _validate_registry_bindings([], registry_operations, issues)
        return _report(catalog_file, registry_file, issues, 0, registry_operations_checked)

    operations_checked = len(operations_value)
    operation_ids: list[str] = []
    operation_names: dict[tuple[str, str], str] = {}
    for index, operation in enumerate(operations_value):
        _validate_catalog_operation(
            operation,
            index,
            catalog_stages,
            issues,
            operation_ids,
            operation_names,
        )

    actual_ids = set(operation_ids)
    for expected_id in sorted(EXPECTED_OPERATION_IDS):
        if expected_id not in actual_ids:
            _issue(issues, "missing_operation_id", "$.operations", "Required operation ID is missing: %s." % expected_id)
    if operations_checked != len(EXPECTED_OPERATION_IDS):
        _issue(issues, "operation_count_mismatch", "$.operations", "Catalog must contain exactly %d operations." % len(EXPECTED_OPERATION_IDS))

    _validate_registry_bindings(operations_value, registry_operations, issues)
    return _report(catalog_file, registry_file, issues, operations_checked, registry_operations_checked)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("catalog", nargs="?", type=Path, help="Catalog JSON path; defaults to the package catalog.")
    parser.add_argument("--repo-root", type=Path, help="Repository root; defaults to the repository containing this script.")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    inferred_root = Path(__file__).resolve().parents[2]
    root = (args.repo_root or inferred_root).resolve()
    catalog = args.catalog.resolve() if args.catalog else None
    result = validate_catalog(root, catalog)
    json.dump(result, sys.stdout, ensure_ascii=False, indent=2, sort_keys=True)
    sys.stdout.write("\n")
    return 0 if result["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
