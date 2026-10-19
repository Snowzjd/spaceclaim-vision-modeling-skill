def operation(p):
    body = require_live_body(p["body"])
    name = require_name(p["name"])
    if any(b != body and b.Name == name for b in current_bodies()):
        raise ValueError("Body name collision")
    result_ok(RenameObject.Execute(BodySelection.Create(body), name), "body rename")
    if body.Name != name:
        raise RuntimeError("Exact body name was not applied")
    return body
