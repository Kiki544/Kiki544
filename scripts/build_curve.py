"""Build Fig. 4, my career as a training curve (light + dark SVG).

Usage: python scripts/build_curve.py [username] [out_dir]
"Loss" falls with every public contribution (from the contribution calendar),
so quiet stretches show up as plateaus. Projects are marked on the curve at the
date each repository was created (from the GitHub API; set GITHUB_TOKEN in CI).
"""
import datetime as dt
import math
import random

from build_activity import FIRST_YEAR, OUT, THEMES, USER, calendar
from build_stats import api

WIDTH, HEIGHT = 880, 330
X0, X1, Y0, Y1 = 70, 840, 84, 262          # plot area: loss 1.0 at Y0, 0.0 at Y1
SCALE = 150                                 # contributions it takes to cut the remaining loss by ~63%
SMOOTH = 21                                 # days of exponential smoothing, so steps read as a curve
PLATEAU_DAYS = 120                          # a quiet stretch this long gets labelled
MERGE_DAYS = 21                             # projects created this close together share one label
LABELS = {
    "RESULT-CHECKER-OOP": "Result Checker",
    "TomatoDisease_Detection": "Tomato detection",
    "OpticalCharacterRecognition": "OCR",
    "ProxyshopV3": "ProxyShop",
    "EliteClub": "EliteClub",
    USER: "This profile",
}


def loss_at(cum):
    return 0.12 + 0.8 * math.exp(-cum / SCALE)


def svg(t, days, repos, today):
    start = min(d for d, n in days.items() if n)
    span = (today - start).days or 1
    cum, smooth, curve, series = 0, None, {}, []
    alpha = 2 / (SMOOTH + 1)
    for i in range(span + 1):
        d = start + dt.timedelta(days=i)
        cum += days.get(d, 0)
        raw = loss_at(cum)
        smooth = raw if smooth is None else smooth + alpha * (raw - smooth)
        curve[d] = smooth
    rng = random.Random(544)
    for i in range(0, span + 1, 6):
        d = start + dt.timedelta(days=i)
        base = curve[d]
        series.append((d, base + rng.uniform(-0.005, 0.005), base + 0.05 + rng.uniform(-0.012, 0.012)))
    last = start + dt.timedelta(days=span)
    if series[-1][0] != last:
        series.append((last, curve[last], curve[last] + 0.05))

    def x(d):
        return X0 + (X1 - X0) * (d - start).days / span

    def y(v):
        return Y1 - (Y1 - Y0) * v

    train = "M" + " L".join(f"{x(d):.1f},{y(v):.1f}" for d, v, _ in series)
    valid = "M" + " L".join(f"{x(d):.1f},{y(v):.1f}" for d, _, v in series)

    # x-axis: one tick per year
    ticks = []
    for yr in range(max(FIRST_YEAR, start.year), today.year + 1):
        d = max(dt.date(yr, 1, 1), start)
        ticks.append(f'<rect x="{x(d):.1f}" y="{Y1}" width="1" height="6" fill="{t["muted"]}"/>'
                     f'<text x="{x(d):.1f}" y="{Y1 + 20}" class="lbl small">{yr}</text>')

    # the longest quiet stretch becomes a labelled plateau
    plateau, run_start, best = "", None, (0, None, None)
    for i in range(span + 1):
        d = start + dt.timedelta(days=i)
        if days.get(d, 0) == 0:
            run_start = run_start or d
            if (d - run_start).days > best[0]:
                best = ((d - run_start).days, run_start, d)
        else:
            run_start = None
    if best[0] >= PLATEAU_DAYS:
        _, a, b = best
        py = y(curve[a]) - 22
        plateau = (f'<g class="fade" style="animation-delay:1.6s">'
                   f'<path d="M{x(a):.1f},{py + 6} V{py} H{x(b):.1f} V{py + 6}" fill="none" stroke="{t["muted"]}" stroke-dasharray="3 3"/>'
                   f'<text x="{(x(a) + x(b)) / 2:.1f}" y="{py - 6}" text-anchor="middle" class="lbl small">PLATEAU · {(b - a).days} QUIET DAYS</text></g>')

    marks, groups = [], []
    for repo in sorted(repos, key=lambda r: r["created_at"]):
        d = dt.date.fromisoformat(repo["created_at"][:10])
        if d < start or d > today:
            continue
        cx, cy = x(d), y(curve[d])
        delay = 0.3 + 2.4 * (d - start).days / span
        name = LABELS.get(repo["name"])
        if not name:
            marks.append(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="3" fill="{t["muted"]}" class="pop" style="animation-delay:{delay:.2f}s"/>')
        elif groups and (d - groups[-1][0]).days <= MERGE_DAYS:
            groups[-1][1].append(name)
        else:
            groups.append((d, [name]))

    for i, (d, names) in enumerate(groups):
        cx, cy = x(d), y(curve[d])
        delay = 0.3 + 2.4 * (d - start).days / span
        name = " + ".join(names)
        dy = -34 if i % 2 == 0 else 40
        anchor = "end" if cx + 4 + 7.5 * len(name) > X1 else "start"  # ~7.5px per character of 14px italic
        tx = cx - 4 if anchor == "end" else cx + 4
        marks.append(
            f'<g class="pop" style="animation-delay:{delay:.2f}s">'
            f'<line x1="{cx:.1f}" y1="{cy:.1f}" x2="{cx:.1f}" y2="{cy + dy + (8 if dy < 0 else -12):.1f}" stroke="{t["rule"]}"/>'
            f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="5" fill="{t["accent"]}" stroke="{t["bg"]}" stroke-width="2"/>'
            f'<text x="{tx:.1f}" y="{cy + dy:.1f}" text-anchor="{anchor}" class="note">{name}</text>'
            f'<text x="{tx:.1f}" y="{cy + dy + 12:.1f}" text-anchor="{anchor}" class="lbl tiny">{d:%b %Y}</text></g>'
        )

    final_loss = series[-1][1]
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{HEIGHT}" viewBox="0 0 {WIDTH} {HEIGHT}" role="img" aria-label="Fig. 4: a training curve where loss falls from {series[0][1]:.2f} to {final_loss:.2f} as public contributions add up, with projects marked at the dates they were created.">
  <style>
    .lbl {{ font: 600 11px Helvetica, Arial, sans-serif; letter-spacing: 2px; fill: {t["muted"]}; }}
    .small {{ font-size: 10px; letter-spacing: 1.5px; }}
    .tiny {{ font-size: 9px; letter-spacing: 1px; }}
    .note {{ font: italic 14px Georgia, "Times New Roman", serif; fill: {t["ink"]}; }}
    .num {{ font: 600 12px "SFMono-Regular", Consolas, monospace; fill: {t["ink"]}; }}
    .train {{ fill: none; stroke: {t["ink"]}; stroke-width: 2.2; stroke-linejoin: round; stroke-dasharray: 1; animation: draw 2.8s cubic-bezier(.4,.1,.3,1) .3s both; }}
    .valid {{ fill: none; stroke: {t["accent"]}; stroke-width: 1.4; stroke-opacity: .7; stroke-dasharray: 4 4; animation: fade 1s ease 2.6s both; }}
    .pop {{ animation: pop .4s cubic-bezier(.2,.75,.2,1) both; }}
    .fade {{ animation: fade .8s ease both; }}
    @keyframes draw {{ from {{ stroke-dashoffset: 1; }} to {{ stroke-dashoffset: 0; }} }}
    @keyframes fade {{ from {{ opacity: 0; }} }}
    @keyframes pop {{ from {{ opacity: 0; transform: translateY(6px); }} }}
    @media (prefers-reduced-motion: reduce) {{ * {{ animation: none !important; }} }}
  </style>
  <rect width="{WIDTH}" height="{HEIGHT}" rx="8" fill="{t["bg"]}"/>

  <rect x="40" y="33" width="9" height="9" fill="{t["accent"]}"/>
  <text x="58" y="42" class="lbl">FIG. 4 — TRAINING CURVE</text>
  <text x="840" y="42" text-anchor="end" class="lbl">EPOCHS: {span} DAYS · SNAPSHOT {today:%d %b %Y}</text>
  <rect x="40" y="57" width="800" height="1" fill="{t["rule"]}"/>

  <!-- axes -->
  <text x="40" y="{Y0 + 4}" class="lbl small">1.0</text>
  <text x="40" y="{(Y0 + Y1) / 2 + 4:.0f}" class="lbl small">0.5</text>
  <text x="40" y="{Y1 + 4}" class="lbl small">0.0</text>
  <rect x="{X0}" y="{(Y0 + Y1) / 2:.0f}" width="{X1 - X0}" height="1" fill="{t["rule"]}" opacity=".6"/>
  <rect x="{X0}" y="{Y1}" width="{X1 - X0}" height="1" fill="{t["rule"]}"/>
  {"".join(ticks)}

  <path d="{valid}" class="valid"/>
  <path d="{train}" pathLength="1" class="train"/>
  {plateau}
  {"".join(marks)}

  <!-- legend -->
  <g class="fade" style="animation-delay:2.8s">
    <rect x="560" y="{Y1 + 46}" width="22" height="2" fill="{t["ink"]}"/>
    <text x="590" y="{Y1 + 50}" class="lbl tiny">TRAINING LOSS</text>
    <path d="M690,{Y1 + 47} h22" stroke="{t["accent"]}" stroke-dasharray="4 4"/>
    <text x="720" y="{Y1 + 50}" class="lbl tiny">VALIDATION</text>
    <text x="40" y="{Y1 + 50}" class="lbl tiny">LOSS FALLS WITH EVERY PUBLIC CONTRIBUTION · NOW <tspan class="num" style="font-size:10px">{final_loss:.2f}</tspan></text>
  </g>
</svg>
"""


def main():
    today = dt.date.today()
    days = {}
    for yr in range(FIRST_YEAR, today.year + 1):
        days.update(calendar(f"{yr}-01-01", f"{yr}-12-31"))
    repos = [r for r in api(f"/users/{USER}/repos?per_page=100&type=owner") if not r["fork"]]
    OUT.mkdir(parents=True, exist_ok=True)
    for name, theme in THEMES.items():
        path = OUT / f"fig-curve-{name}.svg"
        path.write_text(svg(theme, days, repos, today), encoding="utf-8")
        print(f"wrote {path}")


if __name__ == "__main__":
    main()
