"""Create Windows icon sizes from the approved master PNG without redesigning it."""
from __future__ import annotations

from io import BytesIO
from pathlib import Path
import struct

from PIL import Image, ImageFilter


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets"
MASTER = ASSETS / "icon.png"
ICO = ASSETS / "atlas-icon.ico"


def render(size: int, *, sharpen: bool = False) -> Image.Image:
    image = Image.open(MASTER).convert("RGBA")
    image = image.resize((size, size), Image.Resampling.LANCZOS)
    if sharpen and size <= 48:
        # Mild edge sharpening preserves the artwork while compensating for
        # the blur introduced when Windows shows it at taskbar dimensions.
        radius = 0.42 if size <= 20 else 0.5
        amount = 175 if size <= 20 else 145
        image = image.filter(ImageFilter.UnsharpMask(radius, amount, 1))
    return image


def png_bytes(image: Image.Image) -> bytes:
    stream = BytesIO()
    image.save(stream, format="PNG", optimize=True)
    return stream.getvalue()


def main() -> None:
    if not MASTER.is_file():
        raise SystemExit(f"Approved icon source not found: {MASTER}")

    render(1024).save(ASSETS / "atlas-brand-hires.png", optimize=True)
    render(512).save(ASSETS / "atlas-icon-512.png", optimize=True)
    render(256).save(ASSETS / "atlas-icon-256.png", optimize=True)

    sizes = (256, 128, 64, 48, 32, 24, 20, 16)
    frames = [(size, png_bytes(render(size, sharpen=True))) for size in sizes]
    header = struct.pack("<HHH", 0, 1, len(frames))
    offset = 6 + 16 * len(frames)
    entries = bytearray()
    payload = bytearray()
    for size, data in frames:
        dimension = 0 if size == 256 else size
        entries.extend(
            struct.pack(
                "<BBBBHHII",
                dimension,
                dimension,
                0,
                0,
                1,
                32,
                len(data),
                offset,
            )
        )
        payload.extend(data)
        offset += len(data)

    ICO.write_bytes(header + entries + payload)
    print(f"Generated {ICO} from {MASTER}; included sizes: {sizes}")


if __name__ == "__main__":
    main()
