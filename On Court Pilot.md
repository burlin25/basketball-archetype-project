# On-court plus-minus pilot

This audit uses the 2025–26 SportsDataverse releases for [NBA possessions](https://github.com/sportsdataverse/sportsdataverse-data/releases/tag/nba_stats_possessions), [NBA event lineups](https://github.com/sportsdataverse/sportsdataverse-data/releases/tag/nba_stats_game_lineups), [NBA play-by-play](https://github.com/sportsdataverse/sportsdataverse-data/releases/tag/nba_stats_pbp), [NCAA possessions](https://github.com/sportsdataverse/sportsdataverse-data/releases/tag/ncaa_mbb_possessions), and [NCAA matchup stints](https://github.com/sportsdataverse/sportsdataverse-data/releases/tag/ncaa_mbb_matchup_stints).

Use the 2026 CSV gzip files. Save the NBA play-by-play as `nba_pbp.gz` and NCAA possessions as `ncaa_poss.gz`. Keep the other release filenames. Run `python3 audit_on_court.py LINEUP_FOLDER BOX_SCORE_FOLDER on_court_coverage.csv`. The box-score folder uses the inputs documented in [Pilot Data](Pilot%20Data.md).

The NBA clock check uses successive play-by-play clock readings and the ten-player lineup published for the earlier event. It compares reconstructed individual seconds with box-score minutes. NCAA duration coverage uses the published stint durations in the audited ESPN game-ID window, which covers 27 late-round games. Expected game length uses the box-score minute total to infer overtime. Individual NCAA player minutes remain unaudited.

Chart readiness requires reconciling game scores, game-clock coverage and individual player minutes, plus verifying player IDs against the archetype dataset. Count each archetype once per team on a given possession or clock interval, even when two players share it.
