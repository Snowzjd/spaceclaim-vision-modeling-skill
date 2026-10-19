ACTION_ID = "VA-18"


def _va18_current_window_groups():
    """Return groups exposed by the active window.

    ``WindowHelper.GetGroups()`` is the V21 scripting boundary for named
    selections in the active window.  A NamedSelection created in a root part
    may report a generic ``DocObject`` as ``Parent``; comparing that wrapper to
    ``GetRootPart()`` would reject a valid group.
    """
    try:
        return list(WindowHelper.GetGroups())
    except Exception:
        raise ValueError("Named-group enumeration is unsupported")


def _va18_require_group(mapping):
    group = required(mapping, "group", "named_group", "selection")
    if not contains_object(_va18_current_window_groups(), group):
        raise ValueError("Named group is not in the current active window")
    return group


def _va18_member_in_root(member, body_list):
    """Accept only a freshly enumerated current root body/topology object.

    The group handle is scoped by the active window, while its members still
    need an independent root check.  Do not use a parent-chain fallback: a
    stale face can retain a live body's parent after a topology change.
    """
    if member is None:
        return False
    if contains_object(body_list, member):
        return True
    for body in body_list:
        for attribute in ("Faces", "Edges"):
            try:
                if contains_object(list(getattr(body, attribute)), member):
                    return True
            except Exception:
                pass
    return False


def operation(p):
    root = active_root(p)
    group = _va18_require_group(p)
    expected = required(p, "expected_members", "members")
    if not isinstance(expected, (list, tuple)):
        raise ValueError("expected_members must be a collection")
    actual = group_members(group)
    # Check supplied members are current root-scoped objects before comparing;
    # a same-sized stale list must not pass merely because its count matches.
    body_list = root_bodies(root)
    for member in actual:
        if not _va18_member_in_root(member, body_list):
            raise ValueError("Named-group member is stale or outside the current root")
    for member in expected:
        if not _va18_member_in_root(member, body_list):
            raise ValueError("Expected named-group member is stale or outside the current root")
    matches = compare_identity_sets(actual, expected)
    result = passed(
        ACTION_ID,
        group=group,
        members=actual,
        actual_count=len(actual),
        expected_members=list(expected),
        expected_count=len(expected),
        matches=matches,
    )
    result["status"] = "passed" if matches else "failed"
    return result
