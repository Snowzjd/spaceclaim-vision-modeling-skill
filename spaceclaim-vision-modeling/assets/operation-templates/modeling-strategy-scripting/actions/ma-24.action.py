def operation(p):
    body = require_live_body(p["body"])
    face = p["face"]
    if face not in list(body.Faces):
        raise ValueError("Split face must be current and belong to the supplied body")
    curves = list(p["curves"])
    if not curves:
        raise ValueError("Supply nonempty trimmed splitting curves")
    volume_tol = tolerance(p["volume_tolerance_mm3"])
    bbox_tol = tolerance(p["bbox_tolerance_mm"])
    count, volume, bounds = len(list(body.Faces)), volume_mm3(body), bounds_mm(body)
    options = SplitFaceOptions()
    options.MakeCurves = False
    result_ok(SplitFace.ByCurves(FaceSelection.Create(face), Array[ITrimmedCurve](curves), options), "split face")
    current = one([b for b in current_bodies() if bbox_matches(bounds_mm(b), bounds, bbox_tol) and near(volume_mm3(b), volume, volume_tol)], "split parent body")
    if len(list(current.Faces)) <= count:
        raise RuntimeError("Splitting curves did not create additional faces")
    return dict(body=current, faces=list(current.Faces), added_face_count=len(list(current.Faces))-count)
