"""Summarize audited 2025–26 postseason floor time and net rating by role."""

import argparse
import csv
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from statistics import mean

from match_pilot_rosters import read_rows

SEASON = "2026"
MIN_POSSESSIONS = 30
AUDIT_FIELDS = ("game_id", "lineup_present", "possession_score_matches", "official_clock_seconds",
                "covered_clock_seconds", "max_player_seconds_error", "max_player_plus_minus_error",
                "exact_player_plus_minus_rows", "player_plus_minus_rows", "validated", "reason")


@dataclass
class Exposure:
    seconds: float = 0
    offense: int = 0
    defense: int = 0
    scored: int = 0
    allowed: int = 0

    def net_rating(self):
        if self.offense and self.defense:
            return 100 * (self.scored / self.offense - self.allowed / self.defense)
        return None

    def eligible(self):
        return min(self.offense, self.defense) >= MIN_POSSESSIONS


def role_index(players):
    index = {}
    for row in players:
        if row["season"] != SEASON:
            continue
        earned = set(filter(None, row["secondary_tags"].split("; ")))
        if row["primary_met_threshold"] == "True":
            earned.add(row["primary_role"])
        index[row["league"], row["team_id"], row["player_id"]] = (row["primary_role"], earned)
    return index


def accumulate(league, games, index, field):
    exposures = defaultdict(Exposure)
    court_seconds = defaultdict(float)
    unknown_player_seconds = defaultdict(float)
    game_counts = defaultdict(set)

    def roles_on_floor(team, lineup):
        roles = set()
        for player in lineup:
            match = index.get((league, team, player))
            if match:
                primary, earned = match
                roles.add(("main", primary))
                roles.update(("earned", tag) for tag in earned)
        return roles

    for game, stints, possessions in games:
        for duration, team, lineup in stints:
            if team not in field or duration <= 0:
                continue
            court_seconds[team] += duration
            game_counts[team].add(game)
            unknown_player_seconds[team] += duration * sum(
                (league, team, player) not in index for player in lineup
            )
            for view, role in roles_on_floor(team, lineup):
                exposures[team, view, role].seconds += duration

        for off_team, def_team, off_players, def_players, points, counted in possessions:
            if off_team in field:
                for view, role in roles_on_floor(off_team, off_players):
                    exposure = exposures[off_team, view, role]
                    exposure.offense += int(counted)
                    exposure.scored += points
            if def_team in field:
                for view, role in roles_on_floor(def_team, def_players):
                    exposure = exposures[def_team, view, role]
                    exposure.defense += int(counted)
                    exposure.allowed += points

    return exposures, court_seconds, unknown_player_seconds, game_counts


def scheduled_games(league, lineups, boxes):
    schedule = defaultdict(set)
    if league == "NBA":
        for row in read_rows(boxes / "player_boxscores_2026.csv"):
            if row["season_type_id"] == "4":
                schedule[row["team_id"]].add(row["game_id"])
    else:
        for row in read_rows(lineups / "mbb_schedule_2026.csv"):
            if row["season_type"] == "3" and row["tournament_id"] == "22":
                schedule[row["home_id"]].add(row["game_id"])
                schedule[row["away_id"]].add(row["game_id"])
    return schedule


def team_rows(league, field, exposures, court_seconds, unknown_seconds, games, schedule):
    for (team, view, role), value in sorted(exposures.items()):
        total = court_seconds[team]
        rating = value.net_rating()
        yield (league, field[team]["team"], team, view, role, len(games[team]), len(schedule[team]),
               round(value.seconds / 60, 2), round(100 * value.seconds / total, 2) if total else "",
               value.offense, value.defense, value.scored, value.allowed,
               round(rating, 2) if rating is not None else "",
               round(100 * unknown_seconds[team] / (5 * total), 2) if total else "")


def comparison_rows(league, field, exposures, court_seconds, games, schedule):
    champion, = (team for team, info in field.items() if info["on_court_champion"] == "True")
    for (team, view, role), value in sorted(exposures.items()):
        if team != champion or not value.eligible() or not court_seconds[champion]:
            continue
        rating = value.net_rating()
        for size in (16, 8):
            peers = []
            for other, info in field.items():
                if other == champion or (size == 8 and info["final_eight"] != "True"):
                    continue
                exposure = exposures.get((other, view, role))
                if exposure and exposure.eligible() and court_seconds[other]:
                    peers.append(exposure.net_rating())
            if peers:
                average = mean(peers)
                yield (league, size, view, role, field[champion]["team"],
                       round(value.seconds / 60, 2), round(100 * value.seconds / court_seconds[champion], 2),
                       value.offense, value.defense, round(rating, 2), round(average, 2),
                       round(rating - average, 2), len(peers), len(games[champion]),
                       len(schedule[champion]))


def validated_games(league, inspected, audit_rows):
    for audit, stints, possessions in inspected:
        audit_rows.append((league, *(audit.get(key, "") for key in AUDIT_FIELDS)))
        if audit["validated"]:
            yield audit["game_id"], stints, possessions


def save(path, columns, rows):
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.writer(stream, lineterminator="\n")
        writer.writerow(columns)
        writer.writerows(rows)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("lineups", type=Path)
    parser.add_argument("boxes", type=Path)
    parser.add_argument("--league", choices=("NBA", "NCAA"), action="append")
    parser.add_argument("--output-dir", type=Path, default=Path("."))
    args = parser.parse_args()
    index = role_index(read_rows(Path("historical_archetypes.csv")))
    outcomes = list(read_rows(Path("historical_postseason_teams.csv")))
    teams, comparisons, coverage, audits = [], [], [], []
    for league in args.league or ("NBA", "NCAA"):
        if league == "NBA":
            from nba_on_court import inspect_games
        else:
            from ncaa_on_court import inspect_games
        field = {row["team_id"]: row for row in outcomes
                 if row["season"] == SEASON and row["league"] == league}
        validated = validated_games(league, inspect_games(args.lineups, args.boxes), audits)
        exposures, clocks, unknowns, games = accumulate(league, validated, index, field)
        schedule = scheduled_games(league, args.lineups, args.boxes)
        for team, info in sorted(field.items()):
            if not games[team] <= schedule[team]:
                raise ValueError(f"Unexpected postseason games for {league} {info['team']}")
            clock = clocks[team]
            coverage.append((league, info["team"], team, len(games[team]), len(schedule[team]),
                             round(clock / 60, 2),
                             round(100 * unknowns[team] / (5 * clock), 2) if clock else ""))
        teams.extend(team_rows(league, field, exposures, clocks, unknowns, games, schedule))
        comparisons.extend(comparison_rows(league, field, exposures, clocks, games, schedule))
        print(f"{league}: {len(set().union(*games.values()))} games, {sum(bool(game_set) for game_set in games.values())} teams with clock coverage")

    save(args.output_dir / "on_court_reconstruction_audit.csv", ("league", *AUDIT_FIELDS), audits)
    save(args.output_dir / "on_court_team_coverage.csv",
         ("league", "team", "team_id", "validated_games", "scheduled_games",
          "validated_team_minutes", "unmatched_player_clock_pct"), coverage)
    save(args.output_dir / "on_court_team_roles.csv",
         ("league", "team", "team_id", "role_view", "role", "games_with_clock", "scheduled_games",
          "on_court_minutes", "court_pct", "off_possessions", "def_possessions",
          "points_scored", "points_allowed", "net_rating", "unmatched_player_clock_pct"), teams)
    save(args.output_dir / "on_court_role_comparison.csv",
         ("league", "field_size", "role_view", "role", "champion", "champion_minutes",
          "champion_court_pct", "champion_off_possessions", "champion_def_possessions",
          "champion_net_rating", "contender_mean_net_rating", "net_rating_difference",
          "contender_count", "champion_validated_games", "champion_scheduled_games"), comparisons)


if __name__ == "__main__":
    main()
