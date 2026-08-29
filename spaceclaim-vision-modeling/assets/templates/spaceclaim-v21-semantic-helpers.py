# Reusable semantic-selection helpers for SpaceClaim API V21.
# IronPython 2.7 compatible. Import or paste into a case script and define
# geometry-specific predicates outside this file.

from SpaceClaim.Api.V21 import *


MM_PER_M = 1000.0
MM2_PER_M2 = 1.0e6
MM3_PER_M3 = 1.0e9


def near(left, right, tolerance):
    return abs(float(left) - float(right)) <= float(tolerance)


def _coordinate(value, index):
    names = ("X", "Y", "Z")
    try:
        return float(getattr(value, names[index]))
    except:
        return float(value[index])


def point_mm(point):
    return tuple(_coordinate(point, index) * MM_PER_M for index in range(3))


def shape_bbox_mm(shape):
    try:
        box = shape.GetBoundingBox(Matrix.Identity, True)
    except:
        box = shape.GetBoundingBox(Matrix.Identity)
    return point_mm(box.MinCorner) + point_mm(box.MaxCorner)


def bbox_near(actual, expected, tolerance_mm):
    return all(near(actual[index], expected[index], tolerance_mm) for index in range(6))


def body_volume_mm3(body):
    return float(body.Shape.Volume) * MM3_PER_M3


def face_area_mm2(face):
    return float(face.Shape.Area) * MM2_PER_M2


def current_bodies():
    return list(GetRootPart().GetAllBodies())


def find_unique(items, predicate, label):
    matches = [item for item in items if predicate(item)]
    if len(matches) != 1:
        raise ValueError("Expected one %s, found %d" % (label, len(matches)))
    return matches[0]


def find_unique_body(predicate, label):
    return find_unique(current_bodies(), predicate, label)


def find_unique_face(body, predicate, label):
    return find_unique(list(body.Faces), predicate, label)


def assert_body_count(expected):
    actual = len(current_bodies())
    if actual != expected:
        raise ValueError("Expected %d bodies, found %d" % (expected, actual))


def rename_body(body, final_name):
    result = RenameObject.Execute(BodySelection.Create(body), final_name)
    if not result.Success:
        raise ValueError("Body rename failed: %s" % final_name)
    return body


def create_named_face_group(faces, final_name, expected_count=None):
    face_list = list(faces)
    if expected_count is not None and len(face_list) != expected_count:
        raise ValueError(
            "Named selection %s expected %d faces, found %d"
            % (final_name, expected_count, len(face_list))
        )
    result = NamedSelection.Create(
        FaceSelection.Create(*face_list),
        Selection.Empty(),
    )
    if not result.Success or result.CreatedNamedSelection is None:
        raise ValueError("Named selection creation failed: %s" % final_name)
    created = result.CreatedNamedSelection
    rename_result = NamedSelection.Rename(created.Name, final_name)
    if not rename_result.Success:
        raise ValueError("Named selection rename failed: %s" % final_name)
    return created


def write_report(report_path, lines):
    if not report_path:
        return
    stream = open(report_path, "wb")
    try:
        stream.write((u"\r\n".join(lines) + u"\r\n").encode("utf-8"))
    finally:
        stream.close()


# Important usage rule:
# After merge, split, intersect, subtract, repair, or import, call
# current_bodies() again and rebuild face/body selections. Do not reuse handles
# captured before the topology mutation, and do not trust Boolean return order.
