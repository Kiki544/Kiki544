"""Build the contribution activity graph (light + dark SVG).

Usage: python scripts/build_activity.py [username] [out_dir]
Reads the public contribution calendar on github.com, so it needs no token.
"""
import datetime as dt
import math
import re
import sys
import urllib.request
from pathlib import Path

USER = sys.argv[1] if len(sys.argv) > 1 else "Kiki544"
OUT = Path(sys.argv[2]) if len(sys.argv) > 2 else Path(__file__).resolve().parent.parent / "assets"
FIRST_YEAR = 2023

THEMES = {
    "light": dict(bg="#F3F1EA", ink="#1A1D1A", muted="#6B6F68", rule="#CFCBBF", accent="#D2462F",
                  levels=["#E4E0D5", "#BFD3C3", "#86AE92", "#4F8463", "#2F5B42"]),
    "dark": dict(bg="#121412", ink="#ECEAE3", muted="#8E928A", rule="#2C302B", accent="#FF6B4A",
                 levels=["#1E221E", "#2B4A37", "#3F6E50", "#5E9C74", "#8FC9A2"]),
}

CELL, GAP = 10, 2
GRID_X, GRID_Y = 220, 92
WIDTH, HEIGHT = 880, 320


def calendar(frm=None, to=None):
    """Return {date: count} from the public contributions calendar."""
    url = f"https://github.com/users/{USER}/contributions"
    if frm:
        url += f"?from={frm}&to={to}"
    req = urllib.request.Request(url, headers={"User-Agent": "profile-activity-builder"})
    with urllib.request.urlopen(req, timeout=30) as r:
        page = r.read().decode("utf-8")
    dates = {cid: d for d, cid in re.findall(r'data-date="(\d{4}-\d\d-\d\d)"\s+id="(contribution-day-component-[\d-]+)"', page)}
    counts = {}
    for cid, n in re.findall(r'for="(contribution-day-component-[\d-]+)"[^>]*>(\d+|No) contributions?', page):
        if cid in dates:
            counts[dt.date.fromisoformat(dates[cid])] = 0 if n == "No" else int(n)
    if not counts:
        raise SystemExit("Could not read the contribution calendar; GitHub may have changed its markup.")
    return counts


def level(n, peak):
    # square-root scale, so one very busy day doesn't wash out the rest
    return 0 if n == 0 else max(1, min(4, math.ceil(4 * math.sqrt(n / peak))))


def svg(t, days, years, today):
    start = min(days)
    peak = max(days.values()) or 1
    busiest = max(days, key=lambda d: (days[d], d))
    total = sum(days.values())
    active = sum(1 for n in days.values() if n)

    cells, months = [], []
    for d, n in sorted(days.items()):
        col = ((d - start).days + (start.weekday() + 1) % 7) // 7
        row = (d.weekday() + 1) % 7  # Sunday first, like GitHub
        x, y = GRID_X + col * (CELL + GAP), GRID_Y + row * (CELL + GAP)
        extra = f' stroke="{t["accent"]}" stroke-width="2"' if d == busiest and n else ""
        cells.append(f'<rect x="{x}" y="{y}" width="{CELL}" height="{CELL}" rx="2" fill="{t["levels"][level(n, peak)]}"{extra} '
                     f'class="cell" style="animation-delay:{col * 22}ms"><title>{n} on {d:%b} {d.day}, {d.year}</title></rect>')
        if d.day == 1 or d == start:
            months.append((x, d.strftime("%b").upper()))
    # drop a month label that would collide with the next one
    months = [m for i, m in enumerate(months) if i + 1 == len(months) or months[i + 1][0] - m[0] >= 30]
    month_labels = "\n    ".join(f'<text x="{x}" y="{GRID_Y - 10}" class="lbl small">{m}</text>' for x, m in months)

    year_max = max(years.values()) or 1
    bar_rows = []
    for i, (yr, n) in enumerate(sorted(years.items())):
        y = 236 + i * 18
        w = max(2, round(420 * n / year_max)) if n else 0
        bar_rows.append(
            f'<text x="{GRID_X}" y="{y + 9}" class="lbl">{yr}</text>'
            f'<rect x="{GRID_X + 52}" y="{y}" width="{w}" height="10" rx="2" fill="{t["levels"][3]}" class="bar" style="animation-delay:{900 + i * 120}ms"/>'
            f'<text x="{GRID_X + 60 + w}" y="{y + 9}" class="num">{n}</text>'
        )
    bars = "\n    ".join(bar_rows)
    grid_bottom = GRID_Y + 7 * (CELL + GAP)

    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{HEIGHT}" viewBox="0 0 {WIDTH} {HEIGHT}" role="img" aria-label="{USER} contributions: {total} in the last 12 months across {active} active days.">
  <style>
    .lbl {{ font: 600 11px Helvetica, Arial, sans-serif; letter-spacing: 2px; fill: {t["muted"]}; }}
    .small {{ font-size: 10px; letter-spacing: 1.5px; }}
    .big {{ font: 400 64px Georgia, "Times New Roman", serif; fill: {t["ink"]}; }}
    .txt {{ font: 14px Georgia, "Times New Roman", serif; fill: {t["ink"]}; }}
    .num {{ font: 600 11px Helvetica, Arial, sans-serif; fill: {t["ink"]}; }}
    .cell {{ transform-box: fill-box; transform-origin: center; animation: pop .45s cubic-bezier(.2,.75,.2,1) both; }}
    .bar {{ transform-box: fill-box; transform-origin: left; animation: grow 1s cubic-bezier(.2,.75,.2,1) both; }}
    .fade {{ animation: fade 1s ease both; }}
    @keyframes pop {{ from {{ opacity: 0; transform: scale(.3); }} }}
    @keyframes grow {{ from {{ transform: scaleX(0); }} }}
    @keyframes fade {{ from {{ opacity: 0; }} }}
    @media (prefers-reduced-motion: reduce) {{ * {{ animation: none !important; }} }}
  </style>
  <rect width="{WIDTH}" height="{HEIGHT}" rx="8" fill="{t["bg"]}"/>

  <rect x="40" y="33" width="9" height="9" fill="{t["accent"]}"/>
  <text x="58" y="42" class="lbl">CONTRIBUTIONS · LAST 12 MONTHS</text>
  <text x="840" y="42" text-anchor="end" class="lbl">SNAPSHOT {today:%d %b %Y}</text>
  <rect x="40" y="57" width="800" height="1" fill="{t["rule"]}"/>

  <g class="fade">
    <text x="38" y="130" class="big">{total}</text>
    <text x="40" y="158" class="txt">contributions</text>
    <text x="40" y="{grid_bottom}" class="lbl small">{active} ACTIVE DAYS</text>
    <text x="40" y="{grid_bottom + 18}" class="lbl small">BUSIEST · {busiest:%b} {busiest.day} ({days[busiest]})</text>
  </g>

  <g>
    {month_labels}
  </g>
  <g>
    {"".join(cells)}
  </g>

  <rect x="40" y="214" width="800" height="1" fill="{t["rule"]}"/>
  <text x="40" y="245" class="lbl">BY YEAR</text>
  <g>
    {bars}
  </g>
</svg>
"""


def main():
    today = dt.date.today()
    days = calendar()
    years = {}
    for yr in range(FIRST_YEAR, today.year + 1):
        years[yr] = sum(calendar(f"{yr}-01-01", f"{yr}-12-31").values())
    OUT.mkdir(parents=True, exist_ok=True)
    for name, theme in THEMES.items():
        path = OUT / f"activity-{name}.svg"
        path.write_text(svg(theme, days, years, today), encoding="utf-8")
        print(f"wrote {path}")
    print(f"last 12 months: {sum(days.values())}; by year: {years}")


if __name__ == "__main__":
    main()
