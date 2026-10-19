def operation(p):
    # Native root-part target-face extrusion.  The source is a current one-face
    # planar sheet; profile construction and semantic face discovery remain
    # caller-owned actions.
    section_policy = p.get("section_policy", "kernel-managed")
    if section_policy not in ("kernel-managed", "preserve", "consume"):
        raise ValueError("Unsupported section policy")

    profile_face = p["profile_face"]
    target_face = p["target_face"]
    travel = direction(p["direction"])
    seed_point = point_mm(p["seed_point_mm"])
    before = current_bodies()

    profile_owners = [body for body in before if profile_face in list(body.Faces)]
    source = one(profile_owners, "profile sheet owner")
    if len(list(source.Faces)) != 1 or source.Shape.IsClosed:
        raise ValueError("Profile face must be the only face of an open sheet body")
    if profile_face.Shape.Geometry.GetType().Name != "Plane":
        raise ValueError("Profile face must be planar")

    target_owners = [body for body in before if target_face in list(body.Faces)]
    one(target_owners, "target face owner")
    if target_face == profile_face:
        raise ValueError("Profile and target faces must be distinct")

    options = ExtrudeFaceOptions()
    options.ExtrudeType = ExtrudeType.ForceIndependent
    result = ExtrudeFaces.UpTo(
        FaceSelection.Create(profile_face),
        travel,
        FaceSelection.Create(target_face),
        seed_point,
        options,
        None,
    )
    result_ok(result, "extrusion to face")

    after = current_bodies()
    source_count_before = len(profile_owners)
    source_count_after = len([body for body in after if profile_face in list(body.Faces)])
    if section_policy == "preserve" and source_count_after != source_count_before:
        raise RuntimeError("Extrusion did not preserve the profile section")
    if section_policy == "consume" and source_count_after != 0:
        raise RuntimeError("Extrusion did not consume the profile section")

    # Do not dereference consumed pre-operation sheet bodies.
    created = [body for body in after if body not in before]
    solids = [body for body in created if body.Shape.IsClosed and volume_mm3(body) > 0]
    result_body = one(solids, "new solid extrusion")
    return {
        "body": assert_closed(result_body),
        "section_policy": section_policy,
        "source_count_before": source_count_before,
        "source_count_after": source_count_after,
    }
