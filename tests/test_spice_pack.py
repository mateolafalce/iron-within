import pathlib
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
import sys

sys.path.insert(0, str(ROOT / "scripts"))

from pack_spice import UUID, pack  # noqa: E402


# 1x1 black PNG. The spices screenshot is not the icon, so the test only
# needs a real PNG file in that slot.
TINY_PNG = bytes.fromhex(
    "89504e470d0a1a0a0000000d4948445200000001000000010802000000907753"
    "de0000000c4944415408d76360000000020001e221bc330000000049454e44ae426082"
)


class SpicePack(unittest.TestCase):
    def test_tree_is_self_contained(self):
        with tempfile.TemporaryDirectory() as tmp:
            shot = pathlib.Path(tmp) / "shot.png"
            shot.write_bytes(TINY_PNG)
            spice = pack(ROOT, pathlib.Path(tmp) / UUID, screenshot=shot)
            applet = spice / "files" / UUID
            self.assertEqual((spice / "info.json").read_text().strip(), '{\n    "author": "mateolafalce"\n}')
            self.assertFalse((applet / "gradeEngine.js").is_symlink())
            self.assertEqual(
                (applet / "gradeEngine.js").read_bytes(),
                (ROOT / "gradeEngine.js").read_bytes(),
            )
            self.assertTrue((applet / "shaders" / "grade.glsl").is_file())
            self.assertEqual([p.name for p in (spice / "files").iterdir()], [UUID])
