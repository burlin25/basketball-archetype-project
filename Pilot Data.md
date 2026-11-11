# Pilot player data

The four input CSVs come from SportsDataverse. Download the 2007 and 2026 files from each release into one local folder.

- [NBA Stats player box scores](https://github.com/sportsdataverse/sportsdataverse-data/releases/tag/nba_stats_player_boxscores), files `player_boxscores_2007.csv` and `player_boxscores_2026.csv`.
- [ESPN men's college player box scores](https://github.com/sportsdataverse/sportsdataverse-data/releases/tag/espn_mens_college_basketball_player_boxscores), files `player_box_2007.csv` and `player_box_2026.csv`.

Run `python3 build_pilot_totals.py INPUT_FOLDER OUTPUT.csv`. The output has one row per team and player, so a traded NBA player's minutes stay with the team they played for. NBA inputs are restricted to regular-season games. College inputs include games before the first NCAA tournament game, including conference tournaments. Season labels use the calendar year in which the season ended.

The aggregation ran successfully on all four files. It produced 492 NBA and 6,542 college team-player records in 2007 and 673 NBA and 12,502 college records in 2026. College feeds also include teams outside Division I. These raw counts precede the Division I and postseason-field filters.

Joakim Noah's Florida record now has 842 minutes across 33 pre-tournament games, with 77 assists and 57 blocks. Tim Duncan's 190 blocks and Karl-Anthony Towns's 113 made threes on 307 attempts matched the earlier source checks. The box-score position field is incomplete and often broad. The next step is to match the postseason fields and attach roster positions before calculating positional benchmarks. Box scores alone also cannot verify players who never appeared on a game sheet or who departed before the postseason.
