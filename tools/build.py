"""Build the Threadline designs from their editable centerlines."""

from pathlib import Path
from math import atan2, degrees
import subprocess
import sys
import types
import unicodedata

from fontTools.feaLib.builder import addOpenTypeFeaturesFromString
from fontTools.fontBuilder import FontBuilder
from fontTools.pens.ttGlyphPen import TTGlyphPen
from shapely.affinity import rotate, scale, translate
from shapely.geometry import GeometryCollection, LineString, Point
from shapely.geometry.polygon import orient
from shapely.ops import substring, unary_union


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "source"))
from paths import ACCENTS, CHAIN_GLYPHS, GLYPHS, STITCHED_GLYPHS  # noqa: E402

STYLES = ("Running", "Satin", "Applique", "Plain", "Woven", "Chain", "Stitched", "StitchedUI")
NARROW = "iljı!|':;.,`‘’¡"
PAIR_VALUES = {
    "AV": -55, "AW": -35, "AY": -50, "AT": -30, "FA": -30,
    "LT": -30, "LY": -45, "PA": -25, "TA": -45, "Te": -35,
    "Th": -20, "To": -45, "Tu": -25, "VA": -55, "Ve": -30,
    "Vo": -35, "WA": -35, "Wo": -25, "YA": -50, "Ye": -40,
    "Yo": -45, "Wa": -20, "We": -20, "ry": -15,
}


def wanted_characters():
    characters = set(GLYPHS)
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


def form(strokes, style):
    pieces = []
    cuts = []
    stitch_layers = []
    for points in strokes:
        if style in ("Woven", "Chain", "Stitched", "StitchedUI"):
            width_scale = {"Woven": 1.25, "Chain": 1.14,
                           "Stitched": 1.12, "StitchedUI": 1.12}[style]
            points = [(x * width_scale, y) for x, y in points]
        if style == "Chain":
            points = softened(points)
        line = LineString(points)
        if line.length < 25:
            dot_radius = 24 if style == "Running" else 60 if style == "Stitched" else 49 if style in ("Chain", "StitchedUI") else 34
            pieces.append(Point(points[0]).buffer(dot_radius, quad_segs=8))
            if style == "Stitched":
                stitch_layers.append(GeometryCollection())
            continue
        if style == "Running":
            for start in range(0, int(line.length) + 1, 108):
                segment = substring(line, start, min(start + 55, line.length))
                if segment.length:
                    pieces.append(segment.buffer(16, cap_style="round", join_style="round", quad_segs=4))
        else:
            radius = {"Satin": 43, "Applique": 55, "Plain": 36,
                      "Woven": 77, "Chain": 78, "Stitched": 104, "StitchedUI": 72}[style]
            pieces.append(line.buffer(radius, cap_style="round", join_style="round", quad_segs=5))
            if style in ("Satin", "Applique", "Woven"):
                step = {"Satin": 31, "Applique": 48, "Woven": 29}[style]
                for stitch_index, distance in enumerate(range(24, int(line.length) - 15, step)):
                    before = line.interpolate(max(0, distance - 5))
                    after = line.interpolate(min(line.length, distance + 5))
                    dx, dy = after.x - before.x, after.y - before.y
                    length = max((dx * dx + dy * dy) ** 0.5, 1)
                    nx, ny = -dy / length, dx / length
                    center = line.interpolate(distance)
                    if style in ("Satin", "Woven"):
                        half_width = 29 if style == "Satin" else 53
                        skew = 5 if style == "Satin" else 10 + 2 * (stitch_index % 4)
                        slit = LineString([
                            (center.x - nx * half_width - dx / length * skew,
                             center.y - ny * half_width - dy / length * skew),
                            (center.x + nx * half_width + dx / length * skew,
                             center.y + ny * half_width + dy / length * skew),
                        ])
                        cuts.append(slit.buffer(2.8 if style == "Satin" else 5,
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
            elif style == "Chain":
                for stitch_index, distance in enumerate(range(45, int(line.length) - 20, 96)):
                    center = line.interpolate(distance)
                    before = line.interpolate(max(0, distance - 5))
                    after = line.interpolate(min(line.length, distance + 5))
                    dx, dy = after.x - before.x, after.y - before.y
                    length = max((dx * dx + dy * dy) ** 0.5, 1)
                    eye = scale(Point(0, 0).buffer(1, quad_segs=10), xfact=20, yfact=7)
                    eye = rotate(eye, degrees(atan2(dy, dx)), origin=(0, 0))
                    cuts.append(translate(eye, xoff=center.x, yoff=center.y))
                    side = -1 if stitch_index % 2 else 1
                    entry = Point(center.x - dy / length * side * 75,
                                  center.y + dx / length * side * 75).buffer(5, quad_segs=6)
                    cuts.append(entry)
            elif style == "Stitched":
                intervals = (16, 17, 15, 18, 16, 19)
                distance = 12
                stitch_index = 0
                stitch_cuts = []
                while distance < line.length - 8:
                    center = line.interpolate(distance)
                    before = line.interpolate(max(0, distance - 4))
                    after = line.interpolate(min(line.length, distance + 4))
                    dx, dy = after.x - before.x, after.y - before.y
                    length = max((dx * dx + dy * dy) ** 0.5, 1)
                    nx, ny = -dy / length, dx / length
                    half_width = 107 if stitch_index % 7 == 0 else 94 + stitch_index % 4
                    skew = (-5, -2, 0, 3, 5)[stitch_index % 5]
                    slit = LineString([
                        (center.x - nx * half_width - dx / length * skew,
                         center.y - ny * half_width - dy / length * skew),
                        (center.x + nx * 2, center.y + ny * 2),
                        (center.x + nx * half_width + dx / length * skew,
                         center.y + ny * half_width + dy / length * skew),
                    ])
                    stitch_cuts.append(slit.buffer(2.1, cap_style="round", join_style="round", quad_segs=2))
                    distance += intervals[stitch_index % len(intervals)]
                    stitch_index += 1
                stitch_layers.append(unary_union(stitch_cuts))
    shape = unary_union(pieces)
    if style == "Stitched":
        covered = GeometryCollection()
        visible_cuts = []
        for piece, layer_cuts in reversed(list(zip(pieces, stitch_layers))):
            visible_cuts.append(layer_cuts.difference(covered))
            covered = covered.union(piece)
        shape = shape.difference(unary_union(visible_cuts))
    if cuts:
        shape = shape.difference(unary_union(cuts))
    return shape.simplify(1.4, preserve_topology=True)


def glyph_geometry(char, style):
    if char in GLYPHS:
        overrides = CHAIN_GLYPHS if style == "Chain" else STITCHED_GLYPHS if style in ("Stitched", "StitchedUI") else {}
        strokes = overrides.get(char, GLYPHS[char])
        shape = form(strokes, style)
    else:
        parts = unicodedata.normalize("NFD", char)
        base = "ı" if parts[0] == "i" else parts[0]
        overrides = CHAIN_GLYPHS if style == "Chain" else STITCHED_GLYPHS if style in ("Stitched", "StitchedUI") else {}
        base_strokes = overrides.get(base, GLYPHS[base])
        if base == "j":
            base_strokes = base_strokes[:1]
        shape = form(base_strokes, style)
        top = shape.bounds[3]
        marks = []
        for mark in parts[1:]:
            mark_shape = form(ACCENTS[mark], "Plain" if style in ("Chain", "Stitched", "StitchedUI") else style)
            if mark in ("\u0327", "\u0328"):
                mark_shape = translate(mark_shape, yoff=-25)
            else:
                mark_shape = translate(mark_shape, yoff=top - 700 + (45 if style in ("Chain", "Stitched", "StitchedUI") else 0))
            if style in ("Chain", "Stitched", "StitchedUI"):
                mark_shape = translate(mark_shape, xoff=42 if style == "Chain" else 36)
            marks.append(mark_shape)
        shape = unary_union([shape, *marks])
    if style in ("Woven", "Chain", "Stitched", "StitchedUI"):
        if style == "Chain":
            tilt = (-4.0, -1.6, 1.5, 3.6, 0.0)[ord(char) % 5]
            lift = (-27, 0, 24)[ord(char) % 3]
            shape = rotate(shape, tilt, origin="center")
            shape = translate(shape, yoff=lift)
        bearing = 45 if style == "Woven" else 35
        shape = translate(shape, xoff=bearing - shape.bounds[0])
    elif is_narrow(char):
        shape = translate(shape, xoff=-140)
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


def add_kerning(font, characters):
    pairs = []
    for pair, value in PAIR_VALUES.items():
        if all(char in characters for char in pair):
            pairs.append(f"    pos uni{ord(pair[0]):04X} uni{ord(pair[1]):04X} {value};")
    feature = "feature kern {\n" + "\n".join(pairs) + "\n} kern;"
    addOpenTypeFeaturesFromString(font, feature)


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


def save_woff2(path):
    ensure_brotli()
    from fontTools.ttLib import woff2

    woff2.compress(str(path.with_suffix(".ttf")), str(path))


def build(style, characters):
    family = "Threadline Stitched UI" if style == "StitchedUI" else f"Threadline {style}"
    ascent = 1120 if style in ("Stitched", "StitchedUI") else 1100 if style == "Chain" else 1050 if style == "Woven" else 1000
    descent = 330 if style in ("Stitched", "StitchedUI") else 320 if style in ("Woven", "Chain") else 300
    order = [".notdef", "space"] + [f"uni{ord(char):04X}" for char in sorted(characters)]
    notdef = Point(300, 350).buffer(225).boundary.buffer(28)
    glyphs = {".notdef": to_glyph(notdef), "space": TTGlyphPen(None).glyph()}
    metrics = {".notdef": (600, 47), "space": (320, 0)}
    cmap = {32: "space"}
    for char in sorted(characters):
        name = f"uni{ord(char):04X}"
        shape = glyph_geometry(char, style)
        if style in ("Woven", "Chain", "Stitched", "StitchedUI"):
            advance = round(shape.bounds[2] + (45 if style == "Woven" else 35))
        elif is_narrow(char):
            advance = 350
        elif char in "ft()[]{}":
            advance = 560
        else:
            advance = 600
        glyphs[name] = to_glyph(shape)
        metrics[name] = (advance, round(shape.bounds[0]))
        cmap[ord(char)] = name
    builder = FontBuilder(1000, isTTF=True)
    builder.setupGlyphOrder(order)
    builder.setupCharacterMap(cmap)
    builder.setupGlyf(glyphs)
    builder.setupHorizontalMetrics(metrics)
    builder.setupHorizontalHeader(ascent=ascent, descent=-descent)
    builder.setupNameTable({
        "familyName": family,
        "styleName": "Regular",
        "uniqueFontIdentifier": f"{family} 0.2.0",
        "fullName": family,
        "psName": f"Threadline{style}-Regular",
        "version": "Version 0.2.0",
        "copyright": "Copyright 2026 The Threadline Project Authors",
        "licenseDescription": "This Font Software is licensed under the SIL Open Font License, Version 1.1.",
        "licenseInfoURL": "https://openfontlicense.org/open-font-license-official-text/",
    })
    builder.setupOS2(
        version=4,
        sTypoAscender=ascent, sTypoDescender=-descent,
        usWinAscent=ascent, usWinDescent=descent,
        sxHeight=490, sCapHeight=700,
        usWeightClass=800 if style in ("Woven", "Stitched") else 400 if style in ("Running", "Plain") else 700,
        fsSelection=0xC0, fsType=0,
    )
    builder.setupPost()
    builder.setupMaxp()
    font = builder.font
    font.recalcTimestamp = False
    font["head"].created = 3876595200
    font["head"].modified = 3876595200
    add_kerning(font, characters)
    target = ROOT / "fonts" / f"Threadline-{style}.ttf"
    font.save(target)
    save_woff2(target.with_suffix(".woff2"))
    print(f"{family}: {len(cmap)} characters -> TTF and WOFF2")


if __name__ == "__main__":
    characters = wanted_characters()
    for variant in STYLES:
        build(variant, characters)
