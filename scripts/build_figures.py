"""Build the animated figures (light + dark SVG).

Usage: python scripts/build_figures.py [out_dir]
Fig. 2: handwritten characters are drawn into form boxes, "recognised" with a
confidence bar each, then the decoded line types out, like the OCR project.
Fig. 3: a real photo of a tomato leaf with early blight is scanned, lesions get
boxed, and the five classes race to a diagnosis, like the tomato disease project.
Leaf photo: Clemson University - USDA Cooperative Extension Slide Series,
Bugwood.org, CC BY 3.0 US, via Wikimedia Commons (cropped).
"""
import base64
import random
import sys
import urllib.request
from pathlib import Path

OUT = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parent.parent / "assets"

THEMES = {
    "light": dict(bg="#F3F1EA", ink="#1A1D1A", muted="#6B6F68", rule="#CFCBBF", accent="#D2462F", cell="#E4E0D5", good="#4F8463"),
    "dark": dict(bg="#121412", ink="#ECEAE3", muted="#8E928A", rule="#2C302B", accent="#FF6B4A", cell="#1E221E", good="#8FC9A2"),
}

TEXT = "HELLO, I'M KIKI"
CELL_W, CELL_H, X0, Y0 = 44, 56, 110, 92
DRAW = 0.45      # seconds to draw one character
STEP = 0.18      # stagger between characters
WIDTH, HEIGHT = 880, 330


def svg(t):
    rng = random.Random(544)  # fixed seed, so rebuilds don't change the file
    cells, preds = [], []
    for i, ch in enumerate(TEXT):
        x = X0 + i * CELL_W
        cx = x + CELL_W / 2 - 2
        delay = 0.6 + i * STEP
        if ch == " ":
            continue
        tilt = rng.uniform(-8, 6)
        nudge = rng.uniform(-3, 3)
        conf = rng.uniform(0.86, 0.99)
        pdelay = 0.6 + len(TEXT) * STEP + DRAW + i * 0.09
        cells.append(
            f'<rect x="{x + 3}" y="{Y0}" width="{CELL_W - 6}" height="{CELL_H}" rx="3" fill="{t["cell"]}"/>'
            f'<text x="{cx:.1f}" y="{Y0 + 42 + nudge:.1f}" text-anchor="middle" transform="rotate({tilt:.1f} {cx:.1f} {Y0 + 28})" '
            f'class="hand" style="animation-delay:{delay:.2f}s,{delay + DRAW:.2f}s">{ch.replace("&", "&amp;")}</text>'
        )
        preds.append(
            f'<g class="pop" style="animation-delay:{pdelay:.2f}s">'
            f'<text x="{x + CELL_W / 2}" y="{Y0 + CELL_H + 46}" text-anchor="middle" class="pred">{ch.lower()}</text>'
            f'<rect x="{x + 8}" y="{Y0 + CELL_H + 56}" width="{CELL_W - 16}" height="4" rx="2" fill="{t["cell"]}"/>'
            f'<rect x="{x + 8}" y="{Y0 + CELL_H + 56}" width="{(CELL_W - 16) * conf:.1f}" height="4" rx="2" fill="{t["good"]}"/>'
            f'<text x="{x + CELL_W / 2}" y="{Y0 + CELL_H + 74}" text-anchor="middle" class="conf">{conf:.2f}</text>'
            f'</g>'
        )

    end = 0.6 + len(TEXT) * STEP + DRAW + len(TEXT) * 0.09 + 0.4
    decoded = TEXT.lower()
    typed = "".join(
        f'<tspan class="type" style="animation-delay:{end + i * 0.07:.2f}s">{c.replace("&", "&amp;")}</tspan>'
        for i, c in enumerate(decoded)
    )
    cursor_x = 252 + len(decoded) * 11

    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{HEIGHT}" viewBox="0 0 {WIDTH} {HEIGHT}" role="img" aria-label="Animated figure: handwritten characters spelling HELLO, I'M KIKI are recognised one by one and decoded into text.">
  <style>
    .lbl {{ font: 600 11px Helvetica, Arial, sans-serif; letter-spacing: 2px; fill: {t["muted"]}; }}
    .hand {{ font: italic 40px Georgia, "Times New Roman", serif; fill: {t["ink"]}; stroke: {t["ink"]}; stroke-width: 1;
             stroke-dasharray: 160; animation: write {DRAW}s ease-out both, ink .3s ease both; }}
    .pred {{ font: 600 22px "SFMono-Regular", Consolas, monospace; fill: {t["accent"]}; }}
    .conf {{ font: 9px "SFMono-Regular", Consolas, monospace; fill: {t["muted"]}; }}
    .out {{ font: 600 20px "SFMono-Regular", Consolas, monospace; fill: {t["ink"]}; }}
    .pop {{ animation: pop .35s cubic-bezier(.2,.75,.2,1) both; }}
    .type {{ animation: show .01s linear both; }}
    .blink {{ animation: blink 1s steps(1) {end + len(decoded) * 0.07:.2f}s infinite both; }}
    .scan {{ animation: scan {len(TEXT) * STEP + DRAW:.2f}s linear .6s both; }}
    @keyframes write {{ from {{ stroke-dashoffset: 160; }} to {{ stroke-dashoffset: 0; }} }}
    @keyframes ink {{ from {{ fill-opacity: 0; }} to {{ fill-opacity: 1; }} }}
    @keyframes pop {{ from {{ opacity: 0; transform: translateY(6px); }} }}
    @keyframes show {{ from {{ opacity: 0; }} }}
    @keyframes blink {{ 0% {{ opacity: 1; }} 50% {{ opacity: 0; }} }}
    @keyframes scan {{ from {{ transform: translateX(0); opacity: 1; }} 99% {{ opacity: 1; }} to {{ transform: translateX({len(TEXT) * CELL_W}px); opacity: 0; }} }}
    @media (prefers-reduced-motion: reduce) {{ * {{ animation: none !important; }} .scan {{ opacity: 0; }} }}
  </style>
  <rect width="{WIDTH}" height="{HEIGHT}" rx="8" fill="{t["bg"]}"/>

  <rect x="40" y="33" width="9" height="9" fill="{t["accent"]}"/>
  <text x="58" y="42" class="lbl">FIG. 2 — READING HANDWRITING</text>
  <text x="840" y="42" text-anchor="end" class="lbl">OCR · CNN + LSTM</text>
  <rect x="40" y="57" width="800" height="1" fill="{t["rule"]}"/>

  <text x="40" y="{Y0 + 34}" class="lbl">INPUT</text>
  {"".join(cells)}
  <rect x="{X0}" y="{Y0 - 6}" width="2" height="{CELL_H + 12}" fill="{t["accent"]}" class="scan"/>

  <text x="40" y="{Y0 + CELL_H + 46}" class="lbl">READ</text>
  {"".join(preds)}

  <rect x="40" y="{HEIGHT - 72}" width="800" height="1" fill="{t["rule"]}"/>
  <text x="40" y="{HEIGHT - 34}" class="lbl">OUTPUT</text>
  <text x="250" y="{HEIGHT - 32}" class="out">{typed}</text>
  <rect x="{cursor_x:.0f}" y="{HEIGHT - 50}" width="10" height="22" fill="{t["accent"]}" class="blink"/>
  <text x="840" y="{HEIGHT - 34}" text-anchor="end" class="lbl pop" style="animation-delay:{end + len(decoded) * 0.07:.2f}s">EDIT DISTANCE 0</text>
</svg>
"""


# Fig. 3: the five classes from the tomato model, with where each bar wanders
# during the "race" before settling on its final probability.
CLASSES = [
    ("Early blight", [0.30, 0.55, 0.81, 0.92]),
    ("Bacterial spot", [0.45, 0.38, 0.12, 0.04]),
    ("Yellow leaf curl", [0.20, 0.30, 0.06, 0.02]),
    ("Mosaic virus", [0.25, 0.10, 0.03, 0.01]),
    ("Healthy", [0.40, 0.18, 0.05, 0.01]),
]

LEAF_PHOTO = ("https://upload.wikimedia.org/wikipedia/commons/thumb/0/04/"
              "Alternaria_solani_-_leaf_lesions.jpg/500px-Alternaria_solani_-_leaf_lesions.jpg")
# The photo is shown in a 330x228 panel, cropped to the 760x525 region at
# (110, 320) of the 960px original (which also drops the corner watermark).
PANEL = dict(x=40, y=72, w=330, h=228)
CROP_X, CROP_Y, CROP_W, PHOTO_W = 110, 320, 760, 960
# Boxes around the three lesions in the photo, in panel coordinates.
LESION_BOXES = [(53, 76, 46, 114), (199, 116, 58, 70), (93, 247, 139, 52)]


def fetch_photo(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Kiki544-profile-builder/1.0 (github.com/Kiki544)"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return "data:image/jpeg;base64," + base64.b64encode(r.read()).decode()


def svg_leaf(t, photo):
    rows, keyframes = [], []
    for i, (name, path) in enumerate(CLASSES):
        y = 104 + i * 38
        final = path[-1]
        win = i == 0
        stops = " ".join(
            f"{p}% {{ transform: scaleX({v}); }}" for p, v in zip((25, 50, 75, 100), path)
        )
        keyframes.append(f"@keyframes r{i} {{ 0% {{ transform: scaleX(0); }} {stops} }}")
        rows.append(
            f'<text x="430" y="{y + 9}" class="cls{" win" if win else ""}">{name}</text>'
            f'<rect x="572" y="{y}" width="220" height="10" rx="2" fill="{t["cell"]}"/>'
            f'<rect x="572" y="{y}" width="220" height="10" rx="2" fill="{t["accent"] if win else t["good"]}" '
            f'class="race" style="transform: scaleX({final}); animation-name: r{i}"/>'
            f'<text x="840" y="{y + 9}" text-anchor="end" class="val fade" style="animation-delay:3.3s">{final:.2f}</text>'
        )

    boxes = "".join(
        f'<rect x="{x}" y="{y}" width="{w}" height="{h}" pathLength="1" class="box" style="animation-delay:{2.1 + i * 0.2:.1f}s"/>'
        for i, (x, y, w, h) in enumerate(LESION_BOXES)
    )
    p = PANEL
    scale = p["w"] / CROP_W
    img_x, img_y, img_size = p["x"] - CROP_X * scale, p["y"] - CROP_Y * scale, PHOTO_W * scale

    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="880" height="340" viewBox="0 0 880 340" role="img" aria-label="Animated figure: a photo of a tomato leaf is scanned, three lesions are boxed, and five disease classes race until early blight wins at 0.92.">
  <style>
    .lbl {{ font: 600 11px Helvetica, Arial, sans-serif; letter-spacing: 2px; fill: {t["muted"]}; }}
    .cls {{ font: 13px Helvetica, Arial, sans-serif; fill: {t["muted"]}; }}
    .win {{ fill: {t["ink"]}; font-weight: 700; }}
    .val {{ font: 600 12px "SFMono-Regular", Consolas, monospace; fill: {t["ink"]}; }}
    .dx {{ font: 400 34px Georgia, "Times New Roman", serif; fill: {t["ink"]}; }}
    .box {{ fill: none; stroke: {t["accent"]}; stroke-width: 2; stroke-dasharray: 1; animation: draw .5s ease-out both; }}
    .race {{ transform-box: fill-box; transform-origin: left; animation-duration: 2.4s; animation-delay: .9s;
             animation-timing-function: cubic-bezier(.3,.6,.3,1); animation-fill-mode: both; }}
    .fade {{ animation: fade .6s ease both; }}
    .leafin {{ animation: fade .8s ease both; }}
    .scan {{ animation: scan 1.8s ease-in-out .6s both; }}
    @keyframes draw {{ from {{ stroke-dashoffset: 1; }} to {{ stroke-dashoffset: 0; }} }}
    @keyframes fade {{ from {{ opacity: 0; }} }}
    @keyframes scan {{ from {{ transform: translateY(0); opacity: 1; }} 95% {{ opacity: 1; }} to {{ transform: translateY({p["h"]}px); opacity: 0; }} }}
    {" ".join(keyframes)}
    @media (prefers-reduced-motion: reduce) {{ * {{ animation: none !important; }} .scan {{ opacity: 0; }} }}
  </style>
  <defs>
    <clipPath id="panel"><rect x="{p["x"]}" y="{p["y"]}" width="{p["w"]}" height="{p["h"]}" rx="4"/></clipPath>
    <linearGradient id="trail" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="{t["accent"]}" stop-opacity="0"/>
      <stop offset="1" stop-color="{t["accent"]}" stop-opacity=".3"/>
    </linearGradient>
  </defs>
  <rect width="880" height="340" rx="8" fill="{t["bg"]}"/>

  <rect x="40" y="33" width="9" height="9" fill="{t["accent"]}"/>
  <text x="58" y="42" class="lbl">FIG. 3 — DIAGNOSING A LEAF</text>
  <text x="840" y="42" text-anchor="end" class="lbl">KERAS CNN · 5 CLASSES</text>
  <rect x="40" y="57" width="800" height="1" fill="{t["rule"]}"/>

  <!-- the leaf photo -->
  <g clip-path="url(#panel)">
    <image href="{photo}" x="{img_x:.1f}" y="{img_y:.1f}" width="{img_size:.1f}" height="{img_size:.1f}" class="leafin"/>
    <g class="scan"><rect x="{p["x"]}" y="{p["y"] - 40}" width="{p["w"]}" height="40" fill="url(#trail)"/><rect x="{p["x"]}" y="{p["y"] - 1}" width="{p["w"]}" height="2" fill="{t["accent"]}"/></g>
  </g>
  {boxes}
  <text x="40" y="318" class="lbl fade" style="animation-delay:2.6s">3 LESIONS FOUND</text>
  <text x="40" y="332" class="lbl" style="font-size:8.5px;letter-spacing:1px">PHOTO: CLEMSON UNIV. · BUGWOOD.ORG · CC BY 3.0 US</text>

  <!-- the race -->
  <text x="430" y="84" class="lbl">CLASS PROBABILITIES</text>
  {"".join(rows)}
  <rect x="430" y="290" width="410" height="1" fill="{t["rule"]}"/>
  <g class="fade" style="animation-delay:3.4s">
    <text x="430" y="326" class="lbl">DIAGNOSIS</text>
    <text x="540" y="328" class="dx">Early blight<tspan fill="{t["accent"]}">.</tspan></text>
  </g>
</svg>
"""


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    photo = fetch_photo(LEAF_PHOTO)
    for name, theme in THEMES.items():
        for stem, build in (("fig-ocr", svg), ("fig-leaf", lambda t: svg_leaf(t, photo))):
            path = OUT / f"{stem}-{name}.svg"
            path.write_text(build(theme), encoding="utf-8")
            print(f"wrote {path}")


if __name__ == "__main__":
    main()
