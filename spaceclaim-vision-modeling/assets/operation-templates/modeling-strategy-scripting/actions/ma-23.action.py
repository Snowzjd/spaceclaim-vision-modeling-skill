def operation(p):
    body = require_transient(p["body"])
    tolerance(p["volume_tolerance_mm3"])
    before, volume = int(body.PieceCount), volume_mm3(body)
    body.Split(p["plane"], None)
    if int(body.PieceCount) <= before:
        raise RuntimeError("Plane did not split the solid")
    if not near(volume_mm3(body), volume, p["volume_tolerance_mm3"]):
        raise RuntimeError("Split did not conserve volume")
    return {"body": assert_closed(body), "piece_count": int(body.PieceCount)}
