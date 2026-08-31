from __future__ import annotations

import ast
import importlib.util
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TEMPLATE_PATH = (
    ROOT
    / "spaceclaim-vision-modeling"
    / "assets"
    / "templates"
    / "spaceclaim-v21-geometry-audit.py"
)
AUDITOR_PATH = ROOT / "spaceclaim-vision-modeling" / "scripts" / "audit_scscript.py"
PACKAGER_PATH = ROOT / "spaceclaim-vision-modeling" / "scripts" / "package_scscript.py"


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


AUDITOR = load_module("v21_template_auditor", AUDITOR_PATH)
PACKAGER = load_module("v21_template_packager", PACKAGER_PATH)


class V21TemplateTests(unittest.TestCase):
    def test_geometry_audit_uses_v21_compatible_print_syntax(self) -> None:
        source = TEMPLATE_PATH.read_text(encoding="utf-8")
        ast.parse(source, filename=str(TEMPLATE_PATH))
        self.assertIn("from __future__ import print_function", source)
        self.assertIn("print(line)", source)
        self.assertNotIn("print line", source)

    def test_geometry_audit_packages_as_read_only_scscript(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            archive_path = Path(directory) / "geometry-audit.scscript"
            PACKAGER.package_scscript(TEMPLATE_PATH, archive_path)
            result = AUDITOR.audit_archive(
                archive_path,
                require_api="21",
                forbid_numbered_aliases=True,
                forbidden_operations=(
                    "DesignBody.Create",
                    "ConstantRound.Execute",
                    "Chamfer.Execute",
                    "DocumentSave.Execute",
                ),
            )
        self.assertEqual("passed", result["status"])


if __name__ == "__main__":
    unittest.main()
