def operation(p):
    plane, kind = p["plane"], p["kind"]
    if kind in ("rectangle", "circle"):
        center = p["center_uv_mm"]
        if len(center) != 2:
            raise ValueError("Expected two in-plane center coordinates")
        uv = PointUV.Create(finite(center[0], "u")/1000.0, finite(center[1], "v")/1000.0)
        angle = finite(p["angle_deg"], "angle") * math.pi / 180.0
        if kind == "rectangle":
            return RectangleProfile(plane, positive(p["width_mm"], "width")/1000.0, positive(p["height_mm"], "height")/1000.0, uv, angle)
        return CircleProfile(plane, positive(p["radius_mm"], "radius")/1000.0, uv, angle)
    if kind != "polygon":
        raise ValueError("Supported profile variants: rectangle, circle, simple polygon")
    vertices = [vector3(v, "vertex") for v in p["vertices_mm"]]
    if len(vertices) < 3:
        raise ValueError("Polygon needs at least three distinct vertices")
    frame = plane.Frame
    origin = [float(v)*1000 for v in (frame.Origin.X, frame.Origin.Y, frame.Origin.Z)]
    axes = [[float(v) for v in (axis.X, axis.Y, axis.Z)] for axis in (frame.DirX, frame.DirY, frame.DirZ)]
    uv = []
    for vertex in vertices:
        delta = [vertex[i]-origin[i] for i in range(3)]
        if abs(sum(delta[i]*axes[2][i] for i in range(3))) > 1e-6:
            raise ValueError("Polygon vertex does not lie in supplied plane")
        uv.append([sum(delta[i]*axes[j][i] for i in range(3)) for j in (0, 1)])
    def cross(a, b, c):
        return (b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0])
    count = len(uv)
    if abs(sum(uv[i][0]*uv[(i+1)%count][1]-uv[(i+1)%count][0]*uv[i][1] for i in range(count))) <= 1e-9:
        raise ValueError("Polygon is degenerate")
    for i in range(count):
        a, b = uv[i], uv[(i+1)%count]
        if sum((a[j]-b[j])**2 for j in (0, 1)) <= 1e-18:
            raise ValueError("Repeated adjacent polygon vertex")
        for k in range(i+1, count):
            if k in (i, (i+1)%count) or (k+1)%count == i:
                continue
            c, d = uv[k], uv[(k+1)%count]
            if cross(a,b,c)*cross(a,b,d) <= 0 and cross(c,d,a)*cross(c,d,b) <= 0 and max(min(a[0],b[0]),min(c[0],d[0])) <= min(max(a[0],b[0]),max(c[0],d[0])) and max(min(a[1],b[1]),min(c[1],d[1])) <= min(max(a[1],b[1]),max(c[1],d[1])):
                raise ValueError("Polygon self-intersection or nonadjacent touching")
    curves = [CurveSegment.Create(point_mm(vertices[i]), point_mm(vertices[(i+1)%count])) for i in range(count)]
    return Profile(plane, Array[ITrimmedCurve](curves))
