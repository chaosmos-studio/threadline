"""Check that both proof fonts contain the intended printable glyph set."""

from pathlib import Path

from fontTools.ttLib import TTFont


root = Path(__file__).resolve().parents[1]
expected = set(range(32, 127))
for style in ("Running", "Satin"):
    path = root / "fonts" / f"Threadline-{style}.ttf"
    font = TTFont(path)
    mapped = set(font.getBestCmap())
    assert mapped == expected, (style, sorted(expected - mapped), sorted(mapped - expected))
    assert font["head"].unitsPerEm == 1000
    assert font["name"].getDebugName(4) == f"Threadline {style}"
    for codepoint, glyph_name in font.getBestCmap().items():
        if codepoint != 32:
            assert font["glyf"][glyph_name].numberOfContours > 0, (style, codepoint)
    print(f"{style}: {len(mapped)} glyphs, valid names and outlines")
