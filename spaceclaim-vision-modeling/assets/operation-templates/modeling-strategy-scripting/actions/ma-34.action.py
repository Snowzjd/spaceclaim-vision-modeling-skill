def operation(p):
    group, name = p["group"], require_name(p["name"])
    groups = list(WindowHelper.GetGroups())
    if group not in groups or any(g != group and g.Name == name for g in groups):
        raise ValueError("Group is stale or target name collides")
    members = set(group.Members)
    result_ok(NamedSelection.Rename(group.Name, name), "group rename")
    renamed = one([g for g in list(WindowHelper.GetGroups()) if g.Name == name], "renamed group")
    if set(renamed.Members) != members:
        raise RuntimeError("Rename changed group membership")
    return renamed
