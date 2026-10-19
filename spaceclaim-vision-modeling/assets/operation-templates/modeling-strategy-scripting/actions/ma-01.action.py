def operation(p):
    x, y = vector3(p["x_axis"], "x_axis"), vector3(p["y_axis"], "y_axis")
    nx, ny = math.sqrt(sum(v*v for v in x)), math.sqrt(sum(v*v for v in y))
    if nx <= 1e-12 or ny <= 1e-12 or abs(sum(x[i]*y[i] for i in range(3))/(nx*ny)) > 1e-9:
        raise ValueError("Frame axes must be nonzero and orthogonal")
    return Frame.Create(point_mm(p["origin_mm"]), direction(x), direction(y))
