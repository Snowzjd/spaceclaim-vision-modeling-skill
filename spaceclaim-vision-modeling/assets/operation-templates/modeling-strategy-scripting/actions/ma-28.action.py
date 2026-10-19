def operation(p):
    criteria = p["criteria"]
    if any(k not in ("name", "bbox_mm", "volume_mm3") for k in criteria):
        raise ValueError("Unsupported body criterion; do not silently weaken selection")
    if not any(k in criteria for k in ("bbox_mm", "volume_mm3")):
        raise ValueError("Body selection needs a geometric criterion, not name alone")
    matches = []
    for body in current_bodies():
        if "name" in criteria and body.Name != criteria["name"]:
            continue
        if "bbox_mm" in criteria and not bbox_matches(bounds_mm(body), criteria["bbox_mm"], p["bbox_tolerance_mm"]):
            continue
        if "volume_mm3" in criteria and not near(volume_mm3(body), criteria["volume_mm3"], p["volume_tolerance_mm3"]):
            continue
        matches.append(body)
    return one(matches, "semantic body")
