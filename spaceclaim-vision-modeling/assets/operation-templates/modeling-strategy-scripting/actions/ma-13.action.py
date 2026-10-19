def operation(p):
    # Geometry-copy variant; attachment remains a separate MA-12 action.
    source = assert_closed(p["body"])
    tolerance(p["volume_tolerance_mm3"])
    result = shape_of(source).Copy()
    if result == shape_of(source):
        raise RuntimeError("Copy must have independent identity")
    if not near(volume_mm3(result), volume_mm3(source), p["volume_tolerance_mm3"]):
        raise RuntimeError("Copy volume mismatch")
    return require_transient(result)
