"""Render the full-field earned-role pilot comparison as a README SVG."""

import argparse
import csv
import math
from collections import defaultdict
from pathlib import Path
from xml.sax.saxutils import escape

WIDTH = 900
PLOT_LEFT = 200
PLOT_RIGHT = 540
PLOT_ZERO = (PLOT_LEFT + PLOT_RIGHT) / 2
ROW_HEIGHT = 30
PANEL_GAP = 18


def text(x, y, label, *, size=13, color="#172033", anchor="start", bold=False):
    weight = ' font-weight="700"' if bold else ""
    return (
        f'<text x="{x}" y="{y}" font-size="{size}" fill="{color}"'
        f' text-anchor="{anchor}"{weight}>{escape(str(label))}</text>'
    )


def signed(value):
    return f"{value:+.1f}" if round(value, 1) else "0.0"


def scale_step(limit):
    """Choose one of 1, 2, 2.5 or 5 times a power of ten per grid interval."""
    target = limit / 3
    power = 10 ** math.floor(math.log10(target))
    return next(power * value for value in (1, 2, 2.5, 5, 10) if power * value >= target)


def read_panels(path):
    panels = defaultdict(list)
    with path.open(newline="", encoding="utf-8") as source:
        for row in csv.DictReader(source):
            if row["field_size"] != "16" or row["role_view"] != "earned":
                continue
            if not row["net_rating_difference"].strip() or not int(row["contender_count"] or 0):
                continue
            difference = float(row["net_rating_difference"])
            if math.isfinite(difference):
                panels[row["league"], row["champion"]].append(row)
    if not panels:
        raise ValueError("No full-field earned-role comparisons are available to plot.")
    return panels


def render(panels):
    largest = max(abs(float(row["net_rating_difference"])) for rows in panels.values() for row in rows)
    step = scale_step(max(largest, 1))
    extent = step * 3
    height = 88 + sum(67 + ROW_HEIGHT * len(rows) + PANEL_GAP for rows in panels.values()) + 56
    svg = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{height}"'
        f' viewBox="0 0 {WIDTH} {height}" role="img" aria-labelledby="title description">',
        '<title id="title">Postseason on-court net rating by earned archetype</title>',
        '<desc id="description">Bars show how each champion’s on-court net rating compared with'
        ' eligible contenders in the 2025–26 pilot. The chart also reports champion minutes,'
        ' share of court time, and offensive and defensive possessions.</desc>',
        '<rect width="100%" height="100%" fill="#fff"/>',
        '<g font-family="system-ui,sans-serif">',
        text(28, 35, "Postseason on-court net rating by archetype", size=24, bold=True),
        text(28, 59, "2025–26 pilot · Champion minus eligible contender average · Points per 100 possessions"),
    ]

    def plot_x(value):
        return PLOT_ZERO + value / extent * (PLOT_RIGHT - PLOT_ZERO)

    top = 88
    for (league, champion), rows in sorted(panels.items()):
        rows.sort(key=lambda row: (-float(row["net_rating_difference"]), row["role"]))
        sample = rows[0]
        coverage = f'{sample["champion_validated_games"]}/{sample["champion_scheduled_games"]}'
        svg.extend([
            text(28, top + 16, f"{champion}  ·  {league}", size=17, bold=True),
            text(870, top + 16, f"Champion games validated: {coverage}", size=12, anchor="end"),
            text(28, top + 48, "Earned archetype", size=11, bold=True),
            text(588, top + 48, "Gap", size=11, anchor="end", bold=True),
            text(682, top + 48, "Minutes (%)", size=11, anchor="end", bold=True),
            text(805, top + 48, "Off / def poss.", size=11, anchor="end", bold=True),
            text(870, top + 48, "Peers", size=11, anchor="end", bold=True),
        ])
        first_y = top + 70
        last_y = first_y + ROW_HEIGHT * (len(rows) - 1) + 13
        for tick in range(-3, 4):
            value = tick * step
            x = plot_x(value)
            stroke = "#8994a7" if tick == 0 else "#e7eaf0"
            svg.append(
                f'<line x1="{x:.2f}" x2="{x:.2f}" y1="{top + 54}" y2="{last_y}" stroke="{stroke}"/>'
            )
            svg.append(text(f"{x:.2f}", top + 48, f"{value:+g}" if tick else "0", size=10, anchor="middle"))

        for index, row in enumerate(rows):
            y = first_y + ROW_HEIGHT * index
            gap = float(row["net_rating_difference"])
            net = float(row["champion_net_rating"])
            peer_mean = float(row["contender_mean_net_rating"])
            minutes = float(row["champion_minutes"])
            court_share = float(row["champion_court_pct"])
            offense = int(row["champion_off_possessions"])
            defense = int(row["champion_def_possessions"])
            peers = int(row["contender_count"])
            role = row["role"]
            x = plot_x(gap)
            detail = (
                f"{role} · Champion net rating {signed(net)} · Contender average {signed(peer_mean)}"
                f" · Gap {signed(gap)} points per 100 possessions"
            )
            svg.extend([
                f"<g><title>{escape(detail)}</title>",
                text(28, y + 4, role),
                f'<rect x="{min(x, PLOT_ZERO):.2f}" y="{y - 6}" width="{abs(x - PLOT_ZERO):.2f}"'
                f' height="12" fill="{"#176b70" if gap >= 0 else "#a86440"}"/>',
                text(588, y + 4, signed(gap), anchor="end", bold=True),
                text(682, y + 4, f"{minutes:,.1f} ({court_share:.0f}%)", size=12, anchor="end"),
                text(805, y + 4, f"{offense:,} / {defense:,}", size=12, anchor="end"),
                text(870, y + 4, peers, size=12, anchor="end"),
                "</g>",
            ])
        top += 67 + ROW_HEIGHT * len(rows) + PANEL_GAP

    svg.extend([
        text(28, top + 7, "Validated games only. Minutes and possession counts describe the champion sample.", size=12),
        text(28, top + 27, "Roles can overlap. Peers counts the eligible contenders for each row (up to 15).", size=12),
        "</g></svg>",
    ])
    return "\n".join(svg) + "\n"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("comparison_csv", type=Path)
    parser.add_argument("output_svg", type=Path)
    args = parser.parse_args()
    try:
        svg = render(read_panels(args.comparison_csv))
    except (KeyError, ValueError) as exc:
        parser.error(str(exc))
    args.output_svg.write_text(svg, encoding="utf-8")


if __name__ == "__main__":
    main()
