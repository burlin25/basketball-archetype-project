"""Compare main archetype rotation shares for historical champions and contenders."""

import argparse
import csv
from collections import defaultdict
from pathlib import Path
from statistics import mean

from match_pilot_rosters import read_rows


def compare(rotations, outcomes):
    shares = defaultdict(dict)
    for row in rotations:
        key = row["season"], row["league"], row["team"]
        shares[key][row["role"]] = (
            float(row["main_minutes_pct"]), float(row["stricter_minutes_pct"])
        )

    fields = defaultdict(list)
    for team in outcomes:
        fields[team["season"], team["league"]].append(team)

    for (season, league), field in sorted(fields.items()):
        champions = [team for team in field if team["on_court_champion"] == "True"]
        elite = [team for team in field if team["final_eight"] == "True"]
        if len(field) != 16 or len(elite) != 8 or len(champions) != 1 or champions[0] not in elite:
            raise ValueError(f"Invalid postseason outcomes for {season} {league}")
        champion = champions[0]["team"]
        for group in (field, elite):
            contenders = [shares[season, league, team["team"]] for team in group
                          if team["team"] != champion]
            champion_shares = shares[season, league, champion]
            if not champion_shares or any(not team for team in contenders):
                raise ValueError(f"Missing team rotation in {season} {league}")
            roles = set(champion_shares).union(*(team.keys() for team in contenders))
            for role in sorted(roles):
                values = []
                for index in (0, 1):
                    winner = champion_shares.get(role, (0, 0))[index]
                    others = mean(team.get(role, (0, 0))[index] for team in contenders)
                    values.extend((winner, round(others, 2), round(winner - others, 2)))
                yield season, league, len(group), champion, role, *values


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("rotations", type=Path)
    parser.add_argument("outcomes", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    rows = list(compare(read_rows(args.rotations), read_rows(args.outcomes)))
    with args.output.open("w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file, lineterminator="\n")
        writer.writerow(("season", "league", "field_size", "on_court_champion", "primary_role",
                         "champion_minutes_pct", "other_teams_mean_minutes_pct", "difference_pp",
                         "stricter_champion_minutes_pct", "stricter_other_teams_mean_minutes_pct",
                         "stricter_difference_pp"))
        writer.writerows(rows)


if __name__ == "__main__":
    main()
