ACTION_ID = "VA-10"


def operation(p):
    root = active_root(p)
    body = require_body(p, root)
    unit, _, area_scale, _ = unit_spec(p)
    try:
        value = abs(read_scalar(body.Shape, "SurfaceArea", "body surface area")) * area_scale
    except Exception:
        raise ValueError("Body surface area is unavailable")
    if value <= 0.0:
        raise ValueError("Body surface area must be positive")
    expected = optional(p, None, "expected_area", "expected_surface_area")
    matches = None
    tolerance_value = optional(p, None, "tolerance", "area_tolerance")
    if tolerance_value is not None:
        tolerance_value = nonnegative(tolerance_value, "tolerance")
    if expected is not None:
        expected = finite(expected, "expected_area")
        if tolerance_value is None:
            tolerance_value = 0.0
        matches = abs(value - expected) <= tolerance_value
    result = passed(ACTION_ID, body=body, unit=unit, surface_area=value, area=value)
    if matches is not None:
        result.update({"expected_area": expected, "tolerance": tolerance_value, "matches": matches})
        result["status"] = "passed" if matches else "failed"
    return result
