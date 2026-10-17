"""Build the streaks + languages card (light + dark SVG).

Usage: python scripts/build_stats.py [username] [out_dir]
Streaks come from the public contribution calendar. Languages are summed from
the GitHub API across non-fork public repos; set GITHUB_TOKEN to avoid the
unauthenticated rate limit.
"""
import datetime as dt
import json
import os
import urllib.request

from build_activity import FIRST_YEAR, OUT, THEMES, USER, calendar

WIDTH, HEIGHT = 880, 330
# Language swatches in rank order, drawn from the profile's own palette.
LANG_PALETTE = {
    "light": ["#2F5B42", "#D2462F", "#86AE92", "#6B6F68", "#BFD3C3", "#1A1D1A"],
    "dark": ["#8FC9A2", "#FF6B4A", "#3F6E50", "#8E928A", "#2B4A37", "#ECEAE3"],
}


def api(path):
    headers = {"User-Agent": "profile-stats-builder", "Accept": "application/vnd.github+json"}
    if os.environ.get("GITHUB_TOKEN"):
        headers["Authorization"] = f"Bearer {os.environ['GITHUB_TOKEN']}"
    req = urllib.request.Request(f"https://api.github.com{path}", headers=headers)
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def languages(top=6):
    totals = {}
    for repo in api(f"/users/{USER}/repos?per_page=100&type=owner"):
        if repo["fork"]:
            continue
        for lang, size in api(f"/repos/{repo['full_name']}/languages").items():
            totals[lang] = totals.get(lang, 0) + size
    grand = sum(totals.values()) or 1
    ranked = sorted(totals.items(), key=lambda kv: -kv[1])[:top]
    return [(lang, 100 * size / grand) for lang, size in ranked]


def streaks(days, today):
    """Total, first contribution date, current streak, longest streak with its dates."""
    active = sorted(d for d, n in days.items() if n and d <= today)
    total = sum(n for d, n in days.items() if d <= today)
    longest, run, best_end, prev = 0, 0, None, None
    for d in active:
        run = run + 1 if prev and (d - prev).days == 1 else 1
        if run > longest:
            longest, best_end = run, d
        prev = d
    # like most streak counters, an empty today doesn't break the streak yet
    current, d = 0, today if days.get(today) else today - dt.timedelta(days=1)
    while days.get(d):
        current += 1
        d -= dt.timedelta(days=1)
    best_start = best_end - dt.timedelta(days=longest - 1) if best_end else None
    return total, (active[0] if active else None), current, longest, best_start, best_end


def fmt(d):
    return f"{d:%b} {d.day}, {d.year}"


def svg(t, stats, langs, today):
    total, first, current, longest, best_start, best_end = stats
    blocks = [
        (str(total), "contributions", f"SINCE {fmt(first).upper()}" if first else "NO CONTRIBUTIONS YET"),
        (str(current), "day, current streak" if current == 1 else "days, current streak", "KEEP IT GOING" if current else f"AS OF {fmt(today).upper()}"),
        (str(longest), "day, longest streak" if longest == 1 else "days, longest streak",
         f"{best_start:%b} {best_start.day} – {best_end:%b} {best_end.day}, {best_end.year}".upper() if best_end else ""),
    ]
    stat_svg = []
    for i, (num, label, sub) in enumerate(blocks):
        x = 40 + i * 280
        stat_svg.append(
            f'<g class="rise" style="animation-delay:{0.1 + i * 0.15:.2f}s">'
            f'<text x="{x}" y="132" class="big">{num}</text>'
            f'<text x="{x + 2}" y="158" class="txt">{label}</text>'
            f'<text x="{x + 2}" y="180" class="lbl small">{sub}</text></g>'
        )
        if i:
            stat_svg.append(f'<rect x="{x - 24}" y="80" width="1" height="104" fill="{t["rule"]}"/>')

    bar, legend, x = [], [], 40.0
    shown = sum(p for _, p in langs) or 1
    for i, (lang, pct) in enumerate(langs):
        w = max(3, 800 * pct / shown)
        color = t["langs"][i % len(t["langs"])]
        bar.append(f'<rect x="{x:.1f}" y="236" width="{w:.1f}" height="10" fill="{color}" class="grow" style="animation-delay:{0.6 + i * 0.12:.2f}s"/>')
        x += w
        lx, ly = 40 + (i % 3) * 280, 274 + (i // 3) * 22
        legend.append(
            f'<g class="rise" style="animation-delay:{0.9 + i * 0.08:.2f}s">'
            f'<rect x="{lx}" y="{ly - 9}" width="9" height="9" rx="2" fill="{color}"/>'
            f'<text x="{lx + 16}" y="{ly}" class="lang">{lang}</text>'
            f'<text x="{lx + 236}" y="{ly}" text-anchor="end" class="pct">{pct:.1f}%</text></g>'
        )

    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{HEIGHT}" viewBox="0 0 {WIDTH} {HEIGHT}" role="img" aria-label="{total} contributions, current streak {current} days, longest streak {longest} days. Top languages: {', '.join(f'{l} {p:.1f}%' for l, p in langs)}.">
  <style>
    .lbl {{ font: 600 11px Helvetica, Arial, sans-serif; letter-spacing: 2px; fill: {t["muted"]}; }}
    .small {{ font-size: 10px; letter-spacing: 1.5px; }}
    .big {{ font: 400 64px Georgia, "Times New Roman", serif; fill: {t["ink"]}; }}
    .txt {{ font: 15px Georgia, "Times New Roman", serif; fill: {t["ink"]}; }}
    .lang {{ font: 13px Helvetica, Arial, sans-serif; fill: {t["ink"]}; }}
    .pct {{ font: 600 12px "SFMono-Regular", Consolas, monospace; fill: {t["muted"]}; }}
    .rise {{ animation: rise .8s cubic-bezier(.2,.75,.2,1) both; }}
    .grow {{ transform-box: fill-box; transform-origin: left; animation: grow .6s cubic-bezier(.2,.75,.2,1) both; }}
    @keyframes rise {{ from {{ opacity: 0; transform: translateY(10px); }} }}
    @keyframes grow {{ from {{ transform: scaleX(0); }} }}
    @media (prefers-reduced-motion: reduce) {{ * {{ animation: none !important; }} }}
  </style>
  <rect width="{WIDTH}" height="{HEIGHT}" rx="8" fill="{t["bg"]}"/>

  <rect x="40" y="33" width="9" height="9" fill="{t["accent"]}"/>
  <text x="58" y="42" class="lbl">STREAKS &amp; LANGUAGES</text>
  <text x="840" y="42" text-anchor="end" class="lbl">SNAPSHOT {today:%d %b %Y}</text>
  <rect x="40" y="57" width="800" height="1" fill="{t["rule"]}"/>

  {"".join(stat_svg)}

  <rect x="40" y="200" width="800" height="1" fill="{t["rule"]}"/>
  <text x="40" y="225" class="lbl">MOST USED LANGUAGES</text>
  <clipPath id="barclip"><rect x="40" y="236" width="800" height="10" rx="5"/></clipPath>
  <g clip-path="url(#barclip)">{"".join(bar)}</g>
  {"".join(legend)}
</svg>
"""


def main():
    today = dt.date.today()
    days = {}
    for yr in range(FIRST_YEAR, today.year + 1):
        days.update(calendar(f"{yr}-01-01", f"{yr}-12-31"))
    stats = streaks(days, today)
    langs = languages()
    OUT.mkdir(parents=True, exist_ok=True)
    for name, theme in THEMES.items():
        path = OUT / f"stats-{name}.svg"
        path.write_text(svg({**theme, "langs": LANG_PALETTE[name]}, stats, langs, today), encoding="utf-8")
        print(f"wrote {path}")
    print(f"stats: {stats}; languages: {langs}")


if __name__ == "__main__":
    main()
