ACTION_ID = "VA-04"


def operation(p):
    root = active_root(p)
    bodies = root_bodies(root)
    expected = optional(p, None, "expected_count")
    if expected is None:
        matches = None
        status = "passed"
    else:
        expected_number = finite(expected, "expected_count")
        if expected_number != int(expected_number):
            raise ValueError("expected_count must be an integer")
        if expected_number < 0:
            raise ValueError("expected_count must be non-negative")
        matches = len(bodies) == int(expected_number)
        status = "passed" if matches else "failed"
    records = []
    for index, body in enumerate(bodies):
        records.append({
            "index": index,
            "name": safe_name(body, "body name") if hasattr(body, "Name") else "<unnamed>",
        })
    result = passed(ACTION_ID, bodies=bodies, body_records=records, count=len(bodies))
    if matches is not None:
        result["expected_count"] = int(expected_number)
        result["matches"] = matches
        result["status"] = status
    return result
