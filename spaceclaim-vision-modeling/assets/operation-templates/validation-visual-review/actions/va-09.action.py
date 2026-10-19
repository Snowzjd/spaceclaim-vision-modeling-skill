ACTION_ID = "VA-09"


def operation(p):
    root = active_root(p)
    body = require_body(p, root)
    unit, _, _, volume_scale = unit_spec(p)
    try:
        value = abs(read_scalar(body.Shape, "Volume", "body volume")) * volume_scale
    except Exception:
        raise ValueError("Body volume is unavailable")
    if value <= 0.0:
        raise ValueError("Body volume must be positive")
    expected = optional(p, None, "expected_volume", "expected_volume_mm3")
    matches = None
    tolerance_value = optional(p, None, "tolerance", "volume_tolerance")
    if tolerance_value is not None:
        tolerance_value = nonnegative(tolerance_value, "tolerance")
    if expected is not None:
        expected = finite(expected, "expected_volume")
        if tolerance_value is None:
            tolerance_value = 0.0
        matches = abs(value - expected) <= tolerance_value
    result = passed(ACTION_ID, body=body, unit=unit, volume=value)
    if matches is not None:
        result.update({"expected_volume": expected, "tolerance": tolerance_value, "matches": matches})
        result["status"] = "passed" if matches else "failed"
    return result
