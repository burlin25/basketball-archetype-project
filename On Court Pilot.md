# On-court plus-minus pilot

This audit uses the 2025–26 SportsDataverse releases for [NBA possessions](https://github.com/sportsdataverse/sportsdataverse-data/releases/tag/nba_stats_possessions), [NBA event lineups](https://github.com/sportsdataverse/sportsdataverse-data/releases/tag/nba_stats_game_lineups), [NBA play-by-play](https://github.com/sportsdataverse/sportsdataverse-data/releases/tag/nba_stats_pbp), [NCAA possessions](https://github.com/sportsdataverse/sportsdataverse-data/releases/tag/ncaa_mbb_possessions), and [NCAA matchup stints](https://github.com/sportsdataverse/sportsdataverse-data/releases/tag/ncaa_mbb_matchup_stints).

Use the 2026 CSV gzip files. Save the NBA play-by-play as `nba_pbp.gz` and NCAA possessions as `ncaa_poss.gz`. Keep the other release filenames. Run `python3 audit_on_court.py LINEUP_FOLDER BOX_SCORE_FOLDER on_court_coverage.csv`. The box-score folder uses the inputs documented in [Pilot Data](Pilot%20Data.md).

The NBA clock check uses successive play-by-play clock readings and the ten-player lineup published for the earlier event. It compares reconstructed individual seconds with box-score minutes. NCAA duration coverage uses the published stint durations in the audited ESPN game-ID window, which covers 27 late-round games. Expected game length uses the box-score minute total to infer overtime. Individual NCAA player minutes remain unaudited.

Chart readiness requires reconciling game scores, game-clock coverage and individual player minutes, plus verifying player IDs against the archetype dataset. Count each archetype once per team on a given possession or clock interval, even when two players share it.

## Reconstructed lineups and role comparisons

For the NBA, reconstruct periods from substitutions and the event clock. Assign points to the lineup entering the clock reading when the score changes and count possession opportunities at the ending event. The reconstructed team scores and court clocks match the boxes. Individual player minutes agree to within 0.5 seconds. Official player plus-minus is an additional check. It matches exactly in 80 games, with individual discrepancies of one or two points in the other five. Those five games are included. Excluding them in a sensitivity check preserved the direction of all six NBA earned-role gaps shown in the chart.

For college, fill the interval between distinct event clocks with the next event's recorded lineup. Assign points from scoring events and count opportunities with the lineup supplied in the possession feed. Require full game-clock coverage, agreement between both feeds and the box scores on team scoring, and player time within 60 seconds of ESPN's whole-minute boxes. Some of those boxes differ from school scorebooks. Michigan's title game, for example, had a 75-second discrepancy against ESPN and is excluded.

The reconstruction audits the 85 NBA playoff games and the 67 games in the men's NCAA bracket. The college bracket is selected by the NCAA tournament ID in the [ESPN schedule release](https://github.com/sportsdataverse/sportsdataverse-data/releases/tag/espn_mens_college_basketball_schedules). The college event clocks come from the [NCAA play-by-play release](https://github.com/sportsdataverse/sportsdataverse-data/releases/tag/ncaa_mbb_pbp). College lineup players are matched to ESPN box-score IDs using the [player crosswalk](https://github.com/sportsdataverse/sportsdataverse-data/releases/tag/mbb_groups) and names on the game sheet.

In addition to the files above, save `mbb_schedule_2026.csv`, `ncaa_mbb_pbp_2026.csv.gz` and `mbb_player_aliases.csv` in the lineup folder. Run from the repository root:

```sh
python3 summarize_on_court.py LINEUP_FOLDER BOX_SCORE_FOLDER
python3 render_on_court.py on_court_role_comparison.csv on-court-archetypes.svg
```

- [Reconstruction audit](on_court_reconstruction_audit.csv) lists the results for every postseason game checked. [Team coverage](on_court_team_coverage.csv) shows how many games and minutes were included for each study team and how much player court time could not be linked to a pre-postseason archetype.
- [Team role results](on_court_team_roles.csv) report court minutes, share of validated court time, offensive and defensive possessions, points, and net rating. One player or several players of the same role on the floor count as a single role exposure. Minutes can overlap across different roles.
- [Champion comparisons](on_court_role_comparison.csv) include both main and earned role views, against the original 16-team field and the final eight. Each team needs at least 30 offensive and 30 defensive possessions for a role to enter that role's comparison. The baseline is the equal-weight average of the eligible contenders. Net rating is points scored per 100 offensive possessions minus points allowed per 100 defensive possessions.
- The chart reports observed lineup performance. Teammates, opponents, and which games passed validation can affect the results.
