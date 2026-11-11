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
POSITIONS = {"PG", "SG", "SF", "PF", "C", "G", "F", "G-F", "F-G", "F-C", "C-F"}


def read_rows(path):
    with path.open(newline="", encoding="utf-8-sig") as file:
        yield from csv.DictReader(file)


def postseason_teams(folder, year, league):
    if league == "NBA":
        rows = read_rows(folder / f"player_boxscores_{year}.csv")
        teams = {row["team_id"] for row in rows if row["season_type_id"] == "4"}
    else:
        rows = read_rows(folder / f"player_box_{year}.csv")
        games = {game: set() for game in SWEET_SIXTEEN_GAMES[year]}
        for row in rows:
            if row["game_id"] in games and row["season_type"] == "3":
                games[row["game_id"]].add(row["team_id"])
        if any(len(teams) != 2 for teams in games.values()):
            raise ValueError(f"Incomplete Sweet 16 games for {year}")
        teams = set.union(*games.values())
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


def match(folder, totals_path, output):
    fields = {(year, league): postseason_teams(folder, year, league)
              for year in SWEET_SIXTEEN_GAMES for league in ("NBA", "NCAA")}
    old_bios = {row["athlete_id"]: row for row in read_rows(folder / "player_core_2007.csv")}
    recent_bios = {(row["team_id"], row["athlete_id"]): row
                   for row in read_rows(folder / "rosters_2026.csv")}
    nba_by_name = {year: nba_bios(folder, year) for year in SWEET_SIXTEEN_GAMES}
    nba_by_id = {row["personId"]: row for row in read_rows(folder / "nba_players.csv")}
    forward_heights = {}
    for year, bios in ((2007, old_bios.values()), (2026, recent_bios.values())):
        heights = {bio["athlete_id"]: height_inches(bio["height"]) for bio in bios
                   if bio["position_abbreviation"] == "F" and height_inches(bio["height"])}
        forward_heights[year, "NCAA"] = median(heights.values()) if heights else None
        nba_heights = [height_inches(bio["height"]) for group in nba_by_name[year].values()
                       for bio in group if bio["position_abbreviation"] == "F"]
        nba_heights = [height for height in nba_heights if height]
        forward_heights[year, "NBA"] = median(nba_heights) if nba_heights else None

    records = []
    for row in read_rows(totals_path):
        year, league = int(row["season"]), row["league"]
        if row["team_id"] not in fields[year, league]:
            continue
        bio, source = {}, ""
        if league == "NCAA" and year == 2007:
            bio = old_bios.get(row["player_id"], {})
            source = "ESPN player core (2007)"
        elif league == "NCAA":
            bio = recent_bios.get((row["team_id"], row["player_id"]), {})
            source = "ESPN team roster (2026)"
        else:
            bio, source = match_nba_bio(row, nba_by_name[year], nba_by_id)
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
    if covered != expected:
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
    args = parser.parse_args()
    match(args.input_dir, args.totals_csv, args.output)


if __name__ == "__main__":
    main()
