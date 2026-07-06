from __future__ import annotations

import hashlib
import io
from pathlib import Path
from typing import Any


def comfy_image_to_png_bytes(image: Any) -> tuple[bytes, ...]:
    """Convert a ComfyUI IMAGE tensor/array batch into PNG byte payloads."""
    if image is None:
        return ()

    try:
        import numpy as np
        from PIL import Image
    except ImportError as exc:  # pragma: no cover - ComfyUI normally provides these.
        raise ImportError(
            "Optional image input requires numpy and Pillow to encode ComfyUI IMAGE data."
        ) from exc

    if hasattr(image, "detach"):
        image = image.detach().cpu().numpy()

    array = np.asarray(image)
    if array.size == 0:
        return ()

    if array.ndim == 3:
        array = array[None, ...]
    if array.ndim != 4:
        raise ValueError(
            f"Expected ComfyUI IMAGE data with shape [batch, height, width, channels], got {array.shape}."
        )

    pngs: list[bytes] = []
    for frame in array:
        if frame.ndim != 3 or frame.shape[-1] not in (1, 3, 4):
            raise ValueError(
                "Expected image channels to be 1, 3, or 4 for optional image input."
            )

        frame_u8 = (np.clip(frame, 0.0, 1.0) * 255.0).round().astype("uint8")
        if frame_u8.shape[-1] == 1:
            frame_u8 = frame_u8[..., 0]

        pil_image = Image.fromarray(frame_u8)
        buffer = io.BytesIO()
        pil_image.save(buffer, format="PNG")
        pngs.append(buffer.getvalue())

    return tuple(pngs)


def image_digests(image_pngs: tuple[bytes, ...]) -> tuple[str, ...]:
    """Return stable SHA-256 digests for encoded image payloads."""
    return tuple(hashlib.sha256(image_png).hexdigest() for image_png in image_pngs)


def write_pngs(image_pngs: tuple[bytes, ...], directory: Path) -> tuple[str, ...]:
    """Write PNG payloads to a directory and return paths for Pi @image arguments."""
    paths: list[str] = []
    for index, image_png in enumerate(image_pngs):
        path = directory / f"image-{index}.png"
        path.write_bytes(image_png)
        paths.append(str(path))
    return tuple(paths)
