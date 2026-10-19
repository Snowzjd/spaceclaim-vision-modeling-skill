#!/usr/bin/env python3
"""Package isolated V21 action implementations; never launches SpaceClaim."""
from __future__ import annotations
import argparse
import ast
from pathlib import Path
from package_scscript import package_scscript

PACKAGE = Path(__file__).resolve().parents[1]
ACTIONS = PACKAGE / "assets/operation-templates/modeling-strategy-scripting/actions"


def assembled_source(action_path):
    common = (ACTIONS / "common.py").read_text(encoding="utf-8")
    source = action_path.read_text(encoding="utf-8")
    tree = ast.parse(source)
    functions = [node.name for node in tree.body if isinstance(node, ast.FunctionDef)]
    if functions != ["operation"] or any(not isinstance(node, ast.FunctionDef) for node in tree.body):
        raise ValueError("Action source must define exactly one operation function")
    footer = '\nif "ATOMIC_INPUT" not in globals() or not isinstance(ATOMIC_INPUT, dict):\n    raise ValueError("Supply this action contract input dictionary before execution")\nATOMIC_OUTPUT = operation(ATOMIC_INPUT)\n'
    return common + "\n\n" + source + footer


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("ids", nargs="*", help="Specific ma-NN IDs; defaults to all implemented actions")
    args = parser.parse_args(argv)
    sources = [ACTIONS / (ident.lower() + ".action.py") for ident in args.ids] if args.ids else sorted(ACTIONS.glob("ma-*.action.py"))
    for source in sources:
        # These are generated mechanical build artifacts, not editable sources.
        output = source.with_name(source.name.replace(".action.py", ".py"))
        output.write_text(assembled_source(source), encoding="utf-8", newline="\n")
        package_scscript(output, output.with_suffix(".scscript"), api_version="21", force=True)
        print(output.with_suffix(".scscript").name)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
