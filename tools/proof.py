"""Render matched large and one-pixel-per-pixel phone specimens."""

from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "specimens"
STYLES = ("Running", "Satin", "Applique", "Plain", "Woven", "Chain")
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


def raised_text(canvas, position, content, pixels, thread_color, shade_color, highlight_color):
    mask = Image.new("L", canvas.size)
    ImageDraw.Draw(mask).text(position, content, font=font("Chain", pixels), fill=255)
    shadow = ImageChops.offset(mask, 4, 5).filter(ImageFilter.GaussianBlur(3))
    canvas.paste(shade_color, (0, 0), shadow)
    canvas.paste(thread_color, (0, 0), mask)
    highlight = ImageChops.subtract(mask, ImageChops.offset(mask, 0, 2))
    canvas.paste(highlight_color, (0, 0), highlight)


def chain_cloth_page():
    canvas = Image.new("RGB", (1600, 1000), (231, 216, 188))
    draw = ImageDraw.Draw(canvas)
    weave(draw, (0, 0, 1600, 1000), (231, 216, 188), (225, 208, 178))
    draw.rounded_rectangle((62, 60, 1538, 940), radius=38,
                           fill=(247, 237, 218), outline=(177, 139, 115), width=4)
    for x in range(88, 1518, 22):
        draw.line((x, 83, x + 11, 83), fill=(178, 129, 111), width=3)
        draw.line((x, 916, x + 11, 916), fill=(178, 129, 111), width=3)
    for y in range(106, 906, 22):
        draw.line((85, y, 85, y + 11), fill=(178, 129, 111), width=3)
        draw.line((1515, y, 1515, y + 11), fill=(178, 129, 111), width=3)
    draw.text((120, 108), "THREADLINE CHAIN / CLOTH STUDY", font=meta(24), fill=(100, 80, 69))
    raised_text(canvas, (112, 176), "SHIFT", 198,
                (161, 69, 67), (83, 47, 47), (224, 129, 111))
    raised_text(canvas, (120, 415), "The First Stitch", 78,
                (67, 93, 77), (40, 58, 51), (148, 174, 146))
    draw = ImageDraw.Draw(canvas)
    draw.text((125, 568), "PLAY   LEVELS   SETTINGS", font=font("Chain", 47), fill=(66, 59, 57))
    draw.text((125, 680), SENTENCE,
              font=fitted_font("Chain", SENTENCE, 39, 900), fill=(66, 59, 57))
    draw.text((125, 802), "0123456789     Il1  O0", font=font("Chain", 40), fill=(66, 59, 57))
    draw.rounded_rectangle((1080, 155, 1455, 830), radius=28,
                           fill=(48, 60, 64), outline=(98, 112, 103), width=5)
    for y in range(180, 810, 21):
        draw.line((1102, y, 1114, y), fill=(104, 121, 107), width=2)
        draw.line((1422, y, 1434, y), fill=(104, 121, 107), width=2)
    raised_text(canvas, (1120, 235), "PLAY", 62,
                (246, 218, 154), (38, 42, 44), (255, 242, 196))
    raised_text(canvas, (1120, 350), "LEVELS", 48,
                (246, 218, 154), (38, 42, 44), (255, 242, 196))
    raised_text(canvas, (1120, 460), "SETTINGS", 38,
                (246, 218, 154), (38, 42, 44), (255, 242, 196))
    draw = ImageDraw.Draw(canvas)
    draw.text((1120, 670), "SHIFT  01 / 09", font=font("Chain", 27), fill=(244, 230, 202))
    target = OUTPUT / "chain-cloth.png"
    canvas.save(target, optimize=True)
    print(target)


def chain_glyph_page():
    rows = (
        "ABCDEFGHIJKLM",
        "NOPQRSTUVWXYZ",
        "abcdefghijklm",
        "nopqrstuvwxyz",
        "0123456789!?&",
        "ÀÁÂÄÅÆÇÈÉÊËÌÍ",
        "àáâäåæçèéêëìí",
        "ÑÖØÙÜÝßœøłđþ€",
    )
    canvas = Image.new("RGB", (1600, 1120), (245, 235, 215))
    draw = ImageDraw.Draw(canvas)
    weave(draw, (0, 0, 1600, 1120), (245, 235, 215), (238, 225, 203))
    draw.text((75, 38), "THREADLINE CHAIN / GLYPH REVIEW", font=meta(30), fill=(94, 71, 65))
    for row_index, row in enumerate(rows):
        top = 115 + row_index * 122
        for column, char in enumerate(row):
            left = 68 + column * 112
            draw.rounded_rectangle((left, top, left + 100, top + 105), radius=9,
                                   outline=(210, 191, 166), width=2)
            draw.text((left + 18, top + 11), char, font=font("Chain", 68), fill=(62, 54, 52))
    target = OUTPUT / "chain-glyphs.png"
    canvas.save(target, optimize=True)
    print(target)


if __name__ == "__main__":
    OUTPUT.mkdir(exist_ok=True)
    for variant in STYLES:
        direction_page(variant)
        phone_page(variant, False)
        phone_page(variant, True)
    phone_contact_sheet()
    chain_cloth_page()
    chain_glyph_page()
