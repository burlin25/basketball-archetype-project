"""Build pre-postseason player totals from the four SportsDataverse pilot CSVs."""

import argparse
import csv
from collections import Counter
from pathlib import Path

FIRST_NCAA_TOURNAMENT_GAME = {2007: "2007-03-13", 2026: "2026-03-17"}
STATS = ("points", "assists", "steals", "blocks", "turnovers",
         "field_goals_attempted", "free_throws_attempted")
NBA_FIELDS = {"threes_made": "three_pointers_made",
              "threes_attempted": "three_pointers_attempted", "rebounds": "rebounds_total"}
NCAA_FIELDS = {"threes_made": "three_point_field_goals_made",
               "threes_attempted": "three_point_field_goals_attempted", "rebounds": "rebounds"}


def seconds(minutes):
    if ":" in minutes:
        whole, partial = minutes.split(":")
        return int(whole) * 60 + int(partial)
    return round(float(minutes or 0) * 60)


def totals(path, league, year):
    nba = league == "NBA"
    extra = NBA_FIELDS if nba else NCAA_FIELDS
    players = {}
    seen = set()

    with path.open(newline="", encoding="utf-8-sig") as source:
        for row in csv.DictReader(source):
            if int(row["season"]) != year:
                raise ValueError(f"Unexpected season in {path}")
            if nba and row["season_type_id"] != "2":
                continue
            if not nba and (row["season_type"] not in {"2", "3"} or
                            row["game_date"] >= FIRST_NCAA_TOURNAMENT_GAME[year]):
                continue
            player_id = row["person_id" if nba else "athlete_id"]
            if not player_id:
                continue
            key = (row["team_id"], player_id)
            appearance = (*key, row["game_id"])
            if appearance in seen:
                raise ValueError(f"Duplicate box-score row {appearance} in {path}")
            seen.add(appearance)
            team = (f'{row["team_city"]} {row["team_name"]}' if nba else row["team_display_name"])
            player = (f'{row["first_name"]} {row["family_name"]}' if nba
                      else row["athlete_display_name"])
            profile = players.setdefault(key, (team, player, Counter(), Counter()))
            _, _, counts, positions = profile
            position = row["position" if nba else "athlete_position_abbreviation"].strip()
            if position:
                positions[position] += 1
            if not row["minutes"] or (not nba and row["did_not_play"].lower() == "true"):
                continue
            counts["games"] += 1
            counts["seconds"] += seconds(row["minutes"])
            for stat, field in [(name, name) for name in STATS] + list(extra.items()):
                counts[stat] += int(float(row[field] or 0))

    if not players:
        raise ValueError(f"No eligible player records in {path}")
    for (team_id, player_id), (team, player, counts, positions) in sorted(players.items()):
        position = min(positions, key=lambda pos: (-positions[pos], pos)) if positions else ""
        yield (year, league, team_id, team, player_id, player, position, counts["games"],
               round(counts["seconds"] / 60, 2), *(counts[stat] for stat in (*STATS, *extra)))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input_dir", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    rows = []
    for year in FIRST_NCAA_TOURNAMENT_GAME:
        rows.extend(totals(args.input_dir / f"player_boxscores_{year}.csv", "NBA", year))
        rows.extend(totals(args.input_dir / f"player_box_{year}.csv", "NCAA", year))
    with args.output.open("w", newline="", encoding="utf-8") as output:
        writer = csv.writer(output)
        writer.writerow(("season", "league", "team_id", "team", "player_id", "player",
                         "source_position", "games", "minutes", *STATS, *NBA_FIELDS))
        writer.writerows(rows)


if __name__ == "__main__":
    main()
