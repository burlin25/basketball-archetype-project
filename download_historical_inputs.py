"""Download the public season CSVs used by the historical study."""

import argparse
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from urllib.request import urlretrieve

from build_pilot_totals import FIRST_NCAA_TOURNAMENT_GAME

RELEASES = "https://github.com/sportsdataverse/sportsdataverse-data/releases/download"
NBA_DIRECTORY = (
    "https://www.kaggle.com/api/v1/datasets/download/"
    "eoinamoore/historical-nba-data-and-player-box-scores/Players.csv"
)


def downloads():
    for year in range(2007, 2027):
        yield (f"{RELEASES}/nba_stats_player_boxscores/player_boxscores_{year}.csv",
               f"player_boxscores_{year}.csv")
        yield (f"{RELEASES}/espn_nba_player_core/player_core_{year}.csv", f"nba_core_{year}.csv")
        if year in FIRST_NCAA_TOURNAMENT_GAME:
            yield (f"{RELEASES}/espn_mens_college_basketball_player_boxscores/player_box_{year}.csv",
                   f"player_box_{year}.csv")
            yield (f"{RELEASES}/espn_mens_college_basketball_player_core/player_core_{year}.csv",
                   f"player_core_{year}.csv")
    yield (f"{RELEASES}/espn_mens_college_basketball_rosters/rosters_2026.csv", "rosters_2026.csv")
    yield NBA_DIRECTORY, "nba_players.csv"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input_dir", type=Path)
    args = parser.parse_args()
    args.input_dir.mkdir(parents=True, exist_ok=True)

    def download(item):
        url, name = item
        path = args.input_dir / name
        if not path.exists():
            temporary = path.with_suffix(".part")
            urlretrieve(url, temporary)
            temporary.replace(path)

    with ThreadPoolExecutor(max_workers=8) as pool:
        list(pool.map(download, downloads()))


if __name__ == "__main__":
    main()
