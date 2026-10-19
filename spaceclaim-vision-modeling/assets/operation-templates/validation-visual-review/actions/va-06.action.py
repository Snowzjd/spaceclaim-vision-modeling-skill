ACTION_ID = "VA-06"


def operation(p):
    root = active_root(p)
    body = require_body(p, root)
    edges = list(body.Edges)
    expected = optional(p, None, "expected_count")
    result = passed(ACTION_ID, body=body, edges=edges, count=len(edges))
    if expected is not None:
        value = finite(expected, "expected_count")
        if value != int(value) or value < 0:
            raise ValueError("expected_count must be a non-negative integer")
        result["expected_count"] = int(value)
        result["matches"] = len(edges) == int(value)
        result["status"] = "passed" if result["matches"] else "failed"
    return result
