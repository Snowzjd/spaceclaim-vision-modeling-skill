def operation(p):
    body = require_live_body(p["body"])
    delta = vector3(p["delta_mm"], "delta_mm")
    tolerance(p["bbox_tolerance_mm"])
    tolerance(p["volume_tolerance_mm3"])
    distance = math.sqrt(sum(v*v for v in delta))
    before, volume = bounds_mm(body), volume_mm3(body)
    if distance <= 1e-12:
        return body
    result = Move.Translate(BodySelection.Create(body), direction(delta), distance/1000.0, MoveOptions())
    result_ok(result, "translation")
    expected = [before[i]+delta[i%3] for i in range(6)]
    moved = one([candidate for candidate in current_bodies() if bbox_matches(bounds_mm(candidate), expected, p["bbox_tolerance_mm"]) and near(volume_mm3(candidate),volume,p["volume_tolerance_mm3"])], "translated semantic body")
    return moved
