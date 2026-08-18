#!/usr/bin/env python3
"""Generate an animated GitHub-streak SVG (squares light up one by one).
Works standalone; designed to run in a GitHub Action daily to stay live.
Usage: python generate_streak_svg.py [username] [output.svg]
"""
import sys, json, os, datetime, urllib.request

USER = sys.argv[1] if len(sys.argv) > 1 else "PedroAugSouza"
OUT  = sys.argv[2] if len(sys.argv) > 2 else "streak.svg"

HERE = os.path.dirname(os.path.abspath(__file__))


def _levels_from_counts(days):
    """Add a GitHub-style 0..4 level to each {date,count} day, using quartiles
    of the non-zero counts so the palette spreads naturally."""
    nz = sorted(c for c in (d["count"] for d in days) if c > 0)
    if not nz:
        cuts = [1, 1, 1, 1]
    else:
        def q(f):
            return nz[min(len(nz) - 1, int(f * len(nz)))]
        cuts = [1, q(0.25), q(0.5), q(0.75)]
    out = []
    for d in days:
        c = d["count"]
        if c <= 0:
            lvl = 0
        elif c < cuts[1]:
            lvl = 1
        elif c < cuts[2]:
            lvl = 2
        elif c < cuts[3]:
            lvl = 3
        else:
            lvl = 4
        out.append({"date": d["date"], "count": c, "level": lvl})
    return out


def _from_scraped(path):
    """Convert data/contributions.json (fetch_contributions.py output) into the
    jogruber-shaped {contributions:[{date,count,level}], total:{lastYear}}."""
    raw = json.load(open(path))
    days = _levels_from_counts(raw["days"])
    return {"contributions": days,
            "total": {"lastYear": raw.get("total_contributions",
                                          sum(d["count"] for d in days))}}


def get_data(user):
    url = f"https://github-contributions-api.jogruber.de/v4/{user}?y=last"
    try:
        with urllib.request.urlopen(url, timeout=25) as r:
            return json.loads(r.read().decode())
    except Exception as e:
        # 1) real data scraped from github.com by fetch_contributions.py
        scraped = os.path.join(HERE, "..", "data", "contributions.json")
        if os.path.exists(scraped):
            try:
                d = _from_scraped(scraped)
                if d["total"]["lastYear"] > 0:
                    print("API failed (%s); using scraped data/contributions.json" % e)
                    return d
            except Exception as e2:
                print("scraped fallback failed (%s)" % e2)
        # 2) last-resort static snapshot committed next to this script
        here = os.path.join(HERE, "contrib.json")
        if os.path.exists(here):
            print("API failed (%s); using local contrib.json" % e)
            return json.load(open(here))
        raise

data = get_data(USER)
contribs = data["contributions"]
total = data["total"]["lastYear"]

# ---- layout ----
CELL, GAP, RAD, LEFT, TOP = 13, 3, 2.5, 34, 24
COLORS = ["#161b22", "#0e4429", "#006d32", "#26a641", "#39d353"]
FLASH = "#b4ffaa"
GRAY = "#7d8590"
MONTHS = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]

n = len(contribs)
NW = (n + 6) // 7
W = LEFT + NW*(CELL+GAP) + 6
H = TOP + 7*(CELL+GAP) + 22

# timing (seconds)
REVEAL, DUR = 3.6, 0.55
maxorder = (NW-1) + 6*0.55

rects, labels = [], []
sd = datetime.date.fromisoformat(contribs[0]["date"])
last_m = None
for wk in range(NW):
    d = sd + datetime.timedelta(days=wk*7)
    if d.month != last_m:
        last_m = d.month
        labels.append(f'<text class="lbl" x="{LEFT+wk*(CELL+GAP)}" y="{TOP-8}">{MONTHS[d.month-1]}</text>')
for name, r in [("Mon",1),("Wed",3),("Fri",5)]:
    labels.append(f'<text class="lbl" x="2" y="{TOP+r*(CELL+GAP)+CELL-2}">{name}</text>')

for i, c in enumerate(contribs):
    wk, row, lvl = i//7, i%7, c["level"]
    x = LEFT + wk*(CELL+GAP); y = TOP + row*(CELL+GAP)
    delay = round((wk + row*0.55)/maxorder * REVEAL, 3)
    cls = "c g" if lvl >= 1 else "c e"
    rects.append(
        f'<rect class="{cls}" x="{x}" y="{y}" width="{CELL}" height="{CELL}" rx="{RAD}" '
        f'fill="{COLORS[lvl]}" style="animation-delay:{delay}s"/>'
    )

svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" font-family="-apple-system,Segoe UI,Helvetica,Arial,sans-serif">
<style>
  text.lbl {{ fill:{GRAY}; font-size:13px; font-weight:600; }}
  text.total {{ fill:#e6edf3; font-size:15px; font-weight:700; }}
  .c {{ transform-box:fill-box; transform-origin:center; opacity:0; animation:pop {DUR}s ease-out both; }}
  .g {{ animation:pop {DUR}s ease-out both, flash {DUR+0.15}s ease-out both; }}
  @keyframes pop {{ 0%{{opacity:0;transform:scale(.2)}} 60%{{opacity:1;transform:scale(1.1)}} 100%{{opacity:1;transform:scale(1)}} }}
  @keyframes flash {{ 0%{{filter:brightness(2.4)}} 45%{{filter:brightness(2.4)}} 100%{{filter:brightness(1)}} }}
  @media (prefers-reduced-motion: reduce) {{ .c {{ opacity:1 !important; animation:none !important; }} }}
</style>
<rect width="{W}" height="{H}" fill="none"/>
{''.join(labels)}
{''.join(rects)}
<text class="total" x="{LEFT}" y="{H-6}">{total:,} contributions in the last year</text>
</svg>'''

open(OUT, "w").write(svg)
print(f"Wrote {OUT}: {n} days, {total:,} contributions, {len(svg)//1024} KB")
