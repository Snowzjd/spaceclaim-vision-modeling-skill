#!/usr/bin/env python3
"""Build independent read-only V21 validation actions VA-04 through VA-18.

The builder never launches SpaceClaim.  Each action source is assembled with
the common read-only guards, and the exact assembled source is packaged as a
minimal V21 ``.scscript``.  A host harness must inject one explicit
``ATOMIC_INPUT`` dictionary before executing an archive.
"""
from __future__ import annotations

import argparse
import ast
from pathlib import Path
import sys

try:
    from package_scscript import package_scscript
except ModuleNotFoundError:
    # Keep spec-based host tests and direct CLI execution equivalent.
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from package_scscript import package_scscript


PACKAGE = Path(__file__).resolve().parents[1]
ACTIONS = PACKAGE / "assets" / "operation-templates" / "validation-visual-review" / "actions"
ACTION_IDS = tuple("VA-%02d" % number for number in range(4, 19))


def _normalise_id(value):
    text = str(value).strip().upper()
    if text.isdigit():
        text = "VA-%02d" % int(text)
    if text not in ACTION_IDS:
        raise ValueError("Unsupported validation action: %s" % value)
    return text


def _source_path(action_id):
    return ACTIONS / (action_id.lower() + ".action.py")


def assembled_source(action_path):
    """Return one standalone IronPython source for an action."""
    common_path = ACTIONS / "common.py"
    common = common_path.read_text(encoding="utf-8")
    source = action_path.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(action_path))
    operations = [node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "operation"]
    if len(operations) != 1:
        raise ValueError("Validation action must define exactly one operation function")
    if not any(isinstance(node, ast.Assign) and any(
        isinstance(target, ast.Name) and target.id == "ACTION_ID"
        for target in node.targets
    ) for node in tree.body):
        raise ValueError("Validation action must declare ACTION_ID")
    footer = (
        "\n"
        "# ATOMIC_INPUT is intentionally injected by the host harness; this is\n"
        "# the only execution entry point for this independent action.\n"
        "if \"ATOMIC_INPUT\" not in globals() or not isinstance(ATOMIC_INPUT, dict):\n"
        "    raise ValueError(\"Supply one explicit ATOMIC_INPUT dictionary before execution\")\n"
        "ATOMIC_OUTPUT = operation(ATOMIC_INPUT)\n"
    )
    return common.rstrip() + "\n\n" + source.rstrip() + footer


def build(ids=None, *, force=True):
    selected = ACTION_IDS if ids is None else tuple(_normalise_id(value) for value in ids)
    outputs = []
    for action_id in selected:
        source_path = _source_path(action_id)
        if not source_path.is_file():
            raise FileNotFoundError("Missing validation action source: %s" % source_path)
        output = source_path.with_name(action_id.lower() + ".py")
        output.write_text(assembled_source(source_path), encoding="utf-8", newline="\n")
        archive = output.with_suffix(".scscript")
        package_scscript(output, archive, api_version="21", force=force)
        outputs.append((output, archive))
    return outputs


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("ids", nargs="*", help="Specific VA-04..VA-18 IDs; defaults to all")
    parser.add_argument("--no-force", action="store_true", help="Refuse existing archives")
    args = parser.parse_args(argv)
    for _, archive in build(args.ids or None, force=not args.no_force):
        print(archive)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
