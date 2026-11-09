"""Build the Threadline designs from their editable centerlines."""

from pathlib import Path
from math import atan2, degrees
import subprocess
import sys
import types
import unicodedata

from fontTools.fontBuilder import FontBuilder
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.otlLib.builder import buildStatTable
from fontTools.ttLib import TTFont, newTable
from shapely.affinity import rotate, scale, translate
from shapely.geometry import LineString, Point
from shapely.geometry.polygon import orient
from shapely.ops import substring, unary_union
from ufoLib2 import Font


ROOT = Path(__file__).resolve().parents[1]
VERSION = "1.0.0"
FONT_VERSION = "1.000"
sys.path.insert(0, str(ROOT / "sources"))
from paths import ACCENTS, CHAIN_GLYPHS, EXTRA_COMPOSED, GLYPHS  # noqa: E402

STYLES = ("Running", "Satin", "Applique", "Plain", "Woven", "Chain")
WEIGHTS = {
    "Running": ("Regular",), "Plain": ("Regular",),
    "Satin": ("Regular", "Bold"), "Applique": ("Regular", "Bold"),
    "Woven": ("Regular", "ExtraBold"), "Chain": ("Regular", "Bold"),
}
BLANK_ADVANCES = {"\u00A0": 320, "\u2028": 0, "\u2029": 0}


def filename(style, weight):
    return f"Threadline{style}-{weight}"
NARROW = "iljı!|':;.,`‘’¡"
PAIR_VALUES = {
    "AV": -55, "AW": -35, "AY": -50, "AT": -30, "FA": -30,
    "LT": -30, "LY": -45, "PA": -25, "TA": -45, "Te": -35,
    "Th": -20, "To": -45, "Tu": -25, "VA": -55, "Ve": -30,
    "Vo": -35, "WA": -35, "Wo": -25, "YA": -50, "Ye": -40,
    "Yo": -45, "Wa": -20, "We": -20, "ry": -15,
}


def wanted_characters():
    characters = set(GLYPHS) | set(ACCENTS) | set(EXTRA_COMPOSED) | set(BLANK_ADVANCES)
    for codepoint in list(range(0x00C0, 0x0180)) + [0x1E9E]:
        char = chr(codepoint)
        parts = unicodedata.normalize("NFD", char)
        if len(parts) > 1 and parts[0] in GLYPHS and all(mark in ACCENTS for mark in parts[1:]):
            characters.add(char)
    return characters


def is_narrow(char):
    return char in NARROW or unicodedata.normalize("NFD", char)[0] in NARROW


def softened(points, passes=2):
    if len(points) < 3:
        return points
    closed = points[0] == points[-1]
    result = points[:-1] if closed else points
    for _ in range(passes):
        next_points = [] if closed else [result[0]]
        pairs = zip(result, result[1:] + result[:1] if closed else result[1:])
        for start, end in pairs:
            next_points.append((start[0] * 0.75 + end[0] * 0.25,
                                start[1] * 0.75 + end[1] * 0.25))
            next_points.append((start[0] * 0.25 + end[0] * 0.75,
                                start[1] * 0.25 + end[1] * 0.75))
        if not closed:
            next_points.append(result[-1])
        result = next_points
    return result + [result[0]] if closed else result


def form(strokes, style, char=None):
    regular = style.endswith("Regular")
    design = style.removesuffix("Regular") if regular else style
    pieces = []
    cuts = []
    for points in strokes:
        if design in ("Woven", "Chain"):
            width_scale = {"Woven": 1.25, "Chain": 1.14}[design]
            points = [(x * width_scale, y) for x, y in points]
        if design == "Chain":
            points = softened(points)
        line = LineString(points)
        if line.length < 25:
            if char in ("i", "j"):
                dot_radius = {"Running": 36, "Satin": 52, "Applique": 58,
                              "Plain": 47, "Woven": 64, "Chain": 64}[design]
            else:
                dot_radius = 24 if design == "Running" else 49 if design == "Chain" else 34
            if regular:
                dot_radius = round(dot_radius * 0.7)
            dot = Point(points[0]).buffer(dot_radius, quad_segs=8)
            pieces.append(dot)
            continue
        if design == "Running":
            for start in range(0, int(line.length) + 1, 108):
                segment = substring(line, start, min(start + 55, line.length))
                if segment.length:
                    pieces.append(segment.buffer(16, cap_style="round", join_style="round", quad_segs=4))
        else:
            radius = {"Satin": 43, "Applique": 55, "Plain": 36,
                      "Woven": 77, "Chain": 78}[design]
            if regular:
                radius = round(radius * 0.63)
            pieces.append(line.buffer(radius, cap_style="round", join_style="round", quad_segs=5))
            if design in ("Satin", "Applique", "Woven"):
                step = {"Satin": 31, "Applique": 48, "Woven": 29}[design]
                for stitch_index, distance in enumerate(range(24, int(line.length) - 15, step)):
                    before = line.interpolate(max(0, distance - 5))
                    after = line.interpolate(min(line.length, distance + 5))
                    dx, dy = after.x - before.x, after.y - before.y
                    length = max((dx * dx + dy * dy) ** 0.5, 1)
                    nx, ny = -dy / length, dx / length
                    center = line.interpolate(distance)
                    if design in ("Satin", "Woven"):
                        half_width = 29 if design == "Satin" else 53
                        if regular:
                            half_width = round(half_width * 0.65)
                        skew = 5 if design == "Satin" else 10 + 2 * (stitch_index % 4)
                        slit = LineString([
                            (center.x - nx * half_width - dx / length * skew,
                             center.y - ny * half_width - dy / length * skew),
                            (center.x + nx * half_width + dx / length * skew,
                             center.y + ny * half_width + dy / length * skew),
                        ])
                        cuts.append(slit.buffer(2.4 if regular else 2.8 if design == "Satin" else 5,
                                                cap_style="round", quad_segs=3))
                    else:
                        for side in (-1, 1):
                            slit = LineString([
                                (center.x + nx * side * 39 - dx / length * 9,
                                 center.y + ny * side * 39 - dy / length * 9),
                                (center.x + nx * side * 39 + dx / length * 9,
                                 center.y + ny * side * 39 + dy / length * 9),
                            ])
                            cuts.append(slit.buffer(2.5, cap_style="round", quad_segs=3))
            elif design == "Chain":
                for stitch_index, distance in enumerate(range(45, int(line.length) - 20, 96)):
                    center = line.interpolate(distance)
                    before = line.interpolate(max(0, distance - 5))
                    after = line.interpolate(min(line.length, distance + 5))
                    dx, dy = after.x - before.x, after.y - before.y
                    length = max((dx * dx + dy * dy) ** 0.5, 1)
                    eye = scale(Point(0, 0).buffer(1, quad_segs=10),
                                xfact=13 if regular else 20, yfact=5 if regular else 7)
                    eye = rotate(eye, degrees(atan2(dy, dx)), origin=(0, 0))
                    cuts.append(translate(eye, xoff=center.x, yoff=center.y))
                    side = -1 if stitch_index % 2 else 1
                    entry = Point(center.x - dy / length * side * 75,
                                  center.y + dx / length * side * 75).buffer(3 if regular else 5, quad_segs=6)
                    cuts.append(entry)
    shape = unary_union(pieces)
    if cuts:
        shape = shape.difference(unary_union(cuts))
    return shape.simplify(1.4, preserve_topology=True)


def glyph_geometry(char, style, dotless_i=False):
    design = style.removesuffix("Regular") if style.endswith("Regular") else style
    if char in ACCENTS:
        shape = form(ACCENTS[char], "Plain" if design == "Chain" else style)
    elif char in GLYPHS:
        overrides = CHAIN_GLYPHS if design == "Chain" else {}
        strokes = overrides.get(char, GLYPHS[char])
        shape = form(strokes, style, char)
    else:
        parts = unicodedata.normalize("NFD", char)
        base = "i" if char == "į" and not dotless_i else "ı" if parts[0] == "i" else parts[0]
        overrides = CHAIN_GLYPHS if design == "Chain" else {}
        base_strokes = overrides.get(base, GLYPHS[base])
        if base == "j":
            base_strokes = base_strokes[:1]
        shape = form(base_strokes, style, base)
        top = shape.bounds[3]
        marks = []
        for mark in parts[1:]:
            mark_shape = form(ACCENTS[mark], "Plain" if design == "Chain" else style)
            if mark in ("\u0326", "\u0327", "\u0328"):
                mark_shape = translate(mark_shape, yoff=-25)
            else:
                mark_shape = translate(mark_shape, yoff=top - 700 + (45 if design == "Chain" else 0))
            if design == "Chain":
                mark_shape = translate(mark_shape, xoff=42)
            marks.append(mark_shape)
        shape = unary_union([shape, *marks])
    if design in ("Woven", "Chain"):
        if design == "Chain":
            tilt = (-4.0, -1.6, 1.5, 3.6, 0.0)[ord(char) % 5]
            lift = (-27, 0, 24)[ord(char) % 3]
            shape = rotate(shape, tilt, origin="center")
            shape = translate(shape, yoff=lift)
        bearing = 45 if design == "Woven" else 35
        shape = translate(shape, xoff=bearing - shape.bounds[0])
    elif is_narrow(char):
        shape = translate(shape, xoff=-140)
    elif char in "@Ww":
        shape = translate(shape, xoff=35 - shape.bounds[0])
    return shape


def to_glyph(geometry):
    pen = TTGlyphPen(None)
    if geometry.is_empty:
        return pen.glyph()
    polygons = [geometry] if geometry.geom_type == "Polygon" else [g for g in geometry.geoms if g.geom_type == "Polygon"]
    for polygon in polygons:
        polygon = orient(polygon, sign=-1.0)
        for ring in [polygon.exterior, *polygon.interiors]:
            coordinates = [(round(x), round(y)) for x, y in ring.coords[:-1]]
            if len(set(coordinates)) < 3:
                continue
            pen.moveTo(coordinates[0])
            for coordinate in coordinates[1:]:
                pen.lineTo(coordinate)
            pen.closePath()
    return pen.glyph()


def feature_text(characters, bounds):
    pairs = []
    for pair, value in PAIR_VALUES.items():
        if all(char in characters for char in pair):
            pairs.append(f"    pos uni{ord(pair[0]):04X} uni{ord(pair[1]):04X} {value};")
    bottom_marks = {"\u0326", "\u0327", "\u0328"}
    classes = []
    for mark in ACCENTS:
        left, bottom, right, top = bounds[f"uni{ord(mark):04X}"]
        x = round((left + right) / 2)
        side = "BOTTOM" if mark in bottom_marks else "TOP"
        y = 0 if side == "BOTTOM" else 700
        classes.append(f"markClass uni{ord(mark):04X} <anchor {x} {y}> @{side};")
    base_positions = []
    for char in sorted(characters - set(ACCENTS) - set(BLANK_ADVANCES)):
        left, bottom, right, top = bounds[f"uni{ord(char):04X}"]
        x = round((left + right) / 2)
        base_positions.append(
            f"  pos base uni{ord(char):04X} <anchor {x} {round(top + 35)}> mark @TOP "
            f"<anchor {x} {round(min(bottom, 0) - 25)}> mark @BOTTOM;"
        )
    stacked_positions = []
    for mark in ACCENTS:
        left, bottom, right, top = bounds[f"uni{ord(mark):04X}"]
        x = round((left + right) / 2)
        side = "BOTTOM" if mark in bottom_marks else "TOP"
        y = round(bottom - 25) if side == "BOTTOM" else round(top + 35)
        stacked_positions.append(f"  pos mark uni{ord(mark):04X} <anchor {x} {y}> mark @{side};")
    tabular = " ".join(f"uni{ord(char):04X}" for char in "0123456789")
    tabular_alt = " ".join(f"uni{ord(char):04X}.tnum" for char in "0123456789")
    above = " ".join(f"uni{ord(mark):04X}" for mark in ACCENTS if mark not in bottom_marks)
    return "\n".join([
        f"@above = [{above}];",
        *classes,
        "feature ccmp { sub uni0069' @above by uni0131; sub uni006A' @above by uni0237; sub uni012F' @above by uni012F.dotless; } ccmp;",
        "feature kern {", *pairs, "} kern;",
        "feature mark {", *base_positions, "} mark;",
        "feature mkmk {", *stacked_positions, "} mkmk;",
        f"feature tnum {{ sub [{tabular}] by [{tabular_alt}]; }} tnum;",
    ])


def save_ufo(font, family, weight, style, features, cmap):
    source = Font()
    info = source.info
    info.familyName = family
    info.styleName = weight
    info.unitsPerEm = 1000
    info.ascender = font["hhea"].ascent
    info.descender = font["hhea"].descent
    info.capHeight = 700
    info.xHeight = 490
    info.versionMajor = 1
    info.versionMinor = 0
    info.copyright = font["name"].getDebugName(0)
    info.postscriptFontName = filename(style, weight)
    info.openTypeNameDesigner = "Shravanpuri Goswami"
    info.openTypeNameDesignerURL = "https://github.com/shravanngoswamii"
    info.openTypeNameManufacturer = "Chaosmos Studio"
    info.openTypeNameManufacturerURL = "https://chaosmos.studio"
    info.openTypeNameLicense = font["name"].getDebugName(13)
    info.openTypeNameLicenseURL = "https://openfontlicense.org"
    info.openTypeNameUniqueID = f"{FONT_VERSION};Chaosmos Studio;{filename(style, weight)}"
    info.openTypeOS2WeightClass = font["OS/2"].usWeightClass
    info.openTypeOS2Selection = [7, 8]
    info.openTypeOS2Type = []
    info.openTypeOS2VendorID = "CHAO"
    info.openTypeOS2CodePageRanges = [0]
    info.openTypeOS2TypoAscender = font["OS/2"].sTypoAscender
    info.openTypeOS2TypoDescender = font["OS/2"].sTypoDescender
    info.openTypeOS2TypoLineGap = 0
    info.openTypeOS2WinAscent = font["OS/2"].usWinAscent
    info.openTypeOS2WinDescent = font["OS/2"].usWinDescent
    info.openTypeHheaAscender = font["hhea"].ascent
    info.openTypeHheaDescender = font["hhea"].descent
    info.openTypeHheaLineGap = 0
    source.lib["public.glyphOrder"] = font.getGlyphOrder()
    unicodes = {name: codepoint for codepoint, name in cmap.items()}
    for name in font.getGlyphOrder():
        glyph = source.newGlyph(name)
        glyph.width = font["hmtx"][name][0]
        if name in unicodes:
            glyph.unicodes = [unicodes[name]]
        font["glyf"][name].draw(glyph.getPen(), font["glyf"])
    source.features.text = features
    path = ROOT / "sources" / "ufo" / f"{filename(style, weight)}.ufo"
    path.parent.mkdir(parents=True, exist_ok=True)
    source.save(path, overwrite=True)
    return path


def ensure_brotli():
    try:
        import brotli  # noqa: F401
    except ImportError:
        # FontTools needs the Brotli Python API. The system CLI provides the same stream format.
        shim = types.ModuleType("brotli")
        shim.MODE_FONT = 2
        shim.MODE_TEXT = 1

        def compress(data, mode=None):
            return subprocess.run(["brotli", "--stdout", "--quality=11"], input=data,
                                  capture_output=True, check=True).stdout

        def decompress(data):
            return subprocess.run(["brotli", "--stdout", "--decompress"], input=data,
                                  capture_output=True, check=True).stdout

        shim.compress = compress
        shim.decompress = decompress
        sys.modules["brotli"] = shim


def save_woff2(source, target):
    ensure_brotli()
    from fontTools.ttLib import woff2

    woff2.compress(str(source), str(target))


def build(style, weight, characters):
    family = f"Threadline {style}"
    drawing = f"{style}Regular" if weight == "Regular" and len(WEIGHTS[style]) > 1 else style
    ascent = 1120
    descent = 330
    order = [".notdef", "space"] + [f"uni{ord(char):04X}" for char in sorted(characters)]
    order += [f"uni{ord(char):04X}.tnum" for char in "0123456789"]
    order.append("uni012F.dotless")
    notdef = Point(300, 350).buffer(225).boundary.buffer(28)
    glyphs = {".notdef": to_glyph(notdef), "space": TTGlyphPen(None).glyph()}
    metrics = {".notdef": (600, 47), "space": (320, 0)}
    cmap = {32: "space"}
    for blank, advance in BLANK_ADVANCES.items():
        name = f"uni{ord(blank):04X}"
        glyphs[name] = TTGlyphPen(None).glyph()
        metrics[name] = (advance, 0)
        cmap[ord(blank)] = name
    bounds = {}
    digit_shapes = {}
    for char in sorted(characters):
        if char in BLANK_ADVANCES:
            continue
        name = f"uni{ord(char):04X}"
        shape = glyph_geometry(char, drawing)
        bounds[name] = shape.bounds
        if char in ACCENTS:
            advance = 0
        elif style in ("Woven", "Chain"):
            advance = round(shape.bounds[2] + (45 if style == "Woven" else 35))
        elif is_narrow(char):
            advance = 350
        elif char in "ft()[]{}":
            advance = 560
        else:
            advance = 600
        if char not in ACCENTS:
            advance = max(advance, round(shape.bounds[2] + 35))
        glyphs[name] = to_glyph(shape)
        metrics[name] = (advance, round(shape.bounds[0]))
        cmap[ord(char)] = name
        if char in "0123456789":
            digit_shapes[char] = shape
    tabular_width = {"Running": 600, "Plain": 610, "Satin": 640,
                     "Applique": 650, "Woven": 850, "Chain": 740}[style]
    for char, shape in digit_shapes.items():
        name = f"uni{ord(char):04X}.tnum"
        width = metrics[f"uni{ord(char):04X}"][0]
        centered = translate(shape, xoff=round((tabular_width - width) / 2))
        glyphs[name] = to_glyph(centered)
        metrics[name] = (tabular_width, round(centered.bounds[0]))
    dotless = glyph_geometry("į", drawing, dotless_i=True)
    glyphs["uni012F.dotless"] = to_glyph(dotless)
    metrics["uni012F.dotless"] = metrics["uni012F"]
    builder = FontBuilder(1000, isTTF=True)
    builder.setupGlyphOrder(order)
    builder.setupCharacterMap(cmap)
    builder.setupGlyf(glyphs)
    builder.setupHorizontalMetrics(metrics)
    builder.setupHorizontalHeader(ascent=ascent, descent=-descent)
    names = {
        "familyName": f"{family} ExtraBold" if weight == "ExtraBold" else family,
        "styleName": "Bold" if weight == "Bold" else "Regular",
        "uniqueFontIdentifier": f"{family} {weight} {FONT_VERSION}",
        "fullName": f"{family} {weight}",
        "psName": filename(style, weight),
        "version": f"Version {FONT_VERSION}",
        "copyright": (ROOT / "OFL.txt").read_text().splitlines()[0],
        "manufacturer": "Chaosmos Studio",
        "designer": "Shravanpuri Goswami",
        "vendorURL": "https://chaosmos.studio",
        "designerURL": "https://github.com/shravanngoswamii",
        "licenseDescription": "This Font Software is licensed under the SIL Open Font License, Version 1.1. This license is available with a FAQ at: https://openfontlicense.org",
        "licenseInfoURL": "https://openfontlicense.org",
    }
    if weight == "ExtraBold":
        names["typographicFamily"] = family
        names["typographicSubfamily"] = weight
    builder.setupNameTable(names, mac=False)
    builder.setupOS2(
        version=4,
        sTypoAscender=ascent, sTypoDescender=-descent,
        usWinAscent=ascent, usWinDescent=descent,
        sxHeight=490, sCapHeight=700,
        usWeightClass={"Regular": 400, "Bold": 700, "ExtraBold": 800}[weight],
        fsSelection=0x1A0 if weight == "Bold" else 0x1C0, fsType=0,
        achVendID="CHAO",
        ulCodePageRange1=1, ulCodePageRange2=0,
    )
    builder.setupPost()
    builder.setupMaxp()
    font = builder.font
    font["head"].fontRevision = 1.0
    if weight == "Bold":
        font["head"].macStyle = 1
    font.recalcTimestamp = False
    font["head"].created = 3876595200
    font["head"].modified = 3876595200
    source = save_ufo(font, family, weight, style, feature_text(characters, bounds), cmap)
    target = ROOT / "fonts" / "ttf" / f"{filename(style, weight)}.ttf"
    target.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run([sys.executable, "-m", "fontmake", "-u", str(source),
                    "-o", "ttf", "--output-path", str(target)],
                   capture_output=True, text=True, check=True)
    compiled = TTFont(target)
    compiled["OS/2"].fsType = 0
    compiled["head"].created = 3876595200
    compiled["head"].modified = 3876595200
    compiled.recalcTimestamp = False
    gasp = newTable("gasp")
    gasp.gaspRange = {65535: 0x000F}
    compiled["gasp"] = gasp
    meta = newTable("meta")
    meta.data = {"dlng": "Latn", "slng": "Latn"}
    compiled["meta"] = meta
    buildStatTable(compiled, [{"tag": "wght", "name": "Weight", "values": [
        {"value": {"Regular": 400, "Bold": 700, "ExtraBold": 800}[weight],
         "name": weight, "flags": 0x2 if weight == "Regular" else 0}
    ]}])
    compiled.save(target)
    web_target = ROOT / "fonts" / "webfonts" / f"{filename(style, weight)}.woff2"
    web_target.parent.mkdir(parents=True, exist_ok=True)
    save_woff2(target, web_target)
    print(f"{family} {weight}: {len(cmap)} characters -> TTF and WOFF2")


if __name__ == "__main__":
    characters = wanted_characters()
    for variant in STYLES:
        for weight in WEIGHTS[variant]:
            build(variant, weight, characters)
