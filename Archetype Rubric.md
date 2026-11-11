# NBA and NCAA men's basketball archetype rubric

## Pilot scope

Use one rubric for NBA playoff teams and NCAA Division I men's Sweet 16 teams from 2006–07 through 2025–26. Compare champions with the other teams in each field. Exclude the canceled 2020 NCAA tournament. Use only information available before the playoffs or NCAA tournament. Start with an early and a recent season before expanding.

## Shared player roles

- **Creation** — Primary facilitator, secondary facilitator, driving scorer, and shot creator.
- **Off-ball offense** — Spot-up shooter, movement shooter, cutter, and transition finisher.
- **Frontcourt offense** — Stretch big, roll finisher, post scorer, and passing big.
- **Defense and rebounding** — Perimeter stopper, help defender, rim protector, and rebound specialist.
- **Combined roles** — 3-and-D, two-way creator, and floor-spacing rim protector. Require independent evidence for each component.

Power forwards and centers qualify for the stretch-big role. Use roster positions and height to resolve frontcourt eligibility where possible, and flag ambiguity. Track centers separately as potential stretch fives. Measure both attempt rate and accuracy, with a minimum attempt sample before interpreting accuracy.

## How AI assigns roles

Give the AI the player's listed position and standardized stat profile. Withhold the player's name, team identity, seed, and postseason outcome. Assign every rostered player one primary role, with supporting evidence and a confidence rating. Choose the role with the strongest available evidence. For sparse or zero-minute records, assign a provisional role from roster position and any available stats, mark it very low confidence, and disclose when it is position-only. Keep those assignments visible and report how sensitive team comparisons are to them.

## Position-adjusted tag thresholds

Compare each player with players at the same position in the same league and season, using the full league or Division I as the reference pool. Use point guard, shooting guard, small forward, power forward, and center when available. For ambiguous positions, use the supported broader guard, wing, or big group and flag the fallback. Keep raw totals and rates alongside percentiles. Fifteen assists in 150 minutes could rank highly for a center and near the middle for a point guard. The comparison uses rate and sample size together.

Use the same threshold rules in both leagues. These are proposed pilot thresholds. Verify coverage and freeze the final thresholds before testing associations with postseason outcomes.

- **Facilitation** — At least 150 minutes and 15 assists, plus an assist rate per 40 minutes at or above the 80th percentile for the player's position. Center or power forward eligibility supports the passing-big tag. Primary facilitator also requires evidence of a lead share of the team's assists.
- **Stretch big** — Listed power forward or center, at least 150 minutes and 40 three-point attempts, at or above the positional 75th percentile for attempts per 40 minutes and the positional median for accuracy among qualifying shooters. Track eligible centers as stretch fives.
- **Shot blocker or rebound specialist** — At least 150 minutes and the positional 80th percentile for blocks or rebounds per 40 minutes, respectively. Shot-blocking can support a provisional rim-protection role.
- **Driver or 3-and-D** — Use direct statistical evidence where available, such as tracked drives or perimeter matchup data alongside qualifying shooting. Use broader scoring or shooting roles when only box-score proxies are available. Leave specific secondary tags unassigned when the relevant measurements are missing.

Primary roles remain mandatory when no secondary threshold is met. AI selects the primary role and explains it. Compute secondary tag eligibility from the stats so the same player profile consistently unlocks the same tags.

## Pilot review

Show the available fields, example AI assignments, borderline cases, and each sample team's share of regular-season minutes by role. Report the share of player minutes assigned with low or very low confidence. For overlapping tags, report each tag's minutes separately. Review shooting bigs, facilitators, drivers, and 3-and-D players before applying the rubric to the full study.
