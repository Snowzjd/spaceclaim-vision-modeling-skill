def operation(p):
    body = require_live_body(p["body"])
    criteria = p["criteria"]
    if "bbox_mm" not in criteria or any(k not in ("bbox_mm", "curve_type") for k in criteria):
        raise ValueError("This edge variant requires bounds; optional curve_type")
    matches = []
    for edge in list(body.Edges):
        if not bbox_matches(bounds_mm(edge), criteria["bbox_mm"], p["bbox_tolerance_mm"]):
            continue
        if "curve_type" in criteria and edge.Shape.Geometry.GetType().Name != criteria["curve_type"]:
            continue
        matches.append(edge)
    return one(matches, "semantic edge")
