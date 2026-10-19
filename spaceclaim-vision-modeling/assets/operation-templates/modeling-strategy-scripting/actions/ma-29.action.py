def operation(p):
    body = require_live_body(p["body"])
    criteria = p["criteria"]
    if not criteria or any(k not in ("bbox_mm", "normal", "area_mm2") for k in criteria):
        raise ValueError("Unsupported or empty face criteria")
    matches = []
    for face in list(body.Faces):
        if "bbox_mm" in criteria and not bbox_matches(bounds_mm(face), criteria["bbox_mm"], p["bbox_tolerance_mm"]):
            continue
        if "area_mm2" in criteria and not near(float(face.Shape.Area)*1e6, criteria["area_mm2"], p["area_tolerance_mm2"]):
            continue
        if "normal" in criteria:
            if face.Shape.Geometry.GetType().Name != "Plane":
                continue
            expected = direction(criteria["normal"])
            normal = face_normal(face)
            if any(not near(a,b,p["normal_tolerance"]) for a,b in zip(normal,(expected.X,expected.Y,expected.Z))):
                continue
        matches.append(face)
    return one(matches, "semantic face")
