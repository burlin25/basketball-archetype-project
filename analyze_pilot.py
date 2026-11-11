"""Summarize pre-postseason rotation minutes by role from a player CSV."""

import argparse
import csv
import math
from collections import Counter, defaultdict
from pathlib import Path


def analyze(path):
    with path.open(newline="", encoding="utf-8") as source:
        reader = csv.DictReader(source)
        required = {"season", "league", "team", "player", "minutes", "primary_role", "confidence"}
        missing = required.difference(reader.fieldnames or ())
        if missing:
            raise ValueError(f"Missing CSV columns: {', '.join(sorted(missing))}")

        rotations = defaultdict(lambda: (Counter(), Counter()))
        players = set()
        for line, row in enumerate(reader, start=2):
            player = tuple(row[field].strip() for field in ("season", "league", "team", "player"))
            role = row["primary_role"].strip()
            confidence = row["confidence"].strip().lower()
            if not all(player) or not role or confidence not in {"high", "medium", "low", "very low"}:
                raise ValueError(f"Invalid player, role, or confidence on line {line}")
            player_key = (*player[:3], (row.get("player_id") or player[3]).strip())
            if player_key in players:
                raise ValueError(f"Duplicate team-player record on line {line}")
            players.add(player_key)

            minutes = float(row["minutes"])
            if not math.isfinite(minutes) or minutes < 0:
                raise ValueError(f"Invalid minutes on line {line}")

            main, stricter = rotations[player[:3]]
            main[role] += minutes
            stricter["Uncertain" if confidence in {"low", "very low"} else role] += minutes

    if not rotations:
        raise ValueError("No player records found")

    for team, (main, stricter) in sorted(rotations.items()):
        total = sum(main.values())
        if not total:
            raise ValueError(f"No rotation minutes for {', '.join(team)}")
        for role in sorted(main.keys() | stricter.keys()):
            yield (*team, role, round(100 * main[role] / total, 2),
                   round(100 * stricter[role] / total, 2), total)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("players", type=Path, help="CSV of complete team rotations")
    parser.add_argument("output", type=Path)
    args = parser.parse_args()

    try:
        if args.players.resolve() == args.output.resolve():
            raise ValueError("Use a different path for the output CSV")
        rows = list(analyze(args.players))
        with args.output.open("w", newline="", encoding="utf-8") as output:
            writer = csv.writer(output, lineterminator="\n")
            writer.writerow(["season", "league", "team", "role", "main_minutes_pct",
                             "stricter_minutes_pct", "team_minutes_in_input"])
            writer.writerows(rows)
    except (ValueError, OSError) as error:
        parser.exit(1, f"{error}\n")


if __name__ == "__main__":
    main()
