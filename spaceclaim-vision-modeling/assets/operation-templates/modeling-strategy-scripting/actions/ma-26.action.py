def operation(p):
    body = require_live_body(p["body"])
    edges = list(p["edges"])
    if not edges or len(set(edges)) != len(edges) or any(e not in list(body.Edges) for e in edges):
        raise ValueError("Require distinct current edges of supplied body")
    radius = positive(p["radius_mm"], "radius")
    result = ConstantRound.Execute(EdgeSelection.Create(*edges), radius/1000.0)
    result_ok(result, "constant round")
    # All caller topology caches must be discarded after this mutation.
    return {"bodies": current_bodies()}
