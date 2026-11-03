"""Render a cloth and paper specimen for visual review."""

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


root = Path(__file__).resolve().parents[1]
canvas = Image.new("RGB", (1600, 1080), "#e9ddc7")
draw = ImageDraw.Draw(canvas)
for x in range(0, canvas.width, 7):
    draw.line((x, 0, x, canvas.height), fill="#e4d4b9", width=1)
draw.rounded_rectangle((60, 55, 1540, 1025), radius=34, fill="#f6ecda", outline="#9f8070", width=7)
draw.rounded_rectangle((76, 71, 1524, 1009), radius=24, outline="#b58e78", width=3)
draw.text((120, 93), "THREADLINE / FIRST PROOFS", font=ImageFont.truetype(str(root / "fonts" / "Threadline-Satin.ttf"), 46), fill="#754b45")
for offset, style in enumerate(("Running", "Satin")):
    top = 200 + offset * 390
    font = root / "fonts" / f"Threadline-{style}.ttf"
    draw.text((120, top), style.upper(), font=ImageFont.truetype(str(font), 56), fill="#a5544b")
    draw.text((120, top + 100), "PALEWHEEL  /  PLAY  LEVELS  GUIDE", font=ImageFont.truetype(str(font), 64), fill="#493a37")
    draw.text((120, top + 205), "ABCDEFGHIJKLMNOPQRSTUVWXYZ  0123456789", font=ImageFont.truetype(str(font), 36), fill="#493a37")
    draw.text((120, top + 270), "A small shift can change a whole world.", font=ImageFont.truetype(str(font), 38), fill="#493a37")
canvas.save(root / "specimens" / "first-proofs.png", optimize=True)
