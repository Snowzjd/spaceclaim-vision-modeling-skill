"""Runtime artifact relocation without requiring repository-only test files."""
import importlib.util
import json
from pathlib import Path
import shutil
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
PKG=ROOT/'spaceclaim-vision-modeling'
spec=importlib.util.spec_from_file_location('resolver',PKG/'scripts/resolve_operation_artifact.py')
R=importlib.util.module_from_spec(spec)
spec.loader.exec_module(R)

class InstalledArtifactResolutionTests(unittest.TestCase):
    def test_all_139_operation_resources_resolve_under_relocated_package(self):
        registry=json.loads((PKG/'references/operation-registry.json').read_text(encoding='utf-8'))
        with tempfile.TemporaryDirectory() as directory:
            # Copy only the primary artifacts. No parent tests, repository or
            # original directory name is available to the simulated install.
            install=Path(directory)/'relocated-skill'
            primary=[]
            for entry in registry['operations']:
                template=json.loads((PKG/entry['template_path']).read_text(encoding='utf-8'))
                name=template['implementation']['primary_artifact']
                if name is None:
                    self.assertEqual('reasoning_guidance',template['implementation']['mode'])
                    name=next(link['path'] for link in template['artifact_links'] if '/atomic-guidance/' in link['path'])
                self.assertTrue(name.startswith(R.PACKAGE_NAME+'/'))
                relative=Path(*Path(name).parts[1:])
                target=install/relative
                target.parent.mkdir(parents=True,exist_ok=True)
                shutil.copyfile(ROOT/name,target)
                primary.append(name)
            self.assertEqual(139,len(primary))
            for name in primary:
                result=R.resolve_artifact(name,package_root=install)
                self.assertEqual('resolved',result['status'])
                self.assertTrue(Path(result['path']).is_relative_to(install.resolve()))
    def test_repository_tests_are_explicitly_unavailable_without_checkout(self):
        result=R.resolve_artifact('tests/test_package_scscript.py',package_root=PKG)
        self.assertEqual('unavailable',result['status'])
        self.assertIsNone(result['path'])
        result=R.resolve_artifact('tests/test_package_scscript.py',package_root=PKG,repository_root=ROOT)
        self.assertEqual('resolved',result['status'])
    def test_traversal_absolute_and_wrong_checkout_are_rejected(self):
        for value in ['../file.py','spaceclaim-vision-modeling/../secret','C:/file.py','\\\\server\\share','/etc/file']:
            with self.subTest(value=value),self.assertRaises(ValueError): R.resolve_artifact(value,package_root=PKG)
        with tempfile.TemporaryDirectory() as directory,self.assertRaises(ValueError):
            R.resolve_artifact('tests/a.py',package_root=PKG,repository_root=directory)

if __name__=='__main__': unittest.main()
