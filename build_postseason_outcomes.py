"""Attach final-eight and championship outcomes to each historical postseason team."""

import argparse
import csv
from collections import Counter, defaultdict
from pathlib import Path

from compare_stretch_bigs import CHAMPIONS, final_eight
from match_pilot_rosters import read_rows


def nba_champion(folder, year):
    scores = defaultdict(Counter)
    for row in read_rows(folder / f"player_boxscores_{year}.csv"):
        if row["season_type_id"] == "4" and row["game_id"][7:8] == "4":
            scores[row["game_id"]][row["team_id"]] += int(float(row["points"] or 0))
    wins = Counter()
    for teams in scores.values():
        if len(teams) != 2 or len(set(teams.values())) != 2:
            raise ValueError(f"Invalid NBA Finals score in {year}: {teams}")
        wins[teams.most_common(1)[0][0]] += 1
    winners = [team for team, count in wins.items() if count == 4]
    if len(winners) != 1:
        raise ValueError(f"Expected one NBA Finals winner in {year}")
    return winners[0]


def college_champion(folder, year, elite):
    games = defaultdict(dict)
    for row in read_rows(folder / f"player_box_{year}.csv"):
        if (row["season_type"] == "3" and row["game_date"].startswith(f"{year}-04")
                and row["team_id"] in elite and row["opponent_team_id"] in elite):
            key = row["game_date"], row["game_id"]
            games[key][row["team_id"]] = row["team_winner"].lower() == "true"
    if not games:
        raise ValueError(f"Missing NCAA championship game in {year}")
    finalists = games[max(games)]
    if len(finalists) != 2 or sum(finalists.values()) != 1:
        raise ValueError(f"Invalid NCAA championship result in {year}")
    return next(team for team, won in finalists.items() if won)


def outcomes(players, folder):
    fields = defaultdict(dict)
    for row in players:
        fields[int(row["season"]), row["league"]][row["team_id"]] = row["team"]
    for (year, league), teams in sorted(fields.items()):
        elite = final_eight(folder, year, league)
        champion = nba_champion(folder, year) if league == "NBA" else college_champion(folder, year, elite)
        if (len(teams) != 16 or not elite <= teams.keys() or champion not in elite
                or CHAMPIONS.get((year, league), champion) != champion):
            raise ValueError(f"Unexpected postseason field for {league} {year}")
        for team, name in sorted(teams.items(), key=lambda pair: pair[1]):
            yield year, league, team, name, team in elite, team == champion


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("players", type=Path)
    parser.add_argument("input_dir", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    rows = list(outcomes(read_rows(args.players), args.input_dir))
    with args.output.open("w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file, lineterminator="\n")
        writer.writerow(("season", "league", "team_id", "team", "final_eight", "on_court_champion"))
        writer.writerows(rows)


if __name__ == "__main__":
    main()
