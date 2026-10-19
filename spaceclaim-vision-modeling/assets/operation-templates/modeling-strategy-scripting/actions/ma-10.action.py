def operation(p):
    # Native solid variant: consumes two supplied planar sheet sections.
    # Section creation is the caller's responsibility, not part of this atom.
    faces = list(p["section_faces"])
    if len(faces) != 2 or len(set(faces)) != 2:
        raise ValueError("This nonperiodic variant requires two distinct section faces")
    if not isinstance(p["ruled"], bool) or p["section_policy"] != "consume":
        raise ValueError("Supply boolean ruled and explicit consume section policy")
    before = current_bodies()
    sections = []
    for face in faces:
        owner = one([b for b in before if face in list(b.Faces)], "current section owner")
        if len(list(owner.Faces)) != 1 or owner.Shape.IsClosed or face.Shape.Geometry.GetType().Name != "Plane":
            raise ValueError("Sections must be individual planar sheet bodies")
        sections.append(owner)
    if len(set(sections)) != 2:
        raise ValueError("Section owners must be distinct")
    options = LoftOptions()
    options.ExtrudeType = ExtrudeType.ForceIndependent
    options.IsRuled = p["ruled"]
    options.PeriodicBlend = False
    result_ok(Loft.Create(FaceSelection.Create(*faces), None, options), "solid loft")
    after = current_bodies()
    body = one([b for b in after if b not in before and b.Shape.IsClosed and volume_mm3(b) > 0], "new solid loft")
    if any(b in after for b in sections):
        raise RuntimeError("Loft section consumption differed from the declared policy")
    if not body.Shape.IsManifold:
        raise RuntimeError("Loft result is nonmanifold")
    return assert_closed(body)
