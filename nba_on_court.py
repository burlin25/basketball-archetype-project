"""Reconstruct and validate 2025–26 NBA playoff stints from substitutions."""

import csv
import gzip
import re
import unicodedata
from collections import Counter, defaultdict
from itertools import combinations
from math import isclose
from pathlib import Path

from match_pilot_rosters import read_rows


ACTOR_EVENTS = {"made_shot", "missed_shot", "rebound", "turnover", "jump_ball", "free_throw"}
PLAYER_CLOCK_TOLERANCE = 1


def compressed_rows(path):
    with gzip.open(path, "rt", encoding="utf-8", newline="") as stream:
        yield from csv.DictReader(stream)


def name_key(value):
    normalized = unicodedata.normalize("NFD", value.casefold())
    return re.sub("[^a-z0-9]", "", normalized)


def read_boxes(path):
    games = defaultdict(list)
    for row in read_rows(path):
        if row["season_type_id"] == "4":
            games[row["game_id"]].append(row)
    return games


def player_aliases(boxes, events, player_teams):
    aliases = defaultdict(set)
    for row in boxes:
        first, last = row["first_name"], row["family_name"]
        for name in (first, last, row["name_i"], first + last, first[:1] + last, first[:3] + last):
            aliases[row["team_id"], name_key(name)].add(row["person_id"])
    for event in events:
        player = event["person_id"]
        if player in player_teams and event["player_name_i"]:
            aliases[player_teams[player], name_key(event["player_name_i"])].add(player)
    return aliases


def infer_period_starters(events, team, eligible, box_starters, published, aliases):
    required, excluded, seen = set(), set(), set()
    substitutions = {}
    for event in events:
        if event["team_id"] != team:
            continue
        player = event["person_id"]
        if event["is_substitution"] == "true":
            incoming = event["description"].partition(" FOR ")[0].removeprefix("SUB: ")
            candidates = aliases[team, name_key(incoming)] - {player}
            if len(candidates) != 1 or player not in eligible:
                raise ValueError(f'Unresolved substitution {event["description"]}')
            incoming_id = next(iter(candidates))
            if player not in seen:
                required.add(player)
            if incoming_id not in seen:
                excluded.add(incoming_id)
            seen.update((player, incoming_id))
            substitutions[event["order_index"]] = (player, incoming_id)
        elif (player in eligible and player not in seen and event["event_type"] in ACTOR_EVENTS
              and "Technical" not in event["description"]):
            required.add(player)
            seen.add(player)

    period = int(events[0]["period"])
    if period == 1 and len(box_starters) == 5:
        options = [box_starters]
    else:
        if len(required) > 5:
            raise ValueError("More than five inferred period starters")
        options = [required.union(players)
                   for players in combinations(sorted(eligible - required - excluded), 5 - len(required))]
    # The published first lineup breaks ties among starter sets consistent with substitutions.
    for option in sorted(options, key=lambda players: (-len(players & published), sorted(players))):
        active = set(option)
        for outgoing, incoming in substitutions.values():
            if outgoing not in active or incoming in active:
                break
            active.remove(outgoing)
            active.add(incoming)
        else:
            return set(option), substitutions
    raise ValueError(f"No consistent period lineup for team {team}, period {period}")


def reconstruct(events, boxes, published):
    player_teams = {row["person_id"]: row["team_id"] for row in boxes if row["minutes"]}
    eligible = {team: {player for player, value in player_teams.items() if team == value}
                for team in set(player_teams.values())}
    aliases = player_aliases([row for row in boxes if row["minutes"]], events, player_teams)
    by_period = defaultdict(list)
    for event in sorted(events, key=lambda row: int(row["order_index"])):
        by_period[int(event["period"])].append(event)
    expected_periods = set(range(1, max(by_period, default=0) + 1))
    if len(eligible) != 2 or set(by_period) != expected_periods or len(by_period) < 4:
        raise ValueError("Incomplete teams or periods")
    stints, states = [], {}
    scoring = []
    for period, period_events in sorted(by_period.items()):
        active = {}
        substitutions = {}
        prior = published.get((period_events[0]["period"], period_events[0]["action_number"]), set())
        for team, available in eligible.items():
            box_starters = {row["person_id"] for row in boxes if row["team_id"] == team and row["position"]}
            active[team], changes = infer_period_starters(period_events, team, available, box_starters, prior, aliases)
            substitutions.update(changes)
        clock = 720 if period <= 4 else 300
        scoring_lineups = None
        for event in period_events:
            new_clock = float(event["seconds_remaining"])
            if new_clock > clock + 1e-8:
                raise ValueError(f"Clock increased in period {period}")
            index = event["order_index"]
            lineups = {team: tuple(sorted(players)) for team, players in active.items()}
            states[index] = lineups
            if scoring_lineups is None or new_clock < clock:
                scoring_lineups = lineups
            if new_clock < clock:
                stints.extend((clock - new_clock, team, lineup) for team, lineup in lineups.items())
            clock = new_clock
            points = 0
            if event["is_made_shot"] == "true":
                points = int(event["shot_value"])
            elif event["event_type"] == "free_throw" and not event["description"].startswith("MISS"):
                points = 1
            if points:
                team = event["team_id"]
                opponent = next(other for other in active if other != team)
                # Box-score plus-minus generally credits scoring before substitutions
                # at the same clock reading, even when recorded after them.
                scoring.append((team, opponent, scoring_lineups[team],
                                scoring_lineups[opponent], points, False))
            if index in substitutions:
                outgoing, incoming = substitutions[index]
                active[event["team_id"]].remove(outgoing)
                active[event["team_id"]].add(incoming)
        if clock > 0:
            raise ValueError(f"Missing period-end clock in period {period}")
    return stints, states, scoring


def validate(stints, scoring, boxes):
    seconds = Counter()
    points = Counter()
    plus_minus = Counter()
    court_time = Counter()
    for duration, team, lineup in stints:
        court_time[team] += duration
        for player in lineup:
            seconds[player] += duration
    for team, _, offense, defense, value, _ in scoring:
        points[team] += value
        for player in offense:
            plus_minus[player] += value
        for player in defense:
            plus_minus[player] -= value
    official = Counter()
    expected_seconds = {}
    expected_plus_minus = {}
    for row in boxes:
        player = row["person_id"]
        official[row["team_id"]] += int(row["points"] or 0)
        if row["minutes"]:
            minute, second = map(float, row["minutes"].split(":"))
            expected_seconds[player] = minute * 60 + second
            expected_plus_minus[player] = float(row["plus_minus_points"])
    errors = [abs(seconds[p] - expected_seconds.get(p, 0)) for p in seconds.keys() | expected_seconds.keys()]
    clock = 2880 + 300 * max(0, round((sum(expected_seconds.values()) / 10 - 2880) / 300))
    max_clock_error = round(max(errors), 3)
    pm_errors = [abs(plus_minus[p] - expected) for p, expected in expected_plus_minus.items()]
    max_pm_error = max(pm_errors)
    passed = (max_clock_error <= PLAYER_CLOCK_TOLERANCE and points == official
              and len(court_time) == 2 and all(isclose(value, clock) for value in court_time.values()))
    return (passed, clock, min(court_time.values()), max_clock_error, max_pm_error,
            sum(error == 0 for error in pm_errors), len(pm_errors))


def process_games(folder: Path, boxes: Path):
    """Yield (game ID, stints, possession records, validation fields) for each game."""
    box_games = read_boxes(boxes / "player_boxscores_2026.csv")
    event_games, possession_games = defaultdict(list), defaultdict(list)
    published = defaultdict(dict)
    for row in compressed_rows(folder / "nba_pbp.gz"):
        if row["game_id"] in box_games:
            event_games[row["game_id"]].append(row)
    for row in compressed_rows(folder / "nba_lineups_2026.csv.gz"):
        if row["game_id"] in box_games:
            published[row["game_id"]][row["period"], row["action_number"]] = {
                row[f"{side}_player_{slot}"] for side in ("home", "away") for slot in range(1, 6)
            }
    for row in compressed_rows(folder / "nba_possessions_2026.csv.gz"):
        if row["game_id"] in box_games:
            possession_games[row["game_id"]].append(row)

    for game, box in sorted(box_games.items()):
        try:
            stints, states, scoring = reconstruct(event_games[game], box, published[game])
            passed, clock, covered, clock_error, pm_error, pm_exact, pm_total = validate(stints, scoring, box)
            possessions = []
            possession_score = Counter()
            possession_counts = Counter()
            for row in possession_games[game]:
                offense, defense = row["offense_team_id"], row["defense_team_id"]
                possession_score[offense] += int(row["points"])
                if row["count_as_possession"] == "true":
                    lineups = states[row["end_order_index"]]
                    if offense == defense or len(lineups[offense]) != 5 or len(lineups[defense]) != 5:
                        raise ValueError("Invalid possession lineup")
                    possession_counts[offense] += 1
                    possessions.append((offense, defense, lineups[offense], lineups[defense], 0, True))
            scoring_totals = Counter()
            for team, _, _, _, points, _ in scoring:
                scoring_totals[team] += points
            score_match = possession_score == scoring_totals
            passed = passed and score_match and possession_counts.keys() == scoring_totals.keys()
            yield game, stints, scoring + possessions, (
                passed, clock, round(covered, 3), clock_error, pm_error, pm_exact, pm_total,
                score_match, "" if passed else "Validation failed",
            )
        except (ValueError, KeyError) as error:
            yield game, [], [], (False, "", "", "", "", "", "", False, str(error))


def inspect_games(folder: Path, boxes: Path):
    """Yield (audit row, stints, possession records) for all NBA playoff games."""
    for game, stints, possessions, audit in process_games(folder, boxes):
        passed, clock, covered, player_error, pm_error, pm_exact, pm_total, score_match, reason = audit
        yield {
            "game_id": game,
            "lineup_present": bool(stints),
            "possession_score_matches": score_match,
            "official_clock_seconds": clock,
            "covered_clock_seconds": covered,
            "max_player_seconds_error": player_error,
            "validated": passed,
            "max_player_plus_minus_error": pm_error,
            "exact_player_plus_minus_rows": pm_exact,
            "player_plus_minus_rows": pm_total,
            "reason": reason,
        }, stints, possessions
