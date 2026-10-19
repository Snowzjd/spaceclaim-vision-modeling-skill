ACTION_ID = "VA-08"


def operation(p):
    root = active_root(p)
    body = require_body(p, root)
    frame, frame_name = frame_spec(p)
    unit, length_scale, _, _ = unit_spec(p)
    bbox = shape_bbox_in_units(body, frame, length_scale)
    tolerance_value = optional(p, None, "tolerance", "bbox_tolerance")
    if tolerance_value is not None:
        tolerance_value = nonnegative(tolerance_value, "tolerance")
    expected = optional(p, None, "expected_bbox", "expected_bbox_mm")
    matches = None
    if expected is not None:
        if not isinstance(expected, (list, tuple)) or len(expected) != 6:
            raise ValueError("expected_bbox requires six coordinates")
        expected_values = vector3(expected[:3], "expected_bbox minimum") + vector3(expected[3:], "expected_bbox maximum")
        if tolerance_value is None:
            tolerance_value = 0.0
        matches = all(abs(bbox[index] - expected_values[index]) <= tolerance_value for index in range(6))
    result = passed(
        ACTION_ID,
        body=body,
        frame=frame_name,
        unit=unit,
        bbox=bbox,
        bbox_min=bbox[:3],
        bbox_max=bbox[3:],
    )
    if matches is not None:
        result.update({"expected_bbox": expected_values, "tolerance": tolerance_value, "matches": matches})
        result["status"] = "passed" if matches else "failed"
    return result
