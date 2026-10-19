def operation(p):
    # This is a transient, non-associative array.  The source is never
    # transformed; even the zero-angle member is a fresh body copy.
    source = require_transient(p["body"])
    count_value = p["count"]
    if isinstance(count_value, bool):
        raise ValueError("count must be a finite integer >= 2, not boolean")
    count_number = finite(count_value, "count")
    if count_number != int(count_number):
        raise ValueError("count must be an integer >= 2")
    count = int(count_number)
    if count < 2:
        raise ValueError("count must be at least 2")

    step_angle = finite(p["step_angle_degrees"], "step_angle_degrees")
    axis_origin = point_mm(p["axis_origin_mm"])
    axis_direction = direction(p["axis_direction"])
    axis = Line.Create(axis_origin, axis_direction)
    volume_tolerance = tolerance(p["volume_tolerance_mm3"])
    source_volume = volume_mm3(source)

    # Compare angular positions modulo one full turn before creating any
    # copies.  This catches duplicates at 360 degrees and after any number of
    # wrapped turns, including negative steps.
    angles = []
    normalized_angles = []
    for index in range(count):
        angle = step_angle * index
        normalized = math.fmod(angle, 360.0)
        if normalized < 0:
            normalized += 360.0
        for previous in normalized_angles:
            separation = abs(normalized - previous)
            if separation <= 1e-10 or abs(separation - 360.0) <= 1e-10:
                raise ValueError("Circular array contains periodic duplicate angles")
        angles.append(angle)
        normalized_angles.append(normalized)

    instances = []
    for index in range(count):
        instance = source.Copy()
        if instance is source or instance == source:
            raise RuntimeError("Body.Copy did not create an independent instance")
        if index:
            instance.Transform(Matrix.CreateRotation(axis, angles[index] * math.pi / 180.0))
        instance = require_transient(instance)
        if not near(volume_mm3(instance), source_volume, volume_tolerance):
            raise RuntimeError("Circular array instance changed volume")
        instances.append(assert_closed(instance))

    return {
        "instances": instances,
        "angles_degrees": angles,
        "source_policy": "preserved",
        "association": "independent",
    }
