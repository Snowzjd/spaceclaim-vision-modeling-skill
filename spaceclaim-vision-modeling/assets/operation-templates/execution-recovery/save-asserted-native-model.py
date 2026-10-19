# Python Script, API Version = V21
# Editable packaging source. Supply ATOMIC_INPUT before loading the .scscript.
from SpaceClaim.Api.V21 import *
import hashlib
import os
from System.IO import File, FileAttributes


def operation(p):
    # New-output variant only. Baseline-copy overwrite needs a different policy.
    if p['expected_root'] != GetRootPart():
        raise ValueError('Active model differs from the asserted model')
    checks = p['critical_checks']
    if not isinstance(checks, list) or not checks:
        raise ValueError('Supply completed critical checks')
    names = set()
    for check in checks:
        if not isinstance(check, dict) or not check.get('id') or check.get('status') != 'passed':
            raise ValueError('Critical checks are incomplete or failed; save blocked')
        if check['id'] in names:
            raise ValueError('Duplicate critical-check identity')
        names.add(check['id'])
    root = os.path.normcase(os.path.abspath(p['run_root']))
    path = os.path.normcase(os.path.abspath(p['output_path']))
    if not os.path.isabs(p['run_root']) or not os.path.isabs(p['output_path']):
        raise ValueError('Use explicit absolute run-owned paths')
    if not path.startswith(root.rstrip('\\/') + os.sep) or not path.endswith('.scdoc'):
        raise ValueError('Native output must be inside the specified run root')
    if os.path.exists(path) or not os.path.isdir(os.path.dirname(path)):
        raise ValueError('This variant requires a new file in an existing directory')
    cursor = os.path.dirname(path)
    while cursor:
        if File.GetAttributes(cursor) & FileAttributes.ReparsePoint:
            raise ValueError('Reparse-point output ancestors are unsupported')
        parent = os.path.dirname(cursor)
        if parent == cursor:
            break
        cursor = parent
    DocumentSave.Execute(path)
    if not os.path.isfile(path) or os.path.getsize(path) == 0:
        raise RuntimeError('Native save did not produce a nonempty artifact')
    active_path = os.path.normcase(os.path.abspath(Window.ActiveWindow.Document.Path))
    if active_path != path:
        raise RuntimeError('Saved document identity differs from the output')
    with open(path, 'rb') as stream:
        digest = hashlib.sha256(stream.read()).hexdigest()
    return dict(path=path, sha256=digest, native_save='passed', native_reopen='not_tested')


if 'ATOMIC_INPUT' not in globals():
    raise ValueError('Supply ATOMIC_INPUT from the accepted execution contract')
ATOMIC_OUTPUT = operation(ATOMIC_INPUT)
