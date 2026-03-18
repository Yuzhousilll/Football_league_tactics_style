#!/usr/bin/env python3
"""Draw a tactical diagram for Inverted Fullback (边后腰) concept."""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.patches import Arc, Circle, FancyArrowPatch, Polygon, Rectangle

OUTPUT_COLOR_PATH = Path("chapter4_player_role/inverted_fullback_tactical_diagram.png")
CN_FONT_PATH = Path("assets/fonts/SourceHanSansSC-Regular.otf")

COLOR_THEME = {
    "pitch_edge": "#1b5e20",
    "pitch_face": "#2e7d32",
    "line": "white",
    "title": "white",
    "fig_face": "#1b5e20",
    "team_def": "#ffca28",
    "team_mid": "#ffd54f",
    "team_att": "#ffb300",
    "opp_def": "#3949ab",
    "opp_core": "#283593",
    "attack_1": "#ffee58",
    "attack_2": "#fff176",
    "counter": "#ef5350",
    "counter_text": "#ffcdd2",
    "control_poly": "#80deea",
    "control_text": "#e0f7fa",
    "player_text": "white",
    "caption": "#f5f5f5",
}

def draw_pitch(ax, cn_font, theme: dict[str, str]) -> None:
    pitch = Rectangle((0, 0), 120, 80, linewidth=2, edgecolor=theme["pitch_edge"], facecolor=theme["pitch_face"])
    ax.add_patch(pitch)
    ax.plot([60, 60], [0, 80], color=theme["line"], linewidth=1.6)
    ax.add_patch(Circle((60, 40), 10, fill=False, color=theme["line"], linewidth=1.6))

    ax.add_patch(Rectangle((0, 18), 18, 44, fill=False, edgecolor=theme["line"], linewidth=1.6))
    ax.add_patch(Rectangle((102, 18), 18, 44, fill=False, edgecolor=theme["line"], linewidth=1.6))
    ax.add_patch(Rectangle((0, 30), 6, 20, fill=False, edgecolor=theme["line"], linewidth=1.6))
    ax.add_patch(Rectangle((114, 30), 6, 20, fill=False, edgecolor=theme["line"], linewidth=1.6))

    ax.plot(12, 40, "o", color=theme["line"], markersize=2.8)
    ax.plot(108, 40, "o", color=theme["line"], markersize=2.8)
    ax.add_patch(Arc((12, 40), 20, 20, theta1=310, theta2=50, color=theme["line"], linewidth=1.6))
    ax.add_patch(Arc((108, 40), 20, 20, theta1=130, theta2=230, color=theme["line"], linewidth=1.6))

    ax.set_xlim(0, 120)
    ax.set_ylim(0, 80)
    ax.set_aspect("equal")
    ax.axis("off")


def draw_player(ax, x: float, y: float, label: str, color: str, cn_font, theme: dict[str, str], size: float = 2.0) -> None:
    ax.add_patch(Circle((x, y), size, facecolor=color, edgecolor="black", linewidth=1.1, zorder=5))
    ax.text(x, y + 2.8, label, ha="center", va="bottom", fontsize=8.5, color=theme["player_text"], fontweight="bold", fontproperties=cn_font)


def draw_arrow(ax, start: tuple[float, float], end: tuple[float, float], color: str, dashed: bool = False, lw: float = 2.0) -> None:
    ax.add_patch(
        FancyArrowPatch(
            start,
            end,
            arrowstyle="->",
            mutation_scale=12,
            linewidth=lw,
            linestyle="--" if dashed else "-",
            color=color,
            zorder=6,
        )
    )


def draw_left_traditional(ax, cn_font, theme: dict[str, str]) -> None:
    draw_pitch(ax, cn_font, theme)

    # Team in possession (City/Arsenal-like), traditional fullback stays wide
    draw_player(ax, 18, 28, "LB", theme["team_def"], cn_font, theme)
    draw_player(ax, 18, 52, "RB", theme["team_def"], cn_font, theme)
    draw_player(ax, 32, 40, "6", theme["team_def"], cn_font, theme)
    draw_player(ax, 44, 28, "8", theme["team_def"], cn_font, theme)
    draw_player(ax, 44, 52, "8", theme["team_def"], cn_font, theme)
    draw_player(ax, 72, 20, "LW", theme["team_att"], cn_font, theme)
    draw_player(ax, 78, 40, "9", theme["team_att"], cn_font, theme)
    draw_player(ax, 72, 60, "RW", theme["team_att"], cn_font, theme)

    # Opponent front block
    draw_player(ax, 55, 30, "Opp 8", theme["opp_def"], cn_font, theme)
    draw_player(ax, 55, 50, "Opp 8", theme["opp_def"], cn_font, theme)
    draw_player(ax, 68, 40, "Opp 9", theme["opp_core"], cn_font, theme)

    # Wide progression arrows
    draw_arrow(ax, (18, 28), (36, 22), theme["attack_1"])
    draw_arrow(ax, (18, 52), (36, 58), theme["attack_1"])
    draw_arrow(ax, (44, 28), (62, 24), theme["attack_2"])
    draw_arrow(ax, (44, 52), (62, 56), theme["attack_2"])

    # Opponent counterattack lane (more open)
    draw_arrow(ax, (68, 40), (44, 40), theme["counter"], dashed=True, lw=2.2)
    ax.text(43, 42.5, "反击通道较开放", color=theme["counter_text"], fontsize=8.5, fontproperties=cn_font)

    # Midfield control polygon (smaller)
    poly = Polygon([(30, 35), (44, 30), (48, 40), (44, 50), (30, 45)], fill=False, edgecolor=theme["control_poly"], linewidth=2, linestyle="--")
    ax.add_patch(poly)
    ax.text(31, 53, "中场控制区较小", color=theme["control_text"], fontsize=8.3, fontproperties=cn_font)


def draw_right_inverted(ax, cn_font, theme: dict[str, str]) -> None:
    draw_pitch(ax, cn_font, theme)

    # Back 3 and double pivot (with inverted fullback)
    draw_player(ax, 20, 24, "LCB", theme["team_def"], cn_font, theme)
    draw_player(ax, 20, 40, "CB", theme["team_def"], cn_font, theme)
    draw_player(ax, 20, 56, "RCB", theme["team_def"], cn_font, theme)

    draw_player(ax, 36, 34, "6", theme["team_mid"], cn_font, theme)
    draw_player(ax, 36, 46, "IFB", theme["team_mid"], cn_font, theme)  # inverted fullback

    # Front five
    draw_player(ax, 58, 16, "LW", theme["team_att"], cn_font, theme)
    draw_player(ax, 62, 30, "8", theme["team_att"], cn_font, theme)
    draw_player(ax, 72, 40, "9", theme["team_att"], cn_font, theme)
    draw_player(ax, 62, 50, "8", theme["team_att"], cn_font, theme)
    draw_player(ax, 58, 64, "RW", theme["team_att"], cn_font, theme)

    # Opponent forwards trying to counter
    draw_player(ax, 58, 34, "Opp 9", theme["opp_core"], cn_font, theme)
    draw_player(ax, 58, 46, "Opp 10", theme["opp_core"], cn_font, theme)

    # IFB movement and support
    draw_arrow(ax, (20, 56), (36, 46), theme["attack_1"])
    ax.text(37.5, 49, "边后卫内收", color=theme["control_text"], fontsize=8.5, fontproperties=cn_font)

    # Build-up superiority arrows
    draw_arrow(ax, (36, 34), (62, 30), theme["attack_2"])
    draw_arrow(ax, (36, 46), (62, 50), theme["attack_2"])
    draw_arrow(ax, (62, 30), (72, 40), theme["attack_1"])
    draw_arrow(ax, (62, 50), (72, 40), theme["attack_1"])

    # Counterattack blocking lanes
    draw_arrow(ax, (58, 34), (42, 34), theme["counter"], dashed=True)
    draw_arrow(ax, (58, 46), (42, 46), theme["counter"], dashed=True)
    ax.text(40.5, 52, "反击线路被提前封锁", color=theme["counter_text"], fontsize=8.5, fontproperties=cn_font)

    # Larger control polygon in central corridor
    poly = Polygon([(28, 28), (46, 26), (64, 40), (46, 54), (28, 52), (24, 40)], fill=False, edgecolor=theme["control_poly"], linewidth=2.2, linestyle="--")
    ax.add_patch(poly)
    ax.text(29, 58, "中场控制区扩大", color=theme["control_text"], fontsize=8.3, fontproperties=cn_font)


def render_diagram(output_path: Path, theme: dict[str, str], cn_font) -> None:
    fig, axes = plt.subplots(
        2,
        1,
        figsize=(9.2, 11.2),
        facecolor=theme["fig_face"],
        gridspec_kw={"hspace": 0.02},
    )

    draw_left_traditional(axes[0], cn_font, theme)
    draw_right_inverted(axes[1], cn_font, theme)

    fig.subplots_adjust(left=0.02, right=0.98, top=0.995, bottom=0.005, hspace=0.02)
    plt.savefig(output_path, dpi=300, bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close(fig)


def main() -> None:
    OUTPUT_COLOR_PATH.parent.mkdir(parents=True, exist_ok=True)
    cn_font = font_manager.FontProperties(fname=str(CN_FONT_PATH)) if CN_FONT_PATH.exists() else None

    render_diagram(OUTPUT_COLOR_PATH, COLOR_THEME, cn_font)

    print(f"Saved: {OUTPUT_COLOR_PATH}")


if __name__ == "__main__":
    main()
