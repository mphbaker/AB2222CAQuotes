#!/usr/bin/env python3

"""
AB 2222 deduplicated statement extraction.

Starts from the sentence-level context-relevant corpus and returns
one row per original transcript statement.

Multiple matching sentences within the same statement are collapsed
into a single row, while all matched keyword groups and terms are
retained.

Input:
    data/extracted/ab2222_context_relevant_sentences.csv

Outputs:
    data/extracted/ab2222_context_relevant_statements.csv
    data/extracted/ab2222_legislator_context_statements.csv
"""

import pandas as pd


INPUT = "data/extracted/ab2222_context_relevant_sentences.csv"

OUTPUT_ALL = (
    "data/extracted/ab2222_context_relevant_statements.csv"
)

OUTPUT_LEGISLATORS = (
    "data/extracted/ab2222_legislator_context_statements.csv"
)


# ------------------------------------------------------------
# LOAD
# ------------------------------------------------------------

print("=" * 80)
print("AB 2222 DEDUPLICATED STATEMENT EXTRACTION")
print("=" * 80)

df = pd.read_csv(INPUT)

print(f"\nInput keyword-relevant sentences: {len(df):,}")


# ------------------------------------------------------------
# HELPER FUNCTIONS
# ------------------------------------------------------------

def split_values(value):

    if pd.isna(value):
        return []

    return [
        x.strip()
        for x in str(value).split(";")
        if x.strip()
    ]


def unique_values(series):

    values = []

    for value in series:

        for item in split_values(value):

            if item not in values:
                values.append(item)

    return values


# ------------------------------------------------------------
# IDENTIFY THE ORIGINAL STATEMENT
# ------------------------------------------------------------

# The same statement can contain several matching sentences.
# We therefore group using the hearing + statement index.

GROUP_COLS = [
    "hearing_id",
    "statement_index"
]


# ------------------------------------------------------------
# COLLAPSE TO ONE ROW PER STATEMENT
# ------------------------------------------------------------

rows = []

for group_key, group in df.groupby(
    GROUP_COLS,
    sort=False,
    dropna=False
):

    first = group.iloc[0]

    row = {}

    # --------------------------------------------------------
    # Core transcript identifiers
    # --------------------------------------------------------

    row["hearing_id"] = first["hearing_id"]
    row["statement_index"] = first["statement_index"]

    if "dom_id" in group.columns:
        row["dom_id"] = first["dom_id"]

    row["speaker"] = first["speaker"]
    row["speaker_type"] = first["speaker_type"]

    # --------------------------------------------------------
    # Full original statement
    # --------------------------------------------------------

    row["statement"] = first["statement"]

    # --------------------------------------------------------
    # Keyword groups
    # --------------------------------------------------------

    groups = unique_values(
        group["matched_groups"]
    )

    terms = unique_values(
        group["matched_terms"]
    )

    row["matched_groups"] = "; ".join(groups)
    row["matched_terms"] = "; ".join(terms)

    row["n_keyword_groups"] = len(groups)

    # --------------------------------------------------------
    # Matching sentences
    # --------------------------------------------------------

    sentence_indices = []

    for value in group["sentence_index"]:

        if pd.notna(value):

            try:
                sentence_indices.append(int(value))
            except (ValueError, TypeError):
                pass

    sentence_indices = sorted(set(sentence_indices))

    row["matching_sentence_indices"] = "; ".join(
        str(x) for x in sentence_indices
    )

    row["n_matching_sentences"] = len(
        sentence_indices
    )

    # --------------------------------------------------------
    # Matching sentence text
    #
    # This preserves the exact sentences that triggered
    # retrieval, while "statement" contains the full quote.
    # --------------------------------------------------------

    matching_sentences = []

    for _, sentence_row in group.iterrows():

        sentence = str(
            sentence_row.get("sentence", "")
        ).strip()

        if sentence and sentence not in matching_sentences:

            matching_sentences.append(sentence)

    row["matching_sentences"] = " ".join(
        matching_sentences
    )

    rows.append(row)


statements_df = pd.DataFrame(rows)


# ------------------------------------------------------------
# SORT
# ------------------------------------------------------------

statements_df = statements_df.sort_values(
    by=[
        "hearing_id",
        "statement_index"
    ]
).reset_index(drop=True)


# ------------------------------------------------------------
# SAVE ALL SPEAKERS
# ------------------------------------------------------------

statements_df.to_csv(
    OUTPUT_ALL,
    index=False,
    encoding="utf-8"
)


# ------------------------------------------------------------
# LEGISLATORS ONLY
# ------------------------------------------------------------

legislator_df = statements_df[
    statements_df["speaker_type"]
    .astype(str)
    .str.lower()
    .eq("legislator")
].copy()

legislator_df.to_csv(
    OUTPUT_LEGISLATORS,
    index=False,
    encoding="utf-8"
)


# ------------------------------------------------------------
# RESULTS
# ------------------------------------------------------------

print("\n" + "=" * 80)
print("RESULTS")
print("=" * 80)

print(
    f"\nInput keyword-relevant sentences: "
    f"{len(df):,}"
)

print(
    f"Unique transcript statements:       "
    f"{len(statements_df):,}"
)

print(
    f"Legislator statements:              "
    f"{len(legislator_df):,}"
)


# ------------------------------------------------------------
# MATCHING STATEMENTS BY HEARING
# ------------------------------------------------------------

print("\n" + "=" * 80)
print("STATEMENTS BY HEARING")
print("-" * 80)

hearing_counts = (
    statements_df
    .groupby("hearing_id")
    .size()
    .sort_values(ascending=False)
)

for hearing_id, count in hearing_counts.items():

    print(
        f"{str(hearing_id):<20} "
        f"{count:>6}"
    )


# ------------------------------------------------------------
# MATCHING STATEMENTS BY LEGISLATOR
# ------------------------------------------------------------

print("\n" + "=" * 80)
print("LEGISLATOR STATEMENTS")
print("-" * 80)

legislator_counts = (
    legislator_df
    .groupby("speaker")
    .size()
    .sort_values(ascending=False)
)

for speaker, count in legislator_counts.items():

    print(
        f"{str(speaker):<35} "
        f"{count:>6}"
    )


# ------------------------------------------------------------
# MULTIPLE MATCHING SENTENCES
# ------------------------------------------------------------

print("\n" + "=" * 80)
print("STATEMENTS WITH MULTIPLE MATCHING SENTENCES")
print("-" * 80)

multi = statements_df[
    statements_df["n_matching_sentences"] > 1
]

print(
    f"\nStatements containing multiple "
    f"matching sentences: {len(multi):,}"
)


# ------------------------------------------------------------
# SAVE SUMMARY
# ------------------------------------------------------------

print("\n" + "=" * 80)
print("SAVED")
print("-" * 80)

print(OUTPUT_ALL)
print(OUTPUT_LEGISLATORS)

print("\nDone.")
print("=" * 80)
