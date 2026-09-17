"""Prepare a manually verified character crop from anon.png.
The source is a design sheet, so crop coordinates must be supplied by the user.
"""
from pathlib import Path
import argparse
from PIL import Image


def main():
    p = argparse.ArgumentParser(description="Export the full-body character crop")
    p.add_argument("--source", type=Path, default=Path("anon.png"))
    p.add_argument("--box", nargs=4, type=int, metavar=("LEFT", "TOP", "RIGHT", "BOTTOM"), required=True)
    p.add_argument("--output", type=Path, default=Path("assets/character/character_rgba.png"))
    args = p.parse_args()
    image = Image.open(args.source).convert("RGBA")
    crop = image.crop(tuple(args.box))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    crop.save(args.output)
    print(f"Saved {args.output} ({crop.width}x{crop.height}). Review it before using as a character asset.")

if __name__ == "__main__":
    main()
