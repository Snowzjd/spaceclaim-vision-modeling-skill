#!/usr/bin/env python3
"""Package UTF-8 IronPython source as a minimal SpaceClaim ``.scscript``.

SpaceClaim script files are ZIP packages whose executable source is stored in
the ``_script`` member.  This helper deliberately creates the smallest package
used by a V21 new-script document; it does not run SpaceClaim or claim that the
source is geometrically valid.

The archive bytes are reproducible for identical inputs.  In particular, the
member order, ZIP timestamps, version fields, compression choices, and
permissions are fixed.  Existing output is protected unless ``force=True`` is
requested explicitly.
"""

from __future__ import annotations

import argparse
import io
import os
import re
import sys
import zipfile
from pathlib import Path
from typing import Union


PathLike = Union[str, os.PathLike[str]]

MEMBER_ORDER = ("_script", "_apiVersion", "_smartVariableVersion", "[Content_Types].xml")
DEFAULT_API_VERSION = "21"
DEFAULT_SMART_VARIABLE_VERSION = "2"
DETERMINISTIC_TIMESTAMP = (1980, 1, 1, 0, 0, 0)

# This is the content-types part emitted by the minimal V21 script document.
# The UTF-8 BOM is intentional and is retained because native documents use it.
CONTENT_TYPES_XML = (
    b"\xef\xbb\xbf<?xml version=\"1.0\" encoding=\"utf-8\"?>"
    b"<Types xmlns=\"http://schemas.openxmlformats.org/package/2006/content-types\">"
    b"<Override PartName=\"/_script\" ContentType=\"text/plain\" />"
    b"<Override PartName=\"/_apiVersion\" ContentType=\"text/plain\" />"
    b"<Override PartName=\"/_smartVariableVersion\" ContentType=\"text/plain\" />"
    b"</Types>"
)

_ASCII_DIGITS = re.compile(r"^[0-9]+$")
_CENTRAL_DIRECTORY_SIGNATURE = b"PK\x01\x02"
_END_OF_CENTRAL_DIRECTORY_SIGNATURE = b"PK\x05\x06"
_CENTRAL_DIRECTORY_HEADER_SIZE = 46


def _validate_numeric(value: object, name: str) -> str:
    """Return a decimal version string, rejecting non-ASCII digits."""

    if isinstance(value, bool):
        raise ValueError("%s must contain digits only" % name)
    text = str(value)
    if not _ASCII_DIGITS.fullmatch(text):
        raise ValueError("%s must contain digits only" % name)
    return text


def _canonical_path(path: PathLike) -> str:
    # normcase is needed for the case-insensitive Windows filesystem.  realpath
    # also catches an output symlink that resolves to the source file.
    return os.path.normcase(os.path.realpath(os.path.abspath(os.fspath(path))))


def _zip_info(name: str, compression: int) -> zipfile.ZipInfo:
    """Create a fixed metadata record for one archive member.

    Python's ``ZipFile`` fills in host-dependent permissions when
    ``external_attr`` is zero.  A non-zero placeholder prevents that default;
    ``_zero_central_directory_permissions`` normalizes the central directory to
    the zero permission field used by native SpaceClaim packages.
    """

    info = zipfile.ZipInfo(filename=name, date_time=DETERMINISTIC_TIMESTAMP)
    info.compress_type = compression
    info.create_system = 0
    info.create_version = 45
    info.extract_version = 20 if compression == zipfile.ZIP_DEFLATED else 10
    info.external_attr = 1
    info.internal_attr = 0
    info.flag_bits = 0
    return info


def _zero_central_directory_permissions(payload: bytes, member_count: int) -> bytes:
    """Set every central-directory external-attribute field to zero.

    ``zipfile`` otherwise inserts a platform-specific default mode even when a
    ``ZipInfo`` object was supplied.  The local file headers contain no such
    field, so changing the central records is sufficient and keeps the archive
    readable by normal ZIP tooling.
    """

    data = bytearray(payload)
    # The classic EOCD record stores the central-directory offset at +16.  We
    # deliberately disable ZIP64 above, so this offset is unambiguous and does
    # not depend on searching compressed member bytes for a coincidental magic
    # sequence.
    end_record = data.rfind(_END_OF_CENTRAL_DIRECTORY_SIGNATURE)
    if end_record < 0 or end_record + 20 > len(data):
        raise RuntimeError("could not locate ZIP end-of-central-directory record")
    position = int.from_bytes(data[end_record + 16 : end_record + 20], "little")
    found = 0
    while position >= 0 and position + _CENTRAL_DIRECTORY_HEADER_SIZE <= len(data):
        if data[position : position + 4] != _CENTRAL_DIRECTORY_SIGNATURE:
            break
        # Central-directory layout: filename length at +28, extra length +30,
        # comment length +32, and external attributes at +38.
        name_length = int.from_bytes(data[position + 28 : position + 30], "little")
        extra_length = int.from_bytes(data[position + 30 : position + 32], "little")
        comment_length = int.from_bytes(data[position + 32 : position + 34], "little")
        data[position + 38 : position + 42] = b"\x00\x00\x00\x00"
        found += 1
        position += (
            _CENTRAL_DIRECTORY_HEADER_SIZE
            + name_length
            + extra_length
            + comment_length
        )
        if found == member_count:
            break
        if data[position : position + 4] != _CENTRAL_DIRECTORY_SIGNATURE:
            break

    if found != member_count:
        raise RuntimeError(
            "could not normalize ZIP permissions: found %d of %d central records"
            % (found, member_count)
        )
    return bytes(data)


def _build_archive(source: bytes, api_version: str, smart_variable_version: str) -> bytes:
    """Build deterministic archive bytes from already validated member data."""

    members = (
        ("_script", source, zipfile.ZIP_DEFLATED),
        ("_apiVersion", api_version.encode("ascii"), zipfile.ZIP_DEFLATED),
        ("_smartVariableVersion", smart_variable_version.encode("ascii"), zipfile.ZIP_STORED),
        ("[Content_Types].xml", CONTENT_TYPES_XML, zipfile.ZIP_STORED),
    )
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, mode="w", allowZip64=False) as archive:
        for name, data, compression in members:
            archive.writestr(
                _zip_info(name, compression),
                data,
                compress_type=compression,
                compresslevel=9 if compression == zipfile.ZIP_DEFLATED else None,
            )
    return _zero_central_directory_permissions(buffer.getvalue(), len(members))


def package_scscript(
    source_path: PathLike,
    output_path: PathLike,
    *,
    api_version: object = DEFAULT_API_VERSION,
    smart_variable_version: object = DEFAULT_SMART_VARIABLE_VERSION,
    force: bool = False,
) -> Path:
    """Package a UTF-8 IronPython source file and return the output path.

    Parameters are paths, not source text.  The source bytes are preserved
    exactly after UTF-8 validation, including line endings and an optional BOM.
    ``api_version`` and ``smart_variable_version`` are stored as decimal ASCII
    strings; both must contain digits only so malformed metadata cannot be
    mistaken for a valid SpaceClaim package.
    """

    source = Path(source_path)
    output = Path(output_path)
    if _canonical_path(source) == _canonical_path(output):
        raise ValueError("source and output paths must be different")

    if output.exists() and not force:
        raise FileExistsError("refusing to overwrite existing output: %s" % output)

    api_text = _validate_numeric(api_version, "api_version")
    smart_text = _validate_numeric(smart_variable_version, "smart_variable_version")

    source_bytes = source.read_bytes()
    try:
        source_text = source_bytes.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ValueError("source must be UTF-8") from exc
    if not source_text.lstrip("\ufeff").strip():
        raise ValueError("source must not be empty")

    archive_bytes = _build_archive(source_bytes, api_text, smart_text)
    mode = "wb" if force else "xb"
    with output.open(mode) as stream:
        stream.write(archive_bytes)
    return output


# Explicit aliases keep the import surface convenient without changing the
# canonical function name used by the CLI and documentation.
build_scscript = package_scscript
create_scscript = package_scscript


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path, help="UTF-8 IronPython source file")
    parser.add_argument("output", type=Path, help="output .scscript archive")
    parser.add_argument(
        "--api",
        "--api-version",
        dest="api_version",
        default=DEFAULT_API_VERSION,
        help="SpaceClaim API version (digits only; default: %(default)s)",
    )
    parser.add_argument(
        "--smart",
        "--smart-variable-version",
        dest="smart_variable_version",
        default=DEFAULT_SMART_VARIABLE_VERSION,
        help="smart-variable metadata version (default: %(default)s)",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="allow replacement of an existing output archive",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        output = package_scscript(
            args.source,
            args.output,
            api_version=args.api_version,
            smart_variable_version=args.smart_variable_version,
            force=args.force,
        )
    except (OSError, ValueError, RuntimeError) as exc:
        print("error: %s" % exc, file=sys.stderr)
        return 2
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
