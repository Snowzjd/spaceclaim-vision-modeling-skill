def operation(p):
    return Line.Create(point_mm(p["origin_mm"]), direction(p["direction"]))
