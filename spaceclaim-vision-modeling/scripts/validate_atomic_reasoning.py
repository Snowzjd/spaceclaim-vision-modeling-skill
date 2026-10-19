#!/usr/bin/env python3
"""Read-only checks of single GU/MS results, not a source interpretation score."""
from __future__ import annotations

import argparse
import ast
import hashlib
import json
import math
from pathlib import Path

import jsonschema

PACKAGE = Path(__file__).resolve().parents[1]
KINDS = {"image", "drawing", "text", "model", "script", "log", "operation", "api_reference"}
TYPES = {"string": str, "number": (int, float), "array": list, "object": dict, "boolean": bool}


def load(path):
    def reject(value):
        raise ValueError("Non-finite JSON number: " + value)
    return json.loads(Path(path).read_text(encoding="utf-8"), parse_constant=reject)


def specifications():
    result = {}
    for name in ("geometry-understanding-atomic-guidance.json", "strategy-atomic-guidance.json"):
        for item in load(PACKAGE / "references" / name)["operations"]:
            if "path" in item:
                path = (PACKAGE / item["path"]).resolve()
                if not path.is_relative_to(PACKAGE.resolve()):
                    raise ValueError("Guidance path escapes package")
                if hashlib.sha256(path.read_bytes()).hexdigest() != item["sha256"]:
                    raise ValueError("Guidance index hash mismatch")
                spec = load(path)
                if spec["catalog_id"] != item["catalog_id"]:
                    raise ValueError("Guidance index identity mismatch")
                item = spec
            if item["catalog_id"] in result:
                raise ValueError("Duplicate guidance ID")
            result[item["catalog_id"]] = item
    return result


def number(value):
    return type(value) in (int, float) and math.isfinite(value)


def locator_valid(value):
    if isinstance(value, str): return bool(value.strip())
    return isinstance(value, dict) and bool(value) and all(isinstance(k, str) and k.strip() and isinstance(v, str) and v.strip() for k, v in value.items())


def arithmetic(expression, bindings):
    """A bounded arithmetic tree; no eval, calls, powers, indexing or attributes."""
    if not isinstance(expression, str) or len(expression) > 1000:
        raise ValueError("Invalid arithmetic expression")
    if isinstance(bindings, dict):
        bindings = {key: (value.get("value") if isinstance(value, dict) else value) for key, value in bindings.items()}
    if not isinstance(bindings, dict) or not all(number(v) for v in bindings.values()):
        raise ValueError("Bindings must be finite numeric scalars")
    tree = ast.parse(expression, mode="eval")
    if sum(1 for _ in ast.walk(tree)) > 100:
        raise ValueError("Expression exceeds the bounded arithmetic scope")
    def visit(node):
        if isinstance(node, ast.Expression):
            return visit(node.body)
        if isinstance(node, ast.Constant) and number(node.value):
            return node.value
        if isinstance(node, ast.Name) and node.id in bindings:
            return bindings[node.id]
        if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.UAdd, ast.USub)):
            return visit(node.operand) * (-1 if isinstance(node.op, ast.USub) else 1)
        if isinstance(node, ast.BinOp):
            a, b = visit(node.left), visit(node.right)
            if isinstance(node.op, ast.Add): return a + b
            if isinstance(node.op, ast.Sub): return a - b
            if isinstance(node.op, ast.Mult): return a * b
            if isinstance(node.op, ast.Div): return a / b
        raise ValueError("Unsupported arithmetic syntax or missing binding")
    value = visit(tree)
    if not number(value):
        raise ValueError("Non-finite arithmetic result")
    return value


def numeric_checks(op, data):
    issues = []
    if op == "GU-12":
        units = {"mm": ("length", 1), "cm": ("length", 10), "m": ("length", 1000),
                 "in": ("length", 25.4), "mm2": ("area", 1), "cm2": ("area", 100),
                 "m2": ("area", 1e6), "mm3": ("volume", 1), "cm3": ("volume", 1000),
                 "m3": ("volume", 1e9), "deg": ("angle", math.pi / 180), "rad": ("angle", 1)}
        unit_key = lambda unit: unit.replace("^", "").replace("²", "2").replace("³", "3")
        original, target = units.get(unit_key(data["original_unit"])), units.get(unit_key(data["unit"]))
        quantity = {"diameter": "length", "radius": "length"}.get(data["quantity_kind"], data["quantity_kind"])
        if not original or not target or original[0] != target[0] or quantity != target[0]:
            issues.append("Unsupported or incompatible units; provide an explicit supported conversion")
        elif not math.isclose(data["original_value"] * original[1] / target[1], data["value"], rel_tol=1e-10, abs_tol=1e-10):
            issues.append("Unit conversion value mismatch")
    elif op in ("GU-13", "GU-19"):
        if not math.isclose(arithmetic(data["expression"], data["bindings"]), data["value"], rel_tol=1e-10, abs_tol=1e-10):
            issues.append("Derived result does not match expression")
    elif op == "GU-14":
        a, b, tol = data["lhs"], data["rhs"], data["tolerance"]
        if tol < 0:
            issues.append("Negative relation tolerance")
        else:
            predicates = {"eq": abs(a - b) <= tol, "le": a <= b + tol, "ge": a >= b - tol}
            relation = data["relation"]
            if relation not in predicates:
                issues.append("Unsupported dimension relation")
            elif data["verdict"] not in ("consistent", "conflict", "redundant"):
                issues.append("Fully numeric relation must be decided")
            elif predicates[relation] != (data["verdict"] != "conflict"):
                issues.append("Dimension relation verdict mismatch")
    elif op == "GU-15":
        origin, axes = data["origin"], data["axes"]
        if len(origin) != 3 or not all(number(v) for v in origin):
            issues.append("Invalid frame origin")
        if len(axes) != 3 or any(not isinstance(a, list) or len(a) != 3 or not all(number(v) for v in a) for a in axes):
            issues.append("Invalid frame axes")
        else:
            dot = lambda a, b: sum(x*y for x, y in zip(a, b))
            for i in range(3):
                for j in range(3):
                    if not math.isclose(dot(axes[i], axes[j]), 1 if i == j else 0, abs_tol=1e-8):
                        issues.append("Frame axes are not orthonormal")
            a, b, c = axes
            cross = [a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2], a[0]*b[1]-a[1]*b[0]]
            hand = str(data["handedness"]).replace("_", "-")
            sign = {"right-handed": 1, "left-handed": -1}.get(hand)
            if sign is None or not math.isclose(dot(cross, c), sign, abs_tol=1e-8):
                issues.append("Frame handedness mismatch")
    return issues


def strategy_checks(op, data):
    """Required nested payloads and deterministic declarations, not API proof."""
    required = {
        "parameter_declaration": "name value unit allowed_range provenance",
        "constraint_result": "parameter_name value operator operand unit verdict violation_reason",
        "construction_decision": "method_id reason prerequisites covered_effect stability_basis",
        "dependency_edge": "upstream_id downstream_id artifact_or_state rationale",
        "api_binding": "target_version symbol argument_mappings return_mapping source_ref",
        "semantic_predicate": "object_type criteria match_rule refresh_prerequisite",
        "ambiguity_policy": "zero_matches one_match multiple_matches",
        "topology_refresh_declaration": "action_id affected_references refresh_before_next_selection refresh_scope",
        "assertion_definition": "property measurement_method units tolerance pass_rule fail_rule unknown_measurement_rule",
        "output_path_binding": "role path_or_expression run_directory overwrite_policy writes_performed",
        "collision_check": "contained collides protected decision",
    }
    issues = []
    for field, keys in required.items():
        if field in data and data[field] is not None:
            if not isinstance(data[field], dict) or set(keys.split()) - set(data[field]):
                issues.append("Missing nested result members: " + field)
    if issues: return issues
    if op == "MS-01" and data.get("parameter_declaration") is not None:
        value = data["parameter_declaration"]["value"]
        if not number(value): issues.append("Parameter value must be finite numeric")
    if op == "MS-02" and data.get("constraint_result") is not None:
        c = data["constraint_result"]
        a, b = c["value"], c["operand"]
        if c["operator"] in ("in", "not_in"):
            if not number(a) or not isinstance(b, list) or not b or not all(number(v) for v in b):
                issues.append("Membership requires a finite value and a nonempty finite allowed-value list")
            else:
                valid = (a in b) if c["operator"] == "in" else (a not in b)
                if c["verdict"] not in ("pass", "fail", "passed", "failed") or (c["verdict"] in ("pass", "passed")) != valid:
                    issues.append("Parameter constraint verdict mismatch")
        elif not number(a) or not number(b):
            issues.append("Numeric constraint requires finite values")
        else:
            checks = {"gt": a > b, ">": a > b, "ge": a >= b, ">=": a >= b,
                      "lt": a < b, "<": a < b, "le": a <= b, "<=": a <= b,
                      "eq": a == b, "==": a == b, "ne": a != b, "!=": a != b}
            valid = checks.get(c["operator"])
            if valid is None: issues.append("Unsupported scalar constraint; leave it unresolved or supply a supported adapter")
            elif c["verdict"] not in ("pass", "fail", "passed", "failed") or (c["verdict"] in ("pass", "passed")) != valid:
                issues.append("Parameter constraint verdict mismatch")
    if op == "MS-04" and data.get("dependency_edge") is not None:
        edge = data["dependency_edge"]
        if edge["upstream_id"] == edge["downstream_id"]: issues.append("Self dependency")
    if op == "MS-07" and data.get("topology_refresh_declaration") is not None:
        if data["topology_refresh_declaration"]["refresh_before_next_selection"] is not True:
            issues.append("Topology refresh cannot follow the next selection")
    if op == "MS-09" and data.get("output_path_binding") is not None:
        if data["output_path_binding"]["writes_performed"] is not False:
            issues.append("Path binding must not write")
    return issues


def validate(result, manifest, specs=None):
    issues = []
    schema = load(PACKAGE / "references/atomic-reasoning-output.schema.json")
    issues.extend(error.message for error in jsonschema.Draft202012Validator(schema).iter_errors(result))
    if issues:
        return issues
    spec = (specs if specs is not None else specifications()).get(result["catalog_id"])
    if spec is None:
        return ["No atomic reasoning implementation for catalog ID"]
    sources = manifest.get("sources") if isinstance(manifest, dict) else None
    if not isinstance(sources, list) or not sources:
        return ["Source manifest must contain sources"]
    source_ids = set()
    for source in sources:
        if (not isinstance(source, dict) or not isinstance(source.get("id"), str) or not source["id"].strip()
                or not isinstance(source.get("kind"), str) or source["kind"] not in KINDS or not locator_valid(source.get("locator"))):
            issues.append("Invalid source manifest entry")
            continue
        if source["id"] in source_ids: issues.append("Duplicate source ID")
        source_ids.add(source["id"])
    data = result["data"]
    fields = {field["name"]: field for field in spec["result_fields"]}
    if set(data) != set(fields):
        issues.append("Data keys must equal operation-specific result fields")
    for key, value in data.items():
        if key not in fields: continue
        if value is None: continue
        kind = fields[key]["type"]
        if kind == "number":
            correct = number(value)
        else:
            correct = isinstance(value, TYPES[kind])
        if not correct: issues.append("Incorrect data type: " + key)
        if isinstance(value, str) and not value.strip(): issues.append("Blank result: " + key)
    owners = {}
    for item in result["provenance"]:
        for field in item["fields"]:
            if field not in data: issues.append("Unknown provenance field: " + field)
            if field in owners: issues.append("Duplicate provenance owner: " + field)
            owners[field] = item["kind"]
        if set(item["source_refs"]) - source_ids: issues.append("Unknown source reference")
        if item["kind"] in {"observed", "user", "derived"} and not item["source_refs"]:
            issues.append("Evidence-bearing provenance requires source references")
    if set(owners) != set(data): issues.append("Every data field needs provenance")
    unresolved = {item["field"] for item in result["unresolved"]}
    inapplicable = {item["field"] for item in result.get("not_applicable", [])}
    permitted_inapplicable = {"GU-03": {"view_direction"}, "GU-07": {"depth", "depth_unit"}, "GU-17": {"angle"}}.get(result["catalog_id"], set())
    if inapplicable - permitted_inapplicable:
        issues.append("This operation does not allow omitting that field as inapplicable")
    if inapplicable - set(data) or inapplicable & unresolved:
        issues.append("Invalid or conflicting inapplicable field")
    if any(data.get(key) is not None for key in inapplicable):
        issues.append("Inapplicable fields must be null")
    if unresolved - set(data): issues.append("Unresolved item refers to absent result field")
    for key, value in data.items():
        if (value is None or owners.get(key) == "unknown") and key not in unresolved and key not in inapplicable:
            issues.append("Unknown value lacks unresolved record: " + key)
    blocked = any(item["blocking"] for item in result["unresolved"]) or any((v is None or owners.get(k) == "unknown") and k not in inapplicable for k, v in data.items())
    if result["status"] == "resolved" and blocked:
        issues.append("Blocked or unsupported data cannot be resolved")
    if result["status"] == "requires_clarification" and not result["unresolved"]:
        issues.append("Clarification result requires an actionable unresolved item")
    if not issues and result["catalog_id"].startswith("MS-"):
        try:
            issues.extend(strategy_checks(result["catalog_id"], data))
        except (ValueError, KeyError, TypeError):
            issues.append("Malformed strategy declaration")
    if not issues and all(value is not None for value in data.values()):
        try:
            issues.extend(numeric_checks(result["catalog_id"], data))
        except (TypeError, ValueError, KeyError, ZeroDivisionError, OverflowError, SyntaxError, RecursionError) as exc:
            issues.append("Numeric invariant failed: " + str(exc))
    return issues


def handoff_blockers(results, required_instance_ids=None):
    """Case-level propagation only: a valid finding of conflict still blocks a build."""
    blockers, ids, edges = [], set(), {}
    required = set(required_instance_ids) if required_instance_ids is not None else {item["instance_id"] for item in results}
    for item in results:
        ident, op, data = item["instance_id"], item["catalog_id"], item["data"]
        if ident in ids: blockers.append("Duplicate operation instance: " + ident)
        ids.add(ident)
        if ident not in required: continue
        if item["status"] != "resolved": blockers.append(ident + ": unresolved required action")
        if op == "GU-14" and data.get("verdict") in {"conflict", "underdetermined"}:
            blockers.append(ident + ": dimension relation not accepted")
        if op == "GU-18" and data.get("blocks_decision") is True:
            blockers.append(ident + ": unresolved issue blocks geometry")
        if op == "MS-02" and isinstance(data.get("constraint_result"), dict) and data["constraint_result"].get("verdict") in ("fail", "failed"):
            blockers.append(ident + ": parameter constraint failed")
        if op == "MS-04" and isinstance(data.get("dependency_edge"), dict):
            edge = data["dependency_edge"]
            edges.setdefault(edge["upstream_id"], set()).add(edge["downstream_id"])
    for absent in sorted(required - ids): blockers.append("Missing required action: " + absent)
    # Supplied planning instances may refer to future geometry actions; cycles
    # are checked among declared edges without requiring execution results here.
    visiting, visited = set(), set()
    def visit(node):
        if node in visiting: return True
        if node in visited: return False
        visiting.add(node)
        if any(visit(child) for child in edges.get(node, ())): return True
        visiting.remove(node)
        visited.add(node)
        return False
    if any(visit(node) for node in edges): blockers.append("Cyclic operation dependency")
    return blockers


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("result", type=Path, nargs="?")
    parser.add_argument("--sources", type=Path)
    parser.add_argument("--describe", help="Print just one selected GU/MS action specification")
    args = parser.parse_args(argv)
    try:
        if args.describe:
            print(json.dumps(specifications()[args.describe], ensure_ascii=False, indent=2))
            return 0
        if args.result is None or args.sources is None:
            parser.error("Supply result and --sources, or --describe CATALOG-ID")
        issues = validate(load(args.result), load(args.sources))
    except (OSError, ValueError, KeyError, TypeError) as exc:
        issues = [str(exc)]
    print(json.dumps({"status": "failed" if issues else "passed", "evidence_boundary": "host_invariants_only", "issues": issues}, ensure_ascii=False, indent=2))
    return int(bool(issues))


if __name__ == "__main__":
    raise SystemExit(main())
