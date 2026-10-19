ACTION_ID = "VA-15"


def operation(p):
    root = active_root(p)
    body, face = require_face(p, root)
    unit, _, _, _ = unit_spec(p)
    kind = geometry_kind(face)
    if kind != "Torus":
        return manual_review(ACTION_ID, "The supplied face is not a verified V21 Torus; minor radius was not inferred.", body=body, face=face, analytic_type=kind)
    try:
        scale = MM_PER_M if unit == "mm" else (1.0 if unit == "m" else 39.37007874015748)
        minor_radius = abs(read_scalar(face.Shape.Geometry, "MinorRadius", "torus minor radius")) * scale
    except Exception:
        return manual_review(ACTION_ID, "V21 Torus.MinorRadius was not available; toroidal radius is unverified.", body=body, face=face)
    relation = optional(p, None, "fillet_relation", "association", "round_relation")
    result = passed(
        ACTION_ID,
        body=body,
        face=face,
        analytic_type="Torus",
        minor_radius=minor_radius,
        radius_unit=unit,
        association_status="not_verified",
    )
    if relation is None:
        result["status"] = "needs_manual_review"
        result["needs_manual_review"] = True
        result["reason"] = "Torus-to-fillet association is not exposed by the one-face analytic API."
        return result
    if not isinstance(relation, _STRING_TYPES) or relation.strip().lower() not in (
        "minor_radius", "analytic_minor_radius", "toroidal_fillet", "verified"
    ):
        result["status"] = "needs_manual_review"
        result["needs_manual_review"] = True
        result["reason"] = "The supplied fillet association is not a verified V21 relation."
        return result
    result["association_status"] = "declared"
    return result
