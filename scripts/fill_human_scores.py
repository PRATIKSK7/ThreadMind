#!/usr/bin/env python3
"""Fill human scores into human_scoring_subset.csv without altering other columns."""
import csv

SCORES = {
    "GS-163": (3, 5, 3, 5),
    "GS-028": (2, 2, 3, 5),
    "GS-006": (4, 5, 3, 5),
    "GS-189": (5, 5, 5, 5),
    "GS-070": (3, 5, 3, 5),
    "GS-062": (3, 5, 2, 5),
    "GS-057": (5, 5, 5, 5),
    "GS-035": (4, 5, 4, 5),
    "GS-026": (3, 5, 4, 5),
    "GS-173": (3, 5, 2, 5),
    "GS-139": (2, 5, 2, 5),
    "GS-022": (4, 5, 4, 5),
    "GS-151": (4, 5, 4, 5),
    "GS-108": (3, 5, 2, 5),
    "GS-008": (5, 5, 5, 5),
    "GS-007": (4, 5, 4, 5),
    "GS-023": (5, 5, 5, 5),
    "GS-055": (4, 5, 4, 5),
    "GS-059": (5, 5, 5, 5),
    "GS-129": (5, 5, 5, 5),
    "GS-154": (4, 5, 4, 5),
    "GS-193": (2, 4, 2, 5),
    "GS-143": (4, 5, 3, 5),
    "GS-050": (3, 5, 3, 5),
    "GS-166": (4, 5, 4, 5),
    "GS-185": (5, 5, 4, 5),
    "GS-107": (2, 2, 2, 4),
    "GS-056": (3, 2, 4, 5),
    "GS-114": (5, 5, 5, 5),
    "GS-150": (4, 5, 4, 5),
}

csv_path = "reports/human_scoring_subset.csv"

# Read existing rows
with open(csv_path, "r") as f:
    reader = csv.DictReader(f)
    fieldnames = reader.fieldnames
    rows = list(reader)

# Fill in human scores
for row in rows:
    eid = row["example_id"]
    if eid in SCORES:
        c, g, h, t = SCORES[eid]
        row["human_correctness_1_to_5"] = str(c)
        row["human_groundedness_1_to_5"] = str(g)
        row["human_helpfulness_1_to_5"] = str(h)
        row["human_tone_1_to_5"] = str(t)

# Write back preserving all columns
with open(csv_path, "w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(rows)

print(f"Wrote human scores for {len(SCORES)} examples to {csv_path}")

# Validate
with open(csv_path, "r") as f:
    reader = csv.DictReader(f)
    validated = list(reader)

dims = ["human_correctness_1_to_5", "human_groundedness_1_to_5",
        "human_helpfulness_1_to_5", "human_tone_1_to_5"]
errors = 0
for row in validated:
    for d in dims:
        v = int(row[d])
        if v < 1 or v > 5:
            print(f"ERROR: {row['example_id']} {d}={v}")
            errors += 1

if errors == 0:
    print("VALIDATION PASSED: All 30 rows have valid integer scores 1-5.")

print(f"\n{'ID':<8} {'H_C':>4} {'H_G':>4} {'H_H':>4} {'H_T':>4}")
print("-" * 28)
for row in validated:
    print(f"{row['example_id']:<8} {row['human_correctness_1_to_5']:>4} {row['human_groundedness_1_to_5']:>4} {row['human_helpfulness_1_to_5']:>4} {row['human_tone_1_to_5']:>4}")
