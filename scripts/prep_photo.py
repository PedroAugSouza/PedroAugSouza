"""
Composite a background-removed RGBA portrait onto a solid dark background
(so the SVG generator's WHITE_FLOOR trick blanks it out naturally like it
does with GitHub's dark theme), convert to grayscale, and boost local
contrast so the face reads clearly at low ASCII resolution.
"""
from PIL import Image, ImageOps
import sys

SRC = sys.argv[1] if len(sys.argv) > 1 else "source-nobg.png"
OUT = sys.argv[2] if len(sys.argv) > 2 else "source-prepped.png"

BG = (255, 255, 255)  # white: high luminance -> blanked out by WHITE_FLOOR in the SVG generator

im = Image.open(SRC).convert("RGBA")
bg = Image.new("RGBA", im.size, BG + (255,))
composited = Image.alpha_composite(bg, im).convert("RGB")

gray = ImageOps.grayscale(composited)
gray = ImageOps.autocontrast(gray, cutoff=1)

gray.save(OUT)
print("wrote", OUT, gray.size)
