ACTION_ID = "VA-13"


def operation(p):
    root = active_root(p)
    body, face = require_face(p, root)
    unit, _, _, _ = unit_spec(p)
    kind = geometry_kind(face)
    if kind != "Cylinder":
        return manual_review(
            ACTION_ID,
            "The supplied face is not a verified V21 Cylinder; radius/axis/span were not inferred.",
            body=body,
            face=face,
            analytic_type=kind,
        )
    try:
        radius = abs(read_scalar(face.Shape.Geometry, "Radius", "cylinder radius")) * (MM_PER_M if unit == "mm" else (1.0 if unit == "m" else 39.37007874015748))
        axis = geometry_axis(face)
        if axis is None:
            return manual_review(ACTION_ID, "V21 Cylinder.Frame.DirZ was not available; cylinder axis is unverified.", body=body, face=face, radius=radius, unit=unit)
        _, length_scale, _, _ = unit_spec(p)
        span, exact = projected_bbox_span(face, axis, length_scale)
    except Exception as exc:
        return manual_review(ACTION_ID, "Cylinder analytic measurement boundary: %s" % exc, body=body, face=face)
    result = passed(
        ACTION_ID,
        body=body,
        face=face,
        analytic_type="Cylinder",
        radius=radius,
        radius_unit=unit,
        axis=axis,
        span=span,
        span_unit=unit,
        span_method="trimmed-face-bounding-box-axis-projection",
        span_exact=exact,
    )
    if not exact:
        result["status"] = "needs_manual_review"
        result["needs_manual_review"] = True
        result["reason"] = "Rotated cylinder span is a bounding-box projection, not a verified trim-boundary span."
    return result
