"""Host guard tests only; fake saver output is not a native model."""
import ast
import hashlib
import os
from pathlib import Path
import tempfile
from types import SimpleNamespace as NS
import unittest

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'spaceclaim-vision-modeling/assets/operation-templates/execution-recovery/save-asserted-native-model.py'


class NativeSaveGuardTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.directory = Path(self.temp.name)
        self.root = object()
        self.calls = []
        self.document = NS(Path='')
        self.attrs = 0

        def save(path):
            self.calls.append(path)
            Path(path).write_bytes(b'HOST FAKE: not a native model')
            self.document.Path = path

        scope = dict(os=os, hashlib=hashlib, GetRootPart=lambda: self.root,
            File=NS(GetAttributes=lambda path: self.attrs), FileAttributes=NS(ReparsePoint=1024),
            DocumentSave=NS(Execute=save), Window=NS(ActiveWindow=NS(Document=self.document)))
        tree = ast.parse(SOURCE.read_text(encoding='utf-8'))
        function = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == 'operation')
        exec(compile(ast.Module(body=[function], type_ignores=[]), str(SOURCE), 'exec'), scope)
        self.operation = scope['operation']
        self.params = dict(expected_root=self.root, run_root=str(self.directory),
            output_path=str(self.directory / 'result.scdoc'), critical_checks=[dict(id='geometry',status='passed')])

    def test_success_calls_saver_once_and_hashes_returned_file(self):
        result = self.operation(self.params)
        self.assertEqual(1, len(self.calls))
        self.assertEqual(hashlib.sha256(Path(result['path']).read_bytes()).hexdigest(), result['sha256'])
        self.assertEqual('not_tested', result['native_reopen'])

    def test_failed_missing_or_duplicate_checks_prevent_all_writes(self):
        for checks in ([], [{'id':'geometry','status':'failed'}],
                       [{'id':'geometry','status':'not_tested'}], [dict(id='a',status='passed')]*2):
            with self.subTest(checks=checks), self.assertRaises(ValueError):
                self.operation(dict(self.params, critical_checks=checks))
        self.assertEqual([], self.calls)
        self.assertFalse(Path(self.params['output_path']).exists())

    def test_wrong_model_is_rejected_before_save(self):
        with self.assertRaises(ValueError):
            self.operation(dict(self.params, expected_root=object()))
        self.assertEqual([], self.calls)

    def test_existing_output_is_preserved(self):
        target = Path(self.params['output_path'])
        target.write_bytes(b'preserve')
        with self.assertRaises(ValueError):
            self.operation(self.params)
        self.assertEqual(b'preserve', target.read_bytes())
        self.assertEqual([], self.calls)

    def test_outside_wrong_format_relative_and_reparse_paths_are_rejected(self):
        for path in (str(self.directory.parent / 'outside.scdoc'), str(self.directory / 'x.step'), 'relative.scdoc'):
            with self.subTest(path=path), self.assertRaises(ValueError):
                self.operation(dict(self.params, output_path=path))
        self.attrs = 1024
        with self.assertRaises(ValueError):
            self.operation(self.params)
        self.assertEqual([], self.calls)


if __name__ == '__main__':
    unittest.main()
