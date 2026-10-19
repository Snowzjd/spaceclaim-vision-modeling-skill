def operation(p):
    # Native root-part shell.  A signed offset expresses both thickness and
    # direction; removing faces and shelling the whole body are separate API
    # branches selected before the kernel call.
    body = require_live_body(p["body"])
    offset_mm = finite(p["offset_mm"], "offset_mm")
    if abs(offset_mm) <= 1e-12:
        raise ValueError("offset_mm must be finite and nonzero")

    raw_faces = p.get("remove_faces", [])
    if raw_faces is None:
        raw_faces = []
    faces = list(raw_faces)
    if len(faces) != len(set(faces)):
        raise ValueError("remove_faces must contain distinct current faces")
    body_faces = list(body.Faces)
    if any(face not in body_faces for face in faces):
        raise ValueError("Every remove face must belong to the current body")

    before = current_bodies()
    if faces:
        result = Shell.RemoveFaces(
            FaceSelection.Create(*faces),
            offset_mm / 1000.0,
            None,
        )
        mode = "remove-faces"
    else:
        result = Shell.ShellBodies(
            BodySelection.Create(body),
            offset_mm / 1000.0,
            None,
        )
        mode = "whole-body"
    result_ok(result, "shell")

    after = current_bodies()
    surviving = [candidate for candidate in after if candidate == body and volume_mm3(candidate) > 0]
    replacements = [
        candidate
        for candidate in after
        if candidate not in before and volume_mm3(candidate) > 0
    ]
    if len(surviving) == 1 and not replacements:
        result_body = surviving[0]
    elif not surviving and len(replacements) == 1:
        result_body = replacements[0]
    else:
        raise RuntimeError("Shell did not yield one identifiable positive-volume root body")

    return {
        "body": result_body,
        "mode": mode,
        "offset_mm": offset_mm,
        "remove_face_count": len(faces),
        "is_closed": bool(result_body.Shape.IsClosed),
        "volume_mm3": volume_mm3(result_body),
    }
