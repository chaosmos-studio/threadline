"""Render matched large and one-pixel-per-pixel phone specimens."""

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "specimens"
STYLES = ("Running", "Satin", "Applique", "Plain", "Woven")
WORDS = ("PLAY", "LEVELS", "SETTINGS", "SHIFT", "The First Stitch", "0123456789")
SENTENCE = "A small shift can change a whole world."
COLORS = {
    "linen": (242, 231, 208),
    "ink": (52, 48, 47),
    "night": (42, 45, 70),
    "light_thread": (250, 233, 199),
    "accent": (161, 83, 71),
}
META = "/usr/share/fonts/google-noto/NotoSans-Regular.ttf"


def font(style, pixels):
    return ImageFont.truetype(str(ROOT / "fonts" / f"Threadline-{style}.ttf"), pixels)


def meta(pixels):
    return ImageFont.truetype(META, pixels)


def fitted_font(style, text, maximum, width):
    size = maximum
    while size > 15 and font(style, size).getlength(text) > width:
        size -= 1
    return font(style, size)


def weave(draw, box, base, strand):
    draw.rectangle(box, fill=base)
    x0, y0, x1, y1 = box
    for x in range(x0 + 4, x1, 9):
        draw.line((x, y0, x, y1), fill=strand, width=1)
    for y in range(y0 + 6, y1, 12):
        draw.line((x0, y, x1, y), fill=strand, width=1)


def direction_page(style):
    canvas = Image.new("RGB", (1600, 1190), COLORS["linen"])
    draw = ImageDraw.Draw(canvas)
    weave(draw, (0, 0, 1600, 1190), COLORS["linen"], (236, 224, 202))
    draw.rectangle((58, 55, 1542, 1135), fill=(250, 244, 232), outline=(179, 154, 135), width=3)
    draw.text((105, 90), f"THREADLINE / {style.upper()}", font=meta(34), fill=COLORS["accent"])
    draw.text((105, 155), "1:1 OUTLINE STUDY", font=meta(19), fill=(110, 100, 94))
    large = font(style, 87)
    for index, word in enumerate(WORDS[:4]):
        x = 110 if index % 2 == 0 else 810
        y = 235 + index // 2 * 115
        draw.text((x, y), word, font=large, fill=COLORS["ink"])
    draw.text((110, 530), WORDS[4], font=font(style, 84), fill=COLORS["ink"])
    draw.text((110, 665), WORDS[5], font=font(style, 74), fill=COLORS["ink"])
    draw.text((110, 790), SENTENCE, font=font(style, 44), fill=COLORS["ink"])
    draw.text((110, 880), "Il1  O0  AVATAR  To  Wa  Café  forêt  naïve  Ångström", font=font(style, 37), fill=COLORS["ink"])
    draw.text((110, 1020), "Thread paths and counters at display size", font=meta(20), fill=(110, 100, 94))
    target = OUTPUT / f"{style.lower()}-large.png"
    canvas.save(target, optimize=True)
    print(target)


def phone_page(style, dark):
    background = COLORS["night"] if dark else COLORS["linen"]
    text_color = COLORS["light_thread"] if dark else COLORS["ink"]
    strand = (47, 50, 76) if dark else (235, 222, 199)
    canvas = Image.new("RGB", (390, 844), background)
    draw = ImageDraw.Draw(canvas)
    weave(draw, (0, 0, 390, 844), background, strand)
    draw.text((24, 22), "390 x 844 px  /  1:1", font=meta(13), fill=text_color)
    draw.line((24, 54, 366, 54), fill=text_color, width=1)
    draw.text((24, 77), "The First Stitch",
              font=fitted_font(style, "The First Stitch", 33, 342), fill=text_color)
    for index, word in enumerate(WORDS[:4]):
        y = 156 + index * 74
        draw.rounded_rectangle((22, y - 8, 368, y + 55), radius=9,
                               outline=text_color, width=1)
        draw.text((38, y), word, font=font(style, 34), fill=text_color)
    draw.text((24, 475), "0123456789", font=font(style, 28), fill=text_color)
    draw.text((24, 536), "A small shift can", font=font(style, 24), fill=text_color)
    draw.text((24, 568), "change a whole world.", font=font(style, 24), fill=text_color)
    draw.line((24, 629, 366, 629), fill=text_color, width=1)
    draw.text((24, 650), "SHIFT  01 / 09", font=font(style, 21), fill=text_color)
    draw.text((24, 695), "Il1  O0  Café  forêt", font=font(style, 19), fill=text_color)
    draw.text((24, 799), f"{style.upper()} / {'NIGHT' if dark else 'LINEN'}", font=meta(13), fill=text_color)
    target = OUTPUT / f"{style.lower()}-phone-{'night' if dark else 'linen'}.png"
    canvas.save(target, optimize=True)
    print(target)


def phone_contact_sheet():
    canvas = Image.new("RGB", (24 + len(STYLES) * 414, 1810), (226, 220, 205))
    draw = ImageDraw.Draw(canvas)
    draw.text((52, 20), "THREADLINE / MATCHED PHONE STUDIES", font=meta(30), fill=COLORS["ink"])
    for index, style in enumerate(STYLES):
        x = 24 + index * 414
        for row, background in enumerate(("linen", "night")):
            img = Image.open(OUTPUT / f"{style.lower()}-phone-{background}.png")
            canvas.paste(img, (x, 75 + row * 860))
    target = OUTPUT / "phone-comparison.png"
    canvas.save(target, optimize=True)
    print(target)


if __name__ == "__main__":
    OUTPUT.mkdir(exist_ok=True)
    for variant in STYLES:
        direction_page(variant)
        phone_page(variant, False)
        phone_page(variant, True)
    phone_contact_sheet()
