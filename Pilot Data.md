# Pilot player data

The four input CSVs come from SportsDataverse. Download the 2007 and 2026 files from each release into one local folder.

- [NBA Stats player box scores](https://github.com/sportsdataverse/sportsdataverse-data/releases/tag/nba_stats_player_boxscores), files `player_boxscores_2007.csv` and `player_boxscores_2026.csv`.
- [ESPN men's college player box scores](https://github.com/sportsdataverse/sportsdataverse-data/releases/tag/espn_mens_college_basketball_player_boxscores), files `player_box_2007.csv` and `player_box_2026.csv`.

Run `python3 build_pilot_totals.py INPUT_FOLDER OUTPUT.csv`. The output has one row per team and player, so a traded NBA player's minutes stay with the team they played for. NBA inputs are restricted to regular-season games. College inputs include games before the first NCAA tournament game, including conference tournaments. Season labels use the calendar year in which the season ended.

The aggregation ran successfully on all four files. It produced 492 NBA and 6,542 college team-player records in 2007 and 673 NBA and 12,502 college records in 2026. College feeds also include teams outside Division I. These raw counts precede the Division I and postseason-field filters.

Joakim Noah's Florida record now has 842 minutes across 33 pre-tournament games, with 77 assists and 57 blocks. Tim Duncan's 190 blocks and Karl-Anthony Towns's 113 made threes on 307 attempts matched the earlier source checks. The box-score position field is incomplete and often broad. The next step is to match the postseason fields and attach roster positions before calculating positional benchmarks. Box scores alone also cannot verify players who never appeared on a game sheet or who departed before the postseason.

## Postseason team and position match

Download `player_core_2007.csv` from the [ESPN player core release](https://github.com/sportsdataverse/sportsdataverse-data/releases/tag/espn_mens_college_basketball_player_core) and `rosters_2026.csv` from the [ESPN team roster release](https://github.com/sportsdataverse/sportsdataverse-data/releases/tag/espn_mens_college_basketball_rosters) into the same folder. Then run `python3 match_pilot_rosters.py INPUT_FOLDER TOTALS.csv pilot_rosters.csv`.

NBA membership comes from playoff box scores. NCAA membership comes from the eight regional semifinal game IDs per season. The match covers all 64 team-seasons and 1,060 team-player records with pre-postseason game-sheet evidence. It does not certify the postseason roster date or add players absent from the pre-postseason game sheets. The 2007 college bio is joined by player ID, while the 2026 college roster is joined by team and player ID.

For a generic college forward with a listed height, the pilot infers Big above the median of listed forwards in the season's source archive and Wing below it. A tie keeps the broad Forward listing. The archive can include schools outside Division I, so this is a provisional cutoff. Explicit positions and hybrid listings are retained. The output has 126 height-based inferences and 585 unknown positions, all in the NBA. NBA box-score positions are retained as raw evidence but excluded from the analysis position after spot checks found obvious errors, including Dirk Nowitzki listed as a guard. NBA height and position are pending a reliable roster source. This output is a roster match, before calculating position-adjusted tag thresholds or assigning archetypes.
