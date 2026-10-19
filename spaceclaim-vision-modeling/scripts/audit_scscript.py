#!/usr/bin/env python3
"""Perform evidence-bounded static checks on a SpaceClaim .scscript archive.

This tool does not launch SpaceClaim and cannot prove geometry correctness.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import zipfile
from collections import Counter
from pathlib import Path, PurePosixPath
from typing import Any
from xml.etree import ElementTree


CORE_MEMBERS = ("_script", "_apiVersion", "_smartVariableVersion", "[Content_Types].xml")
CONTENT_TYPES_NAMESPACE = "http://schemas.openxmlformats.org/package/2006/content-types"
REQUIRED_CONTENT_TYPES = {
    "/_script": "text/plain",
    "/_apiVersion": "text/plain",
    "/_smartVariableVersion": "text/plain",
}
NUMBERED_ALIAS_PATTERN = re.compile(
    r"\b(?:Body|Face|Edge|DatumPlane|Component|Part)\d+\b"
)
WINDOWS_PATH_PATTERN = re.compile(r"[A-Za-z]:\\[^\r\n\"']+")
OPERATION_PATTERN = re.compile(r"\b[A-Za-z_]\w*(?:\.[A-Za-z_]\w*)+")
MAX_ARCHIVE_BYTES = 64 * 1024 * 1024
MAX_MEMBER_COUNT = 256
MAX_MEMBER_BYTES = 32 * 1024 * 1024


def _canonical_path(path: Path) -> str:
    """Return a case-normalized real path for destructive-output checks."""

    return os.path.normcase(os.path.realpath(os.path.abspath(os.fspath(path))))
MAX_TOTAL_UNCOMPRESSED_BYTES = 64 * 1024 * 1024
MAX_COMPRESSION_RATIO = 200.0


def mask_comments_and_strings(source: str) -> str:
    """Return *source* with comments and string literals replaced by spaces.

    ``.scscript`` files contain Python-like source, but they are ultimately
    consumed by a host application rather than by this interpreter.  Using a
    small lexical scanner instead of ``tokenize`` keeps the audit useful for
    scripts containing host-specific syntax or an incomplete edit.  Newline
    characters are retained so that line-oriented diagnostics remain stable.
    """

    chars = list(source)
    length = len(chars)
    index = 0
    state = "code"
    quote = ""
    triple = False

    def blank(position: int) -> None:
        if chars[position] not in "\r\n":
            chars[position] = " "

    while index < length:
        char = source[index]
        if state == "code":
            if char == "#":
                state = "comment"
                blank(index)
            elif char in "'\"":
                quote = char
                triple = source.startswith(char * 3, index)
                state = "string"
                blank(index)
                if triple:
                    blank(index + 1)
                    blank(index + 2)
                    index += 2
            index += 1
            continue

        if state == "comment":
            if char in "\r\n":
                state = "code"
            else:
                blank(index)
            index += 1
            continue

        # String state.  Preserve line breaks, but mask every other character
        # so that identifiers inside a literal cannot become audit tokens.
        if triple and source.startswith(quote * 3, index):
            blank(index)
            blank(index + 1)
            blank(index + 2)
            index += 3
            state = "code"
            continue
        if not triple and char == quote:
            blank(index)
            index += 1
            state = "code"
            continue
        if char == "\\":
            blank(index)
            index += 1
            if index < length:
                # A backslash-newline pair is legal in a Python-like string;
                # retain the newline while masking the escape marker.
                blank(index)
                index += 1
            continue
        blank(index)
        index += 1

    return "".join(chars)


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def decode_member(data: bytes) -> str:
    # SpaceClaim exports are commonly UTF-8, while older/host-generated
    # packages may use UTF-16 (with or without a BOM).  Keep a deterministic
    # fallback for opaque metadata members as well.
    if data.startswith((b"\xff\xfe", b"\xfe\xff")):
        try:
            return data.decode("utf-16")
        except UnicodeDecodeError:
            pass
    if len(data) >= 4:
        even_nuls = data[0::2].count(0)
        odd_nuls = data[1::2].count(0)
        pairs = max(1, len(data) // 2)
        if odd_nuls > pairs // 3 and even_nuls == 0:
            try:
                return data.decode("utf-16-le")
            except UnicodeDecodeError:
                pass
        if even_nuls > pairs // 3 and odd_nuls == 0:
            try:
                return data.decode("utf-16-be")
            except UnicodeDecodeError:
                pass
    for encoding in ("utf-8-sig", "utf-8", "utf-16"):
        try:
            return data.decode(encoding)
        except UnicodeDecodeError:
            continue
    return data.decode("latin-1")


def add_issue(
    issues: list[dict[str, str]], severity: str, code: str, message: str
) -> None:
    issues.append({"severity": severity, "code": code, "message": message})


def audit_archive(
    archive_path: Path,
    *,
    require_api: str | None = None,
    forbid_numbered_aliases: bool = False,
    required_operations: tuple[str, ...] = (),
    forbidden_operations: tuple[str, ...] = (),
) -> dict[str, Any]:
    issues: list[dict[str, str]] = []
    result: dict[str, Any] = {
        "schema_version": 1,
        "evidence_level": "static_archive_audit_only",
        "archive": str(archive_path.resolve()),
        "archive_sha256": None,
        "status": "failed",
        "members": {},
        "api_version": None,
        "smart_variable_version": None,
        "script_line_count": 0,
        "operation_counts": {},
        "numbered_aliases": [],
        "windows_backslash_paths": [],
        "issues": issues,
    }

    if not archive_path.is_file():
        add_issue(issues, "error", "archive_missing", "The .scscript file does not exist.")
        return result

    archive_size = archive_path.stat().st_size
    if archive_size > MAX_ARCHIVE_BYTES:
        add_issue(
            issues,
            "error",
            "archive_size_limit",
            "Archive size %d exceeds the %d byte safety limit."
            % (archive_size, MAX_ARCHIVE_BYTES),
        )
        return result

    result["archive_sha256"] = sha256_bytes(archive_path.read_bytes())

    try:
        with zipfile.ZipFile(archive_path, "r") as archive:
            member_infos = archive.infolist()
            member_names = [info.filename for info in member_infos]
            if len(member_infos) > MAX_MEMBER_COUNT:
                add_issue(
                    issues,
                    "error",
                    "member_count_limit",
                    "Archive has %d members; the safety limit is %d."
                    % (len(member_infos), MAX_MEMBER_COUNT),
                )

            duplicates = sorted(name for name, count in Counter(member_names).items() if count > 1)
            if duplicates:
                add_issue(
                    issues,
                    "error",
                    "duplicate_members",
                    "Duplicate archive members: %s" % ", ".join(duplicates),
                )

            total_uncompressed = 0
            for info in member_infos:
                path = PurePosixPath(info.filename.replace("\\", "/"))
                if path.is_absolute() or ".." in path.parts:
                    add_issue(
                        issues,
                        "error",
                        "unsafe_member_name",
                        "Unsafe archive member name: %s" % info.filename,
                    )
                if info.flag_bits & 0x1:
                    add_issue(
                        issues,
                        "error",
                        "encrypted_member",
                        "Encrypted archive member is not supported: %s" % info.filename,
                    )
                if info.file_size > MAX_MEMBER_BYTES:
                    add_issue(
                        issues,
                        "error",
                        "member_size_limit",
                        "Archive member %s exceeds the %d byte safety limit."
                        % (info.filename, MAX_MEMBER_BYTES),
                    )
                total_uncompressed += info.file_size
                if info.file_size and (
                    info.compress_size == 0
                    or float(info.file_size) / float(info.compress_size)
                    > MAX_COMPRESSION_RATIO
                ):
                    add_issue(
                        issues,
                        "error",
                        "compression_ratio_limit",
                        "Archive member %s exceeds the %.0f:1 compression-ratio safety limit."
                        % (info.filename, MAX_COMPRESSION_RATIO),
                    )

            if total_uncompressed > MAX_TOTAL_UNCOMPRESSED_BYTES:
                add_issue(
                    issues,
                    "error",
                    "uncompressed_size_limit",
                    "Archive expands to %d bytes; the safety limit is %d."
                    % (total_uncompressed, MAX_TOTAL_UNCOMPRESSED_BYTES),
                )

            if any(issue["severity"] == "error" for issue in issues):
                return result

            bad_member = archive.testzip()
            if bad_member is not None:
                add_issue(
                    issues,
                    "error",
                    "crc_mismatch",
                    "Archive member failed its CRC check: %s" % bad_member,
                )
                return result

            member_data: dict[str, bytes] = {}
            for name in sorted(set(member_names)):
                data = archive.read(name)
                member_data[name] = data
                result["members"][name] = {
                    "size": len(data),
                    "sha256": sha256_bytes(data),
                }
    except (OSError, RuntimeError, NotImplementedError, zipfile.BadZipFile) as exc:
        add_issue(issues, "error", "invalid_archive", str(exc))
        return result

    for name in CORE_MEMBERS:
        if name not in member_data:
            add_issue(issues, "error", "missing_member", "Required member missing: %s" % name)

    content_types_data = member_data.get("[Content_Types].xml")
    if content_types_data is not None:
        try:
            root = ElementTree.fromstring(content_types_data)
            overrides: dict[str, str] = {}
            for element in root.findall("{%s}Override" % CONTENT_TYPES_NAMESPACE):
                part_name = element.attrib.get("PartName", "")
                content_type = element.attrib.get("ContentType", "")
                if part_name in overrides:
                    add_issue(
                        issues,
                        "error",
                        "duplicate_content_type_override",
                        "Duplicate content-type override for %s." % part_name,
                    )
                overrides[part_name] = content_type
            for part_name, expected_type in REQUIRED_CONTENT_TYPES.items():
                actual_type = overrides.get(part_name)
                if actual_type != expected_type:
                    add_issue(
                        issues,
                        "error",
                        "content_type_override_missing",
                        "Expected %s to declare content type %s; found %s."
                        % (part_name, expected_type, actual_type or "<missing>"),
                    )
        except ElementTree.ParseError as exc:
            add_issue(
                issues,
                "error",
                "invalid_content_types_xml",
                "[Content_Types].xml is not well formed: %s" % exc,
            )

    if "_script" not in member_data:
        return result

    script = decode_member(member_data["_script"])
    result["script_line_count"] = len(script.splitlines())
    api_version = decode_member(member_data.get("_apiVersion", b"")).strip()
    smart_version = decode_member(member_data.get("_smartVariableVersion", b"")).strip()
    result["api_version"] = api_version or None
    result["smart_variable_version"] = smart_version or None

    if not script.strip():
        add_issue(issues, "error", "empty_script", "The _script member is empty.")
    if not api_version:
        add_issue(issues, "error", "empty_api_version", "The _apiVersion member is empty.")
    if not smart_version:
        add_issue(
            issues,
            "error",
            "empty_smart_variable_version",
            "The _smartVariableVersion member is empty.",
        )

    if require_api is not None and api_version != str(require_api):
        add_issue(
            issues,
            "error",
            "api_version_mismatch",
            "Expected API version %s, found %s." % (require_api, api_version or "<empty>"),
        )

    executable_source = mask_comments_and_strings(script)
    operation_counts = Counter(OPERATION_PATTERN.findall(executable_source))
    result["operation_counts"] = dict(sorted(operation_counts.items()))
    invalid_tokens = sorted(
        set(required_operations + forbidden_operations)
        - {token for token in required_operations + forbidden_operations if OPERATION_PATTERN.fullmatch(token)}
    )
    for token in invalid_tokens:
        add_issue(
            issues,
            "error",
            "invalid_operation_token",
            "Operation token is not a dotted identifier: %s" % token,
        )
    for token in required_operations:
        if token not in operation_counts:
            add_issue(
                issues,
                "error",
                "required_operation_missing",
                "Required operation token not found: %s" % token,
            )
    for token in forbidden_operations:
        if token in operation_counts:
            add_issue(
                issues,
                "error",
                "forbidden_operation_present",
                "Forbidden operation token found: %s" % token,
            )

    aliases = sorted(set(NUMBERED_ALIAS_PATTERN.findall(executable_source)))
    result["numbered_aliases"] = aliases
    user_objects_text = decode_member(member_data.get("_userScriptObjects", b""))
    user_object_aliases = set(NUMBERED_ALIAS_PATTERN.findall(user_objects_text))
    missing_alias_objects = [alias for alias in aliases if alias not in user_object_aliases]
    if missing_alias_objects:
        add_issue(
            issues,
            "error",
            "smart_variable_closure_missing",
            "Aliases absent from _userScriptObjects: %s" % ", ".join(missing_alias_objects),
        )
    if aliases:
        severity = "error" if forbid_numbered_aliases else "warning"
        add_issue(
            issues,
            severity,
            "topology_sensitive_aliases",
            "Recorded numbered aliases require replacement or same-topology validation: %s"
            % ", ".join(aliases),
        )

    paths = sorted(set(WINDOWS_PATH_PATTERN.findall(script)))
    result["windows_backslash_paths"] = paths
    if paths:
        add_issue(
            issues,
            "warning",
            "backslash_path_literals",
            "Windows backslash paths may trigger escape parsing in embedded Python; prefer forward slashes.",
        )

    result["status"] = (
        "failed" if any(issue["severity"] == "error" for issue in issues) else "passed"
    )
    return result


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("archive", type=Path, help="SpaceClaim .scscript archive")
    parser.add_argument("--report", type=Path, help="Optional JSON report path")
    parser.add_argument("--require-api", help="Required _apiVersion value, for example 21")
    parser.add_argument(
        "--forbid-numbered-aliases",
        action="store_true",
        help="Fail if recorded BodyN/FaceN-style aliases are present",
    )
    parser.add_argument(
        "--require-operation",
        action="append",
        default=[],
        help="Operation token that must appear; repeat as needed",
    )
    parser.add_argument(
        "--forbid-operation",
        action="append",
        default=[],
        help="Operation token that must not appear; repeat as needed",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    report = audit_archive(
        args.archive,
        require_api=args.require_api,
        forbid_numbered_aliases=args.forbid_numbered_aliases,
        required_operations=tuple(args.require_operation),
        forbidden_operations=tuple(args.forbid_operation),
    )
    report_conflicts_with_archive = bool(
        args.report
        and _canonical_path(args.report) == _canonical_path(args.archive)
    )
    if report_conflicts_with_archive:
        add_issue(
            report.setdefault("issues", []),
            "error",
            "report_path_collision",
            "The JSON report path resolves to the input archive; the archive was not overwritten.",
        )
        report["status"] = "failed"
    rendered = json.dumps(report, ensure_ascii=False, indent=2)
    print(rendered)
    if args.report and not report_conflicts_with_archive:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(rendered + "\n", encoding="utf-8")
    return 0 if report["status"] == "passed" else 2


if __name__ == "__main__":
    sys.exit(main())
