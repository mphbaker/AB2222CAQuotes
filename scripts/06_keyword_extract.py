#!/usr/bin/env python3

"""
AB 2222 sentence-level keyword/topic extraction.

Purpose:
    Find individual sentences in the AB 2222 transcript corpus
    that contain terms relating to:
      - the bill itself
      - local news / journalism
      - journalists / reporters
      - news organizations
      - decline of local news
      - civic effects
      - information effects
      - employment / workforce
      - tax credits
      - editorial independence
      - nonprofit / small outlets

Input:
    data/extracted/ab2222_all_statements.csv

Outputs:
    data/extracted/ab2222_all_sentences.csv
    data/extracted/ab2222_keyword_relevant_sentences.csv
    data/extracted/ab2222_legislator_keyword_sentences.csv
"""

import os
import re
import pandas as pd


# ---------------------------------------------------------------------
# PATHS
# ---------------------------------------------------------------------

INPUT_FILE = "data/extracted/ab2222_all_statements.csv"

OUTPUT_ALL = "data/extracted/ab2222_all_sentences.csv"
OUTPUT_RELEVANT = "data/extracted/ab2222_keyword_relevant_sentences.csv"
OUTPUT_LEGISLATORS = "data/extracted/ab2222_legislator_keyword_sentences.csv"


# ---------------------------------------------------------------------
# KEYWORD DICTIONARY
# ---------------------------------------------------------------------

KEYWORD_GROUPS = {

    "bill_reference": [
        r"\bab\s*2222\b",
        r"\ba\.?\s*b\.?\s*2222\b",
        r"\bav\s*2222\b",
        r"\bcommunity news act\b",
        r"\bcommunity newsroom employment\b",
        r"\bworkforce sustainability act\b",
        r"\bcommunity newsroom\b",
    ],

    "local_news": [
        r"\blocal news\b",
        r"\blocal journalism\b",
        r"\blocal reporting\b",
        r"\blocal reporter\b",
        r"\blocal reporters\b",
        r"\blocal journalist\b",
        r"\blocal journalists\b",
        r"\blocal newspaper\b",
        r"\blocal newspapers\b",
        r"\blocal media\b",
        r"\bcommunity news\b",
        r"\bcommunity journalism\b",
        r"\bcommunity reporting\b",
        r"\bcommunity newspaper\b",
        r"\bnews desert\b",
        r"\bnews deserts\b",
    ],

    "journalists_reporters": [
        r"\bjournalist\b",
        r"\bjournalists\b",
        r"\breporter\b",
        r"\breporters\b",
        r"\bnews reporter\b",
        r"\bnews reporters\b",
        r"\bjournalism\b",
    ],

    "news_organizations": [
        r"\bnewsroom\b",
        r"\bnewsrooms\b",
        r"\bnewspaper\b",
        r"\bnewspapers\b",
        r"\bnews organization\b",
        r"\bnews organizations\b",
        r"\bnews outlet\b",
        r"\bnews outlets\b",
        r"\bmedia outlet\b",
        r"\bmedia outlets\b",
        r"\bpress\b",
    ],

    "news_decline": [
        r"\bdecline of (?:local )?news\b",
        r"\bdecline in (?:local )?news\b",
        r"\bdecline of journalism\b",
        r"\bdecline in journalism\b",
        r"\bshrinking newspaper\b",
        r"\bshrinking newspapers\b",
        r"\bnewspaper (?:has )?closed\b",
        r"\bnewspapers (?:have )?closed\b",
        r"\bnewspaper closures?\b",
        r"\bnewsroom closures?\b",
        r"\bnews desert\b",
        r"\bnews deserts\b",
        r"\blost (?:our )?local newspaper\b",
        r"\blosing (?:our )?local newspaper\b",
        r"\blost (?:our )?local news\b",
        r"\blosing (?:our )?local news\b",
        r"\bnewsrooms? (?:are )?shrinking\b",
        r"\bjournalism (?:is )?disappearing\b",
        r"\bjournalists? (?:are )?disappearing\b",
    ],

    "civic_effects": [
        r"\bcivic engagement\b",
        r"\bcivic participation\b",
        r"\bvoter participation\b",
        r"\bvoter engagement\b",
        r"\bgovernment accountability\b",
        r"\baccountability\b",
        r"\bdemocracy\b",
        r"\bdemocratic participation\b",
        r"\bcivic life\b",
        r"\bcivic health\b",
        r"\bcivic institutions?\b",
        r"\bpublic accountability\b",
    ],

    "information_effects": [
        r"\breliable information\b",
        r"\btrusted information\b",
        r"\btrustworthy information\b",
        r"\blocal information\b",
        r"\bcommunity information\b",
        r"\bpublic information\b",
        r"\bfactual information\b",
        r"\bmisinformation\b",
        r"\bdisinformation\b",
        r"\bfalse information\b",
        r"\binformation gap\b",
        r"\binformation gaps\b",
        r"\binformed public\b",
        r"\binformed citizens?\b",
        r"\bsocial media\b",
        r"\bcivil discourse\b",
    ],

    "employment_workforce": [
        r"\bemployment\b",
        r"\bemploy\b",
        r"\bemploying\b",
        r"\bemployees\b",
        r"\bworker\b",
        r"\bworkers\b",
        r"\bworkforce\b",
        r"\bjobs?\b",
        r"\bhire\b",
        r"\bhiring\b",
        r"\bretain\b",
        r"\bretaining\b",
        r"\bretention\b",
        r"\bnew hires?\b",
        r"\bfull[- ]time\b",
        r"\bpart[- ]time\b",
        r"\bwages?\b",
        r"\bsalar(?:y|ies)\b",
    ],

    "tax_credit": [
        r"\btax credit\b",
        r"\btax credits\b",
        r"\brefundable tax credit\b",
        r"\brefundable credit\b",
        r"\bcredit for employers\b",
        r"\bcredit for employment\b",
        r"\bcredit amount\b",
        r"\bdollar amount\b",
        r"\bpercentage of wages?\b",
        r"\bwage percentage\b",
    ],

    "editorial_independence": [
        r"\beditorial independence\b",
        r"\beditorial standards?\b",
        r"\beditorial control\b",
        r"\beditorial discretion\b",
        r"\beditorial integrity\b",
        r"\bpolitical neutrality\b",
        r"\bpolitical influence\b",
        r"\bpolitical interference\b",
        r"\bguardrails?\b",
        r"\bindependent journalism\b",
        r"\bindependent news\b",
        r"\bindependent newsroom\b",
        r"\bindependent outlet\b",
        r"\bjournalistic independence\b",
    ],

    "nonprofit_small_outlets": [
        r"\bnonprofit\b",
        r"\bnon-profit\b",
        r"\bsmall outlet\b",
        r"\bsmall outlets\b",
        r"\bsmall newspaper\b",
        r"\bsmall newspapers\b",
        r"\bsmall newsroom\b",
        r"\bsmall newsrooms\b",
        r"\bindependent outlet\b",
        r"\bindependent outlets\b",
        r"\bindependent publisher\b",
        r"\bindependent publishers\b",
        r"\bcommunity[- ]based outlet\b",
        r"\bcommunity[- ]based outlets\b",
    ],
}


# ---------------------------------------------------------------------
# COMPILE REGEXES
# ---------------------------------------------------------------------

COMPILED_GROUPS = {
    group: [(pattern, re.compile(pattern, re.IGNORECASE))
            for pattern in patterns]
    for group, patterns in KEYWORD_GROUPS.items()
}


# ---------------------------------------------------------------------
# SENTENCE SPLITTER
# ---------------------------------------------------------------------

def split_sentences(text):
    """
    Lightweight transcript-oriented sentence splitter.

    Keeps punctuation attached to the sentence.
    Avoids splitting on common abbreviations.
    """

    if pd.isna(text):
        return []

    text = str(text).strip()

    if not text:
        return []

    # Normalize whitespace
    text = re.sub(r"\s+", " ", text)

    # Protect common abbreviations
    protected = {
        "Mr.": "MR___",
        "Mrs.": "MRS___",
        "Ms.": "MS___",
        "Dr.": "DR___",
        "Rep.": "REP___",
        "Sen.": "SEN___",
        "Gov.": "GOV___",
        "St.": "ST___",
        "No.": "NO___",
        "e.g.": "EG___",
        "i.e.": "IE___",
    }

    for original, replacement in protected.items():
        text = text.replace(original, replacement)

    # Split after sentence-ending punctuation.
    sentences = re.split(r"(?<=[.!?])\s+", text)

    restored = []

    for sentence in sentences:
        sentence = sentence.strip()

        if not sentence:
            continue

        for original, replacement in protected.items():
            sentence = sentence.replace(replacement, original)

        restored.append(sentence)

    return restored


# ---------------------------------------------------------------------
# KEYWORD MATCHING
# ---------------------------------------------------------------------

def find_keyword_matches(text):
    """
    Return:
        matched_groups
        matched_terms
    """

    matched_groups = []
    matched_terms = []

    if not text:
        return matched_groups, matched_terms

    for group, patterns in COMPILED_GROUPS.items():

        group_matched = False

        for original_pattern, regex in patterns:

            matches = regex.findall(text)

            if matches:
                group_matched = True

                for match in matches:

                    if isinstance(match, tuple):
                        match = " ".join(match)

                    matched_terms.append(str(match).strip())

        if group_matched:
            matched_groups.append(group)

    # Deduplicate while preserving order
    matched_groups = list(dict.fromkeys(matched_groups))
    matched_terms = list(dict.fromkeys(matched_terms))

    return matched_groups, matched_terms


# ---------------------------------------------------------------------
# LOAD DATA
# ---------------------------------------------------------------------

print("=" * 80)
print("AB 2222 SENTENCE-LEVEL KEYWORD / TOPIC EXTRACTION")
print("=" * 80)

if not os.path.exists(INPUT_FILE):
    raise FileNotFoundError(
        f"Input file not found:\n{INPUT_FILE}\n\n"
        "Run scripts/04_extract_ab2222.py first."
    )

df = pd.read_csv(INPUT_FILE)

print(f"\nInput statements: {len(df):,}")


# ---------------------------------------------------------------------
# EXTRACT SENTENCES
# ---------------------------------------------------------------------

rows = []

for _, row in df.iterrows():

    statement = str(row.get("statement", ""))

    sentences = split_sentences(statement)

    for sentence_index, sentence in enumerate(sentences, start=1):

        matched_groups, matched_terms = find_keyword_matches(sentence)

        output = row.to_dict()

        # Replace statement-specific fields with sentence metadata
        output["sentence_index"] = sentence_index
        output["sentence"] = sentence

        output["matched_groups"] = "; ".join(matched_groups)
        output["matched_terms"] = "; ".join(matched_terms)
        output["n_keyword_groups"] = len(matched_groups)
        output["keyword_match"] = bool(matched_groups)

        rows.append(output)


sentences_df = pd.DataFrame(rows)


# ---------------------------------------------------------------------
# OUTPUT 1: ALL SENTENCES
# ---------------------------------------------------------------------

sentences_df.to_csv(
    OUTPUT_ALL,
    index=False,
    encoding="utf-8"
)


# ---------------------------------------------------------------------
# OUTPUT 2: KEYWORD-RELEVANT SENTENCES
# ---------------------------------------------------------------------

relevant_df = sentences_df[
    sentences_df["keyword_match"] == True
].copy()

relevant_df.to_csv(
    OUTPUT_RELEVANT,
    index=False,
    encoding="utf-8"
)


# ---------------------------------------------------------------------
# OUTPUT 3: LEGISLATOR KEYWORD SENTENCES
# ---------------------------------------------------------------------

legislator_df = relevant_df[
    relevant_df["speaker_type"]
    .astype(str)
    .str.lower()
    .eq("legislator")
].copy()

legislator_df.to_csv(
    OUTPUT_LEGISLATORS,
    index=False,
    encoding="utf-8"
)


# ---------------------------------------------------------------------
# RESULTS
# ---------------------------------------------------------------------

print("\n" + "=" * 80)
print("RESULTS")
print("=" * 80)

print(f"\nStatements:                 {len(df):,}")
print(f"Sentences:                  {len(sentences_df):,}")
print(f"Keyword-relevant sentences: {len(relevant_df):,}")
print(f"Legislator keyword sentences:{len(legislator_df):,}")


# ---------------------------------------------------------------------
# MATCHES BY CATEGORY
# ---------------------------------------------------------------------

print("\n" + "=" * 80)
print("MATCHES BY CATEGORY")
print("-" * 80)

category_counts = {}

for group in KEYWORD_GROUPS:

    count = sentences_df["matched_groups"].fillna("").apply(
        lambda x: group in [
            item.strip()
            for item in str(x).split(";")
            if item.strip()
        ]
    ).sum()

    category_counts[group] = int(count)

for group, count in category_counts.items():

    print(f"{group:<35} {count:>6}")


# ---------------------------------------------------------------------
# MATCHES BY HEARING
# ---------------------------------------------------------------------

print("\n" + "=" * 80)
print("MATCHES BY HEARING")
print("-" * 80)

if len(relevant_df):

    hearing_counts = (
        relevant_df
        .groupby("hearing_id")
        .size()
        .sort_values(ascending=False)
    )

    for hearing_id, count in hearing_counts.items():
        print(f"{str(hearing_id):<20} {count:>6}")


# ---------------------------------------------------------------------
# MATCHES BY LEGISLATOR
# ---------------------------------------------------------------------

print("\n" + "=" * 80)
print("MATCHES BY LEGISLATOR")
print("-" * 80)

if len(legislator_df):

    legislator_counts = (
        legislator_df
        .groupby("speaker")
        .size()
        .sort_values(ascending=False)
    )

    for speaker, count in legislator_counts.items():
        print(f"{str(speaker):<35} {count:>6}")


# ---------------------------------------------------------------------
# MULTI-CATEGORY SENTENCES
# ---------------------------------------------------------------------

print("\n" + "=" * 80)
print("SENTENCES MATCHING MULTIPLE CATEGORIES")
print("-" * 80)

multi_df = relevant_df[
    relevant_df["n_keyword_groups"] >= 2
].copy()

print(f"\nMulti-category sentences: {len(multi_df):,}")

if len(multi_df):

    for _, row in multi_df.head(20).iterrows():

        print("\n" + "-" * 80)
        print(
            f"{row.get('hearing_id', '')} | "
            f"{row.get('speaker', '')} | "
            f"statement {row.get('statement_index', '')} | "
            f"sentence {row.get('sentence_index', '')}"
        )

        print(
            f"Groups: {row.get('matched_groups', '')}"
        )

        print(
            f"Terms: {row.get('matched_terms', '')}"
        )

        print(
            f"Sentence: {row.get('sentence', '')}"
        )


# ---------------------------------------------------------------------
# SAVE SUMMARY
# ---------------------------------------------------------------------

print("\n" + "=" * 80)
print("SAVED")
print("-" * 80)

print(f"\n{OUTPUT_ALL}")
print(OUTPUT_RELEVANT)
print(OUTPUT_LEGISLATORS)

print("\nDone.")
print("=" * 80)
