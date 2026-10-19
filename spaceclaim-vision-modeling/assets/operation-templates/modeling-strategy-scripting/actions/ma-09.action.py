def operation(p):
    # Caller supplies a closed planar profile and an ordered connected path.
    path = list(p["path"])
    if not path:
        raise ValueError("Require a nonempty ordered path of trimmed curves")
    return assert_closed(ModelerBody.SweepProfile(p["profile"], Array[ITrimmedCurve](path)))
