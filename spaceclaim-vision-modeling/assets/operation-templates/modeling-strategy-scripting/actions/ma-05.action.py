def operation(p):
    lo, hi = vector3(p["min_mm"], "min_mm"), vector3(p["max_mm"], "max_mm")
    if any(hi[i] <= lo[i] for i in range(3)):
        raise ValueError("Block extents must be positive")
    tolerance(p["bbox_tolerance_mm"])
    before = current_bodies()
    result = BlockBody.Create(point_mm(lo), point_mm(hi), ExtrudeType.ForceIndependent)
    result_ok(result, "block creation")
    created = one([b for b in current_bodies() if b not in before], "created block")
    if not bbox_matches(bounds_mm(created), lo+hi, p["bbox_tolerance_mm"]):
        raise RuntimeError("Created block bounds mismatch")
    return assert_closed(created)
