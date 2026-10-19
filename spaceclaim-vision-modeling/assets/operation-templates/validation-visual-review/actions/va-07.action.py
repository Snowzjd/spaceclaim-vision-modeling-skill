ACTION_ID = "VA-07"


def operation(p):
    root = active_root(p)
    raw = required(p, "objects", "items", "collection")
    try:
        objects = list(raw)
    except Exception:
        raise ValueError("objects must be a finite collection")
    expected = finite(required(p, "expected_count"), "expected_count")
    if expected != int(expected) or expected < 0:
        raise ValueError("expected_count must be a non-negative integer")
    kind = optional(p, None, "object_kind", "kind")
    if kind is not None and kind not in ("body", "face", "edge", "group"):
        raise ValueError("Unsupported object_kind")

    body = optional(p, None, "body", "current_body")
    if kind in ("face", "edge"):
        if body is None:
            raise ValueError("body is required when counting faces or edges")
        body_mapping = dict(p)
        body_mapping["body"] = body
        require_body(body_mapping, root)

    for left_index in range(len(objects)):
        for right_index in range(left_index):
            if same_object(objects[left_index], objects[right_index]):
                raise ValueError("objects must not contain duplicate identities")

    current_bodies = root_bodies(root)
    inferred_kinds = []
    if kind == "body":
        valid = all(contains_object(current_bodies, item) for item in objects)
    elif kind == "face":
        valid = all(contains_object(list(body.Faces), item) for item in objects)
    elif kind == "edge":
        valid = all(contains_object(list(body.Edges), item) for item in objects)
    elif kind == "group":
        valid = all(contains_object(groups_for_root(root), item) for item in objects)
    else:
        # Infer only when every member has exactly one current root scope.  A
        # missing or mixed scope is rejected rather than counted blindly.
        valid = True
        for item in objects:
            matches = []
            if contains_object(current_bodies, item):
                matches.append("body")
            for candidate in current_bodies:
                if contains_object(list(candidate.Faces), item):
                    matches.append("face")
                if contains_object(list(candidate.Edges), item):
                    matches.append("edge")
            if len(matches) != 1:
                valid = False
                break
            inferred_kinds.append(matches[0])
        if valid and inferred_kinds and len(set(inferred_kinds)) != 1:
            raise ValueError("objects must contain one object type only")
    if not valid:
        raise ValueError("objects include an unsupported, stale, or out-of-scope object")
    matches = len(objects) == int(expected)
    result = passed(
        ACTION_ID,
        object_kind=kind or (inferred_kinds[0] if inferred_kinds else "inferred"),
        objects=objects,
        count=len(objects),
        expected_count=int(expected),
        matches=matches,
    )
    result["status"] = "passed" if matches else "failed"
    return result
