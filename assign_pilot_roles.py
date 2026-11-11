"""Apply the shared, stats-based pilot rubric to pre-postseason player profiles."""

import argparse
import csv
from bisect import bisect_left, bisect_right
from collections import defaultdict
from pathlib import Path

from match_pilot_rosters import read_rows

MIN_MINUTES = 150
MIN_PEERS = 20
BIGS = {"PF", "C", "F-C", "C-F", "Big"}
POSITION_FAMILY = {
    "PG": "Guard", "SG": "Guard", "G": "Guard",
    "SF": "Wing", "Wing": "Wing", "G-F": "Wing", "F-G": "Wing",
    "F": "Forward", **dict.fromkeys(BIGS, "Big"),
}
METRICS = ("assists", "threes_attempted", "three_accuracy", "blocks", "rebounds", "points")


def metrics(row):
    minutes = float(row["minutes"])
    values = {key: 40 * int(row[key]) / minutes if minutes else 0.0
              for key in METRICS if key != "three_accuracy"}
    attempts = int(row["threes_attempted"])
    values["three_accuracy"] = int(row["threes_made"]) / attempts if attempts >= 40 else None
    return values


def cohorts(reference):
    pools = defaultdict(list)
    for row in reference:
        if float(row["minutes"]) < MIN_MINUTES:
            continue
        prefix = (row["league"], row["season"])
        position = row["analysis_position"]
        family = POSITION_FAMILY.get(position)
        groups = {("all", "")}
        if position:
            groups.update({("position", position), ("family", family or position)})
        for metric, value in metrics(row).items():
            if value is not None:
                for level, group in groups:
                    pools[(*prefix, level, group, metric)].append(value)
    for values in pools.values():
        values.sort()
    return pools


def benchmarks(row, pools):
    position = row["analysis_position"]
    result = {}
    for metric, value in metrics(row).items():
        if value is None:
            result[metric] = (None, "missing")
            continue
        for level, group in (("position", position), ("family", POSITION_FAMILY.get(position, position)),
                             ("all", "")):
            peers = pools.get((row["league"], row["season"], level, group, metric), [])
            if len(peers) >= MIN_PEERS:
                rank = (bisect_left(peers, value) + bisect_right(peers, value)) / (2 * len(peers))
                result[metric] = (rank, level)
                break
        else:
            result[metric] = (None, "missing")
    return result


def classify(row, ranks, team_assists):
    minutes = float(row["minutes"])
    big = row["analysis_position"] in BIGS
    tags = []
    signals = []

    def rank(metric):
        value, _ = ranks[metric]
        return value if value is not None else 0

    def qualifies(metric, threshold):
        return ranks[metric][1] in {"position", "family"} and rank(metric) >= threshold

    if minutes >= MIN_MINUTES:
        if int(row["assists"]) >= 15 and qualifies("assists", 0.80):
            lead = int(row["assists"]) >= 0.20 * team_assists
            role = "Passing big" if big else "Primary facilitator" if lead else "Secondary facilitator"
            tags.append(role)
            signals.append((rank("assists"), role, "assists"))
        if qualifies("threes_attempted", 0.75) and qualifies("three_accuracy", 0.50):
            role = "Stretch big" if big else "High-volume shooter"
            tags.append(role)
            signals.append((rank("threes_attempted"), role, "threes_attempted"))
            if row["listed_position"] == "C" and row["position_source"] != "NBA player directory":
                tags.append("Stretch five")
        for metric, role in (("blocks", "Shot blocker"), ("rebounds", "Rebound specialist")):
            if qualifies(metric, 0.80):
                tags.append(role)
                signals.append((rank(metric), role, metric))

    if not signals:
        for metric, role in (("points", "Scorer"), ("assists", "Facilitator"),
                             ("threes_attempted", "Perimeter shooter"),
                             ("rebounds", "Rebounder"), ("blocks", "Shot blocker")):
            if int(row[metric]) > 0:
                signals.append((rank(metric), role, metric))

    if signals:
        strength, primary, evidence = max(signals, key=lambda signal: signal[0])
        confidence = "low" if minutes < MIN_MINUTES else "medium"
        if (minutes >= 300 and strength >= 0.85 and primary in tags and
                ranks[evidence][1] == "position" and row["position_method"] == "listed"):
            confidence = "high"
        explanation = f"{metrics(row)[evidence]:.2f} {evidence} per 40 minutes"
    else:
        primary = "Interior player" if big else "Perimeter player" if row["analysis_position"] else "Reserve"
        confidence = "very low"
        explanation = "Roster position or reserve status only"

    return primary, "; ".join(tag for tag in tags if tag != primary), primary in tags, confidence, explanation


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("players", type=Path)
    parser.add_argument("reference", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    pools = cohorts(read_rows(args.reference))
    players = list(read_rows(args.players))
    team_assists = defaultdict(int)
    for row in players:
        team_assists[row["league"], row["season"], row["team_id"]] += int(row["assists"])
    with args.output.open("w", newline="", encoding="utf-8") as file:
        fields = (*players[0], "primary_role", "secondary_tags", "primary_met_threshold", "confidence", "role_evidence",
                  *(f"{metric}_{suffix}" for metric in METRICS for suffix in ("percentile", "cohort")))
        writer = csv.DictWriter(file, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        for row in players:
            ranks = benchmarks(row, pools)
            role, tags, qualified, confidence, evidence = classify(
                row, ranks, team_assists[row["league"], row["season"], row["team_id"]])
            row.update(primary_role=role, secondary_tags=tags, primary_met_threshold=qualified,
                       confidence=confidence,
                       role_evidence=evidence)
            for metric, (rank, cohort) in ranks.items():
                row[f"{metric}_percentile"] = "" if rank is None else round(100 * rank, 2)
                row[f"{metric}_cohort"] = cohort
            writer.writerow(row)


if __name__ == "__main__":
    main()
