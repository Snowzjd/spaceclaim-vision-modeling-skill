ACTION_ID = "VA-12"


def operation(p):
    root = active_root(p)
    body, face = require_face(p, root)
    try:
        kind = geometry_kind(face)
    except ValueError:
        return manual_review(ACTION_ID, "Face geometry type is not exposed by the current V21 object.", body=body, face=face)
    analytic_types = ("Plane", "Cylinder", "Cone", "Torus", "Sphere")
    if kind in analytic_types:
        return passed(ACTION_ID, body=body, face=face, analytic_type=kind, is_analytic=True)
    # Preserve the unknown boundary instead of fitting a free-form surface to
    # the nearest analytic label.
    return passed(
        ACTION_ID,
        body=body,
        face=face,
        analytic_type="unknown",
        raw_geometry_type=kind,
        is_analytic=False,
    )
