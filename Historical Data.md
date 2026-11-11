# Historical expansion

The same pilot rubric now runs from 2006–07 through 2025–26. Each NBA field contains the 16 playoff teams, and each NCAA field contains the Sweet 16. The canceled 2020 NCAA tournament contributes no postseason field. NBA play-in games are excluded from both the regular-season inputs and the playoff field.

## Reproduce the results

Run these from the project folder using Python 3. The first step downloads roughly 1.8 GB of public source CSVs. Choose a local folder for the raw inputs and the two intermediate totals files.

```sh
python3 download_historical_inputs.py INPUT_FOLDER
python3 build_pilot_totals.py INPUT_FOLDER INPUT_FOLDER/totals.csv --historical
python3 match_pilot_rosters.py INPUT_FOLDER INPUT_FOLDER/totals.csv INPUT_FOLDER/rosters.csv
python3 match_pilot_rosters.py INPUT_FOLDER INPUT_FOLDER/totals.csv INPUT_FOLDER/reference.csv --all-teams
python3 assign_pilot_roles.py INPUT_FOLDER/rosters.csv INPUT_FOLDER/reference.csv historical_archetypes.csv
python3 analyze_pilot.py historical_archetypes.csv historical_team_rotations.csv
python3 build_postseason_outcomes.py historical_archetypes.csv INPUT_FOLDER historical_postseason_teams.csv
python3 compare_historical_roles.py historical_team_rotations.csv historical_postseason_teams.csv historical_role_comparison.csv
```

## Interpretation

- Archetypes use pre-postseason box scores. Older college seasons use the season player profile archive for roster details. Team-player rows represent pre-postseason game-sheet records and can include players who left a team during the season.
- The reference includes college teams outside Division I when the underlying feed includes them. Position estimates and coverage remain provisional. The role definitions and confidence rules are shared across leagues.
- The final eight are NBA conference semifinalists and NCAA regional semifinal winners. NCAA fields are assembled from postseason game sheets on the regional semifinal dates, excluding identified games from other tournaments. The builder checks for exactly eight matchups and 16 teams.
- The championship flag records the on-court winner. This includes Louisville in 2013, whose [NCAA title was later vacated](https://fs.ncaa.org/Docs/stats/m_final4/2021/MFFBook.pdf). The comparison shows descriptive differences in rotation shares and uses equal-weight contender averages.
