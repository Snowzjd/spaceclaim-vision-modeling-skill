def operation(p):
    # This binding is deliberately limited to a native, non-nested .scdoc
    # component.  It does not open/replace the active document or apply unit
    # overrides for foreign formats.
    import hashlib
    import os

    source_path = p["source_path"]
    if not isinstance(source_path, basestring) or not source_path.strip():
        raise ValueError("source_path must be a nonempty path")
    source_path = source_path.strip()
    if not source_path.lower().endswith(".scdoc"):
        raise ValueError("Only native .scdoc sources are supported")
    if not os.path.isfile(source_path):
        raise ValueError("source_path must identify an existing file")
    if any(key in p for key in ("format", "units", "unit_override", "import_options")):
        raise ValueError("Foreign-format and unit-override options are unsupported")

    expected_hash = p["source_sha256"]
    if not isinstance(expected_hash, basestring) or len(expected_hash) != 64:
        raise ValueError("source_sha256 must be a 64-character hexadecimal digest")
    expected_hash = expected_hash.lower()
    if any(character not in "0123456789abcdef" for character in expected_hash):
        raise ValueError("source_sha256 must be hexadecimal")

    expected_count_value = p["expected_body_count"]
    if isinstance(expected_count_value, bool):
        raise ValueError("expected_body_count must be a positive integer, not boolean")
    expected_count_number = finite(expected_count_value, "expected_body_count")
    if expected_count_number != int(expected_count_number):
        raise ValueError("expected_body_count must be an integer")
    expected_count = int(expected_count_number)
    if expected_count <= 0:
        raise ValueError("expected_body_count must be positive")

    bbox_tolerance = tolerance(p["bbox_tolerance_mm"])
    volume_tolerance = tolerance(p["volume_tolerance_mm3"])
    signatures = list(p["expected_body_signatures"])
    if len(signatures) != expected_count:
        raise ValueError("expected_body_signatures must match expected_body_count")
    normalized_signatures = []
    for signature in signatures:
        if not isinstance(signature, dict) or "bbox_mm" not in signature or "volume_mm3" not in signature:
            raise ValueError("Each body signature requires bbox_mm and volume_mm3")
        bbox = signature["bbox_mm"]
        if not isinstance(bbox, (list, tuple)) or len(bbox) != 6:
            raise ValueError("Each body signature bbox_mm requires six coordinates")
        bbox = [finite(value, "bbox_mm") for value in bbox]
        volume = finite(signature["volume_mm3"], "volume_mm3")
        if volume <= 0:
            raise ValueError("Expected body volumes must be positive")
        normalized_signatures.append((bbox, volume))

    with open(source_path, "rb") as source_file:
        verified_hash = hashlib.sha256(source_file.read()).hexdigest().lower()
    if verified_hash != expected_hash:
        raise ValueError("source_sha256 does not match source_path")

    # The active root part is the only supported import target.  All guards
    # above run before Component.CreateFromFile can mutate the document.
    root = GetRootPart()
    if Window.ActiveWindow.ActiveContext.ActivePart != root:
        raise ValueError("This import variant requires the root part to be active")
    before_components = [component for component in root.GetDescendants[Component]() if component.Parent == root]

    options = ImportOptions.Create()
    Component.CreateFromFile(root, source_path, options)

    after_components = [component for component in root.GetDescendants[Component]() if component.Parent == root]
    imported_components = [component for component in after_components if component not in before_components]
    component = one(imported_components, "new direct-root imported component")
    if component.Parent != root:
        raise RuntimeError("Imported component is not a direct child of the active root")

    nested_components = list(component.Content.Components)
    if nested_components:
        raise RuntimeError("Nested .scdoc component sources are outside this variant")

    bodies = list(component.Content.Bodies)
    if len(bodies) != expected_count:
        raise RuntimeError("Imported body count differs from expected_body_count")

    measurements = []
    for body in bodies:
        assert_closed(body.Master)
        measurements.append({
            "body": body,
            "bbox_mm": bounds_mm(body),
            "volume_mm3": volume_mm3(body.Shape),
        })

    # Match each supplied signature uniquely by geometry, never by import
    # enumeration order or the opaque return value of CreateFromFile.
    remaining = list(range(len(measurements)))
    for expected_bbox, expected_volume in normalized_signatures:
        matches = [
            index for index in remaining
            if bbox_matches(measurements[index]["bbox_mm"], expected_bbox, bbox_tolerance)
            and near(measurements[index]["volume_mm3"], expected_volume, volume_tolerance)
        ]
        if len(matches) != 1:
            raise RuntimeError("Expected body signature did not resolve uniquely")
        remaining.remove(matches[0])
    if remaining:
        raise RuntimeError("Imported body signatures did not cover every body")

    with open(source_path, "rb") as source_file:
        unchanged_hash = hashlib.sha256(source_file.read()).hexdigest().lower()
    if unchanged_hash != verified_hash:
        raise RuntimeError("Source file changed during import")

    return {
        "component": component,
        "bodies": bodies,
        "source_sha256": verified_hash,
        "measurements": measurements,
    }
