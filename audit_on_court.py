"""Audit 2025–26 postseason lineup sources against game box scores."""

import argparse
import csv
import gzip
from collections import Counter, defaultdict
from pathlib import Path

from match_pilot_rosters import read_rows


def compressed(path):
    with gzip.open(path, "rt", newline="", encoding="utf-8") as stream:
        yield from csv.DictReader(stream)


def audit_nba(folder, boxes):
    expected = defaultdict(Counter)
    minutes = defaultdict(dict)
    for row in read_rows(boxes / "player_boxscores_2026.csv"):
        if row["season_type_id"] != "4":
            continue
        game = row["game_id"]
        expected[game][row["team_id"]] += int(row["points"] or 0)
        if row["minutes"]:
            minute, second = map(float, row["minutes"].split(":"))
            minutes[game][row["person_id"]] = minute * 60 + second

    scores = defaultdict(Counter)
    for row in compressed(folder / "nba_possessions_2026.csv.gz"):
        if row["game_id"] in expected:
            scores[row["game_id"]][row["offense_team_id"]] += int(row["points"])

    lineups = {}
    for row in compressed(folder / "nba_lineups_2026.csv.gz"):
        if row["game_id"] in expected:
            key = row["game_id"], row["action_number"]
            lineups[key] = [row[f"{side}_player_{slot}"]
                            for side in ("home", "away") for slot in range(1, 6)]

    events = defaultdict(list)
    for row in compressed(folder / "nba_pbp.gz"):
        if row["game_id"] in expected:
            events[row["game_id"]].append(row)

    for game, official in sorted(expected.items()):
        reconstructed = Counter()
        covered = 0
        periods = defaultdict(list)
        for row in events[game]:
            periods[int(row["period"])].append(row)
        for period, rows in periods.items():
            rows.sort(key=lambda row: int(row["order_index"]))
            for row, following in zip(rows, rows[1:]):
                duration = float(row["seconds_remaining"]) - float(following["seconds_remaining"])
                players = lineups.get((game, row["action_number"]), [])
                if duration > 0 and len(set(players) - {"", "0"}) == 10:
                    covered += duration
                    for player in players:
                        reconstructed[player] += duration
        # Total logged player seconds divided by ten gives game-clock seconds.
        clock = round(sum(minutes[game].values()) / 10)
        errors = [abs(reconstructed[p] - minutes[game].get(p, 0))
                  for p in reconstructed.keys() | minutes[game].keys()]
        yield ("NBA", game, bool(periods), scores[game] == official, clock, round(covered, 2),
               round(max(errors, default=0), 2))


def audit_ncaa(folder, boxes):
    # Audit the late-round ESPN ID window first. Earlier games need a bracket crosswalk.
    expected = defaultdict(dict)
    clocks = Counter()
    for row in read_rows(boxes / "player_box_2026.csv"):
        game = row["game_id"]
        if row["season_type"] == "3" and "401856534" <= game <= "401856600":
            expected[game][row["team_id"]] = int(row["team_score"])
            clocks[game] += float(row["minutes"] or 0) * 6

    scores = defaultdict(Counter)
    contests = {}
    for row in compressed(folder / "ncaa_poss.gz"):
        game = row["espn_game_id"]
        if game in expected:
            contests[row["contest_id"]] = game
            team = row["poss_team_espn_team_id"]
            scores[game][team] += int(row["pts"])

    covered = Counter()
    for row in compressed(folder / "ncaa_mbb_matchup_stints_2026.csv.gz"):
        game = contests.get(row["contest_id"])
        if game:
            covered[game] += int(row["duration_seconds"])
    for game, official in sorted(expected.items()):
        clock = 2400 + 300 * max(0, round((clocks[game] - 2400) / 300))
        yield ("NCAA", game, game in covered, scores[game] == official, clock, covered[game], "")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("lineups", type=Path)
    parser.add_argument("box_scores", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    rows = list(audit_nba(args.lineups, args.box_scores)) + list(audit_ncaa(args.lineups, args.box_scores))
    with args.output.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.writer(stream, lineterminator="\n")
        writer.writerow(("league", "game_id", "lineup_present", "possession_score_matches",
                         "official_clock_seconds", "covered_clock_seconds", "max_player_seconds_error"))
        writer.writerows(rows)


if __name__ == "__main__":
    main()
