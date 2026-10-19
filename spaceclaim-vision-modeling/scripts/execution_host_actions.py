#!/usr/bin/env python3
"""Deterministic host-side helpers for execution/recovery atomic actions.

The helpers in this module never launch SpaceClaim and never claim that a
script was observed running.  They enforce the filesystem and event contracts
around an authorized run.  A caller must still provide trustworthy run
ownership and authorization records; this module does not manufacture either
one from a JSON file.
"""

from __future__ import annotations

import copy
import datetime as _datetime
import hashlib
import math
import os
from pathlib import Path
import re
import shutil
import stat
from typing import Any, Callable, Iterable, Mapping, Sequence
import zipfile


SHA256_PATTERN = re.compile(r"^[0-9a-fA-F]{64}$")
NUMERIC_VERSION_PATTERN = re.compile(r"^[0-9]+$")


class HostActionError(ValueError):
    """A fail-closed host action precondition or safety violation."""

    def __init__(self, message: str, code: str = "invalid_input") -> None:
        super().__init__(message)
        self.code = code


def _fail(message: str, code: str = "invalid_input") -> None:
    raise HostActionError(message, code)


def _path(value: Any, name: str) -> Path:
    if isinstance(value, (str, os.PathLike)) and not isinstance(value, bytes):
        text = os.fspath(value)
        if not str(text).strip():
            _fail("%s must not be empty" % name)
        return Path(text).absolute()
    _fail("%s must be a path-like value" % name)
    raise AssertionError("unreachable")


def _canonical(path: Path) -> Path:
    return Path(os.path.normcase(os.path.realpath(os.path.abspath(os.fspath(path)))))


def _path_key(path: Path) -> str:
    return os.path.normcase(os.path.realpath(os.path.abspath(os.fspath(path))))


def _is_reparse_point(path: Path) -> bool:
    """Return true for symlinks and Windows reparse points/junctions."""

    try:
        if path.is_symlink() or os.path.islink(os.fspath(path)):
            return True
        attributes = getattr(path.stat(), "st_file_attributes", 0)
    except OSError:
        return False
    return bool(attributes & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400))


def _assert_no_symlink_components(path: Path, name: str) -> None:
    """Reject symlink/reparse components, including a dangling final link."""

    current = path
    while True:
        if _is_reparse_point(current):
            _fail("%s contains a symlink or reparse point: %s" % (name, current), "symlink")
        parent = current.parent
        if parent == current:
            return
        current = parent


def _assert_directory(path: Path, name: str) -> None:
    _assert_no_symlink_components(path, name)
    if not path.is_dir():
        _fail("%s must be an existing directory: %s" % (name, path), "missing_directory")


def _assert_regular_file(path: Path, name: str) -> None:
    _assert_no_symlink_components(path, name)
    try:
        mode = path.stat().st_mode
    except OSError as exc:
        _fail("%s is not readable: %s" % (name, path), "missing_file")
        raise AssertionError("unreachable") from exc
    if not stat.S_ISREG(mode):
        _fail("%s must be a regular file: %s" % (name, path), "not_regular_file")
    if not os.access(os.fspath(path), os.R_OK):
        _fail("%s is not readable: %s" % (name, path), "unreadable_file")


def _assert_new_file_path(path: Path, name: str) -> None:
    _assert_no_symlink_components(path.parent, name + " parent")
    if path.exists() or path.is_symlink():
        _fail("%s must be a new path: %s" % (name, path), "existing_output")
    if not path.parent.is_dir():
        _fail("%s parent must be an existing directory: %s" % (name, path.parent), "missing_directory")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _validate_sha256(value: Any, name: str) -> str:
    if not isinstance(value, str) or not SHA256_PATTERN.fullmatch(value.strip()):
        _fail("%s must be a 64-character hexadecimal SHA-256 digest" % name, "invalid_hash")
    return value.strip().lower()


def _validate_run_ref(value: Any, name: str = "run_ref") -> str:
    if not isinstance(value, str) or not value.strip():
        _fail("%s must be a non-empty string" % name, "missing_run_ref")
    return value.strip()


def _is_within(path: Path, root: Path, *, allow_equal: bool = False) -> bool:
    path_key = _path_key(path)
    root_key = _path_key(root)
    if path_key == root_key:
        return allow_equal
    try:
        return os.path.commonpath((path_key, root_key)) == root_key
    except ValueError:
        return False


def _assert_inside(path: Path, root: Path, name: str, *, allow_equal: bool = False) -> None:
    if not _is_within(path, root, allow_equal=allow_equal):
        _fail("%s must remain inside run root: %s" % (name, path), "outside_run_root")


def _reserved_collision(path: Path, reserved: Path) -> bool:
    return _is_within(path, reserved, allow_equal=True)


def _as_path_list(value: Any, name: str) -> list[Path]:
    if value is None:
        return []
    if isinstance(value, (str, os.PathLike)) and not isinstance(value, bytes):
        return [_path(value, name)]
    if isinstance(value, Mapping):
        values = value.values()
    else:
        try:
            values = iter(value)
        except TypeError:
            _fail("%s must be a path or iterable of paths" % name)
    result = []
    for index, item in enumerate(values):
        result.append(_path(item, "%s[%d]" % (name, index)))
    return result


def copy_baseline_model(
    baseline_path: Any,
    run_copy_path: Any,
    expected_sha256: Any = None,
    *,
    run_ref: Any = None,
) -> dict[str, Any]:
    """Copy one baseline file to a new path and verify both hashes.

    The source is never opened for writing.  The destination must not exist,
    and a source change detected around the copy removes only the newly
    created destination before failing.
    """

    ref = _validate_run_ref(run_ref) if run_ref is not None else None
    source = _path(baseline_path, "baseline_path")
    destination = _path(run_copy_path, "run_copy_path")
    _assert_regular_file(source, "baseline_path")
    _assert_new_file_path(destination, "run_copy_path")
    if _path_key(source) == _path_key(destination):
        _fail("baseline and run copy paths must be different", "same_path")

    expected = None
    if expected_sha256 is not None:
        expected = _validate_sha256(expected_sha256, "expected_sha256")
    source_before = _sha256(source)
    if expected is not None and source_before != expected:
        _fail("baseline hash does not match expected_sha256", "hash_mismatch")

    created = False
    try:
        flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_BINARY", 0)
        descriptor = os.open(os.fspath(destination), flags, 0o666)
        created = True
        with os.fdopen(descriptor, "wb") as output, source.open("rb") as original:
            shutil.copyfileobj(original, output, length=1024 * 1024)
        shutil.copystat(source, destination, follow_symlinks=False)
    except FileExistsError as exc:
        _fail("run copy path was created concurrently: %s" % destination, "existing_output")
        raise AssertionError("unreachable") from exc
    except Exception:
        if created and destination.exists() and not destination.is_symlink():
            destination.unlink()
        raise

    source_after = _sha256(source)
    copied = _sha256(destination)
    if source_after != source_before:
        destination.unlink()
        _fail("baseline changed during copy", "source_changed")
    if copied != source_before:
        destination.unlink()
        _fail("run copy hash differs from baseline", "copy_hash_mismatch")

    result = {
        "action_id": "EX-05",
        "status": "passed",
        "baseline_path": str(source),
        "run_copy_path": str(destination),
        "baseline_sha256": source_before,
        "copy_sha256": copied,
        "source_preserved": True,
        "destination_was_new": True,
        "evidence_level": "host_checked",
    }
    if run_ref is not None:
        result["run_ref"] = ref
    return result


def _normalise_output_specs(output_paths: Any) -> list[dict[str, Any]]:
    if isinstance(output_paths, Mapping):
        if "path" in output_paths or "output_path" in output_paths:
            raw_specs = [output_paths]
        else:
            raw_specs = []
            for role, value in output_paths.items():
                if isinstance(value, Mapping):
                    spec = dict(value)
                    spec.setdefault("role", role)
                else:
                    spec = {"role": role, "path": value}
                raw_specs.append(spec)
    elif isinstance(output_paths, (str, os.PathLike)) and not isinstance(output_paths, bytes):
        raw_specs = [{"role": "output", "path": output_paths}]
    else:
        try:
            raw_specs = list(output_paths)
        except TypeError:
            _fail("output_paths must be a path, mapping, or iterable", "invalid_outputs")

    result = []
    for index, raw in enumerate(raw_specs):
        if isinstance(raw, Mapping):
            path_value = raw.get("path", raw.get("output_path"))
            role = raw.get("role", "output-%d" % index)
            overwrite = raw.get("overwrite", False)
        else:
            path_value = raw
            role = "output-%d" % index
            overwrite = False
        if not isinstance(role, str) or not role.strip():
            _fail("output role must be a non-empty string", "invalid_role")
        if not isinstance(overwrite, bool):
            _fail("output overwrite flag must be boolean", "invalid_overwrite_policy")
        result.append({"path": _path(path_value, "output[%d].path" % index), "role": role.strip(), "overwrite": overwrite})
    if not result:
        _fail("at least one output path is required", "invalid_outputs")
    return result


def _normalise_overwrite_policy(value: Any) -> str:
    if value is None:
        return "new_only"
    if not isinstance(value, str):
        _fail("overwrite_policy must be a string", "invalid_overwrite_policy")
    policy = value.strip().lower().replace("-", "_")
    aliases = {"new": "new_only", "forbid_existing": "new_only", "allow_run_owned": "run_owned", "replace_run_owned": "run_owned"}
    policy = aliases.get(policy, policy)
    if policy not in {"new_only", "run_owned"}:
        _fail("unsupported overwrite_policy: %s" % value, "invalid_overwrite_policy")
    return policy


def verify_run_output_path(
    output_paths: Any,
    run_root: Any,
    *,
    baseline_path: Any = None,
    evidence_paths: Any = None,
    overwrite_policy: Any = "new_only",
    owned_paths: Any = None,
    run_ref: Any = None,
) -> dict[str, Any]:
    """Validate run-owned outputs without touching the filesystem."""

    root = _path(run_root, "run_root")
    _assert_directory(root, "run_root")
    outputs = _normalise_output_specs(output_paths)
    policy = _normalise_overwrite_policy(overwrite_policy)
    owned = {_path_key(item) for item in _as_path_list(owned_paths, "owned_paths")}
    reserved = []
    if baseline_path is not None:
        reserved.append(_path(baseline_path, "baseline_path"))
    reserved.extend(_as_path_list(evidence_paths, "evidence_paths"))
    for item in reserved:
        _assert_no_symlink_components(item, "reserved path")

    roles = set()
    paths = set()
    checked = []
    for item in outputs:
        path = item["path"]
        role = item["role"]
        if role in roles:
            _fail("output role collision: %s" % role, "role_collision")
        roles.add(role)
        _assert_no_symlink_components(path, "output path")
        _assert_inside(path, root, "output path")
        key = _path_key(path)
        if key in paths:
            _fail("output path collision: %s" % path, "path_collision")
        paths.add(key)
        for reserved_path in reserved:
            if _reserved_collision(path, reserved_path):
                _fail("output path would overwrite baseline/evidence: %s" % path, "reserved_path_collision")

        exists = path.exists() or path.is_symlink()
        if exists:
            if _is_reparse_point(path):
                _fail("output path is a symlink or reparse point: %s" % path, "symlink")
            if not path.is_file():
                _fail("existing output is not a regular file: %s" % path, "not_regular_file")
            if policy != "run_owned" or not item["overwrite"] or key not in owned:
                _fail("existing output is not replaceable under run ownership policy: %s" % path, "existing_output")
        elif item["overwrite"] and policy != "run_owned":
            _fail("overwrite=True requires run_owned policy", "invalid_overwrite_policy")
        checked.append({"role": role, "path": str(path), "exists": exists, "overwrite": item["overwrite"]})

    result = {
        "action_id": "EX-07",
        "status": "passed",
        "run_root": str(root),
        "outputs": checked,
        "overwrite_policy": policy,
        "evidence_level": "host_checked",
    }
    if run_ref is not None:
        result["run_ref"] = _validate_run_ref(run_ref)
    return result


def _validate_numeric_version(value: Any, name: str) -> str:
    if isinstance(value, bool):
        _fail("%s must contain digits only" % name, "invalid_api_version")
    text = str(value).strip()
    if not NUMERIC_VERSION_PATTERN.fullmatch(text):
        _fail("%s must contain digits only" % name, "invalid_api_version")
    return text


def record_executed_artifact_identity(
    artifact_path: Any = None,
    expected_sha256: Any = None,
    expected_api_version: Any = None,
    run_ref: Any = None,
    *,
    script_path: Any = None,
    expected_hash: Any = None,
    api_version: Any = None,
    run_reference: Any = None,
) -> dict[str, Any]:
    """Bind a run reference to one exact, hash- and API-checked archive.

    This is host identity evidence only.  ``execution_observed`` is always
    false because finding a valid archive cannot prove that SpaceClaim ran it.
    """

    artifact_value = artifact_path if artifact_path is not None else script_path
    if artifact_value is None:
        _fail("artifact_path is required", "missing_artifact")
    expected_value = expected_sha256 if expected_sha256 is not None else expected_hash
    if expected_value is None:
        _fail("expected_sha256 is required", "missing_hash")
    api_value = expected_api_version if expected_api_version is not None else api_version
    if api_value is None:
        _fail("expected_api_version is required", "missing_api_version")
    reference = run_ref if run_ref is not None else run_reference
    ref = _validate_run_ref(reference)
    artifact = _path(artifact_value, "artifact_path")
    _assert_regular_file(artifact, "artifact_path")
    if artifact.suffix.lower() != ".scscript":
        _fail("artifact_path must have a .scscript extension", "invalid_artifact_extension")
    expected_hash_value = _validate_sha256(expected_value, "expected_sha256")
    expected_api = _validate_numeric_version(api_value, "expected_api_version")
    actual_hash = _sha256(artifact)
    if actual_hash != expected_hash_value:
        _fail("executed artifact hash does not match expected_sha256", "hash_mismatch")

    try:
        with zipfile.ZipFile(artifact, "r") as archive:
            names = set(archive.namelist())
            if "_script" not in names or "_apiVersion" not in names:
                _fail(".scscript archive lacks required script metadata", "invalid_scscript")
            if archive.testzip() is not None:
                _fail(".scscript archive contains a corrupt member", "invalid_scscript")
            try:
                actual_api = archive.read("_apiVersion").decode("ascii").strip()
            except (UnicodeDecodeError, KeyError) as exc:
                _fail(".scscript API metadata is not ASCII", "invalid_api_version")
                raise AssertionError("unreachable") from exc
    except zipfile.BadZipFile as exc:
        _fail("artifact_path is not a readable .scscript archive", "invalid_scscript")
        raise AssertionError("unreachable") from exc

    actual_api = _validate_numeric_version(actual_api, "archive API version")
    if int(actual_api) != int(expected_api):
        _fail(".scscript API version does not match expected_api_version", "api_version_mismatch")
    result = {
        "action_id": "EX-11",
        "status": "passed",
        "run_ref": ref,
        "artifact_path": str(artifact),
        "artifact_sha256": actual_hash,
        "expected_sha256": expected_hash_value,
        "api_version": actual_api,
        "expected_api_version": expected_api,
        "identity_match": True,
        "execution_observed": False,
        "runtime_observation": "not_tested",
        "evidence_level": "host_checked",
        "claim_boundary": "artifact identity only; this does not prove independent execution",
    }
    return result


FAILURE_STATUSES = {
    "failed",
    "failure",
    "error",
    "exception",
    "aborted",
    "blocked",
    "critical_failure",
    "critical-failure",
}


def _event_status(event: Mapping[str, Any]) -> str:
    for key in ("status", "state", "kind", "type", "phase_status"):
        value = event.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip().lower()
    return ""


def _is_failure_event(event: Mapping[str, Any]) -> bool:
    status = _event_status(event)
    if status in FAILURE_STATUSES:
        return True
    if event.get("failed") is True or event.get("failure") is True:
        return True
    return bool(event.get("error") or event.get("exception"))


def _is_critical_failure(event: Mapping[str, Any]) -> bool:
    if event.get("critical") is True or event.get("critical_failure") is True:
        return True
    severity = event.get("severity", event.get("level"))
    if isinstance(severity, str) and severity.strip().lower() in {"critical", "fatal"}:
        return True
    if _event_status(event) in {"critical_failure", "critical-failure"}:
        return True
    return False


def _event_timestamp(value: Any) -> float | None:
    if isinstance(value, bool) or value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value) if math.isfinite(float(value)) else None
    if not isinstance(value, str) or not value.strip():
        return None
    text = value.strip()
    try:
        return float(text)
    except ValueError:
        pass
    try:
        parsed = _datetime.datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=_datetime.timezone.utc)
    return parsed.timestamp()


def _event_sequence(event: Mapping[str, Any]) -> float | None:
    for key in ("sequence", "seq", "order", "index"):
        value = event.get(key)
        if isinstance(value, bool) or value is None:
            continue
        try:
            number = float(value)
        except (TypeError, ValueError):
            continue
        if math.isfinite(number):
            return number
    return None


def _normalise_events(events: Any) -> list[Mapping[str, Any]]:
    if isinstance(events, Mapping):
        for key in ("events", "stage_events", "error_logs"):
            if key in events:
                events = events[key]
                break
        else:
            events = [events]
    if isinstance(events, (str, bytes)):
        _fail("events must be an iterable of event objects", "invalid_events")
    try:
        values = list(events)
    except TypeError:
        _fail("events must be an iterable of event objects", "invalid_events")
    if not all(isinstance(item, Mapping) for item in values):
        _fail("each event must be an object", "invalid_event")
    return values


def _event_run_ref(event: Mapping[str, Any]) -> Any:
    for key in ("run_ref", "run_reference", "run_id"):
        if key in event:
            return event[key]
    return None


def capture_earliest_failure_state(
    events: Any,
    *,
    run_ref: Any = None,
    ordered: bool = False,
) -> dict[str, Any]:
    """Return the first recorded failure only when its order is evidenced."""

    values = _normalise_events(events)
    candidates = [(index, event) for index, event in enumerate(values) if _is_failure_event(event)]
    if not candidates:
        _fail("no failed event was supplied", "no_failure")

    requested_ref = _validate_run_ref(run_ref) if run_ref is not None else None
    observed_refs = []
    for _, event in candidates:
        event_ref = _event_run_ref(event)
        if event_ref is not None:
            observed_refs.append(_validate_run_ref(event_ref, "event.run_ref"))
    if requested_ref is not None and any(item != requested_ref for item in observed_refs):
        _fail("failure candidates contain a different run_ref", "run_ref_mismatch")
    if requested_ref is None and len(set(observed_refs)) > 1:
        _fail("failure candidates contain multiple run_ref values", "run_ref_mismatch")
    result_ref = requested_ref or (observed_refs[0] if observed_refs else None)

    timestamped = [
        (
            index,
            event,
            _event_timestamp(event.get("timestamp", event.get("time", event.get("occurred_at")))),
        )
        for index, event in candidates
    ]
    sequence_values = [_event_sequence(event) for _, event in candidates]
    timestamp_values = [value for _, _, value in timestamped]
    if all(value is not None for value in timestamp_values):
        if len(set(timestamp_values)) != len(timestamp_values):
            if not all(value is not None for value in sequence_values) or len(set(sequence_values)) != len(sequence_values):
                _fail("failure timestamps do not establish a unique order", "ambiguous_order")
        ordered = sorted(
            timestamped,
            key=lambda item: (
                item[2],
                _event_sequence(item[1]) if _event_sequence(item[1]) is not None else float("inf"),
                item[0],
            ),
        )
        ordering_basis = "timestamp"
    elif all(value is not None for value in sequence_values):
        if len(set(sequence_values)) != len(sequence_values):
            _fail("failure sequence values do not establish a unique order", "ambiguous_order")
        ordered = sorted(
            ((index, event, None) for index, event in candidates),
            key=lambda item: (
                _event_sequence(item[1]),
                item[0],
            ),
        )
        ordering_basis = "sequence"
    elif len(candidates) == 1:
        ordered = [(candidates[0][0], candidates[0][1], None)]
        ordering_basis = "single_event"
    elif ordered:
        ordered = [(index, event, None) for index, event in candidates]
        ordering_basis = "explicit_input_order"
    else:
        _fail("failure candidates do not provide a complete comparable order", "ambiguous_order")

    original_index, earliest, timestamp = ordered[0]
    result = {
        "action_id": "EX-12",
        "status": "passed",
        "failure_event": copy.deepcopy(dict(earliest)),
        "event": copy.deepcopy(dict(earliest)),
        "earliest_failure": copy.deepcopy(dict(earliest)),
        "source_event_index": original_index,
        "ordering_basis": ordering_basis,
        "ordering_timestamp": timestamp,
        "root_cause_inferred": False,
        "claim_boundary": "earliest recorded failure only; no root cause substitution",
        "evidence_level": "host_checked",
    }
    if result_ref is not None:
        result["run_ref"] = result_ref
    return result


def block_save_after_critical_failure(
    failure_event: Any = None,
    saver: Callable[[], Any] | None = None,
    *,
    events: Any = None,
    save_callback: Callable[[], Any] | None = None,
    critical_failure: Any = None,
    run_ref: Any = None,
) -> dict[str, Any]:
    """Return a save decision without invoking a save callback.

    A critical event returns ``blocked``; a known non-critical failure returns
    ``eligible``.  Actual saving belongs to EX-14 and is intentionally never
    performed here, even when a callback is supplied.
    """

    supplied = events if events is not None else failure_event
    values = []
    if critical_failure is True:
        values = [{"status": "critical_failure", "critical": True}]
    elif isinstance(critical_failure, Mapping):
        values = [critical_failure]
    elif supplied is not None:
        values = _normalise_events(supplied)
    if not values:
        _fail("a failure event is required for EX-13", "unknown_failure_state")
    failures = [event for event in values if _is_failure_event(event) or _is_critical_failure(event)]
    if not failures:
        _fail("failure state is unknown or not failed", "unknown_failure_state")
    critical_event = next((event for event in failures if _is_critical_failure(event)), None)
    if critical_event is not None:
        result = {
            "action_id": "EX-13",
            "status": "blocked",
            "save_state": "blocked_after_critical_failure",
            "save_allowed": False,
            "save_called": False,
            "save_callback_ignored": True,
            "critical_failure": copy.deepcopy(dict(critical_event)),
            "evidence_level": "host_checked",
        }
        if run_ref is not None:
            result["run_ref"] = _validate_run_ref(run_ref)
        return result
    result = {
        "action_id": "EX-13",
        "status": "eligible",
        "save_state": "eligible_but_not_saved",
        "save_allowed": True,
        "save_called": False,
        "save_callback_ignored": True,
        "evidence_level": "host_checked",
    }
    if run_ref is not None:
        result["run_ref"] = _validate_run_ref(run_ref)
    return result


def _ownership_ref(ownership: Any, artifact_run_ref: Any) -> str | None:
    if artifact_run_ref is not None:
        return _validate_run_ref(artifact_run_ref, "artifact_run_ref")
    if isinstance(ownership, str):
        return _validate_run_ref(ownership, "ownership")
    if isinstance(ownership, Mapping):
        if ownership.get("owned") is False or ownership.get("run_owned") is False:
            return None
        value = ownership.get("run_ref", ownership.get("owner_ref", ownership.get("run_id")))
        if value is not None:
            return _validate_run_ref(value, "ownership.run_ref")
    return None


def _failure_record_matches(record: Any, target: Path) -> bool:
    if not isinstance(record, Mapping):
        return False
    status = _event_status(record)
    if not (
        status in FAILURE_STATUSES
        or record.get("failed") is True
        or record.get("failure") is True
        or record.get("critical") is True
        or record.get("critical_failure") is True
        or record.get("failure_id")
        or record.get("error")
    ):
        return False
    for key in ("path", "artifact_path", "failed_artifact", "output_path"):
        if key in record and record[key] is not None:
            try:
                if _path_key(_path(record[key], key)) != _path_key(target):
                    return False
            except HostActionError:
                return False
            break
    return True


def remove_run_owned_failed_artifact(
    artifact_path: Any = None,
    run_root: Any = None,
    *,
    path: Any = None,
    run_ref: Any = None,
    ownership: Any = None,
    artifact_run_ref: Any = None,
    failure_record: Any = None,
    expected_sha256: Any = None,
    expected_hash: Any = None,
    baseline_path: Any = None,
    baseline_paths: Any = None,
    evidence_paths: Any = None,
    evidence_path: Any = None,
    quarantine_dir: Any = None,
    mode: str = "quarantine",
) -> dict[str, Any]:
    """Quarantine or unlink exactly one owned failed regular file.

    Ownership, failure binding, hash, run-root containment, and reserved-path
    checks all precede the mutation.  Quarantine is the default and no
    recursive deletion is used.
    """

    target_value = artifact_path if artifact_path is not None else path
    if target_value is None:
        _fail("artifact_path is required", "missing_artifact")
    if run_root is None:
        _fail("run_root is required", "missing_run_root")
    ref = _validate_run_ref(run_ref)
    owner = _ownership_ref(ownership, artifact_run_ref)
    if owner != ref:
        _fail("artifact ownership does not match run_ref", "ownership_mismatch")
    if not _failure_record_matches(failure_record, _path(target_value, "artifact_path")):
        _fail("failure_record must identify this failed artifact", "invalid_failure_record")
    expected_value = expected_sha256 if expected_sha256 is not None else expected_hash
    expected = _validate_sha256(expected_value, "expected_sha256")

    root = _path(run_root, "run_root")
    _assert_directory(root, "run_root")
    target = _path(target_value, "artifact_path")
    _assert_inside(target, root, "artifact_path")
    _assert_regular_file(target, "artifact_path")
    reserved = []
    baselines = []
    if baseline_path is not None:
        baselines.append(_path(baseline_path, "baseline_path"))
    baselines.extend(_as_path_list(baseline_paths, "baseline_paths"))
    for baseline_item in baselines:
        _assert_no_symlink_components(baseline_item, "baseline_path")
        reserved.append(baseline_item)
    evidence = _as_path_list(evidence_paths, "evidence_paths")
    evidence.extend(_as_path_list(evidence_path, "evidence_path"))
    for item in evidence:
        _assert_no_symlink_components(item, "evidence path")
        reserved.append(item)
    for item in reserved:
        if _reserved_collision(target, item):
            _fail("failed artifact is a baseline/evidence path", "reserved_path_collision")

    actual = _sha256(target)
    if actual != expected:
        _fail("failed artifact hash does not match expected_sha256", "hash_mismatch")

    operation = str(mode).strip().lower().replace("-", "_")
    if operation in {"move", "quarantine"}:
        qdir = _path(quarantine_dir, "quarantine_dir") if quarantine_dir is not None else root / ".quarantine"
        _assert_inside(qdir, root, "quarantine_dir")
        _assert_no_symlink_components(qdir, "quarantine_dir")
        for reserved_path in reserved:
            if _reserved_collision(qdir, reserved_path):
                _fail("quarantine path would overwrite baseline/evidence", "reserved_path_collision")
        if qdir.exists() and not qdir.is_dir():
            _fail("quarantine_dir must be a directory", "invalid_quarantine_path")
        if not qdir.exists():
            qdir.mkdir(parents=False, exist_ok=False)
        destination = qdir / (target.stem + ".failed-" + actual[:12] + target.suffix)
        for reserved_path in reserved:
            if _reserved_collision(destination, reserved_path):
                _fail("quarantine destination would overwrite baseline/evidence", "reserved_path_collision")
        _assert_new_file_path(destination, "quarantine destination")
        target.rename(destination)
        if _sha256(destination) != actual:
            # The move is within one run root; restore the original exact path
            # before reporting an integrity failure.
            destination.rename(target)
            _fail("quarantine hash verification failed", "quarantine_hash_mismatch")
        return {
            "action_id": "ER-11",
            "status": "quarantined",
            "artifact_path": str(target),
            "quarantine_path": str(destination),
            "sha256": actual,
            "ownership_verified": True,
            "failure_record_preserved": True,
            "recoverable": True,
            "recursive": False,
            "evidence_level": "host_checked",
            "run_ref": ref,
        }
    if operation not in {"delete", "unlink", "remove"}:
        _fail("unsupported cleanup mode: %s" % mode, "invalid_cleanup_mode")
    target.unlink()
    return {
        "action_id": "ER-11",
        "status": "deleted",
        "artifact_path": str(target),
        "sha256": actual,
        "ownership_verified": True,
        "failure_record_preserved": True,
        "recoverable": False,
        "recursive": False,
        "evidence_level": "host_checked",
        "run_ref": ref,
    }


def confirm_control_authorization(
    authorization: Any,
    task_scope: Any = None,
    *,
    run_ref: Any = None,
) -> dict[str, Any]:
    """Check authorization record shape; do not self-authorize from JSON."""

    if not isinstance(authorization, Mapping):
        _fail("authorization must be a structured record", "invalid_authorization")
    if authorization.get("authorized") is not True:
        _fail("authorization record is not explicitly authorized", "authorization_missing")
    scope = authorization.get("scope", authorization.get("task_scope"))
    if scope is None:
        _fail("authorization scope is required", "authorization_scope_missing")
    if task_scope is not None:
        requested = {task_scope} if isinstance(task_scope, str) else set(task_scope)
        granted = {scope} if isinstance(scope, str) else set(scope)
        if not requested.issubset(granted):
            _fail("authorization scope does not cover requested task", "authorization_scope_mismatch")
    if run_ref is not None:
        ref = _validate_run_ref(run_ref)
        record_ref = authorization.get("run_ref")
        if record_ref is not None and record_ref != ref:
            _fail("authorization run_ref does not match current run", "authorization_run_mismatch")
    return {
        "action_id": "EX-01",
        "status": "passed",
        "authorization_structure_valid": True,
        "authorized_by_caller": True,
        "self_authorization": False,
        "caller_must_supply_trusted_authorization": True,
        "evidence_level": "host_checked",
    }


ACTION_HANDLERS: dict[str, Callable[..., dict[str, Any]]] = {
    "EX-01": confirm_control_authorization,
    "EX-05": copy_baseline_model,
    "EX-07": verify_run_output_path,
    "EX-11": record_executed_artifact_identity,
    "EX-12": capture_earliest_failure_state,
    "EX-13": block_save_after_critical_failure,
    "ER-11": remove_run_owned_failed_artifact,
}

_ACTION_ALIASES = {
    "CONFIRM-CONTROL-AUTHORIZATION": "EX-01",
    "COPY-BASELINE-MODEL": "EX-05",
    "VERIFY-RUN-OUTPUT-PATH": "EX-07",
    "RECORD-EXECUTED-ARTIFACT-IDENTITY": "EX-11",
    "CAPTURE-EARLIEST-FAILURE-STATE": "EX-12",
    "BLOCK-SAVE-AFTER-CRITICAL-FAILURE": "EX-13",
    "REMOVE-RUN-OWNED-FAILED-ARTIFACT": "ER-11",
}


def _normalise_action_id(action_id: Any) -> str:
    if not isinstance(action_id, str) or not action_id.strip():
        _fail("action_id must be a non-empty string", "unknown_action")
    value = action_id.strip().upper().replace("_", "-")
    if re.fullmatch(r"(?:EX|ER)-?\d+", value):
        value = value.replace("-", "")
        value = value[:2] + "-" + value[2:]
    return _ACTION_ALIASES.get(value, value)


def dispatch(action_id: Any, payload: Mapping[str, Any] | None = None, **kwargs: Any) -> dict[str, Any]:
    """Dispatch exactly one host action by catalog ID or operation name."""

    if isinstance(action_id, Mapping):
        record = action_id
        action_id = record.get("action_id", record.get("id", record.get("operation")))
        embedded = record.get("payload", record.get("inputs", {}))
        if payload is not None or kwargs:
            _fail("action record cannot be combined with explicit payload", "invalid_dispatch")
        payload = embedded
    action = _normalise_action_id(action_id)
    handler = ACTION_HANDLERS.get(action)
    if handler is None:
        _fail("unsupported execution host action: %s" % action_id, "unknown_action")
    if payload is None:
        arguments: dict[str, Any] = {}
    elif isinstance(payload, Mapping):
        arguments = dict(payload)
    else:
        _fail("payload must be a mapping", "invalid_dispatch")
        raise AssertionError("unreachable")
    overlap = set(arguments).intersection(kwargs)
    if overlap:
        _fail("duplicate dispatch arguments: %s" % ", ".join(sorted(overlap)), "invalid_dispatch")
    arguments.update(kwargs)
    return handler(**arguments)


# Explicit aliases keep the function surface discoverable without making the
# dispatcher a multi-action transaction.
ex05_copy_baseline_model = copy_baseline_model
ex07_verify_run_output_path = verify_run_output_path
ex11_record_executed_artifact_identity = record_executed_artifact_identity
ex12_capture_earliest_failure_state = capture_earliest_failure_state
ex13_block_save_after_critical_failure = block_save_after_critical_failure
er11_remove_run_owned_failed_artifact = remove_run_owned_failed_artifact
