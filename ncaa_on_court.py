"""Normalize audited 2025–26 men's NCAA tournament stints and possessions."""

import csv
import gzip
import re
import unicodedata
from collections import Counter, defaultdict
from itertools import chain, groupby

from match_pilot_rosters import read_rows

MINUTE_TOLERANCE_SECONDS = 60  # ESPN supplies whole-minute player totals.
SIDES = ("home", "away")


def name_key(name):
    return "".join(char for char in unicodedata.normalize("NFKD", name.casefold()) if char.isalnum())


def tournament_rows(path, ids):
    # Match game ID fields before parsing. The full play-by-play file spans
    # the regular season and is much larger than the tournament subset.
    pattern = re.compile(",(?:" + "|".join(sorted(ids)) + "),")
    with gzip.open(path, "rt", newline="", encoding="utf-8") as stream:
        header = next(stream)
        reader = csv.DictReader(chain((header,), (line for line in stream if pattern.search(line))))
        for row in reader:
            if row["espn_game_id"] in ids:
                yield row


def player_aliases(path):
    aliases = defaultdict(set)
    for row in read_rows(path):
        if (row["source"] == "ncaa" and row["valid_from"] and row["valid_to"]
                and int(row["valid_from"]) <= 2026 <= int(row["valid_to"])):
            aliases[(row["team_id"], row["source_player_id"])].add(row["athlete_id"])
    return aliases


def box_scores(path, schedule):
    names, seconds, scores = defaultdict(lambda: defaultdict(set)), defaultdict(dict), defaultdict(dict)
    for row in read_rows(path):
        game = row["game_id"]
        if game not in schedule:
            continue
        team, player = row["team_id"], row["athlete_id"]
        names[(game, team)][name_key(row["athlete_display_name"])].add(player)
        seconds[game][(team, player)] = float(row["minutes"] or 0) * 60
        scores[game][team] = int(row["team_score"])
    return names, seconds, scores


def identify(row, team, identifier, name, names, aliases, official):
    by_id = {player for player in aliases.get((team, identifier), ()) if (team, player) in official}
    by_name = names.get((row["espn_game_id"], team), {}).get(name_key(name), set())
    # Reject a disagreement between two positive identity matches.
    players = by_id & by_name if by_id and by_name else by_id or by_name
    return next(iter(players)) if len(players) == 1 else None


def lineup_for(row, side, names, aliases, official):
    team = row[f"{side}_espn_team_id"]
    lineup = []
    for slot in range(1, 6):
        player = identify(row, team, row[f"{side}_{slot}_player_id"],
                          row[f"{side}_{slot}_clean_name"], names, aliases, official)
        if player is None:
            return team, ()
        lineup.append(player)
    return team, tuple(sorted(lineup)) if len(set(lineup)) == 5 else ()


def clock_stints(events, periods, names, aliases, official):
    by_period = defaultdict(list)
    for row in events:
        by_period[int(row["period"])].append(row)

    stints = []
    for period in range(1, periods + 1):
        rows = by_period[period]
        if not rows:
            continue
        start = 1200 * min(period - 1, 2) + 300 * max(period - 3, 0)
        end = start + (1200 if period <= 2 else 300)
        clocks = [int(row["game_seconds"]) for row in rows]
        if clocks != sorted(clocks) or clocks[0] < start or clocks[-1] > end:
            continue
        groups = [(int(second), list(group))
                  for second, group in groupby(rows, lambda row: row["game_seconds"])]
        for side in SIDES:
            team, starters = lineup_for(rows[0], side, names, aliases, official)
            if starters and clocks[0] > start:
                stints.append((clocks[0] - start, team, starters))
        # The feed records lineups before each event. The first event at
        # the next clock reading sees substitutions from the prior clock.
        boundaries = groups[1:] + [(end, [rows[-1]])]
        for (left, _), (right, next_group) in zip(groups, boundaries):
            if right <= left:
                continue
            for side in SIDES:
                team, lineup = lineup_for(next_group[0], side, names, aliases, official)
                if lineup:
                    stints.append((right - left, team, lineup))
    return stints


def possession_rows(rows, names, aliases, official):
    possessions = []
    complete = True
    for row in rows:
        sides = dict(lineup_for(row, side, names, aliases, official) for side in SIDES)
        offense = row["poss_team_espn_team_id"]
        opponents = sides.keys() - {offense}
        if offense not in sides or len(opponents) != 1 or not all(sides.values()):
            complete = False
            continue
        defense = next(iter(opponents))
        possessions.append((offense, defense, sides[offense], sides[defense], int(row["pts"]), True))
    return possessions, complete


def scoring_rows(events, names, aliases, official):
    """Credit points to the lineup on each made-shot event."""
    result = []
    for row in events:
        if row["event_result"] != "made" or not row["shot_value"]:
            continue
        change = int(row["shot_value"])
        team = row["event_team_espn_team_id"]
        sides = dict(lineup_for(row, side, names, aliases, official) for side in SIDES)
        if team not in sides or len(sides) != 2 or not all(sides.values()):
            return [], False
        opponent = next(iter(sides.keys() - {team}))
        result.append((team, opponent, sides[team], sides[opponent], change, False))
    return result, True


def inspect_games(folder, boxes):
    schedule = {row["game_id"]: row for row in read_rows(folder / "mbb_schedule_2026.csv")
                if row["season_type"] == "3" and row["tournament_id"] == "22"}
    if len(schedule) != 67:
        raise ValueError(f"Expected 67 NCAA bracket games, got {len(schedule)}")

    names, seconds, scores = box_scores(boxes / "player_box_2026.csv", schedule)
    aliases = player_aliases(folder / "mbb_player_aliases.csv")
    events, raw_possessions = defaultdict(list), defaultdict(list)
    for row in tournament_rows(folder / "ncaa_mbb_pbp_2026.csv.gz", schedule):
        events[row["espn_game_id"]].append(row)
    for row in tournament_rows(folder / "ncaa_poss.gz", schedule):
        raw_possessions[row["espn_game_id"]].append(row)

    for game, scheduled in sorted(schedule.items()):
        official = seconds[game]
        periods = int(float(scheduled["status_period"]))
        clock = 2400 + 300 * (periods - 2)
        stints = clock_stints(events[game], periods, names, aliases, official)
        possessions, complete = possession_rows(raw_possessions[game], names, aliases, official)
        observed_scores, team_time, player_time = Counter(), Counter(), Counter()
        for offense, _, _, _, points, _ in possessions:
            observed_scores[offense] += points
        for duration, team, lineup in stints:
            team_time[team] += duration
            for player in lineup:
                player_time[(team, player)] += duration
        expected_scores = {scheduled[f"{side}_id"]: int(scheduled[f"{side}_score"]) for side in SIDES}
        max_error = max((abs(player_time[key] - official.get(key, 0))
                         for key in player_time.keys() | official.keys()), default=None)
        points, scoring_complete = scoring_rows(events[game], names, aliases, official)
        reconstructed_points = Counter()
        for offense, _, _, _, value, _ in points:
            reconstructed_points[offense] += value
        score_matches = (complete and scoring_complete
                         and reconstructed_points == observed_scores == expected_scores == scores[game])
        # Count possession opportunities with the possession feed's lineups,
        # while attributing points to the lineups attached to scoring events.
        possessions = [(off, de, off_lineup, de_lineup, 0, count)
                       for off, de, off_lineup, de_lineup, _, count in possessions] + points
        clock_matches = team_time == dict.fromkeys(expected_scores, clock)
        minutes_match = max_error is not None and max_error <= MINUTE_TOLERANCE_SECONDS
        failures = [reason for passed, reason in (
            (bool(events[game]), "missing play-by-play"),
            (score_matches, "scoring or possession lineup discrepancy"),
            (clock_matches, "incomplete lineup clock"),
            (minutes_match, "player minutes exceed tolerance"),
        ) if not passed]
        audit = {
            "game_id": game, "lineup_present": bool(events[game]),
            "possession_score_matches": score_matches, "official_clock_seconds": clock,
            "covered_clock_seconds": min((team_time[team] for team in expected_scores), default=0),
            "max_player_seconds_error": max_error, "validated": not failures,
            "reason": " | ".join(failures),
        }
        yield audit, stints, possessions
