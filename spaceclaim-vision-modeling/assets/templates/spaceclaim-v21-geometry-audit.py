# SpaceClaim 2022 R1 / API V21 read-only geometry audit template.
# IronPython 2.7 compatible. This script does not modify or save the model.
# Adapt the import when targeting another installed SpaceClaim API version.

from __future__ import print_function

from SpaceClaim.Api.V21 import *


INCLUDE_FACE_DETAILS = False
REPORT_PATH = None  # Example: "C:/work/geometry-audit.txt"


def _safe_text(value):
    try:
        return unicode(value).replace(u"|", u"/").replace(u"\r", u" ").replace(u"\n", u" ")
    except:
        return u"<unavailable>"


def _number(value, scale):
    try:
        return "%.9g" % (float(value) * scale)
    except:
        return "nan"


def _coordinate(value, index):
    names = ("X", "Y", "Z")
    try:
        return float(getattr(value, names[index]))
    except:
        pass
    try:
        return float(value[index])
    except:
        pass
    try:
        return float(value.Vector[index])
    except:
        return None


def _point_mm(point):
    values = [_coordinate(point, index) for index in range(3)]
    if any(value is None for value in values):
        return _safe_text(point)
    return "%.9g,%.9g,%.9g" % tuple(value * 1000.0 for value in values)


def _box(shape):
    try:
        return shape.GetBoundingBox(Matrix.Identity, True)
    except:
        return shape.GetBoundingBox(Matrix.Identity)


def _geometry_type(face):
    try:
        return _safe_text(face.Shape.Geometry.GetType().Name)
    except:
        return u"<unknown>"


def _group_member_count(group):
    for attribute in ("Members", "Items"):
        try:
            return int(getattr(group, attribute).Count)
        except:
            pass
    return -1


def collect_audit_lines():
    part = GetRootPart()
    bodies = part.GetAllBodies()
    groups = WindowHelper.GetGroups()
    face_count = sum([body.Faces.Count for body in bodies])
    edge_count = sum([body.Edges.Count for body in bodies])
    lines = []
    lines.append(
        u"AUDIT_SUMMARY|bodies=%d|faces=%d|edges=%d|groups=%d"
        % (bodies.Count, face_count, edge_count, groups.Count)
    )

    for body_index, body in enumerate(bodies):
        shape = body.Shape
        box = _box(shape)
        lines.append(
            u"BODY|index=%d|name=%s|volume_mm3=%s|surface_mm2=%s|faces=%d|edges=%d|bbox_min_mm=%s|bbox_max_mm=%s"
            % (
                body_index,
                _safe_text(body.Name),
                _number(shape.Volume, 1.0e9),
                _number(shape.SurfaceArea, 1.0e6),
                body.Faces.Count,
                body.Edges.Count,
                _point_mm(box.MinCorner),
                _point_mm(box.MaxCorner),
            )
        )

        if INCLUDE_FACE_DETAILS:
            for face_index, face in enumerate(body.Faces):
                face_box = _box(face.Shape)
                lines.append(
                    u"FACE|body_index=%d|face_index=%d|geometry=%s|area_mm2=%s|bbox_min_mm=%s|bbox_max_mm=%s"
                    % (
                        body_index,
                        face_index,
                        _geometry_type(face),
                        _number(face.Shape.Area, 1.0e6),
                        _point_mm(face_box.MinCorner),
                        _point_mm(face_box.MaxCorner),
                    )
                )

    for group_index, group in enumerate(groups):
        lines.append(
            u"GROUP|index=%d|name=%s|members=%d"
            % (group_index, _safe_text(group.Name), _group_member_count(group))
        )
    return lines


def emit_audit(lines):
    for line in lines:
        print(line)
    if REPORT_PATH:
        stream = open(REPORT_PATH, "wb")
        try:
            stream.write((u"\r\n".join(lines) + u"\r\n").encode("utf-8"))
        finally:
            stream.close()


emit_audit(collect_audit_lines())
