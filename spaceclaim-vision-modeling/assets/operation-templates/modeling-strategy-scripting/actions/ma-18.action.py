def operation(p):
    # This is a transient, non-associative array.  The source is never
    # transformed; even the zero-offset member is a fresh body copy.
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

    spacing = positive(p["spacing_mm"], "spacing_mm")
    raw_direction = vector3(p["direction"], "direction")
    # Use the shared helper for the API-valid direction check, while retaining
    # normalized scalar components for the translation vector construction.
    direction(p["direction"])
    direction_length = math.sqrt(sum(v*v for v in raw_direction))
    unit_direction = [v / direction_length for v in raw_direction]
    volume_tolerance = tolerance(p["volume_tolerance_mm3"])
    source_volume = volume_mm3(source)

    offsets = []
    for index in range(count):
        offsets.append([spacing * index * unit_direction[axis] for axis in range(3)])

    instances = []
    for index in range(count):
        instance = source.Copy()
        if instance is source or instance == source:
            raise RuntimeError("Body.Copy did not create an independent instance")
        if index:
            offset = offsets[index]
            translation = Vector.Create(
                offset[0] / 1000.0,
                offset[1] / 1000.0,
                offset[2] / 1000.0,
            )
            instance.Transform(Matrix.CreateTranslation(translation))
        instance = require_transient(instance)
        if not near(volume_mm3(instance), source_volume, volume_tolerance):
            raise RuntimeError("Linear array instance changed volume")
        instances.append(assert_closed(instance))

    return {
        "instances": instances,
        "offsets_mm": offsets,
        "source_policy": "preserved",
        "association": "independent",
    }
