def operation(p):
    # Already enclosed region, seeded on a current face. No caps or repairs.
    source = require_live_body(p["source_body"])
    face = p["seed_face"]
    if face not in list(source.Faces):
        raise ValueError("Seed face must belong to the current source body")
    point = point_mm(p["seed_point_mm"])
    tol = tolerance(p["position_tolerance_mm"])
    seed = face.Shape.ProjectPoint(point)
    if sum((float(getattr(seed.Point, a))-float(getattr(point, a)))**2 for a in ("X", "Y", "Z")) > (tol/1000.0)**2:
        raise ValueError("Seed point must lie on the supplied trimmed face")
    # V21 places the extracted volume under a new component.  The shared
    # current_bodies() helper is intentionally root-body-only. Locate the
    # newly created component and inspect its Content without changing it.
    root = GetRootPart()
    before_components = list(root.GetDescendants[Component]())
    options = VolumeExtractOptions()
    options.CreateShareTopology = False
    options.ImprintCappingEdges = False
    options.MergeCreatedVolume = False
    options.SeedPoint = seed
    result_ok(VolumeExtract.Create(Selection.Empty(), FaceSelection.Create(face), options), "enclosed volume extraction")
    after_bodies = list(root.GetDescendants[DesignBody]())
    after_components = list(root.GetDescendants[Component]())
    created_components = [component for component in after_components if component not in before_components]
    component = one(created_components, "new volume extraction component")
    if source not in after_bodies:
        raise RuntimeError("Volume extraction did not preserve the source body")
    content = component.Content
    if content is None:
        raise RuntimeError("New volume extraction component has no content part")
    component_bodies = list(content.Bodies)
    # Content is PartGeneral; its occurrences are DesignBodyGeneral, not
    # concrete DesignBody. Use IPart.Bodies inside the identified component.
    body = one(component_bodies, "extracted region in new component")
    if list(content.Components):
        raise RuntimeError("Nested extraction components are outside this variant")
    # Occurrence Shape is TrimmedSpace; kernel topology is on its master.
    assert_closed(body.Master)
    return body
