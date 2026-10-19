ACTION_ID = "VA-05"


def operation(p):
    root = active_root(p)
    body = require_body(p, root)
    faces = list(body.Faces)
    expected = optional(p, None, "expected_count")
    result = passed(ACTION_ID, body=body, faces=faces, count=len(faces))
    if expected is not None:
        value = finite(expected, "expected_count")
        if value != int(value) or value < 0:
            raise ValueError("expected_count must be a non-negative integer")
        result["expected_count"] = int(value)
        result["matches"] = len(faces) == int(value)
        result["status"] = "passed" if result["matches"] else "failed"
    return result
