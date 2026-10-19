def operation(p):
    # Transient variant. Positive +Z rotation maps +X toward +Y (right hand).
    body = require_transient(p["body"])
    tolerance(p["volume_tolerance_mm3"])
    axis = Line.Create(point_mm(p["axis_origin_mm"]), direction(p["axis_direction"]))
    angle = finite(p["angle_degrees"], "angle") * math.pi/180.0
    volume = volume_mm3(body)
    body.Transform(Matrix.CreateRotation(axis, angle))
    if not near(volume_mm3(body), volume, p["volume_tolerance_mm3"]):
        raise RuntimeError("Rotation changed volume")
    return assert_closed(body)
