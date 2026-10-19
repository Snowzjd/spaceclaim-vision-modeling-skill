def operation(p):
    transient = require_transient(p["body"])
    name = require_name(p["name"])
    before = current_bodies()
    if any(body.Name == name for body in before):
        raise ValueError("Body name already exists")
    result = DesignBody.Create(GetRootPart(), name, transient)
    after = current_bodies()
    if len(after) != len(before)+1 or result not in after or result.Name != name:
        raise RuntimeError("Attachment did not create the declared body identity")
    return assert_closed(result)
