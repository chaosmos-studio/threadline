"""Render matched large and one-pixel-per-pixel phone specimens."""

from pathlib import Path
from random import Random
import sys

from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont
from shapely.geometry import LineString

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "source"))
from paths import GLYPHS, STITCHED_GLYPHS  # noqa: E402


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "specimens"
STYLES = ("Running", "Satin", "Applique", "Plain", "Woven", "Chain", "Stitched", "StitchedUI")
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


def natural_weave(canvas, base, seed=2604):
    draw = ImageDraw.Draw(canvas)
    draw.rectangle((0, 0, canvas.width, canvas.height), fill=base)
    random = Random(seed)
    strength = 7 if sum(base) > 400 else 4
    for y in range(0, canvas.height, 6):
        for x in range(0, canvas.width, 6):
            vx = x + random.choice((-1, 0, 0, 1))
            hy = y + random.choice((-1, 0, 0, 1))
            vshade = random.randint(-strength, strength)
            hshade = random.randint(-strength, strength)
            vertical = tuple(max(0, min(255, channel + vshade)) for channel in base)
            horizontal = tuple(max(0, min(255, channel + hshade)) for channel in base)
            draw.line((vx, y, vx, y + 4), fill=vertical, width=2)
            draw.line((x, hy + 3, x + 4, hy + 3), fill=horizontal, width=1)


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
    if style in ("Stitched", "StitchedUI"):
        natural_weave(canvas, background)
    else:
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


def raised_text(canvas, position, content, pixels, thread_color, shade_color, highlight_color,
                style="Chain"):
    mask = Image.new("L", canvas.size)
    ImageDraw.Draw(mask).text(position, content, font=font(style, pixels), fill=255)
    if style == "Stitched":
        shadow = ImageChops.offset(mask, 2, 3).filter(ImageFilter.GaussianBlur(5))
        canvas.paste(shade_color, (0, 0), shadow.point(lambda value: round(value * 0.28)))
        underlay = mask.filter(ImageFilter.MaxFilter(3))
        groove_color = tuple(round(channel * 0.88) for channel in thread_color)
        canvas.paste(groove_color, (0, 0), underlay)
        thread_layer = Image.new("RGB", canvas.size, thread_color)
        thread_draw = ImageDraw.Draw(thread_layer)
        if pixels >= 100:
            face = font(style, pixels)
            random = Random(sum(ord(char) for char in content) + pixels)
            bounds = mask.getbbox()
            if bounds:
                for _ in range((bounds[2] - bounds[0]) * (bounds[3] - bounds[1]) // 6):
                    x = random.randrange(bounds[0], bounds[2])
                    y = random.randrange(bounds[1], bounds[3])
                    if mask.getpixel((x, y)):
                        change = random.randrange(-9, 10)
                        tone = tuple(max(0, min(255, channel + change)) for channel in thread_color)
                        thread_draw.point((x, y), fill=tone)
            for index, char in enumerate(content):
                if char not in GLYPHS:
                    continue
                left = position[0] + face.getlength(content[:index])
                box = thread_draw.textbbox((left, position[1]), char, font=face)
                strokes = STITCHED_GLYPHS.get(char, GLYPHS[char])
                points = [(x * 1.12, y) for stroke in strokes for x, y in stroke]
                min_x = min(x for x, _ in points) - 108
                max_x = max(x for x, _ in points) + 108
                min_y = min(y for _, y in points) - 108
                max_y = max(y for _, y in points) + 108
                x_scale = (box[2] - box[0]) / (max_x - min_x)
                y_scale = (box[3] - box[1]) / (max_y - min_y)
                for stroke in strokes:
                    line = LineString([(x * 1.12, y) for x, y in stroke])
                    distance = 6
                    while distance < line.length:
                        center = line.interpolate(distance)
                        before = line.interpolate(max(0, distance - 4))
                        after = line.interpolate(min(line.length, distance + 4))
                        dx, dy = after.x - before.x, after.y - before.y
                        length = max((dx * dx + dy * dy) ** 0.5, 1)
                        nx, ny = -dy / length, dx / length
                        endpoints = []
                        half_width = 98 + random.randrange(7)
                        for side in (-1, 1):
                            x = center.x + nx * side * half_width
                            y = center.y + ny * side * half_width
                            endpoints.append((box[0] + (x - min_x) * x_scale,
                                              box[3] - (y - min_y) * y_scale))
                        change = random.choice((-7, -3, 6, 9, 12))
                        tone = tuple(max(0, min(255, channel + change)) for channel in thread_color)
                        thread_draw.line(endpoints, fill=tone, width=1)
                        distance += random.choice((9, 10, 11, 12))
        canvas.paste(thread_layer, (0, 0), mask)
        highlight = ImageChops.subtract(mask, ImageChops.offset(mask, 0, 1))
        canvas.paste(highlight_color, (0, 0),
                     highlight.point(lambda value: round(value * 0.22)))
        return
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


def glyph_page(style):
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
    draw.text((75, 38), f"THREADLINE {style.upper()} / GLYPH REVIEW",
              font=meta(30), fill=(94, 71, 65))
    for row_index, row in enumerate(rows):
        top = 115 + row_index * 122
        for column, char in enumerate(row):
            left = 68 + column * 112
            draw.rounded_rectangle((left, top, left + 100, top + 105), radius=9,
                                   outline=(210, 191, 166), width=2)
            draw.text((left + 18, top + 11), char, font=font(style, 68), fill=(62, 54, 52))
    target = OUTPUT / f"{style.lower()}-glyphs.png"
    canvas.save(target, optimize=True)
    print(target)


def stitched_reference_page():
    canvas = Image.new("RGB", (1600, 1000), (227, 226, 216))
    natural_weave(canvas, (227, 226, 216))
    draw = ImageDraw.Draw(canvas)
    draw.text((82, 58), "THREADLINE STITCHED / SATIN EMBROIDERY STUDY",
              font=meta(25), fill=(68, 66, 62))
    for left, glyph, colors in (
        (300, "A", ((194, 52, 119), (104, 42, 78), (243, 128, 169))),
        (650, "B", ((68, 49, 136), (38, 33, 81), (143, 116, 202))),
        (980, "C", ((221, 49, 42), (120, 38, 39), (255, 125, 104))),
    ):
        raised_text(canvas, (left, 65), glyph, 400, *colors, style="Stitched")
    draw = ImageDraw.Draw(canvas)
    draw.line((82, 555, 1518, 555), fill=(153, 151, 140), width=2)
    raised_text(canvas, (100, 590), "SHIFT", 148,
                (176, 71, 72), (91, 49, 50), (236, 143, 134), style="Stitched")
    draw = ImageDraw.Draw(canvas)
    draw.text((760, 633), "PLAY  LEVELS  SETTINGS", font=font("Stitched", 50),
              fill=(62, 58, 59))
    draw.text((105, 835), SENTENCE,
              font=fitted_font("StitchedUI", SENTENCE, 35, 1320), fill=(62, 58, 59))
    target = OUTPUT / "stitched-embroidery.png"
    canvas.save(target, optimize=True)
    print(target)


def stitched_pair_phone(dark):
    background = (44, 53, 59) if dark else COLORS["linen"]
    ink = (246, 231, 205) if dark else (58, 53, 49)
    title_color = (251, 200, 144) if dark else (169, 66, 73)
    canvas = Image.new("RGB", (390, 844), background)
    draw = ImageDraw.Draw(canvas)
    natural_weave(canvas, background)
    draw.text((24, 24), "390 x 844 px / 1:1", font=meta(13), fill=ink)
    draw.line((24, 55, 366, 55), fill=ink, width=1)
    draw.text((24, 80), "SHIFT", font=font("Stitched", 65), fill=title_color)
    draw.text((24, 183), "The First Stitch",
              font=fitted_font("StitchedUI", "The First Stitch", 31, 342), fill=ink)
    for index, word in enumerate(("PLAY", "LEVELS", "SETTINGS")):
        top = 260 + index * 88
        draw.rounded_rectangle((22, top - 7, 368, top + 61), radius=11,
                               outline=ink, width=2)
        draw.text((42, top + 1), word, font=font("StitchedUI", 35), fill=ink)
    draw.text((24, 545), "A small shift can", font=font("StitchedUI", 24), fill=ink)
    draw.text((24, 580), "change a whole world.", font=font("StitchedUI", 24), fill=ink)
    draw.line((24, 650, 366, 650), fill=ink, width=1)
    draw.text((24, 675), "SHIFT  01 / 09", font=font("StitchedUI", 22), fill=ink)
    draw.text((24, 724), "Il1  O0  Café  forêt", font=font("StitchedUI", 19), fill=ink)
    target = OUTPUT / f"stitched-pair-{'night' if dark else 'linen'}.png"
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
    for variant in ("Chain", "Stitched", "StitchedUI"):
        glyph_page(variant)
    stitched_reference_page()
    stitched_pair_phone(False)
    stitched_pair_phone(True)
