def operation(p):
    distance = finite(p["distance_mm"], "distance")
    if abs(distance) <= 1e-9:
        raise ValueError("Extrusion distance must be nonzero")
    # Profile creation and design-tree attachment are separate caller-owned actions.
    return assert_closed(ModelerBody.ExtrudeProfile(p["profile"], distance/1000.0))
