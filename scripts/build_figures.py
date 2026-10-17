"""Build the animated OCR figure (light + dark SVG).

Usage: python scripts/build_figures.py [out_dir]
Handwritten characters are drawn into form boxes, then "recognised" with a
confidence bar each, then the decoded line types out, like the OCR project.
"""
import random
import sys
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


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    for name, theme in THEMES.items():
        path = OUT / f"fig-ocr-{name}.svg"
        path.write_text(svg(theme), encoding="utf-8")
        print(f"wrote {path}")


if __name__ == "__main__":
    main()
