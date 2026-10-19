def operation(p):
    body = require_live_body(p["body"])
    edges = list(p["edges"])
    if not edges or len(set(edges)) != len(edges) or any(e not in list(body.Edges) for e in edges):
        raise ValueError("Require distinct current edges of supplied body")
    distance = positive(p["distance_mm"], "distance")
    result = Chamfer.Execute(EdgeSelection.Create(*edges), distance/1000.0, False)
    result_ok(result, "equal-distance chamfer")
    return {"bodies": current_bodies()}
