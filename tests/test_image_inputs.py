from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import numpy as np

from image_inputs import comfy_image_to_png_bytes, image_digests, write_pngs


class ImageInputTests(unittest.TestCase):
    def test_converts_comfy_image_batch_to_png_bytes(self):
        image = np.zeros((1, 2, 2, 3), dtype=np.float32)
        image[..., 0] = 1.0

        pngs = comfy_image_to_png_bytes(image)

        self.assertEqual(len(pngs), 1)
        self.assertTrue(pngs[0].startswith(b"\x89PNG"))

    def test_image_digests_are_stable(self):
        image = np.ones((1, 1, 1, 3), dtype=np.float32)
        pngs = comfy_image_to_png_bytes(image)

        self.assertEqual(image_digests(pngs), image_digests(pngs))

    def test_write_pngs_returns_paths(self):
        pngs = comfy_image_to_png_bytes(np.zeros((1, 1, 1, 3), dtype=np.float32))

        with tempfile.TemporaryDirectory() as tmpdir:
            paths = write_pngs(pngs, Path(tmpdir))

            self.assertEqual(len(paths), 1)
            self.assertTrue(Path(paths[0]).exists())


if __name__ == "__main__":
    unittest.main()
