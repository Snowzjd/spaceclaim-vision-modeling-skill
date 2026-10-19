def operation(p):
    # Create-only face-group variant; exact rename is separate MA-34.
    faces = list(p["faces"])
    current = [f for b in current_bodies() for f in list(b.Faces)]
    if not faces or len(set(faces)) != len(faces) or any(f not in current for f in faces):
        raise ValueError("Require distinct current faces")
    result = NamedSelection.Create(FaceSelection.Create(*faces), Selection.Empty())
    result_ok(result, "face group creation")
    if result.CreatedNamedSelection is None:
        raise RuntimeError("No named selection returned")
    if set(result.CreatedNamedSelection.Members) != set(faces):
        raise RuntimeError("Created group membership differs from supplied faces")
    return result.CreatedNamedSelection
