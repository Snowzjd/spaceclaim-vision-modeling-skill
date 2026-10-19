#!/usr/bin/env python3
"""Validate v0.3 operation-registry relationships on the host.

JSON Schema checks each document's shape. This validator checks relationships
that JSON Schema cannot express conveniently: unique identifiers, matching
template metadata, dependency integrity, artifact existence, SHA-256 evidence,
and exact template-version binding. It does not run SpaceClaim or upgrade any
declared evidence layer.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any

try:
    from jsonschema import Draft202012Validator
    from jsonschema.exceptions import SchemaError
except ImportError:  # pragma: no cover - exercised only on hosts missing the dependency
    Draft202012Validator = None
    SchemaError = Exception


STAGES = (
    "geometry_understanding",
    "modeling_strategy_scripting",
    "execution_recovery",
    "validation_visual_review",
)
EVIDENCE_LAYERS = (
    "design_only",
    "host_checked",
    "spaceclaim_execution",
    "geometry_measurements",
    "native_save",
    "native_reopen",
    "visual_review",
    "requested_export",
)
EVIDENCE_STATES = ("passed", "failed", "not_tested", "not_applicable")
TEMPLATE_REQUIRED = (
    "operation_id",
    "template_version",
    "contract_version",
    "status",
    "stage",
    "purpose",
    "trigger",
    "inputs",
    "preconditions",
    "outputs",
    "postconditions",
    "implementation",
    "semantic_selection",
    "failure_modes",
    "recovery",
    "validation",
    "dependencies",
    "evidence_level",
    "artifact_links",
)
RECORDED_ALIAS_RE = re.compile(r"(?:face|body)\d+", re.IGNORECASE)
WINDOWS_ABSOLUTE_RE = re.compile(r"^[A-Za-z]:[\\/]")
MAX_JSON_BYTES = 4 * 1024 * 1024


def add_issue(
    issues: list[dict[str, str]], code: str, path: str, message: str
) -> None:
    issues.append({"code": code, "path": path, "message": message})


def load_json(path: Path) -> Any:
    if path.stat().st_size > MAX_JSON_BYTES:
        raise ValueError("JSON file exceeds %d bytes: %s" % (MAX_JSON_BYTES, path))
    return json.loads(path.read_text(encoding="utf-8"))


def schema_error_path(error: Any, root: str) -> str:
    path = root
    for item in error.absolute_path:
        if isinstance(item, int):
            path += "[%d]" % item
        else:
            path += "." + str(item)
    return path


def load_schema_validators(
    package_root: Path, issues: list[dict[str, str]]
) -> tuple[Any | None, Any | None, Any | None]:
    if Draft202012Validator is None:
        add_issue(
            issues,
            "schema_validator_unavailable",
            "$",
            "The jsonschema package is required; validation fails closed when it is unavailable.",
        )
        return None, None, None
    references = package_root / "references"
    try:
        registry_schema = load_json(references / "operation-registry.schema.json")
        template_schema = load_json(references / "operation-template.schema.json")
        evidence_schema = load_json(references / "operation-evidence.schema.json")
        Draft202012Validator.check_schema(registry_schema)
        Draft202012Validator.check_schema(template_schema)
        Draft202012Validator.check_schema(evidence_schema)
    except (OSError, ValueError, json.JSONDecodeError, SchemaError) as exc:
        add_issue(issues, "schema_load_failed", "$", str(exc))
        return None, None, None
    return (
        Draft202012Validator(registry_schema),
        Draft202012Validator(template_schema),
        Draft202012Validator(evidence_schema),
    )


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def resolve_repo_path(
    repo_root: Path,
    value: Any,
    issue_path: str,
    issues: list[dict[str, str]],
) -> Path | None:
    if not isinstance(value, str) or not value.strip():
        add_issue(issues, "invalid_path", issue_path, "Expected a non-empty path string.")
        return None
    normalized = value.replace("\\", "/")
    if normalized.startswith("/") or WINDOWS_ABSOLUTE_RE.match(normalized):
        add_issue(issues, "absolute_path", issue_path, "Expected a repository-relative path.")
        return None
    candidate = (repo_root / Path(normalized)).resolve()
    try:
        candidate.relative_to(repo_root.resolve())
    except ValueError:
        add_issue(issues, "path_escape", issue_path, "Path escapes the repository root.")
        return None
    return candidate


def verify_file_ref(
    repo_root: Path,
    ref: Any,
    issue_path: str,
    issues: list[dict[str, str]],
    *,
    require_hash: bool,
) -> None:
    if not isinstance(ref, dict):
        add_issue(issues, "invalid_file_ref", issue_path, "Expected an object.")
        return
    path = resolve_repo_path(repo_root, ref.get("path"), issue_path + ".path", issues)
    if path is None:
        return
    if not path.is_file():
        add_issue(issues, "missing_artifact", issue_path + ".path", "Referenced file does not exist.")
        return
    expected_hash = ref.get("sha256")
    if require_hash and not isinstance(expected_hash, str):
        add_issue(issues, "missing_sha256", issue_path + ".sha256", "Evidence requires SHA-256.")
        return
    if expected_hash is not None:
        if not isinstance(expected_hash, str) or not re.fullmatch(r"[a-fA-F0-9]{64}", expected_hash):
            add_issue(issues, "invalid_sha256", issue_path + ".sha256", "Expected 64 hexadecimal characters.")
        elif sha256_file(path).lower() != expected_hash.lower():
            add_issue(issues, "sha256_mismatch", issue_path + ".sha256", "Referenced file hash does not match.")


def validate_operation_evidence(
    record: Any,
    template: dict[str, Any],
    repo_root: Path,
    issue_path: str,
    issues: list[dict[str, str]],
    schema_validator: Any,
) -> None:
    for error in sorted(
        schema_validator.iter_errors(record),
        key=lambda item: tuple(str(part) for part in item.absolute_path),
    ):
        add_issue(
            issues,
            "evidence_schema_violation",
            schema_error_path(error, issue_path),
            error.message,
        )
    if not isinstance(record, dict):
        return
    if record.get("operation_id") != template.get("operation_id"):
        add_issue(
            issues,
            "evidence_operation_mismatch",
            issue_path + ".operation_id",
            "Evidence operation_id must equal the template operation_id.",
        )
    if record.get("template_version") != template.get("template_version"):
        add_issue(
            issues,
            "evidence_record_version_mismatch",
            issue_path + ".template_version",
            "Evidence template_version must equal the template version.",
        )

    template_layers = template.get("evidence_level", {}).get("layers", {})
    record_layers = record.get("evidence_boundary")
    if isinstance(template_layers, dict) and isinstance(record_layers, dict):
        for layer in EVIDENCE_LAYERS:
            template_status = template_layers.get(layer, {}).get("status")
            record_status = record_layers.get(layer, {}).get("status")
            if template_status != record_status:
                add_issue(
                    issues,
                    "evidence_boundary_mismatch",
                    "%s.evidence_boundary.%s.status" % (issue_path, layer),
                    "Evidence boundary status must equal the template layer status.",
                )

    artifacts = record.get("artifacts")
    role_map: dict[str, list[dict[str, Any]]] = {}
    if isinstance(artifacts, list):
        for index, artifact in enumerate(artifacts):
            verify_file_ref(
                repo_root,
                artifact,
                "%s.artifacts[%d]" % (issue_path, index),
                issues,
                require_hash=True,
            )
            if isinstance(artifact, dict) and isinstance(artifact.get("role"), str):
                role_map.setdefault(artifact["role"], []).append(artifact)
    for role, path_field, hash_field in (
        ("tool", "tool", "tool_sha256"),
        ("test", "test", "test_sha256"),
    ):
        matching = [
            item
            for item in role_map.get(role, [])
            if item.get("path") == record.get(path_field)
            and item.get("sha256") == record.get(hash_field)
        ]
        if len(matching) != 1:
            add_issue(
                issues,
                "evidence_artifact_identity_mismatch",
                issue_path + ".artifacts",
                "Evidence %s path and SHA-256 must match exactly one %s artifact." % (path_field, role),
            )
    implementation = template.get("implementation")
    primary_artifact = implementation.get("primary_artifact") if isinstance(implementation, dict) else None
    host_checker = template.get("host_checker")
    expected_tool = primary_artifact
    expected_template_role = "implementation"
    if expected_tool is None and isinstance(host_checker, dict):
        expected_tool = host_checker.get("path")
        expected_template_role = "evaluation"
    if record.get("tool") != expected_tool:
        add_issue(
            issues,
            "evidence_primary_artifact_mismatch",
            issue_path + ".tool",
            "Evidence tool must equal the template primary_artifact or its declared host_checker when no primary artifact exists.",
        )
    template_links = template.get("artifact_links")
    if isinstance(template_links, list):
        for path_field, hash_field, template_role in (
            ("tool", "tool_sha256", expected_template_role),
            ("test", "test_sha256", "test"),
        ):
            matching_links = [
                item
                for item in template_links
                if isinstance(item, dict)
                and item.get("role") == template_role
                and item.get("path") == record.get(path_field)
                and item.get("sha256") == record.get(hash_field)
            ]
            if len(matching_links) != 1:
                add_issue(
                    issues,
                    "evidence_template_artifact_mismatch",
                    issue_path + "." + path_field,
                    "Evidence %s path and SHA-256 must match exactly one template %s artifact link."
                    % (path_field, template_role),
                )
    expected_host_status = "passed" if record.get("result") == "passed" else "failed"
    actual_host_status = (
        record_layers.get("host_checked", {}).get("status")
        if isinstance(record_layers, dict)
        else None
    )
    if actual_host_status != expected_host_status:
        add_issue(
            issues,
            "evidence_result_mismatch",
            issue_path + ".result",
            "Evidence result must match the host_checked boundary status.",
        )


def validate_template(
    template: Any,
    entry: dict[str, Any],
    repo_root: Path,
    issue_path: str,
    issues: list[dict[str, str]],
    evidence_schema_validator: Any,
) -> dict[str, Any] | None:
    if not isinstance(template, dict):
        add_issue(issues, "invalid_template", issue_path, "Template must be a JSON object.")
        return None
    for field in TEMPLATE_REQUIRED:
        if field not in template:
            add_issue(issues, "missing_template_field", issue_path + "." + field, "Required field is missing.")
    if any(field not in template for field in TEMPLATE_REQUIRED):
        return template

    for field in ("operation_id", "stage", "status", "template_version"):
        if entry.get(field) != template.get(field):
            add_issue(
                issues,
                "registry_template_mismatch",
                issue_path + "." + field,
                "Registry and template values must match.",
            )

    operation_id = template.get("operation_id")
    stage = template.get("stage")
    if isinstance(operation_id, str) and isinstance(stage, str):
        if operation_id.split(".", 1)[0] != stage:
            add_issue(issues, "operation_stage_mismatch", issue_path + ".operation_id", "Operation ID prefix must equal stage.")
        if RECORDED_ALIAS_RE.search(operation_id):
            add_issue(issues, "recorded_alias_in_id", issue_path + ".operation_id", "Recorded FaceN or BodyN aliases are forbidden.")

    implementation = template.get("implementation")
    if isinstance(implementation, dict):
        primary = implementation.get("primary_artifact")
        if primary is None:
            notes = implementation.get("notes")
            if not isinstance(notes, str) or not notes.strip():
                add_issue(issues, "missing_primary_artifact_reason", issue_path + ".implementation.notes", "Explain why primary_artifact is null.")
        else:
            path = resolve_repo_path(repo_root, primary, issue_path + ".implementation.primary_artifact", issues)
            if path is not None and not path.is_file():
                add_issue(issues, "missing_primary_artifact", issue_path + ".implementation.primary_artifact", "Primary artifact does not exist.")

    for binding_name, link_role in (("output_schema", "reference"), ("host_checker", "evaluation")):
        binding = template.get(binding_name)
        if binding is None:
            continue
        if not isinstance(binding, dict):
            add_issue(issues, "invalid_%s" % binding_name, issue_path + "." + binding_name, "Expected a path and SHA-256 binding object.")
            continue
        verify_file_ref(repo_root, binding, issue_path + "." + binding_name, issues, require_hash=True)
        links = template.get("artifact_links")
        matching = [
            item
            for item in links if isinstance(links, list) and isinstance(item, dict)
            and item.get("role") == link_role
            and item.get("path") == binding.get("path")
            and item.get("sha256") == binding.get("sha256")
        ] if isinstance(links, list) else []
        if len(matching) != 1:
            add_issue(issues, "%s_artifact_link_mismatch" % binding_name, issue_path + "." + binding_name, "%s must match exactly one %s artifact link." % (binding_name, link_role))

    host_status = template.get("evidence_level", {}).get("layers", {}).get("host_checked", {}).get("status")
    primary_artifact = implementation.get("primary_artifact") if isinstance(implementation, dict) else None
    if host_status in {"passed", "failed"} and primary_artifact is None and not isinstance(template.get("host_checker"), dict):
        add_issue(issues, "missing_host_checker", issue_path + ".host_checker", "Host evidence for a reasoning-guidance operation requires a declared host_checker.")

    artifact_links = template.get("artifact_links")
    validated_operation_evidence_refs: set[tuple[str, str]] = set()
    if not isinstance(artifact_links, list) or not artifact_links:
        add_issue(issues, "missing_artifact_links", issue_path + ".artifact_links", "At least one artifact link is required.")
    else:
        for index, link in enumerate(artifact_links):
            verify_file_ref(repo_root, link, "%s.artifact_links[%d]" % (issue_path, index), issues, require_hash=False)
            if (
                isinstance(link, dict)
                and link.get("role") == "evidence"
                and isinstance(link.get("path"), str)
                and link["path"].replace("\\", "/").startswith(
                    "spaceclaim-vision-modeling/assets/operation-templates/evidence/"
                )
            ):
                evidence_path = resolve_repo_path(
                    repo_root,
                    link["path"],
                    "%s.artifact_links[%d].path" % (issue_path, index),
                    issues,
                )
                if evidence_path is not None and evidence_path.is_file():
                    try:
                        record = load_json(evidence_path)
                    except (OSError, ValueError, json.JSONDecodeError) as exc:
                        add_issue(
                            issues,
                            "evidence_load_failed",
                            "%s.artifact_links[%d].path" % (issue_path, index),
                            str(exc),
                        )
                    else:
                        validate_operation_evidence(
                            record,
                            template,
                            repo_root,
                            "%s.operation_evidence" % issue_path,
                            issues,
                            evidence_schema_validator,
                        )
                        evidence_hash = link.get("sha256")
                        if isinstance(evidence_hash, str):
                            validated_operation_evidence_refs.add(
                                (
                                    link["path"].replace("\\", "/"),
                                    evidence_hash.lower(),
                                )
                            )

    evidence = template.get("evidence_level")
    passed_layers: list[str] = []
    if not isinstance(evidence, dict):
        add_issue(issues, "invalid_evidence_level", issue_path + ".evidence_level", "Expected an object.")
    else:
        if evidence.get("template_version") != template.get("template_version"):
            add_issue(issues, "evidence_version_mismatch", issue_path + ".evidence_level.template_version", "Evidence version must equal template_version.")
        layers = evidence.get("layers")
        if not isinstance(layers, dict):
            add_issue(issues, "invalid_evidence_layers", issue_path + ".evidence_level.layers", "Expected an object.")
        else:
            for layer in EVIDENCE_LAYERS:
                record = layers.get(layer)
                layer_path = "%s.evidence_level.layers.%s" % (issue_path, layer)
                if not isinstance(record, dict):
                    add_issue(issues, "missing_evidence_layer", layer_path, "Every evidence layer is required.")
                    continue
                status = record.get("status")
                refs = record.get("evidence_refs")
                if status not in EVIDENCE_STATES:
                    add_issue(issues, "invalid_evidence_status", layer_path + ".status", "Invalid evidence status.")
                    continue
                if status == "passed":
                    passed_layers.append(layer)
                if not isinstance(refs, list):
                    add_issue(issues, "invalid_evidence_refs", layer_path + ".evidence_refs", "Expected an array.")
                    continue
                if status in ("passed", "failed") and not refs:
                    add_issue(issues, "unbound_evidence", layer_path + ".evidence_refs", "Passed or failed evidence requires at least one hashed reference.")
                if status in ("not_tested", "not_applicable") and refs:
                    add_issue(issues, "unexpected_evidence_ref", layer_path + ".evidence_refs", "Untested or inapplicable evidence must not have references.")
                for index, ref in enumerate(refs):
                    verify_file_ref(repo_root, ref, "%s.evidence_refs[%d]" % (layer_path, index), issues, require_hash=True)
                    if (
                        isinstance(ref, dict)
                        and isinstance(ref.get("path"), str)
                        and ref["path"].replace("\\", "/").startswith(
                            "spaceclaim-vision-modeling/assets/operation-templates/evidence/"
                        )
                    ):
                        evidence_hash = ref.get("sha256")
                        identity = (
                            ref["path"].replace("\\", "/"),
                            evidence_hash.lower()
                            if isinstance(evidence_hash, str)
                            else "",
                        )
                        if identity not in validated_operation_evidence_refs:
                            add_issue(
                                issues,
                                "unregistered_operation_evidence_ref",
                                "%s.evidence_refs[%d]" % (layer_path, index),
                                "Operation evidence must match a semantically validated evidence artifact link by path and SHA-256.",
                            )

    declared_layers = entry.get("evidence_layers")
    if not isinstance(declared_layers, list) or set(declared_layers) != set(passed_layers):
        add_issue(issues, "registry_evidence_mismatch", issue_path + ".evidence_level.layers", "Registry evidence_layers must equal template layers with passed status.")

    failure_modes = template.get("failure_modes")
    recovery = template.get("recovery")
    if isinstance(failure_modes, list) and isinstance(recovery, list):
        failure_ids = {item.get("failure_id") for item in failure_modes if isinstance(item, dict)}
        recovery_ids = {item.get("failure_id") for item in recovery if isinstance(item, dict)}
        if failure_ids != recovery_ids:
            add_issue(issues, "recovery_coverage_mismatch", issue_path + ".recovery", "Recovery entries must cover exactly the declared failure modes.")
    return template


def find_dependency_cycles(
    dependencies: dict[str, list[str]], issues: list[dict[str, str]]
) -> None:
    state: dict[str, int] = {}

    def visit(operation_id: str, stack: list[str]) -> None:
        marker = state.get(operation_id, 0)
        if marker == 1:
            start = stack.index(operation_id) if operation_id in stack else 0
            cycle = stack[start:] + [operation_id]
            add_issue(issues, "dependency_cycle", "$.operations", "Dependency cycle: %s" % " -> ".join(cycle))
            return
        if marker == 2:
            return
        state[operation_id] = 1
        for dependency in dependencies.get(operation_id, []):
            if dependency in dependencies:
                visit(dependency, stack + [operation_id])
        state[operation_id] = 2

    for operation_id in dependencies:
        visit(operation_id, [])


def validate_registry(repo_root: Path, registry_path: Path | None = None) -> dict[str, Any]:
    repo_root = repo_root.resolve()
    package_root = repo_root / "spaceclaim-vision-modeling"
    registry_path = registry_path or package_root / "references" / "operation-registry.json"
    issues: list[dict[str, str]] = []
    (
        registry_schema_validator,
        template_schema_validator,
        evidence_schema_validator,
    ) = load_schema_validators(
        package_root, issues
    )
    if (
        registry_schema_validator is None
        or template_schema_validator is None
        or evidence_schema_validator is None
    ):
        return {"schema_version": 1, "evidence_level": "host_registry_validation_only", "status": "failed", "operations_checked": 0, "extensions_checked": 0, "issues": issues}
    try:
        registry = load_json(registry_path)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        add_issue(issues, "registry_load_failed", "$", str(exc))
        return {"schema_version": 1, "evidence_level": "host_registry_validation_only", "status": "failed", "operations_checked": 0, "extensions_checked": 0, "issues": issues}

    for error in sorted(
        registry_schema_validator.iter_errors(registry),
        key=lambda item: tuple(str(part) for part in item.absolute_path),
    ):
        add_issue(
            issues,
            "registry_schema_violation",
            schema_error_path(error, "$"),
            error.message,
        )

    operations = registry.get("operations") if isinstance(registry, dict) else None
    if not isinstance(operations, list):
        add_issue(issues, "invalid_operations", "$.operations", "Expected an array.")
        operations = []

    extension_points = registry.get("extension_points") if isinstance(registry, dict) else None
    if not isinstance(extension_points, list):
        add_issue(issues, "invalid_extension_points", "$.extension_points", "Expected an array.")
        extension_points = []
    extension_ids: set[str] = set()
    for index, extension in enumerate(extension_points):
        extension_path = "$.extension_points[%d]" % index
        if not isinstance(extension, dict):
            add_issue(issues, "invalid_extension_point", extension_path, "Expected an object.")
            continue
        extension_id = extension.get("extension_id")
        if not isinstance(extension_id, str) or not extension_id:
            add_issue(issues, "invalid_extension_id", extension_path + ".extension_id", "Expected a non-empty string.")
        elif extension_id in extension_ids:
            add_issue(issues, "duplicate_extension_id", extension_path + ".extension_id", "Extension IDs must be unique.")
        else:
            extension_ids.add(extension_id)
        if extension.get("bypass_core_stages") is not False:
            add_issue(issues, "extension_bypasses_core", extension_path + ".bypass_core_stages", "Extensions must re-enter the core workflow.")
        if extension.get("status") != "reserved":
            contract_path = resolve_repo_path(
                package_root,
                extension.get("contract_path"),
                extension_path + ".contract_path",
                issues,
            )
            if contract_path is not None and not contract_path.is_file():
                add_issue(issues, "missing_extension_contract", extension_path + ".contract_path", "Non-reserved extension contract does not exist.")

    entries: dict[str, dict[str, Any]] = {}
    templates: dict[str, dict[str, Any]] = {}
    for index, entry in enumerate(operations):
        entry_path = "$.operations[%d]" % index
        if not isinstance(entry, dict):
            add_issue(issues, "invalid_registry_entry", entry_path, "Expected an object.")
            continue
        operation_id = entry.get("operation_id")
        if not isinstance(operation_id, str) or not operation_id:
            add_issue(issues, "invalid_operation_id", entry_path + ".operation_id", "Expected a non-empty string.")
            continue
        if operation_id in entries:
            add_issue(issues, "duplicate_operation_id", entry_path + ".operation_id", "Operation IDs must be unique.")
            continue
        entries[operation_id] = entry
        template_relative = entry.get("template_path")
        template_path = resolve_repo_path(package_root, template_relative, entry_path + ".template_path", issues)
        if template_path is None or not template_path.is_file():
            if template_path is not None:
                add_issue(issues, "missing_template", entry_path + ".template_path", "Template file does not exist.")
            continue
        expected_template_hash = entry.get("template_sha256")
        if not isinstance(expected_template_hash, str) or not re.fullmatch(
            r"[a-fA-F0-9]{64}", expected_template_hash
        ):
            add_issue(
                issues,
                "invalid_template_sha256",
                entry_path + ".template_sha256",
                "Expected 64 hexadecimal characters.",
            )
        elif sha256_file(template_path).lower() != expected_template_hash.lower():
            add_issue(
                issues,
                "template_sha256_mismatch",
                entry_path + ".template_sha256",
                "Registered template hash does not match the template file.",
            )
        try:
            template = load_json(template_path)
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            add_issue(issues, "template_load_failed", entry_path + ".template_path", str(exc))
            continue
        for error in sorted(
            template_schema_validator.iter_errors(template),
            key=lambda item: tuple(str(part) for part in item.absolute_path),
        ):
            add_issue(
                issues,
                "template_schema_violation",
                schema_error_path(error, entry_path + ".template"),
                error.message,
            )
        checked = validate_template(
            template,
            entry,
            repo_root,
            entry_path + ".template",
            issues,
            evidence_schema_validator,
        )
        if checked is not None:
            templates[operation_id] = checked

    dependency_graph: dict[str, list[str]] = {}
    stage_index = {stage: index for index, stage in enumerate(STAGES)}
    for operation_id, template in templates.items():
        dependencies = template.get("dependencies")
        if not isinstance(dependencies, list):
            add_issue(issues, "invalid_dependencies", "$.operations[%s].dependencies" % operation_id, "Expected an array.")
            dependencies = []
        dependency_graph[operation_id] = [item for item in dependencies if isinstance(item, str)]
        for dependency in dependency_graph[operation_id]:
            if dependency not in entries:
                add_issue(issues, "missing_dependency", "$.operations[%s].dependencies" % operation_id, "Dependency is not registered: %s" % dependency)
                continue
            if entries[operation_id].get("status") == "active" and entries[dependency].get("status") != "active":
                add_issue(issues, "inactive_dependency", "$.operations[%s].dependencies" % operation_id, "An active operation may depend only on active operations.")
            own_stage = template.get("stage")
            dependency_stage = entries[dependency].get("stage")
            if own_stage in stage_index and dependency_stage in stage_index and stage_index[dependency_stage] > stage_index[own_stage]:
                add_issue(issues, "later_stage_dependency", "$.operations[%s].dependencies" % operation_id, "An operation cannot depend on a later workflow stage.")
    find_dependency_cycles(dependency_graph, issues)

    return {
        "schema_version": 1,
        "evidence_level": "host_registry_validation_only",
        "status": "failed" if issues else "passed",
        "operations_checked": len(operations),
        "extensions_checked": len(extension_points),
        "issues": issues,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("registry", nargs="?", type=Path, help="Registry JSON path")
    parser.add_argument("--repo-root", type=Path, help="Repository root")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    inferred_root = Path(__file__).resolve().parents[2]
    repo_root = (args.repo_root or inferred_root).resolve()
    registry = args.registry.resolve() if args.registry else None
    result = validate_registry(repo_root, registry)
    json.dump(result, sys.stdout, indent=2, sort_keys=True)
    sys.stdout.write("\n")
    return 0 if result["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
