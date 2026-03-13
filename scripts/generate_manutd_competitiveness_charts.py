#!/usr/bin/env python3
"""Generate Manchester Utd PCA/index charts as SVG using stdlib only."""

from __future__ import annotations

import csv
from pathlib import Path

SCORES_CSV = Path("chapter3_competitiveness/competitiveness_pca_scores.csv")
OUT_PCA = Path("chapter3_competitiveness/competitiveness_manutd_pca_trends.svg")
OUT_INDEX = Path("chapter3_competitiveness/competitiveness_manutd_index_rank.svg")


def load_team_rows(path: Path, team: str = "Manchester Utd"):
    rows = []
    with path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            if r["Squad"] == team:
                rows.append(
                    {
                        "Season": r["Season"],
                        "year": int(r["season_year"]),
                        "PC1": float(r["PC1"]),
                        "PC2": float(r["PC2"]),
                        "PC3": float(r["PC3"]),
                        "index": float(r["competitiveness_index"]),
                        "rank": float(r["season_rank_by_index"]),
                    }
                )
    rows.sort(key=lambda x: x["year"])
    return rows


def scale(v, a, b, c, d):
    if b == a:
        return (c + d) / 2
    return c + (v - a) * (d - c) / (b - a)


def polyline(points, color, width=2):
    pts = " ".join(f"{x:.1f},{y:.1f}" for x, y in points)
    return f'<polyline fill="none" stroke="{color}" stroke-width="{width}" points="{pts}" />'


def circles(points, color):
    return "\n".join(
        f'<circle cx="{x:.1f}" cy="{y:.1f}" r="3.2" fill="{color}" />' for x, y in points
    )


def write_pca_svg(rows, out_path: Path):
    w, h = 1100, 620
    ml, mr, mt, mb = 90, 120, 60, 70
    plot_w, plot_h = w - ml - mr, h - mt - mb
    years = [r["year"] for r in rows]
    vals = [r[k] for r in rows for k in ("PC1", "PC2", "PC3")]
    vmin, vmax = min(vals), max(vals)
    pad = 0.2 * (vmax - vmin if vmax != vmin else 1)
    vmin, vmax = vmin - pad, vmax + pad

    def x(year):
        return scale(year, min(years), max(years), ml, ml + plot_w)

    def y(val):
        return scale(val, vmin, vmax, mt + plot_h, mt)

    series = {
        "PC1": "#1f77b4",
        "PC2": "#d62728",
        "PC3": "#2ca02c",
    }

    grid = []
    for i in range(6):
        yy = mt + i * plot_h / 5
        vv = scale(yy, mt + plot_h, mt, vmin, vmax)
        grid.append(f'<line x1="{ml}" y1="{yy:.1f}" x2="{ml+plot_w}" y2="{yy:.1f}" stroke="#e5e7eb"/>')
        grid.append(f'<text x="{ml-12}" y="{yy+4:.1f}" text-anchor="end" font-size="12" fill="#555">{vv:.2f}</text>')

    x_ticks = []
    for yr in years:
        xx = x(yr)
        x_ticks.append(f'<line x1="{xx:.1f}" y1="{mt+plot_h}" x2="{xx:.1f}" y2="{mt+plot_h+6}" stroke="#333"/>')
        x_ticks.append(f'<text x="{xx:.1f}" y="{mt+plot_h+24}" text-anchor="middle" font-size="12">{yr}</text>')

    lines = []
    legend = []
    ly = mt + 10
    for i, (k, c) in enumerate(series.items()):
        pts = [(x(r["year"]), y(r[k])) for r in rows]
        lines.append(polyline(pts, c, 2.5))
        lines.append(circles(pts, c))
        legend.append(f'<line x1="{w-mr+10}" y1="{ly+24*i}" x2="{w-mr+40}" y2="{ly+24*i}" stroke="{c}" stroke-width="3"/>')
        legend.append(f'<text x="{w-mr+48}" y="{ly+24*i+5}" font-size="13">{k}</text>')

    zero_y = y(0)
    zero = f'<line x1="{ml}" y1="{zero_y:.1f}" x2="{ml+plot_w}" y2="{zero_y:.1f}" stroke="#9ca3af" stroke-dasharray="4,4"/>'

    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}">
<rect width="100%" height="100%" fill="white"/>
<text x="{w/2}" y="32" text-anchor="middle" font-size="24" font-weight="bold">Manchester Utd PCA Component Trends</text>
{''.join(grid)}
<line x1="{ml}" y1="{mt}" x2="{ml}" y2="{mt+plot_h}" stroke="#333"/>
<line x1="{ml}" y1="{mt+plot_h}" x2="{ml+plot_w}" y2="{mt+plot_h}" stroke="#333"/>
{''.join(x_ticks)}
{zero}
{''.join(lines)}
{''.join(legend)}
<text x="{w/2}" y="{h-16}" text-anchor="middle" font-size="13">Season (start year)</text>
<text x="20" y="{h/2}" transform="rotate(-90,20,{h/2})" text-anchor="middle" font-size="13">Principal Component Score</text>
</svg>'''
    out_path.write_text(svg, encoding="utf-8")


def write_index_svg(rows, out_path: Path):
    w, h = 1100, 620
    ml, mr, mt, mb = 90, 130, 60, 70
    plot_w, plot_h = w - ml - mr, h - mt - mb
    years = [r["year"] for r in rows]
    idx_vals = [r["index"] for r in rows]
    rank_vals = [r["rank"] for r in rows]

    imin, imax = min(idx_vals), max(idx_vals)
    ipad = 0.15 * (imax - imin if imax != imin else 1)
    imin, imax = imin - ipad, imax + ipad

    rmin, rmax = min(rank_vals), max(rank_vals)

    def x(year):
        return scale(year, min(years), max(years), ml, ml + plot_w)

    def y_idx(v):
        return scale(v, imin, imax, mt + plot_h, mt)

    def y_rank(v):
        return scale(v, rmin, rmax, mt, mt + plot_h)  # inverted

    grid = []
    for i in range(6):
        yy = mt + i * plot_h / 5
        vv = scale(yy, mt + plot_h, mt, imin, imax)
        grid.append(f'<line x1="{ml}" y1="{yy:.1f}" x2="{ml+plot_w}" y2="{yy:.1f}" stroke="#e5e7eb"/>')
        grid.append(f'<text x="{ml-12}" y="{yy+4:.1f}" text-anchor="end" font-size="12" fill="#1f77b4">{vv:.2f}</text>')

    for i in range(int(rmin), int(rmax) + 1):
        yy = y_rank(i)
        grid.append(f'<text x="{ml+plot_w+10}" y="{yy+4:.1f}" font-size="12" fill="#d62728">{i}</text>')

    x_ticks = []
    for yr in years:
        xx = x(yr)
        x_ticks.append(f'<line x1="{xx:.1f}" y1="{mt+plot_h}" x2="{xx:.1f}" y2="{mt+plot_h+6}" stroke="#333"/>')
        x_ticks.append(f'<text x="{xx:.1f}" y="{mt+plot_h+24}" text-anchor="middle" font-size="12">{yr}</text>')

    idx_pts = [(x(r["year"]), y_idx(r["index"])) for r in rows]
    rank_pts = [(x(r["year"]), y_rank(r["rank"])) for r in rows]

    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}">
<rect width="100%" height="100%" fill="white"/>
<text x="{w/2}" y="32" text-anchor="middle" font-size="24" font-weight="bold">Manchester Utd Competitiveness Index and Rank</text>
{''.join(grid)}
<line x1="{ml}" y1="{mt}" x2="{ml}" y2="{mt+plot_h}" stroke="#1f77b4"/>
<line x1="{ml+plot_w}" y1="{mt}" x2="{ml+plot_w}" y2="{mt+plot_h}" stroke="#d62728"/>
<line x1="{ml}" y1="{mt+plot_h}" x2="{ml+plot_w}" y2="{mt+plot_h}" stroke="#333"/>
{''.join(x_ticks)}
{polyline(idx_pts, '#1f77b4', 2.5)}
{circles(idx_pts, '#1f77b4')}
{polyline(rank_pts, '#d62728', 2.5)}
{circles(rank_pts, '#d62728')}
<line x1="{w-mr+10}" y1="{mt+10}" x2="{w-mr+40}" y2="{mt+10}" stroke="#1f77b4" stroke-width="3"/>
<text x="{w-mr+48}" y="{mt+15}" font-size="13">competitiveness_index</text>
<line x1="{w-mr+10}" y1="{mt+34}" x2="{w-mr+40}" y2="{mt+34}" stroke="#d62728" stroke-width="3"/>
<text x="{w-mr+48}" y="{mt+39}" font-size="13">season_rank_by_index</text>
<text x="{w/2}" y="{h-16}" text-anchor="middle" font-size="13">Season (start year)</text>
<text x="20" y="{h/2}" transform="rotate(-90,20,{h/2})" text-anchor="middle" font-size="13" fill="#1f77b4">Competitiveness Index</text>
<text x="{w-18}" y="{h/2}" transform="rotate(90,{w-18},{h/2})" text-anchor="middle" font-size="13" fill="#d62728">Season Rank (lower is better)</text>
</svg>'''
    out_path.write_text(svg, encoding="utf-8")


def main():
    rows = load_team_rows(SCORES_CSV)
    if not rows:
        raise SystemExit("No Manchester Utd rows found in PCA scores CSV")
    write_pca_svg(rows, OUT_PCA)
    write_index_svg(rows, OUT_INDEX)
    print(f"Saved: {OUT_PCA}")
    print(f"Saved: {OUT_INDEX}")


if __name__ == "__main__":
    main()
