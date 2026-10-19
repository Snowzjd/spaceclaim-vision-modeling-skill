def operation(p):
    # Native root-part face revolve.  This variant intentionally accepts a
    # planar sheet face rather than inventing a profile-construction step.
    section_policy = p.get("section_policy", "kernel-managed")
    if section_policy not in ("kernel-managed", "preserve", "consume"):
        raise ValueError("Unsupported section policy")

    angle_degrees = finite(p["angle_degrees"], "angle_degrees")
    if abs(angle_degrees) <= 1e-12 or abs(angle_degrees) > 360.0:
        raise ValueError("angle_degrees must be nonzero and within +/-360 degrees")
    axis = Line.Create(
        point_mm(p["axis_origin_mm"]),
        direction(p["axis_direction"]),
    )

    profile_face = p["profile_face"]
    before = current_bodies()
    profile_owners = [body for body in before if profile_face in list(body.Faces)]
    source = one(profile_owners, "profile sheet owner")
    if len(list(source.Faces)) != 1 or source.Shape.IsClosed:
        raise ValueError("Profile face must be the only face of an open sheet body")
    if profile_face.Shape.Geometry.GetType().Name != "Plane":
        raise ValueError("Profile face must be planar")

    options = RevolveFaceOptions()
    options.ExtrudeType = ExtrudeType.ForceIndependent
    options.PullSymmetric = False
    result = RevolveFaces.Execute(
        FaceSelection.Create(profile_face),
        axis,
        angle_degrees * math.pi / 180.0,
        options,
        None,
    )
    result_ok(result, "face revolve")

    after = current_bodies()
    source_count_before = len(profile_owners)
    source_count_after = len([body for body in after if profile_face in list(body.Faces)])
    if section_policy == "preserve" and source_count_after != source_count_before:
        raise RuntimeError("Revolve did not preserve the profile section")
    if section_policy == "consume" and source_count_after != 0:
        raise RuntimeError("Revolve did not consume the profile section")

    # Do not dereference consumed pre-operation sheet bodies.
    created = [body for body in after if body not in before]
    solids = [body for body in created if body.Shape.IsClosed and volume_mm3(body) > 0]
    result_body = one(solids, "new solid revolve")
    return {
        "body": assert_closed(result_body),
        "section_policy": section_policy,
        "source_count_before": source_count_before,
        "source_count_after": source_count_after,
    }
