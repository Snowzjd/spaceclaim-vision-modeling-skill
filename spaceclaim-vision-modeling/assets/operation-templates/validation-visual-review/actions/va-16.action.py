ACTION_ID = "VA-16"

# Circular interface (all coordinates and tolerances are millimetres):
#
#   {
#       "positions_mm": [[x, y, z], ...],
#       "tolerance_mm": 0.01,
#       "expected_rule": {
#           "mode": "circular",
#           "center_mm": [x, y, z],
#           "axis": [x, y, z],
#           "pitch_radius_mm": 10.0,
#           "angle_step_deg": 90.0,
#           "count": 4,
#       },
#   }
#
# ``angle_step_deg`` is the expected angular step, but angular discrepancies
# are converted to chord-length millimetres before comparison with the one
# ``tolerance_mm`` value.  The output retains both angular and distance errors
# so a JSON report never mixes degree and millimetre quantities.


def _cross(left, right):
    return [
        left[1] * right[2] - left[2] * right[1],
        left[2] * right[0] - left[0] * right[2],
        left[0] * right[1] - left[1] * right[0],
    ]


def operation(p):
    root = active_root(p)
    raw = required(p, "feature_positions_mm", "positions_mm", "positions")
    if not isinstance(raw, (list, tuple)) or len(raw) < 2:
        return manual_review(ACTION_ID, "At least two ordered feature positions are required for a repeated-placement check.")
    positions = [vector3(value, "feature position") for value in raw]
    tolerance_value = nonnegative(required(p, "tolerance_mm", "tolerance"), "tolerance_mm")
    rule = required(p, "expected_rule", "rule")
    if not isinstance(rule, dict):
        raise ValueError("expected_rule must be a dictionary")
    mode = optional(rule, None, "mode", "kind", "type")
    if not isinstance(mode, _STRING_TYPES):
        return manual_review(ACTION_ID, "Repeated-placement rule mode is missing or ambiguous.")
    mode = mode.strip().lower()
    expected_count = optional(rule, None, "count", "expected_count")
    if expected_count is not None:
        expected_count = finite(expected_count, "expected repeated count")
        if expected_count != int(expected_count) or expected_count < 2:
            raise ValueError("expected repeated count must be an integer >= 2")
    errors = []
    angular_errors_deg = []
    angular_errors_mm = []
    normalized_rule = {"mode": mode}
    count_matches = True
    if mode in ("linear", "translation"):
        step = optional(rule, None, "step_mm", "delta_mm", "spacing_vector_mm")
        if step is None:
            return manual_review(ACTION_ID, "Linear repeat requires an explicit three-dimensional step vector.")
        step = vector3(step, "repeat step")
        normalized_rule["step_mm"] = step
        for index in range(1, len(positions)):
            delta = subtract(positions[index], positions[index - 1])
            errors.append(norm(subtract(delta, step), "linear placement error"))
    elif mode in ("circular", "polar"):
        center = vector3(required(rule, "center_mm", "center"), "repeat center")
        axis = normalize(required(rule, "axis", "axis_direction"), "repeat axis")
        radius = positive(required(rule, "pitch_radius_mm", "radius_mm", "radius"), "pitch radius")
        angle_step = finite(required(rule, "angle_step_deg", "angular_step_deg"), "angle step")
        if abs(angle_step) <= 1.0e-12:
            raise ValueError("angle step must be nonzero")
        normalized_rule.update(
            center_mm=center,
            axis=axis,
            pitch_radius_mm=radius,
            angle_step_deg=angle_step,
        )
        first_radial = subtract(positions[0], center)
        first_axial = dot(first_radial, axis)
        first_radial = [first_radial[i] - first_axial * axis[i] for i in range(3)]
        first_length = norm(first_radial, "first radial vector")
        if first_length <= 1.0e-12:
            return manual_review(ACTION_ID, "First repeated feature lies on the repeat axis; angular placement is ambiguous.")
        for index, position in enumerate(positions):
            relative = subtract(position, center)
            axial = dot(relative, axis)
            radial = [relative[i] - axial * axis[i] for i in range(3)]
            radial_length = norm(radial, "radial placement")
            radial_error = abs(radial_length - radius)
            axial_error = abs(axial)
            cross = _cross(first_radial, radial)
            actual_angle = math.atan2(dot(axis, cross), dot(first_radial, radial)) * 180.0 / PI
            angular_error_deg = abs(angle_wrap_degrees(actual_angle - index * angle_step))
            # Convert the angular discrepancy to a chord-length error before
            # combining it with radial/axial millimetre errors.  A single
            # tolerance must never compare unlike units.
            angular_error_mm = 2.0 * radius * math.sin(angular_error_deg * PI / 360.0)
            angular_errors_deg.append(angular_error_deg)
            angular_errors_mm.append(angular_error_mm)
            errors.append(max(radial_error, axial_error, angular_error_mm))
    else:
        return manual_review(ACTION_ID, "Unsupported repeated-placement rule; use linear or circular.", mode=mode)
    if expected_count is not None:
        normalized_rule["count"] = int(expected_count)
        if len(positions) != int(expected_count):
            count_matches = False
    if not errors:
        return manual_review(ACTION_ID, "Repeated-placement rule produced no independent comparisons.")
    max_error = max(errors)
    matches = count_matches and max_error <= tolerance_value
    result = passed(
        ACTION_ID,
        root_scope="current_root",
        positions_mm=positions,
        rule=normalized_rule,
        errors=errors,
        angular_errors_deg=angular_errors_deg,
        angular_errors_mm=angular_errors_mm,
        max_error=max_error,
        tolerance=tolerance_value,
        tolerance_mm=tolerance_value,
        count_matches=count_matches,
        matches=matches,
    )
    result["status"] = "passed" if matches else "failed"
    return result
