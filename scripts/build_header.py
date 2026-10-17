"""Build the animated profile header (light + dark SVG).

Usage: python scripts/build_header.py [username] [out_dir]
Downloads the GitHub avatar and embeds it, so the SVG has no external references.
"""
import base64
import datetime
import sys
import urllib.request
from pathlib import Path

USER = sys.argv[1] if len(sys.argv) > 1 else "Kiki544"
OUT = Path(sys.argv[2]) if len(sys.argv) > 2 else Path(__file__).resolve().parent.parent / "assets"

THEMES = {
    "light": dict(bg="#F3F1EA", ink="#1A1D1A", muted="#6B6F68", rule="#CFCBBF", accent="#D2462F", frame="#E4E0D5"),
    "dark": dict(bg="#121412", ink="#ECEAE3", muted="#8E928A", rule="#2C302B", accent="#FF6B4A", frame="#1E221E"),
}

# Photo panel and the "detected face" box inside it (tuned to the current avatar).
PX, PY, PS = 640, 76, 200
BOX = dict(x=PX + 60, y=PY + 28, w=88, h=100)


def fetch_avatar():
    req = urllib.request.Request(f"https://github.com/{USER}.png?size=400", headers={"User-Agent": "profile-header-builder"})
    with urllib.request.urlopen(req, timeout=30) as r:
        mime = r.headers.get_content_type() or "image/jpeg"
        return f"data:{mime};base64," + base64.b64encode(r.read()).decode()


def corner_paths(x, y, w, h, n=16):
    """Four L-shaped brackets, like a vision model's bounding box."""
    return [
        f"M{x},{y + n} V{y} H{x + n}",
        f"M{x + w - n},{y} H{x + w} V{y + n}",
        f"M{x + w},{y + h - n} V{y + h} H{x + w - n}",
        f"M{x + n},{y + h} H{x} V{y + h - n}",
    ]


def svg(t, photo):
    brackets = "\n    ".join(
        f'<path d="{d}" class="draw d4" pathLength="1" style="stroke-dasharray:1"/>' for d in corner_paths(**BOX)
    )
    return f"""<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="880" height="340" viewBox="0 0 880 340" role="img" aria-label="John Kikiiyin Aboderin. Models that see and read, and the software around them.">
  <style>
    .lbl {{ font: 600 11px Helvetica, Arial, sans-serif; letter-spacing: 2px; fill: {t["muted"]}; }}
    .name {{ font: 800 86px "Helvetica Neue", Helvetica, Arial, sans-serif; letter-spacing: -4px; fill: {t["ink"]}; }}
    .tag {{ font: italic 20px Georgia, "Times New Roman", serif; fill: {t["ink"]}; }}
    .mono {{ font: 600 10px "SFMono-Regular", Consolas, monospace; fill: {t["bg"]}; }}
    .rise {{ animation: rise 1s cubic-bezier(.2,.75,.2,1) both; }}
    .fade {{ animation: fade 1.1s ease both; }}
    .draw {{ fill: none; stroke: {t["accent"]}; stroke-width: 2.5; animation: draw .7s ease-out both; }}
    .rule {{ transform-box: fill-box; transform-origin: left; animation: grow 1.2s cubic-bezier(.2,.75,.2,1) both; }}
    .scan {{ animation: scan 5s ease-in-out 1.6s infinite both; }}
    .d1 {{ animation-delay: .15s; }} .d2 {{ animation-delay: .35s; }} .d3 {{ animation-delay: .8s; }} .d4 {{ animation-delay: 1.3s; }}
    @keyframes rise {{ from {{ transform: translateY(105px); }} }}
    @keyframes fade {{ from {{ opacity: 0; }} }}
    @keyframes draw {{ from {{ stroke-dashoffset: 1; }} to {{ stroke-dashoffset: 0; }} }}
    @keyframes grow {{ from {{ transform: scaleX(0); }} }}
    @keyframes scan {{ 0%, 100% {{ transform: translateY(0); opacity: 0; }} 8%, 92% {{ opacity: .9; }} 50% {{ transform: translateY({PS - 2}px); }} }}
    @media (prefers-reduced-motion: reduce) {{ * {{ animation: none !important; }} .scan {{ opacity: 0; }} }}
  </style>
  <defs>
    <clipPath id="line1"><rect x="30" y="72" width="600" height="104"/></clipPath>
    <clipPath id="line2"><rect x="30" y="164" width="600" height="104"/></clipPath>
    <clipPath id="photo"><rect x="{PX}" y="{PY}" width="{PS}" height="{PS}" rx="4"/></clipPath>
    <linearGradient id="trail" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="{t["accent"]}" stop-opacity="0"/>
      <stop offset="1" stop-color="{t["accent"]}" stop-opacity=".35"/>
    </linearGradient>
  </defs>

  <rect width="880" height="340" rx="8" fill="{t["bg"]}"/>

  <!-- masthead -->
  <rect x="40" y="33" width="9" height="9" fill="{t["accent"]}" class="fade"/>
  <text x="58" y="42" class="lbl fade">KIKI544 · JOHN KIKIIYIN ABODERIN</text>
  <text x="840" y="42" text-anchor="end" class="lbl fade">NOTEBOOK / {datetime.date.today().year}</text>
  <rect x="40" y="57" width="800" height="1" fill="{t["rule"]}" class="rule"/>

  <!-- name -->
  <g clip-path="url(#line1)"><text x="34" y="160" class="name rise d1">John Kikiiyin</text></g>
  <g clip-path="url(#line2)"><text x="34" y="252" class="name rise d2">Aboderin<tspan fill="{t["accent"]}">.</tspan></text></g>
  <text x="40" y="294" class="tag fade d3">Models that see and read, and the software around them.</text>

  <!-- photo, read like a computer-vision sample -->
  <rect x="{PX - 6}" y="{PY - 6}" width="{PS + 12}" height="{PS + 12}" rx="6" fill="{t["frame"]}" class="fade d1"/>
  <image href="{photo}" xlink:href="{photo}" x="{PX}" y="{PY}" width="{PS}" height="{PS}" clip-path="url(#photo)" preserveAspectRatio="xMidYMid slice" class="fade d2"/>
  <g clip-path="url(#photo)">
    <g class="scan"><rect x="{PX}" y="{PY - 40}" width="{PS}" height="40" fill="url(#trail)"/><rect x="{PX}" y="{PY - 1}" width="{PS}" height="2" fill="{t["accent"]}"/></g>
  </g>
  <g>
    {brackets}
  </g>
  <g class="fade d4">
    <rect x="{BOX["x"]}" y="{BOX["y"] - 18}" width="74" height="16" fill="{t["accent"]}"/>
    <text x="{BOX["x"] + 6}" y="{BOX["y"] - 6}" class="mono">kiki · 0.99</text>
  </g>
  <text x="{PX + PS}" y="{PY + PS + 22}" text-anchor="end" class="lbl fade d3">FIG. 1 — FACE DETECTED</text>

  <!-- footer rule -->
  <rect x="40" y="310" width="800" height="1" fill="{t["rule"]}" class="rule d2"/>
  <text x="40" y="328" class="lbl fade d3">MACHINE LEARNING · COMPUTER VISION · PYTHON · WEB</text>
  <text x="840" y="328" text-anchor="end" class="lbl fade d3">GITHUB.COM/{USER.upper()}</text>
</svg>
"""


def main():
    photo = fetch_avatar()
    OUT.mkdir(parents=True, exist_ok=True)
    for name, theme in THEMES.items():
        (OUT / f"header-{name}.svg").write_text(svg(theme, photo), encoding="utf-8")
        print(f"wrote {OUT / f'header-{name}.svg'}")


if __name__ == "__main__":
    main()
