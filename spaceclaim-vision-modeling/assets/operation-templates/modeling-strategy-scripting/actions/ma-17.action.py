def operation(p):
    # Non-associative, non-merging native body mirror; source is preserved.
    body = require_live_body(p["body"])
    plane_face = p["plane_face"]
    if not any(plane_face in list(b.Faces) for b in current_bodies()):
        raise ValueError("Mirror plane face must be current in this root design")
    if plane_face.Shape.Geometry.GetType().Name != "Plane":
        raise ValueError("This mirror variant requires a planar face")
    if p["source_policy"] != "preserve":
        raise ValueError("This independent mirror variant preserves the source")
    vtol = tolerance(p["volume_tolerance_mm3"])
    btol = tolerance(p["bbox_tolerance_mm"])
    before = current_bodies()
    volume, bounds = volume_mm3(body), bounds_mm(body)
    options = MirrorOptions()
    options.CreateRelationships = False
    options.MergeObjects = False
    result_ok(Mirror.Execute(BodySelection.Create(body), FaceSelection.Create(plane_face), options), "mirror body")
    after = current_bodies()
    mirrored = one([b for b in after if b not in before and b.Shape.IsClosed and volume_mm3(b) > 0], "mirrored body")
    if body not in after or not near(volume_mm3(body), volume, vtol) or not bbox_matches(bounds_mm(body), bounds, btol):
        raise RuntimeError("Mirror changed the preserved source")
    if not near(volume_mm3(mirrored), volume, vtol):
        raise RuntimeError("Mirror volume differs from the source")
    return assert_closed(mirrored)
