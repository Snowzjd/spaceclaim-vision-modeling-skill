"""Installed-package isolation checks, not live Computer Use/CAD acceptance."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / 'spaceclaim-vision-modeling'
sys.path.insert(0, str(PACKAGE / 'scripts'))
import check_installation as C


class InstallationIndependenceTests(unittest.TestCase):
    def test_all_registered_resources_available_without_repository_tests(self):
        result = C.inspect_package()
        self.assertEqual([], result['issues'])
        self.assertEqual(139, result['operation_count'])
        self.assertEqual({'host_tool': 16, 'reasoning_guidance': 38,
                          'computer_use': 34, 'spaceclaim_scscript': 51}, result['modes'])
        self.assertTrue(all(x['resource_status'] == 'passed' for x in result['operations']))

    def test_missing_dependency_fails_with_install_instruction(self):
        env = dict(os.environ, PYTHONUTF8='1')
        # -I excludes script-directory imports; restore only the installed scripts,
        # never site-packages, then exercise the dependency check itself.
        code = 'import sys;sys.path.insert(0,%r);import check_installation;print(check_installation.check_environment())' % str(PACKAGE / 'scripts')
        result = subprocess.run([sys.executable, '-I', '-S', '-B', '-c', code],
                                capture_output=True, text=True, env=env)
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertIn('Missing jsonschema', result.stdout)
        self.assertIn('README', result.stdout)

    def test_wrong_python_profile_not_silently_accepted(self):
        with patch.object(C.sys, 'version_info', (3, 9, 0)):
            self.assertTrue(any('3.12' in x for x in C.check_environment()['issues']))

    def test_missing_or_corrupted_template_rejected(self):
        original = C.sha256
        with patch.object(C, 'sha256', side_effect=lambda path: '0' * 64 if path.name == 'package-scscript.json' else original(path)):
            result = C.inspect_package()
        self.assertTrue(any('Hash mismatch' in x for x in result['issues']))

    def test_cli_does_not_certify_unobserved_runtime(self):
        result = subprocess.run([sys.executable, '-B', str(PACKAGE / 'scripts/check_installation.py')],
                                capture_output=True, text=True)
        data = json.loads(result.stdout)
        # Developer Python need not be the documented venv; either exit must
        # preserve the unobserved CAD/controller boundary.
        self.assertFalse(data['all_operations_verified'])
        self.assertEqual('not_tested', data['interactive_setup'])

    def test_renamed_install_cli_works_without_checkout_or_cwd_assumptions(self):
        with tempfile.TemporaryDirectory(prefix='sc-installed-') as directory:
            root = Path(directory)
            installed = root / 'renamed skill'
            # Only registered package artifacts and installed runtime resources;
            # do not copy repository tests or machine-local ignored development data.
            names = set()
            names.add('requirements.txt')
            registry = json.loads((PACKAGE / 'references/operation-registry.json').read_text(encoding='utf-8'))
            names.update(p.relative_to(PACKAGE).as_posix() for p in (PACKAGE / 'scripts').glob('*.py')
                         if p.name != 'generate_geometry_understanding_blind_set.py')
            names.update(p.relative_to(PACKAGE).as_posix() for p in (PACKAGE / 'references').rglob('*') if p.is_file())
            for entry in registry['operations']:
                names.add(entry['template_path'])
                template = json.loads((PACKAGE / entry['template_path']).read_text(encoding='utf-8'))
                for ref in template['artifact_links']:
                    if ref['path'].startswith('spaceclaim-vision-modeling/'):
                        names.add(ref['path'].split('/', 1)[1])
            names.add('assets/operation-templates/evaluation-fixtures/geometry-understanding/dimensions-ready.json')
            for name in names:
                destination = installed / name
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(PACKAGE / name, destination)
            result = C.inspect_package(installed)
            self.assertEqual([], result['issues'])
            self.assertFalse((root / 'tests').exists())
            self.assertFalse((root / 'spaceclaim-vision-modeling').exists())
            env = dict(os.environ, PYTHONUTF8='1', PYTHONDONTWRITEBYTECODE='1')
            env.pop('PYTHONPATH', None)
            env.pop('PYTHONHOME', None)
            probe = subprocess.run([sys.executable, '-B', str(installed / 'scripts/check_installation.py')],
                                   cwd=root, capture_output=True, text=True, env=env)
            self.assertEqual(0, probe.returncode, probe.stdout + probe.stderr)
            self.assertEqual('host_ready', json.loads(probe.stdout)['status'])
            fixture = installed / 'assets/operation-templates/evaluation-fixtures/geometry-understanding/dimensions-ready.json'
            cli = [sys.executable, '-B', str(installed / 'scripts/validate_geometry_understanding_outputs.py'), '--input', str(fixture)]
            run = subprocess.run(cli, cwd=root, capture_output=True, text=True, env=env)
            self.assertEqual(0, run.returncode, run.stdout + run.stderr)
            self.assertTrue(json.loads(run.stdout)['valid'])
            schema = root / 'own-schema.json'
            shutil.copyfile(installed / 'references/geometry-understanding-output.schema.json', schema)
            run = subprocess.run(cli + ['--schema', 'own-schema.json'], cwd=root,
                                 capture_output=True, text=True, env=env)
            self.assertEqual(0, run.returncode, run.stdout + run.stderr)


if __name__ == '__main__':
    unittest.main()
