"""Check the installed package and host dependencies, without controlling CAD.

Run after installation/update, not between mouse actions. A host pass is NOT
proof of controller availability, licensing, visual ability or model correctness.
"""
from __future__ import annotations

import argparse
import ast
from collections import Counter
import hashlib
import importlib.metadata
import json
from pathlib import Path
import sys
import zipfile

from resolve_operation_artifact import resolve_artifact

PACKAGE = Path(__file__).resolve().parents[1]
MODES = {'host_tool', 'reasoning_guidance', 'spaceclaim_scscript', 'computer_use'}
CAD_IMPORTS = {'__future__', 'SpaceClaim', 'System', 'math', 'os', 'hashlib'}


def sha256(path):
    with path.open('rb') as stream:
        digest = hashlib.file_digest(stream, 'sha256')
    return digest.hexdigest()


def inspect_package(package=PACKAGE):
    """Resolve every registered resource from the install root, not the checkout."""
    package = Path(package).resolve()
    issues, operations = [], []
    counts = Counter()
    checked = {}
    repository_refs = set()

    def check_ref(ref, prefixed=True):
        if not isinstance(ref, dict) or not isinstance(ref.get('path'), str):
            raise ValueError('Expected an artifact reference')
        name = ref['path'] if prefixed else 'spaceclaim-vision-modeling/' + ref['path']
        if not name.startswith('spaceclaim-vision-modeling/'):
            # Historical tests are maintainer evidence, not installed implementation.
            if name.startswith('tests/'):
                repository_refs.add(name)
                return None
            raise ValueError('Undeclared resource outside package: ' + name)
        result = resolve_artifact(name, package_root=package)
        if result['status'] != 'resolved':
            raise ValueError(name + ': ' + result['reason'])
        path = Path(result['path'])
        if name not in checked:
            checked[name] = sha256(path)
        digest = checked[name]
        expected = ref.get('sha256')
        if expected is not None and (not isinstance(expected, str) or digest != expected.lower()):
            raise ValueError('Hash mismatch: ' + name)
        return path

    registry = json.loads((package / 'references/operation-registry.json').read_text(encoding='utf-8'))
    catalog = json.loads((package / 'references/operation-catalog.json').read_text(encoding='utf-8'))
    entries = registry['operations']
    expected_ids = [item['registry_operation_id'] for item in catalog['operations']]
    actual_ids = [item['operation_id'] for item in entries]
    if len(set(actual_ids)) != len(actual_ids) or set(actual_ids) != set(expected_ids):
        issues.append('Catalog/registry operation coverage differs')
    for entry in entries:
        identity = entry['operation_id']
        row = {'operation_id': identity, 'lifecycle': entry['status'], 'resource_status': 'passed'}
        try:
            path = check_ref({'path': entry['template_path'], 'sha256': entry['template_sha256']}, False)
            template = json.loads(path.read_text(encoding='utf-8'))
            mode = template['implementation']['mode']
            if mode not in MODES:
                raise ValueError('Unknown implementation mode: ' + str(mode))
            counts[mode] += 1
            row['mode'] = mode
            if template['operation_id'] != identity:
                raise ValueError('Template identity mismatch')
            for link in template['artifact_links']:
                check_ref(link)
            primary = template['implementation'].get('primary_artifact')
            if primary:
                path = check_ref({'path': primary})
                if path is None:
                    raise ValueError('Primary implementation cannot be repository-only')
            elif mode != 'reasoning_guidance':
                raise ValueError('Missing primary implementation')
            elif not any('/atomic-guidance/' in x['path'] for x in template['artifact_links']):
                raise ValueError('Missing single-action reasoning guidance')
            if mode == 'spaceclaim_scscript':
                with zipfile.ZipFile(path) as archive:
                    if archive.read('_apiVersion').strip() != b'21':
                        raise ValueError('Unsupported action API metadata')
                    tree = ast.parse(archive.read('_script').decode('utf-8-sig'))
                for node in ast.walk(tree):
                    modules = ([a.name for a in node.names] if isinstance(node, ast.Import)
                               else [node.module or ''] if isinstance(node, ast.ImportFrom) else [])
                    if any(m.split('.')[0] not in CAD_IMPORTS for m in modules):
                        raise ValueError('Undeclared script import: ' + ', '.join(modules))
            row['external_requirements'] = {
                'host_tool': ['host_python'],
                'reasoning_guidance': ['agent_reasoning', 'source_access', 'host_python', 'jsonschema'],
                'spaceclaim_scscript': ['spaceclaim_v21', 'computer_use_runtime'],
                'computer_use': ['agent_vision', 'computer_use_runtime', 'spaceclaim_v21'],
            }[mode]
        except (KeyError, TypeError, ValueError, OSError, SyntaxError, zipfile.BadZipFile) as error:
            row['resource_status'] = 'failed'
            row['reason'] = str(error)
            issues.append(identity + ': ' + str(error))
        operations.append(row)
    return {'issues': issues, 'operation_count': len(operations), 'modes': dict(counts),
            'package_files_checked': len(checked), 'repository_only_test_files': sorted(repository_refs),
            'operations': operations}


def check_environment():
    issues = []
    if sys.version_info[:2] != (3, 12):
        issues.append('Use the documented CPython 3.12.x host environment; this checker does not certify other versions')
    try:
        import jsonschema
        installed = importlib.metadata.version('jsonschema')
        jsonschema.Draft202012Validator.check_schema({'type': 'object'})
    except (ImportError, importlib.metadata.PackageNotFoundError) as error:
        installed = None
        issues.append('Missing jsonschema: run the README virtual-environment installation: ' + str(error))
    try:
        for line in (PACKAGE / 'requirements.txt').read_text(encoding='utf-8').splitlines():
            requirement = line.split('#', 1)[0].strip()
            if not requirement:
                continue
            name, expected = requirement.split('==', 1)
            try:
                actual = importlib.metadata.version(name)
            except importlib.metadata.PackageNotFoundError:
                actual = None
            if actual != expected:
                issues.append('Install requirements.txt: %s requires %s, found %s' % (name, expected, actual))
    except (OSError, ValueError) as error:
        issues.append('Cannot read pinned runtime requirements: ' + str(error))
    return {'python': sys.version.split()[0], 'python_executable': sys.executable,
            'jsonschema': installed, 'issues': issues}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--package-root', type=Path, default=PACKAGE)
    parser.add_argument('--spaceclaim-exe', type=Path)
    parser.add_argument('--details', action='store_true', help='Include per-operation dependency rows')
    args = parser.parse_args(argv)
    environment = check_environment()
    try:
        package = inspect_package(args.package_root)
    except (OSError, ValueError, KeyError, TypeError) as error:
        package = {'issues': [str(error)], 'operations': []}
    issues = environment['issues'] + package['issues']
    executable = None
    if args.spaceclaim_exe is not None:
        exe = args.spaceclaim_exe
        if not exe.is_absolute() or not exe.is_file() or exe.name.lower() != 'spaceclaim.exe':
            issues.append('Supply an existing absolute SpaceClaim.exe path')
        else:
            executable = str(exe.resolve())
    if not args.details:
        package.pop('operations', None)
    result = {'status': 'failed' if issues else 'host_ready', 'environment': environment,
              'package': package, 'issues': issues, 'spaceclaim_executable': executable,
              'interactive_setup': 'not_tested', 'all_operations_verified': False,
              'boundary': 'Installed resources and host dependencies only. Executable presence is not API/license proof. Complete the README live setup check before desktop work; inspect exact operation evidence and controller routes.'}
    print(json.dumps(result, indent=2))
    return 1 if issues else 0


if __name__ == '__main__':
    raise SystemExit(main())
