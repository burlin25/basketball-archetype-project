"""Compare champion stretch-big minutes with other contenders in the pilot."""

import argparse
import csv
from collections import defaultdict
from pathlib import Path
from statistics import mean

from assign_pilot_roles import BIGS
from match_pilot_rosters import read_rows, sweet_sixteen_games

CHAMPIONS = {(2007, "NBA"): "1610612759", (2026, "NBA"): "1610612752",
             (2007, "NCAA"): "57", (2026, "NCAA"): "130"}


def final_eight(folder, year, league):
    if league == "NBA":
        rows = read_rows(folder / f"player_boxscores_{year}.csv")
        teams = {r["team_id"] for r in rows
                 if r["season_type_id"] == "4" and r["game_id"][7:8] == "2"}
    else:
        game_ids = sweet_sixteen_games(folder, year)
        rows = read_rows(folder / f"player_box_{year}.csv")
        teams = {r["team_id"] for r in rows if r["game_id"] in game_ids
                 and r["team_winner"].lower() == "true"}
    if len(teams) != 8:
        raise ValueError(f"Expected eight advancing teams for {league} {year}, found {len(teams)}")
    return teams


def qualifies(row, cutoff):
    return (row["analysis_position"] in BIGS
            and float(row["minutes"]) >= 150
            and int(row["threes_attempted"]) >= 40
            and row["threes_attempted_cohort"] in {"position", "family"}
            and row["three_accuracy_cohort"] in {"position", "family"}
            and float(row["threes_attempted_percentile"]) >= cutoff
            and float(row["three_accuracy_percentile"]) >= 50)


def compare(players, folder):
    teams = defaultdict(lambda: defaultdict(list))
    for row in players:
        teams[int(row["season"]), row["league"]][row["team_id"]].append(row)
    for (year, league), rotations in sorted(teams.items()):
        elite = final_eight(folder, year, league)
        champion = CHAMPIONS[year, league]
        if len(rotations) != 16 or not elite <= rotations.keys() or champion not in elite:
            raise ValueError(f"Unexpected postseason field for {league} {year}")
        for cutoff in (75, 70):
            shares = {
                team: 100 * sum(float(r["minutes"]) for r in roster if qualifies(r, cutoff))
                / sum(float(r["minutes"]) for r in roster)
                for team, roster in rotations.items()
            }
            for field in (set(rotations), elite):
                other = mean(shares[team] for team in field - {champion})
                yield (year, league, len(field), cutoff, rotations[champion][0]["team"],
                       round(shares[champion], 2), round(other, 2),
                       round(shares[champion] - other, 2))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("players", type=Path)
    parser.add_argument("input_dir", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    rows = list(compare(read_rows(args.players), args.input_dir))
    with args.output.open("w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file, lineterminator="\n")
        writer.writerow(("season", "league", "field_size", "volume_percentile_cutoff",
                         "champion", "champion_minutes_pct", "other_teams_mean_minutes_pct",
                         "difference_percentage_points"))
        writer.writerows(rows)


if __name__ == "__main__":
    main()
