# Design and release checklist

## Game candidate

- [x] Draw original uppercase, lowercase, numerals, punctuation, and useful accented Latin letters.
- [x] Build the earlier studies and a Stitched display face with a related Stitched UI face.
- [x] Export installable TTF and WOFF2 files from editable source drawings.
- [x] Render matched large and 390 by 844 pixel phone specimens on light and dark backgrounds.
- [x] Check character mapping, font names, outlines, metrics, kerning presence, and WOFF2 decoding.
- [x] Repeat the build and compare output hashes.
- [ ] Review Stitched and Stitched UI inside the Godot 4.7 game on an Android phone.
- [ ] Refine spacing and curves after actual device review, including small instruction text.

## Public gallery gate

- [ ] Audit against the [current GF Latin Core glyphset](https://github.com/googlefonts/glyphsets/blob/main/GLYPHSETS.md) and add missing characters and marks.
- [ ] Export UFO editor sources from the Python drawings and keep them in the repository.
- [ ] Run the [Fontspector Google Fonts profile](https://googlefonts.github.io/gf-guide/qa.html) and resolve its findings.
- [ ] Test installation and rendering in browsers, desktop apps, Godot, Android, and print.
- [ ] Ask a type designer to review outlines, accents, spacing, and language coverage.
- [ ] Add CI for production builds and validation.
- [ ] Submit only after the [Google Fonts production requirements](https://googlefonts.github.io/gf-guide/production.html) are met.
