"""Match the pilot postseason fields to player totals and available roster bios."""

import argparse
import csv
import re
import unicodedata
from collections import defaultdict
from pathlib import Path
from statistics import median

SWEET_SIXTEEN_GAMES = {
    2007: {"274000022", "274000060", "274000029", "274000053",
           "274000038", "274000014", "274000045", "274000007"},
    2026: {"401856570", "401856572", "401856571", "401856573",
           "401856569", "401856568", "401856566", "401856567"},
}
SWEET_SIXTEEN_START = {
    2007: 22, 2008: 27, 2009: 26, 2010: 25, 2011: 24, 2012: 22,
    2013: 28, 2014: 27, 2015: 26, 2016: 24, 2017: 23, 2018: 22,
    2019: 28, 2021: 27, 2022: 24, 2023: 23, 2024: 28, 2025: 27, 2026: 26,
}
# Other postseason tournaments can play on the same dates as the Sweet 16.
NON_NCAA_GAMES = {
    "400872592", "401125273", "401124960", "401125175", "401124959",
    "401311785", "401311786", "401311787", "401311788",
    "290850295", "300842026", "310842567", "400548956", "400786688", "400786689", "401027112", "401026678",
}
POSITIONS = {"PG", "SG", "SF", "PF", "C", "G", "F", "G-F", "F-G", "F-C", "C-F"}


def read_rows(path):
    with path.open(newline="", encoding="utf-8-sig") as file:
        yield from csv.DictReader(file)


def sweet_sixteen_games(folder, year):
    day = SWEET_SIXTEEN_START[year]
    dates = {f"{year}-03-{date:02d}" for date in (day, day + 1)}
    known = SWEET_SIXTEEN_GAMES.get(year)
    games = defaultdict(set)
    for row in read_rows(folder / f"player_box_{year}.csv"):
        if row["season_type"] != "3" or row["game_date"] not in dates:
            continue
        if row["game_id"] in NON_NCAA_GAMES:
            continue
        if known is None or row["game_id"] in known:
            games[row["game_id"]].add(row["team_id"])
    if len(games) != 8 or any(len(teams) != 2 for teams in games.values()):
        raise ValueError(f"Expected eight two-team Sweet 16 games for {year}; found {dict(games)}")
    return games


def postseason_teams(folder, year, league):
    if league == "NBA":
        rows = read_rows(folder / f"player_boxscores_{year}.csv")
        teams = {row["team_id"] for row in rows if row["season_type_id"] == "4"}
    else:
        teams = set().union(*sweet_sixteen_games(folder, year).values())
    if len(teams) != 16:
        raise ValueError(f"Expected 16 teams for {league} {year}, found {len(teams)}")
    return teams


def height_inches(value):
    value = value.strip()
    feet_inches = re.fullmatch(r"(\d)'\s*(\d{1,2})\"", value)
    if feet_inches:
        feet, inches = map(int, feet_inches.groups())
        return 12 * feet + inches if inches < 12 else ""
    if re.fullmatch(r"\d{2}(\.0+)?", value):
        return int(float(value))
    return ""


def name_key(name):
    normalized = unicodedata.normalize("NFKD", name.casefold())
    return "".join(char for char in normalized if char.isalnum())


def nba_bios(folder, year):
    by_name = defaultdict(list)
    for bio in read_rows(folder / f"nba_core_{year}.csv"):
        by_name[name_key(bio["full_name"])].append(bio)
    return by_name


def match_nba_bio(row, by_name, by_id):
    identity = by_id.get(row["player_id"], {})
    canonical_name = f'{identity.get("firstName", "")} {identity.get("lastName", "")}'
    candidates = by_name.get(name_key(canonical_name or row["player"]), [])
    if not candidates:
        candidates = by_name.get(name_key(row["player"]), [])
    birth_date = identity.get("birthDate")
    if birth_date:
        candidates = [bio for bio in candidates if bio["date_of_birth"][:10] == birth_date[:10]]
    if len(candidates) == 1 and candidates[0]["position_abbreviation"] in POSITIONS:
        return candidates[0], "ESPN NBA player core"

    positions = "-".join(code for field, code in (("guard", "G"), ("forward", "F"), ("center", "C"))
                         if identity.get(field) == "1")
    return {"position_abbreviation": positions, "height": identity.get("heightInches", "")}, "NBA player directory"


def match(folder, totals_path, output, all_teams=False):
    totals = list(read_rows(totals_path))
    season_leagues = {(int(row["season"]), row["league"]) for row in totals}
    fields = {(year, league): postseason_teams(folder, year, league)
              for year, league in sorted(season_leagues)}
    college_bios = {}
    team_bios = {}
    nba_by_name = {}
    nba_by_id = {row["personId"]: row for row in read_rows(folder / "nba_players.csv")}
    forward_heights = {}
    for year, league in sorted(season_leagues):
        if league == "NCAA":
            season_file = folder / f"rosters_{year}.csv"
            if season_file.exists():
                bios = list(read_rows(season_file))
                team_bios[year] = {(row["team_id"], row["athlete_id"]): row for row in bios}
            else:
                bios = list(read_rows(folder / f"player_core_{year}.csv"))
                college_bios[year] = {row["athlete_id"]: row for row in bios}
        else:
            nba_by_name[year] = nba_bios(folder, year)
            bios = [bio for group in nba_by_name[year].values() for bio in group]
        heights = {bio["athlete_id"]: height_inches(bio["height"]) for bio in bios
                   if bio["position_abbreviation"] == "F" and height_inches(bio["height"])}
        forward_heights[year, league] = median(heights.values()) if heights else None

    records = []
    for row in totals:
        year, league = int(row["season"]), row["league"]
        if not all_teams and row["team_id"] not in fields[year, league]:
            continue
        if league == "NCAA" and year in team_bios:
            bio = team_bios[year].get((row["team_id"], row["player_id"]), {})
            source = f"ESPN team roster ({year})"
        elif league == "NCAA":
            bio = college_bios[year].get(row["player_id"], {})
            source = f"ESPN player core ({year})"
        else:
            bio, source = match_nba_bio(row, nba_by_name[year], nba_by_id)
            if not row["player"].strip():
                identity = nba_by_id.get(row["player_id"], {})
                name = f'{identity.get("firstName", "")} {identity.get("lastName", "")}'.strip()
                row["player"] = name or f'Unnamed player ({row["player_id"]})'
        position = bio.get("position_abbreviation", "").strip()
        if position not in POSITIONS and league == "NCAA":
            position = row["source_position"]
            source = "Game box scores"
        height = height_inches(bio.get("height", ""))
        row.update(listed_position=position if position in POSITIONS else "",
                   position_source=source if position in POSITIONS else "",
                   height_inches=height)
        group, method = position, "listed"
        if position not in POSITIONS:
            group, method = "", "unknown"
        elif position == "F" and height and forward_heights[year, league]:
            midpoint = forward_heights[year, league]
            if height > midpoint:
                group, method = "Big", "height inference"
            elif height < midpoint:
                group, method = "Wing", "height inference"
        row.update(analysis_position=group, position_method=method)
        records.append(row)
    covered = {(int(row["season"]), row["league"], row["team_id"]) for row in records}
    expected = {(year, league, team) for (year, league), teams in fields.items() for team in teams}
    if not expected <= covered:
        raise ValueError(f"Teams without player totals: {sorted(expected - covered)}")
    with output.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=list(records[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(records)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input_dir", type=Path)
    parser.add_argument("totals_csv", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--all-teams", action="store_true", help="Include the benchmark population")
    args = parser.parse_args()
    match(args.input_dir, args.totals_csv, args.output, args.all_teams)


if __name__ == "__main__":
    main()
