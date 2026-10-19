ACTION_ID = "VA-17"


def operation(p):
    root = active_root(p)
    target, object_kind = object_identity(p, root)
    expected = required(p, "expected_name", "name")
    if not isinstance(expected, _STRING_TYPES):
        raise ValueError("expected_name must be a nonempty string")
    expected_text = text(expected)
    if not expected_text.strip():
        raise ValueError("expected_name must be a nonempty string")
    actual = safe_name(target)
    matches = actual == expected_text
    result = passed(
        ACTION_ID,
        object_kind=object_kind,
        actual_name=actual,
        expected_name=expected_text,
        matches=matches,
    )
    result["status"] = "passed" if matches else "failed"
    return result
