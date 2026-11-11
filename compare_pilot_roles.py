"""Compare champions' main-role minutes with other pilot postseason teams."""

import argparse
import csv
from collections import Counter, defaultdict
from pathlib import Path
from statistics import mean

from compare_stretch_bigs import CHAMPIONS, final_eight
from match_pilot_rosters import read_rows


def compare(players, folder):
    fields = defaultdict(lambda: defaultdict(list))
    for row in players:
        fields[int(row["season"]), row["league"]][row["team_id"]].append(row)
    if fields.keys() != CHAMPIONS.keys():
        raise ValueError("Expected both pilot seasons for both leagues")

    for (year, league), teams in sorted(fields.items()):
        champion = CHAMPIONS[year, league]
        elite = final_eight(folder, year, league)
        if len(teams) != 16 or not elite <= teams.keys() or champion not in elite:
            raise ValueError(f"Unexpected postseason field for {league} {year}")

        shares = {}
        roles = {"Uncertain"}
        for team, players in teams.items():
            main, stricter = Counter(), Counter()
            for player in players:
                minutes = float(player["minutes"])
                role = player["primary_role"]
                main[role] += minutes
                stricter["Uncertain" if player["confidence"] in {"low", "very low"} else role] += minutes
            total = sum(main.values())
            roles.update(main)
            shares[team] = [{role: minutes * 100 / total for role, minutes in counts.items()}
                            for counts in (main, stricter)]

        for field in (set(teams), elite):
            for role in sorted(roles):
                values = []
                for index in (0, 1):
                    winner = shares[champion][index].get(role, 0)
                    others = mean(shares[team][index].get(role, 0) for team in field - {champion})
                    values.extend((round(winner, 2), round(others, 2), round(winner - others, 2)))
                yield (year, league, len(field), teams[champion][0]["team"], role, *values)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("players", type=Path)
    parser.add_argument("input_dir", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    rows = list(compare(read_rows(args.players), args.input_dir))
    with args.output.open("w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file, lineterminator="\n")
        writer.writerow(("season", "league", "field_size", "champion", "primary_role",
                         "champion_minutes_pct", "other_teams_mean_minutes_pct", "difference_pp",
                         "stricter_champion_minutes_pct", "stricter_other_teams_mean_minutes_pct",
                         "stricter_difference_pp"))
        writer.writerows(rows)


if __name__ == "__main__":
    main()
