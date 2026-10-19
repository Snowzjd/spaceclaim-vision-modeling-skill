ACTION_ID = "VA-14"


def operation(p):
    root = active_root(p)
    body, face = require_face(p, root)
    unit, length_scale, _, _ = unit_spec(p)
    mode = optional(p, None, "angle_mode", "angle_definition", "angle_kind")
    if mode is None:
        return manual_review(ACTION_ID, "Cone angle must explicitly declare half-angle or full-angle semantics.", body=body, face=face)
    if not isinstance(mode, _STRING_TYPES):
        raise ValueError("angle_mode must be a string")
    mode = mode.strip().lower()
    if mode not in ("half", "half_angle", "full", "full_angle"):
        raise ValueError("angle_mode must be half or full")
    kind = geometry_kind(face)
    if kind != "Cone":
        return manual_review(ACTION_ID, "The supplied face is not a verified V21 Cone; cone angle/span were not inferred.", body=body, face=face, analytic_type=kind)
    try:
        half_angle = abs(degrees(read_scalar(face.Shape.Geometry, "HalfAngle", "cone half-angle"), "cone half-angle"))
        angle = half_angle if mode in ("half", "half_angle") else 2.0 * half_angle
        axis = geometry_axis(face)
        if axis is None:
            return manual_review(ACTION_ID, "V21 Cone.Frame.DirZ was not available; cone axis/span is unverified.", body=body, face=face, angle=angle, angle_mode=mode, unit=unit)
        span, exact = projected_bbox_span(face, axis, length_scale)
    except Exception as exc:
        return manual_review(ACTION_ID, "Cone analytic measurement boundary: %s" % exc, body=body, face=face)
    result = passed(
        ACTION_ID,
        body=body,
        face=face,
        analytic_type="Cone",
        angle=angle,
        angle_unit="deg",
        angle_mode="half" if mode in ("half", "half_angle") else "full",
        axis=axis,
        span=span,
        span_unit=unit,
        span_method="trimmed-face-bounding-box-axis-projection",
        span_exact=exact,
    )
    if not exact:
        result["status"] = "needs_manual_review"
        result["needs_manual_review"] = True
        result["reason"] = "Rotated cone span is a bounding-box projection, not a verified trim-boundary span."
    return result
