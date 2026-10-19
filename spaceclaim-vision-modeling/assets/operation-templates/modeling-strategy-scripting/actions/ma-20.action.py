def operation(p):
    target = require_transient(p["target"])
    tools = [require_transient(b) for b in p["tools"]]
    if not tools or any(b == target for b in tools) or len(set(tools)) != len(tools):
        raise ValueError("Distinct nonempty transient tools are required")
    if p["tool_policy"] != "consume":
        raise ValueError("This variant consumes tools; copy separately to retain")
    target.Unite(Array[ModelerBody](tools))
    assert_closed(target)
    if not all(b.IsDeleted for b in tools):
        raise RuntimeError("Union did not consume all tools")
    return {"body": target, "piece_count": int(target.PieceCount)}
