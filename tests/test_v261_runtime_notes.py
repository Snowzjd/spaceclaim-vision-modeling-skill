from __future__ import annotations

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
NOTES_PATH = ROOT / "spaceclaim-vision-modeling" / "references" / "v261-runtime-notes.md"
SKILL_PATH = ROOT / "spaceclaim-vision-modeling" / "SKILL.md"


class V261RuntimeNotesTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.notes = NOTES_PATH.read_text(encoding="utf-8")
        cls.skill = SKILL_PATH.read_text(encoding="utf-8")

    def test_notes_exist_and_keep_the_compatibility_boundary(self) -> None:
        self.assertIn("# Runtime notes: SpaceClaim 2026 R1", self.notes)
        self.assertIn("not** a compatibility claim", self.notes)
        self.assertIn("2022 R1", self.notes)

    def test_notes_record_the_unit_convention(self) -> None:
        self.assertIn("cubic metres", self.notes)
        self.assertIn("Shape.Volume * 1e9", self.notes)

    def test_notes_record_the_working_save_and_export_routes(self) -> None:
        self.assertIn("DocumentSave.Execute", self.notes)
        self.assertIn(".scdocx", self.notes)
        self.assertIn("Part.Export(PartExportFormat.Step", self.notes)

    def test_notes_mark_blocked_paths_as_blocked(self) -> None:
        self.assertIn("Status: `blocked` for `Document.SaveAs`", self.notes)
        self.assertIn("Status: `blocked`.", self.notes)

    def test_notes_record_the_working_fillet_and_chamfer_route(self) -> None:
        self.assertIn("SpaceClaim.Api.V261.Scripting.dll", self.notes)
        self.assertIn("ConstantRound.Execute", self.notes)
        self.assertIn("Chamfer.Execute", self.notes)
        self.assertIn("SpaceClaim.Api.V261.Scripting.Selection", self.notes)
        self.assertIn("844,161.572182", self.notes)

    def test_skill_routes_to_the_notes(self) -> None:
        self.assertIn("references/v261-runtime-notes.md", self.skill)


if __name__ == "__main__":
    unittest.main()
