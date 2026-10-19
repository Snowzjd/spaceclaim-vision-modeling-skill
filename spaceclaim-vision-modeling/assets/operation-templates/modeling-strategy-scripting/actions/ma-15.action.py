def operation(p):
    # Point-to-planar-face variant: translates, never rotates or deforms.
    # The caller supplies a reference point on one current face of the body.
    body = require_live_body(p["body"])
    reference, target = p["reference_face"], p["target_face"]
    if reference not in list(body.Faces):
        raise ValueError("Reference face must belong to the current moving body")
    if not any(target in list(candidate.Faces) for candidate in current_bodies() if candidate != body):
        raise ValueError("Target face must belong to a different current root body")
    if target.Shape.Geometry.GetType().Name != "Plane":
        raise ValueError("This variant requires a planar target face")
    tol = tolerance(p["position_tolerance_mm"])
    vtol = tolerance(p["volume_tolerance_mm3"])
    reference_point = point_mm(p["reference_point_mm"])
    projected = reference.Shape.ProjectPoint(reference_point).Point
    if sum((float(getattr(projected, a))-float(getattr(reference_point, a)))**2 for a in ("X", "Y", "Z")) > (tol/1000.0)**2:
        raise ValueError("Reference point does not lie on the supplied trimmed face")
    travel = direction(p["direction"])
    plane = target.Shape.Geometry
    n = plane.Frame.DirZ
    denominator = sum(float(getattr(n, a))*float(getattr(travel, a)) for a in ("X", "Y", "Z"))
    if abs(denominator) < 1e-10:
        raise ValueError("Travel direction is parallel to the target plane")
    distance = sum((float(getattr(plane.Frame.Origin, a))-float(getattr(reference_point, a)))*float(getattr(n, a)) for a in ("X", "Y", "Z"))/denominator
    if distance < -tol/1000.0:
        raise ValueError("Target lies behind the supplied travel direction")
    distance = max(0.0, distance)
    endpoint = Point.Create(*[float(getattr(reference_point, a))+distance*float(getattr(travel, a)) for a in ("X", "Y", "Z")])
    projected = target.Shape.ProjectPoint(endpoint).Point
    if sum((float(getattr(projected, a))-float(getattr(endpoint, a)))**2 for a in ("X", "Y", "Z")) > (tol/1000.0)**2:
        raise ValueError("Reference point would miss the trimmed target face")
    before, volume = bounds_mm(body), volume_mm3(body)
    delta = [distance*float(getattr(travel, a))*1000.0 for a in ("X", "Y", "Z")]
    if distance > 0:
        result_ok(Move.Translate(BodySelection.Create(body), travel, distance, MoveOptions()), "move to planar face")
    expected = [before[i]+delta[i%3] for i in range(6)]
    moved = one([b for b in current_bodies() if bbox_matches(bounds_mm(b), expected, tol) and near(volume_mm3(b), volume, vtol)], "moved body")
    return dict(body=moved, delta_mm=delta, reference_endpoint_mm=[float(getattr(endpoint, a))*1000.0 for a in ("X", "Y", "Z")])
