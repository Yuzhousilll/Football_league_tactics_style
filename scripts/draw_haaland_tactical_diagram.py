#!/usr/bin/env python3
"""Draw a tactical diagram: Haaland pins two center-backs to free KDB and Foden."""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.patches import Arc, Circle, Rectangle

OUTPUT_PATH = Path("chapter4_player_role/haaland_space_creation_tactical_diagram.png")
CN_FONT_PATH = Path("assets/fonts/SourceHanSansSC-Regular.otf")


def draw_pitch(ax) -> None:
    # Full pitch dimensions in normalized coordinates
    pitch = Rectangle((0, 0), 120, 80, linewidth=2, edgecolor="#1b5e20", facecolor="#2e7d32")
    ax.add_patch(pitch)

    # Halfway line and center circle
    ax.plot([60, 60], [0, 80], color="white", linewidth=2)
    center_circle = Circle((60, 40), 10, fill=False, color="white", linewidth=2)
    ax.add_patch(center_circle)

    # Penalty boxes
    ax.add_patch(Rectangle((0, 18), 18, 44, fill=False, edgecolor="white", linewidth=2))
    ax.add_patch(Rectangle((102, 18), 18, 44, fill=False, edgecolor="white", linewidth=2))

    # Six-yard boxes
    ax.add_patch(Rectangle((0, 30), 6, 20, fill=False, edgecolor="white", linewidth=2))
    ax.add_patch(Rectangle((114, 30), 6, 20, fill=False, edgecolor="white", linewidth=2))

    # Penalty spots
    ax.plot(12, 40, "wo", markersize=3)
    ax.plot(108, 40, "wo", markersize=3)

    # Penalty arcs
    ax.add_patch(Arc((12, 40), 20, 20, angle=0, theta1=310, theta2=50, color="white", linewidth=2))
    ax.add_patch(Arc((108, 40), 20, 20, angle=0, theta1=130, theta2=230, color="white", linewidth=2))


def draw_player(ax, x: float, y: float, label: str, color: str, edge: str = "black") -> None:
    node = Circle((x, y), 2.2, facecolor=color, edgecolor=edge, linewidth=1.5, zorder=5)
    ax.add_patch(node)
    ax.text(x, y + 3.4, label, ha="center", va="bottom", fontsize=9, color="white", weight="bold")


def draw_arrow(ax, start: tuple[float, float], end: tuple[float, float], color: str, style: str = "-") -> None:
    ax.annotate(
        "",
        xy=end,
        xytext=start,
        arrowprops=dict(
            arrowstyle="->",
            color=color,
            linewidth=2,
            linestyle=style,
            shrinkA=5,
            shrinkB=5,
        ),
        zorder=6,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Draw tactical diagram with configurable annotation font scale.")
    parser.add_argument("--font-scale", type=float, default=1.0, help="Scale factor for the Chinese annotation block font size.")
    parser.add_argument("--output", default=str(OUTPUT_PATH), help="Output image path.")
    args = parser.parse_args()

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    cn_font = font_manager.FontProperties(fname=str(CN_FONT_PATH)) if CN_FONT_PATH.exists() else None
    annotation_font_size = 10 * args.font_scale

    fig, ax = plt.subplots(figsize=(14, 9))
    draw_pitch(ax)

    # Opponent defensive line (right side, defending own goal)
    draw_player(ax, 92, 18, "LB", "#3949ab")
    draw_player(ax, 96, 32, "LCB", "#283593")
    draw_player(ax, 96, 48, "RCB", "#283593")
    draw_player(ax, 92, 62, "RB", "#3949ab")

    # Manchester City attacking structure
    draw_player(ax, 86, 40, "Haaland", "#fdd835")
    draw_player(ax, 78, 30, "De Bruyne", "#ffb300")
    draw_player(ax, 78, 50, "Foden", "#ffb300")
    draw_player(ax, 68, 40, "Rodri", "#ffca28")
    draw_player(ax, 74, 22, "Silva", "#ffca28")
    draw_player(ax, 74, 58, "Grealish", "#ffca28")

    # Defensive line guide
    ax.plot([92, 96, 96, 92], [18, 32, 48, 62], color="#90caf9", linewidth=2, linestyle="--", alpha=0.8)
    ax.text(98, 66, "Opponent Back Line", color="#bbdefb", fontsize=10, weight="bold")

    # Haaland pinning both center-backs (movement / attention arrows)
    draw_arrow(ax, (96, 32), (87, 38), "#ef5350", style="--")
    draw_arrow(ax, (96, 48), (87, 42), "#ef5350", style="--")

    # Space created in half-spaces
    ax.add_patch(Rectangle((74, 24), 10, 12, fill=False, edgecolor="#80deea", linewidth=2, linestyle="--"))
    ax.add_patch(Rectangle((74, 44), 10, 12, fill=False, edgecolor="#80deea", linewidth=2, linestyle="--"))
    ax.text(79, 37, "Free\nHalf-Space", color="#e0f7fa", fontsize=8, ha="center")
    ax.text(79, 57, "Free\nHalf-Space", color="#e0f7fa", fontsize=8, ha="center")

    # Main attacking ideas
    draw_arrow(ax, (68, 40), (78, 30), "#ffee58")
    draw_arrow(ax, (68, 40), (78, 50), "#ffee58")
    draw_arrow(ax, (78, 30), (86, 40), "#ffd54f")
    draw_arrow(ax, (78, 50), (86, 40), "#ffd54f")
    draw_arrow(ax, (74, 22), (78, 30), "#fff176", style="--")
    draw_arrow(ax, (74, 58), (78, 50), "#fff176", style="--")

    # Annotation block
    ax.text(
        4,
        75,
        "曼城进攻思路：\n"
        "1）哈兰德牵制两名中卫\n"
        "2）德布劳内/福登在半空间接应\n"
        "3）通过第三人跑动与倒三角制造中路机会",
        fontsize=annotation_font_size,
        color="white",
        va="top",
        fontproperties=cn_font,
        bbox=dict(boxstyle="round,pad=0.4", facecolor="#1e1e1e", edgecolor="#bdbdbd", alpha=0.85),
    )

    ax.set_xlim(0, 120)
    ax.set_ylim(0, 80)
    ax.set_aspect("equal")
    ax.axis("off")
    ax.set_title("哈兰德牵制中卫与曼城前场空当利用示意图", fontsize=14, weight="bold", color="white", pad=12, fontproperties=cn_font)

    fig.patch.set_facecolor("#1b5e20")
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close(fig)

    print(f"Saved: {output_path}")


if __name__ == "__main__":
    main()
