ACTION_ID = "VA-11"


def operation(p):
    root = active_root(p)
    body, face = require_face(p, root)
    mode = required(p, "property", "mode", "attribute")
    if not isinstance(mode, _STRING_TYPES):
        raise ValueError("face semantic property must be a string")
    mode = mode.strip().lower()
    unit, length_scale, area_scale, _ = unit_spec(p)
    if mode in ("area", "surface_area"):
        value = abs(read_scalar(face.Shape, "Area", "face area")) * area_scale
        return passed(ACTION_ID, body=body, face=face, mode="area", unit=unit, area=value)
    if mode in ("center", "bbox_center", "bounding_box_center"):
        frame, frame_name = frame_spec(p)
        bbox = shape_bbox_in_units(face, frame, length_scale)
        center = [0.5 * (bbox[index] + bbox[index + 3]) for index in range(3)]
        return passed(
            ACTION_ID,
            body=body,
            face=face,
            mode="center",
            center=center,
            center_kind="bounding_box_center",
            frame=frame_name,
            unit=unit,
        )
    if mode == "normal":
        kind = geometry_kind(face)
        if kind != "Plane":
            return manual_review(
                ACTION_ID,
                "Curved-face normal requires a verified V21 sample-point evaluation signature.",
                body=body,
                face=face,
                mode="normal",
                analytic_type=kind,
            )
        try:
            direction = point_components(face.Shape.Geometry.Frame.DirZ, "face normal")
            sign = -1.0 if face.Shape.IsReversed else 1.0
            normal = [sign * value for value in direction]
            normal = normalize(normal, "face normal")
        except Exception:
            return manual_review(
                ACTION_ID,
                "Planar face normal properties were not available in this V21 object.",
                body=body,
                face=face,
                mode="normal",
            )
        return passed(
            ACTION_ID,
            body=body,
            face=face,
            mode="normal",
            normal=normal,
            sample_binding="planar_face_frame",
        )
    raise ValueError("Unsupported face semantic property; use area, normal, or center")
