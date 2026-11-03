"""Compile original centerline drawings into two scalable stitched TTF studies."""

from pathlib import Path
import sys

from fontTools.fontBuilder import FontBuilder
from fontTools.pens.ttGlyphPen import TTGlyphPen
from shapely.affinity import translate
from shapely.geometry import GeometryCollection, LineString, Point
from shapely.geometry.polygon import orient
from shapely.ops import substring, unary_union


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "source"))
from paths import GLYPHS  # noqa: E402


def outline(strokes, style):
    pieces = []
    grooves = []
    for points in strokes:
        line = LineString(points)
        if line.length < 25:
            pieces.append(Point(points[0]).buffer(30 if style == "Running" else 48, quad_segs=8))
            continue
        if style == "Running":
            for start in range(0, int(line.length) + 1, 94):
                segment = substring(line, start, min(start + 56, line.length))
                pieces.append(segment.buffer(15, cap_style="round", join_style="round", quad_segs=5))
        else:
            pieces.append(line.buffer(52, cap_style="round", join_style="round", quad_segs=6))
            for distance in range(26, int(line.length), 38):
                center = line.interpolate(distance)
                before = line.interpolate(max(0, distance - 4))
                after = line.interpolate(min(line.length, distance + 4))
                tangent_x = after.x - before.x
                tangent_y = after.y - before.y
                norm = max((tangent_x * tangent_x + tangent_y * tangent_y) ** 0.5, 1)
                normal_x = -tangent_y / norm
                normal_y = tangent_x / norm
                slit = LineString([
                    (center.x - normal_x * 34 - tangent_x / norm * 10,
                     center.y - normal_y * 34 - tangent_y / norm * 10),
                    (center.x + normal_x * 34 + tangent_x / norm * 10,
                     center.y + normal_y * 34 + tangent_y / norm * 10),
                ])
                grooves.append(slit.buffer(3, cap_style="round", quad_segs=3))
    shape = unary_union(pieces)
    if grooves:
        shape = shape.difference(unary_union(grooves))
    return shape.simplify(1.2, preserve_topology=True)


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


def build(style):
    family = "Threadline"
    glyph_order = [".notdef", "space"] + [f"uni{ord(char):04X}" for char in sorted(GLYPHS)]
    glyphs = {".notdef": to_glyph(Point(300, 350).buffer(200).boundary.buffer(30)), "space": TTGlyphPen(None).glyph()}
    metrics = {name: (600, 0) for name in glyph_order}
    metrics["space"] = (330, 0)
    cmap = {32: "space"}
    for char, strokes in GLYPHS.items():
        name = f"uni{ord(char):04X}"
        shape = outline(strokes, style)
        if char in "ilj!|':;.,`":
            shape = translate(shape, xoff=-140)
            metrics[name] = (350, 0)
        elif char in "ft()[]{}":
            metrics[name] = (560, 0)
        glyphs[name] = to_glyph(shape)
        cmap[ord(char)] = name
    builder = FontBuilder(1000, isTTF=True)
    builder.setupGlyphOrder(glyph_order)
    builder.setupCharacterMap(cmap)
    builder.setupGlyf(glyphs)
    builder.setupHorizontalMetrics(metrics)
    builder.setupHorizontalHeader(ascent=850, descent=-250)
    builder.setupNameTable({
        "familyName": family,
        "styleName": style,
        "uniqueFontIdentifier": f"Threadline {style} 0.1.0",
        "fullName": f"Threadline {style}",
        "psName": f"Threadline-{style}",
        "version": "Version 0.1.0",
        "copyright": "Copyright 2026 The Threadline Project Authors",
        "licenseDescription": "This Font Software is licensed under the SIL Open Font License, Version 1.1.",
        "licenseInfoURL": "https://openfontlicense.org/open-font-license-official-text/",
    })
    builder.setupOS2(
        sTypoAscender=850,
        sTypoDescender=-250,
        usWinAscent=850,
        usWinDescent=250,
        sxHeight=490,
        sCapHeight=700,
        usWeightClass=400 if style == "Running" else 700,
    )
    builder.setupPost()
    builder.setupMaxp()
    output = ROOT / "fonts" / f"Threadline-{style}.ttf"
    builder.save(output)
    print(output, len(cmap), "characters")


for variant in ("Running", "Satin"):
    build(variant)
