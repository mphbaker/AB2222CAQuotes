#!/usr/bin/env python3

"""
07_classify_quote_types.py

Classify already-extracted legislator statements into interpretable
quote types using transparent keyword/phrase rules.

This is a multi-label classification:
a statement can belong to more than one quote type.

Input:
    data/extracted/ab2222_legislator_context_statements.csv

Output:
    data/extracted/ab2222_legislator_quote_types.csv
"""

from pathlib import Path
import re
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]

INPUT = ROOT / "data/extracted/ab2222_legislator_context_statements.csv"
OUTPUT = ROOT / "data/extracted/ab2222_legislator_quote_types.csv"


# ---------------------------------------------------------------------
# Quote-type rules
# ---------------------------------------------------------------------

QUOTE_TYPES = {

    # Describes the decline, closure, staffing collapse, or broader
    # problem facing local journalism.
    "problem": [
        r"\bcrisis\b",
        r"\bdeclin\w*\b",
        r"\bshrinking\b",
        r"\bclosures?\b",
        r"\bclos(ed|ing)\b",
        r"\blayoffs?\b",
        r"\bloss of\b",
        r"\bdisappear\w*\b",
        r"\bdisappearing\b",
        r"\bstruggling\b",
        r"\bcollapse\b",
        r"\bwiped out\b",
        r"\blosing\b",
        r"\bunder attack\b",
    ],

    # Connects journalism to democracy, civic participation,
    # accountability, watchdog functions, or the public good.
    "civic_value": [
        r"\bcivic engagement\b",
        r"\bvoter participation\b",
        r"\bdemocr\w*\b",
        r"\bgovernment accountability\b",
        r"\baccountability\b",
        r"\bwatchdog\w*\b",
        r"\bcivic infrastructure\b",
        r"\bpublic good\b",
        r"\bhold power accountable\b",
    ],

    # Describes journalism as a source of trusted, reliable,
    # factual, accurate, or community information.
    "information_value": [
        r"\btrusted\b",
        r"\breliable\b",
        r"\blocal information\b",
        r"\breliable local reporting\b",
        r"\bmisinformation\b",
        r"\bdisinformation\b",
        r"\bfacts?\b",
        r"\baccurac\w*\b",
        r"\bbias\b",
        r"\bwhat is real\b",
        r"\btrustworthy\b",
        r"\bcredible reporting\b",
    ],

    # Describes the concrete role of local journalists in covering
    # schools, government, public safety, neighborhoods, etc.
    "community_coverage": [
        r"\bschools?\b",
        r"\bschool board\b",
        r"\bcity council\b",
        r"\blocal government\b",
        r"\bpublic safety\b",
        r"\bneighborhoods?\b",
        r"\bcommunity issues?\b",
        r"\bcovering\b",
        r"\bcover\b",
        r"\bcoverage\b",
        r"\bserve communities\b",
    ],

    # Describes journalists as workers or discusses hiring,
    # retention, staffing, employment, or newsroom jobs.
    "jobs_workforce": [
        r"\bjournalists?\b",
        r"\breporters?\b",
        r"\bjobs?\b",
        r"\bhir(e|ing|ed)\b",
        r"\bretain\w*\b",
        r"\bretention\b",
        r"\bemployment\b",
        r"\bworkforce\b",
        r"\bstaff\w*\b",
        r"\bnewsroom\b",
        r"\bfreelance\w*\b",
        r"\bsole proprietors?\b",
        r"\bstaffing\b",
    ],

    # Explains the actual intervention: tax credit, refundable credit,
    # investment, or direct support for journalism.
    #
    # Generic phrases such as "this bill", "the bill", and "AB 2222"
    # are intentionally NOT sufficient matches.
    "policy_mechanism": [
        r"\btax credit\b",
        r"\brefundable tax credit\b",
        r"\bcredit\b",
        r"\binvests? in\b",
        r"\binvestment\b",
        r"\bsupport\w* local journalism\b",
        r"\bsupport\w* local news\b",
        r"\bestablish\w* .*credit\b",
        r"\bcreat\w* .*credit\b",
    ],

    # Describes who qualifies, the amount/form of the credit,
    # outlet types, residency, hours, wages, etc.
    #
    # Generic "amendment" language is deliberately excluded.
    "policy_design": [
        r"\bsmall independent\b",
        r"\bsmall local\b",
        r"\bindependent\b",
        r"\bnonprofit\w*\b",
        r"\bpart[- ]time\b",
        r"\bsole proprietors?\b",
        r"\bprint\b",
        r"\bdigital\b",
        r"\bbroadcast\b",
        r"\bamount\b",
        r"\bfixed amount\b",
        r"\bpercentage\b",
        r"\bwages?\b",
        r"\bqualif\w*\b",
        r"\beligib\w*\b",
        r"\bfirst five\b",
        r"\badditional journalist\b",
        r"\bnew journalism position\b",
        r"\bresiden(t|cy)\b",
        r"\bminimum number of hours\b",
    ],

    # Safeguards intended to address editorial independence,
    # political influence, ownership, transparency, etc.
    "safeguards": [
        r"\beditorial independence\b",
        r"\bpolitical influence\b",
        r"\bpolitical organization\b",
        r"\bpolitical organizations\b",
        r"\b501\s*\(?c\)?\s*4\b",
        r"\bownership\b",
        r"\bgovernance\b",
        r"\btransparency\b",
        r"\bcorrections?\b",
        r"\bmedia liability\b",
        r"\bcontent[- ]neutral\b",
        r"\bcontent neutral\b",
        r"\bobjective standards?\b",
        r"\bwithout influencing content\b",
        r"\bpolitical[- ]perspective neutral\b",
        r"\bpolitical perspectives\b",
        r"\bwinners or losers\b",
    ],

    # Explicitly connects journalism to automation, AI, or technology.
    "ai_technology": [
        r"\bartificial intelligence\b",
        r"\bAI\b",
        r"\bautomation\b",
        r"\bgenerative AI\b",
        r"\btechnology\b",
    ],
}


# ---------------------------------------------------------------------
# Strongly procedural language
# ---------------------------------------------------------------------

# These are intentionally narrow. We do NOT flag ordinary phrases such
# as "thank you", "vote", or "aye vote" because substantive statements
# can contain those phrases at the beginning or end.
PROCEDURAL_PATTERNS = [
    r"\bfile item\b",
    r"\bsuspense file\b",
    r"\bthe measure passes\b",
    r"\bdebate having ceased\b",
    r"\bclerk will\b",
    r"\bclerk will open\b",
    r"\bclerk will close\b",
    r"\btally the votes\b",
    r"\bayes\s+\d+\b",
    r"\bnoes\s+\d+\b",
    r"\bcome to the microphone\b",
    r"\bname, your organization\b",
]


# ---------------------------------------------------------------------
# Functions
# ---------------------------------------------------------------------

def normalize(text):
    """Normalize whitespace while preserving substantive text."""
    return re.sub(r"\s+", " ", str(text)).strip()


def find_matches(text, patterns):
    """Return the actual text matched by each regex pattern."""
    matches = []

    for pattern in patterns:
        for match in re.finditer(
            pattern,
            text,
            flags=re.IGNORECASE
        ):
            matches.append(match.group(0))

    return sorted(set(m.lower() for m in matches))


def classify_statement(text):
    """
    Apply all quote-type rules.

    Returns:
        matched_types
        matched_terms
    """

    text = normalize(text)

    matched_types = []
    matched_terms = {}

    for quote_type, patterns in QUOTE_TYPES.items():

        terms = find_matches(
            text,
            patterns
        )

        if terms:
            matched_types.append(
                quote_type
            )

            matched_terms[quote_type] = terms

    return matched_types, matched_terms


def is_purely_procedural(text):
    """
    Flag statements containing strongly procedural/hearing language.

    This is intentionally conservative. A statement that contains
    substantive discussion plus a closing request for a vote should
    remain a quote candidate.
    """

    text = normalize(text)

    for pattern in PROCEDURAL_PATTERNS:

        if re.search(
            pattern,
            text,
            flags=re.IGNORECASE
        ):
            return True

    return False


# ---------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------

def main():

    if not INPUT.exists():
        raise FileNotFoundError(
            f"Input file not found: {INPUT}"
        )

    df = pd.read_csv(INPUT)

    if "statement" not in df.columns:
        raise ValueError(
            "Input file does not contain a 'statement' column."
        )

    matched_types_all = []
    matched_terms_all = []
    procedural_flags = []

    for statement in df["statement"]:

        types, terms = classify_statement(
            statement
        )

        matched_types_all.append(types)
        matched_terms_all.append(terms)

        procedural_flags.append(
            is_purely_procedural(statement)
        )

    # ---------------------------------------------------------------
    # Add classification fields
    # ---------------------------------------------------------------

    df["quote_types"] = [
        "; ".join(types)
        for types in matched_types_all
    ]

    df["n_quote_types"] = [
        len(types)
        for types in matched_types_all
    ]

    df["quote_type_terms"] = [
        "; ".join(
            f"{quote_type}: {', '.join(terms)}"
            for quote_type, terms in term_dict.items()
        )
        for term_dict in matched_terms_all
    ]

    df["quote_type_match"] = (
        df["n_quote_types"] > 0
    )

    df["purely_procedural"] = procedural_flags

    # A substantive quote candidate must have at least one
    # quote classification and must not be purely procedural.
    df["substantive_quote_candidate"] = (
        df["quote_type_match"]
        & ~df["purely_procedural"]
    )

    # ---------------------------------------------------------------
    # Save
    # ---------------------------------------------------------------

    df.to_csv(
        OUTPUT,
        index=False
    )

    # ---------------------------------------------------------------
    # Summary
    # ---------------------------------------------------------------

    print("\n=== Quote Type Classification ===")

    print(
        f"Input statements: "
        f"{len(df):,}"
    )

    print(
        f"Statements with at least one quote type: "
        f"{df['quote_type_match'].sum():,}"
    )

    print(
        f"Statements flagged as purely procedural: "
        f"{df['purely_procedural'].sum():,}"
    )

    print(
        f"Substantive quote candidates: "
        f"{df['substantive_quote_candidate'].sum():,}"
    )

    print("\n=== Quote Type Counts ===")

    for quote_type in QUOTE_TYPES:

        count = df["quote_types"].apply(
            lambda x:
                quote_type in str(x).split("; ")
        ).sum()

        print(
            f"{quote_type:22s} {count:4d}"
        )

    print("\n=== Multi-type statements ===")

    print(
        (df["n_quote_types"] > 1).sum()
    )

    # ---------------------------------------------------------------
    # Display classified statements
    # ---------------------------------------------------------------

    print("\n=== Classified Statements ===")

    display_cols = [
        "speaker",
        "hearing_id",
        "statement_index",
        "quote_types",
        "quote_type_terms",
        "purely_procedural",
        "substantive_quote_candidate",
        "statement",
    ]

    classified = df[
        df["quote_type_match"]
    ].copy()

    for _, row in classified[
        display_cols
    ].iterrows():

        print("\n----------------------------------------")

        print(
            f"{row['speaker']} | "
            f"hearing {row['hearing_id']} | "
            f"statement {row['statement_index']}"
        )

        print(
            f"TYPES: {row['quote_types']}"
        )

        print(
            f"MATCHES: {row['quote_type_terms']}"
        )

        print(
            f"PURELY PROCEDURAL: "
            f"{row['purely_procedural']}"
        )

        print(
            f"QUOTE CANDIDATE: "
            f"{row['substantive_quote_candidate']}"
        )

        print(
            f"STATEMENT: "
            f"{row['statement']}"
        )

    print(
        f"\nSaved: {OUTPUT}"
    )


if __name__ == "__main__":
    main()
