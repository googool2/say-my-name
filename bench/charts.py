#!/usr/bin/env python3
"""Draw the README charts into assets/ (light + dark SVG each). Stdlib only.

  bench/phase5.json   # 12 live pages, written from the phase 5 full run
  python bench/charts.py
"""
import json
from pathlib import Path
from xml.sax.saxutils import escape

HERE = Path(__file__).resolve().parent
OUT = HERE.parent / "assets"

# Same palette as Thanks Mom, checked for color blindness and contrast on GitHub's backgrounds.
THEMES = {
    "light": dict(surface="#ffffff", ink="#0b0b0b", ink2="#52514e", muted="#898781", grid="#e1e0d9",
                  line="rgba(11,11,11,0.10)", accent="#2a78d6"),
    "dark": dict(surface="#0d1117", ink="#f0efec", ink2="#c3c2b7", muted="#898781", grid="#2c2c2a",
                 line="rgba(255,255,255,0.12)", accent="#3987e5"),
}
FONT = 'system-ui, -apple-system, "Segoe UI", Helvetica, Arial, sans-serif'
W = 760
CHAR = 0.45  # average character width in system-ui, in em (measured)


def fits(s, size, width):
    assert len(s) * size * CHAR <= width, f"text too long for its box: {s!r}"


def text(x, y, s, t, size=12, fill="ink2", anchor="start", weight=400):
    return (f'<text x="{x:.1f}" y="{y:.1f}" font-size="{size}" fill="{t[fill]}" text-anchor="{anchor}" '
            f'font-weight="{weight}">{escape(s)}</text>')


def dot(x, y, color, t, r=5, hollow=False):
    fill, stroke = (t["surface"], color) if hollow else (color, t["surface"])
    return f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r}" fill="{fill}" stroke="{stroke}" stroke-width="2"/>'


def svg(t, height, title, body):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{height}" viewBox="0 0 {W} {height}" '
            f'role="img" aria-label="{escape(title)}" font-family=\'{FONT}\'>\n<title>{escape(title)}</title>\n'
            + "\n".join(body) + "\n</svg>\n")


def header(title, sub, t, legend=()):
    body = [text(0, 20, title, t, 16, "ink", weight=600)]
    y = 40
    for line in sub:
        fits(line, 12, W)
        body.append(text(0, y, line, t, 12))
        y += 17
    x = W
    for label, color, hollow in reversed(legend):  # right-aligned on the title row
        x -= len(label) * 6.6 + 8
        body.append(text(x, 20, label, t, 12, "ink2"))
        x -= 14
        body.append(dot(x + 5, 16, color, t, 4, hollow))
        x -= 14
    return body, y + 6


def stats(tiles, t, title):
    gap, h = 12, 96
    w = (W - gap * (len(tiles) - 1)) / len(tiles)
    body = []
    for n, (value, label, sub) in enumerate(tiles):
        x = n * (w + gap)
        for s, size in ((value, 28), (label, 12), (sub, 11)):
            fits(s, size, w - 32)
        body.append(f'<rect x="{x + 0.5:.1f}" y="0.5" width="{w - 1:.1f}" height="{h - 1}" rx="10" '
                    f'fill="none" stroke="{t["line"]}"/>')
        body.append(text(x + 16, 42, value, t, 28, "ink", weight=600))
        body.append(text(x + 16, 66, label, t, 12, "ink"))
        body.append(text(x + 16, 82, sub, t, 11, "muted"))
    return svg(t, h, title, body)


def pages_chart(d, t):
    """One row per page: quote share as is (gray) and of the best rewrite (blue if it WON, hollow if not)."""
    title = "12 live pages: as they are vs the best rewrite"
    body, y = header(title, [
        f"Quote share: how much of the AI's answer came from the page. {d['questions_per_page']} buyer questions x "
        f"{d['runs_per_question']} paired runs per version.",
        "Right: the paired-test verdict for that rewrite. Most pages were already cited every time."],
        t, [("As is", t["muted"], False), ("Best rewrite", t["accent"], True), ("WIN", t["accent"], False)])
    X0, X1, top = 250, W - 120, 0.6
    xs = lambda v: X0 + (X1 - X0) * v / top
    y += 10
    for p in d["pages"]:
        best = max(("answer-first", "structure"), key=lambda v: (p[v]["verdict"] == "WIN", p[v]["quote"]))
        v = p[best]
        win = v["verdict"] == "WIN"
        cy = y + 14
        name, note = p["page"], f"{p['niche']} · {'Persian' if p['lang'] == 'fa' else 'English'}"
        fits(note, 11, X0 - 12)
        body.append(text(0, cy - 1, name, t, 13, "ink"))
        body.append(text(0, cy + 15, note, t, 11, "ink2"))
        body.append(f'<line x1="{X0}" y1="{cy}" x2="{X1}" y2="{cy}" stroke="{t["grid"]}" stroke-width="1"/>')
        a, b = xs(p["baseline"]["quote"]), xs(v["quote"])
        body.append(f'<line x1="{min(a, b):.1f}" y1="{cy}" x2="{max(a, b):.1f}" y2="{cy}" stroke="{t["accent"]}" '
                    f'stroke-width="2" stroke-opacity="0.35"/>')
        body.append(dot(a, cy, t["muted"], t))
        body.append(dot(b, cy, t["accent"], t, 5, hollow=not win))
        winners = [k for k in ("answer-first", "structure") if p[k]["verdict"] == "WIN"]
        verdict = ("WIN · both rewrites" if len(winners) == 2 else f"WIN · {best}") if win else "no difference"
        body.append(text(W, cy + 4, verdict, t, 12, "ink" if win else "muted", "end", 600 if win else 400))
        y += 40
    for v in (0, 0.2, 0.4, 0.6):
        body.append(text(xs(v), y + 14, f"{v:.1f}", t, 11, "muted", "middle"))
    body.append(text(X0, y + 30, "quote share", t, 11, "muted"))
    return svg(t, y + 40, title, body)


def main():
    d = json.loads((HERE / "phase5.json").read_text(encoding="utf-8"))
    rows = [p[v] for p in d["pages"] for v in ("answer-first", "structure")]
    aa = [p["aa"] for p in d["pages"]]
    n_win = sum(r["verdict"] == "WIN" for r in rows)
    n_worse = sum(r["verdict"] == "WORSE" for r in rows)
    a_win = sum(r["verdict"] == "WIN" for r in aa)
    out = {}  # build every chart first; only then replace the files, so an error never leaves assets/ half-written
    for mode, t in THEMES.items():
        out[f"stats-{mode}.svg"] = stats([
            (f"{a_win} / {len(aa)}", "false wins", "identical-copy controls"),
            (f"{n_win} / {len(rows)}", "rewrites won", f"{len(d['pages'])} live pages, EN + FA"),
            (f"{n_worse} / {len(rows)}", "made a page worse", "paired tests, p < 0.025"),
            (f"${d['cost_usd'] / d['answers']:.2f}", "per test call", "Claude Sonnet, measured"),
        ], t, "Say My Name in numbers")
        out[f"pages-{mode}.svg"] = pages_chart(d, t)
    OUT.mkdir(exist_ok=True)
    for name, s in out.items():
        (OUT / name).write_text(s, encoding="utf-8")
    print(f"wrote {len(out)} charts to {OUT}")


if __name__ == "__main__":
    main()
