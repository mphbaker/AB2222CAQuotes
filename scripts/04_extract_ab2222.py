from pathlib import Path
import pandas as pd
import re


OUT = Path("data")
PARSED = OUT / "parsed"
EXTRACTED = OUT / "extracted"

EXTRACTED.mkdir(parents=True, exist_ok=True)


# -------------------------------------------------------------------
# AB 2222 recognition
# -------------------------------------------------------------------

AB2222_PATTERNS = [

    r"\bab\s*2222\b",

    r"\ba\s*b\s*2222\b",

    r"\bav\s*2222\b",

    r"\b[a-z]*b\s*2222\b",

    r"\btwenty[- ]?two[- ]?twenty[- ]?two\b",

    r"\bcommunity news act\b",

    r"\bcommunity newsroom employment\b",

    r"\bworkforce sustainability act\b",
]


def is_ab2222(text):

    text = text.lower()

    for pattern in AB2222_PATTERNS:

        if re.search(
            pattern,
            text,
            flags=re.IGNORECASE
        ):
            return True

    return False


# -------------------------------------------------------------------
# Procedural statement classification
# -------------------------------------------------------------------

PROCEDURAL_PATTERNS = [

    r"\byou may proceed\b",

    r"\bplease proceed\b",

    r"\bthank you very much\b",

    r"\bthank you\b",

    r"\bnext witness\b",

    r"\bfirst witness\b",

    r"\bnext speaker\b",

    r"\banyone .* wishing to speak\b",

    r"\bcome to the microphone\b",

    r"\bseeing no one\b",

    r"\bbring it back to the committee\b",

    r"\bthis bill will be referred\b",

    r"\bthis bill will refer\b",

    r"\bsuspense file\b",

    r"\byou may close\b",

    r"\bwe have an author\b",

    r"\bfile item number\b",

]


def classify_statement(row):

    text = str(row["statement"]).strip()

    speaker_type = str(
        row["speaker_type"]
    ).strip()

    if not text:

        return "unclear"

    # Non-legislators are not being classified here.
    # We retain them in the raw corpus.
    if speaker_type != "Legislator":

        return "non_legislator"

    lower = text.lower()

    # Clear procedural language.
    for pattern in PROCEDURAL_PATTERNS:

        if re.search(
            pattern,
            lower
        ):

            # A statement can contain both procedure and substance.
            # The specific substantive exceptions below override this.
            if len(text) < 250:
                return "procedural"

    # Questions or comments involving substantive policy.
    substantive_signals = [

        "why is the",
        "why are",
        "why does",
        "support this",
        "support for",
        "local news",
        "local journalism",
        "journalist",
        "journalists",
        "newspaper",
        "newsroom",
        "newsrooms",
        "tax credit",
        "credit",
        "wages",
        "hire",
        "hiring",
        "retain",
        "retaining",
        "democracy",
        "civic",
        "voter",
        "accountability",
        "editorial",
        "political influence",
        "news desert",
        "community",
        "journalism",
        "facts",
        "misinformation",
    ]

    signal_count = sum(
        signal in lower
        for signal in substantive_signals
    )

    if signal_count >= 1:
        return "substantive"

    # Longer legislator statements are provisionally substantive.
    if len(text) >= 250:
        return "substantive"

    return "unclear"


# -------------------------------------------------------------------
# Find likely bill boundaries
# -------------------------------------------------------------------

def extract_number(text):

    """
    Extract a legislative file-item number when present.
    """

    patterns = [

        r"file item number\s+(\d+)",

        r"file item\s+(\d+)",

        r"item number\s+(\d+)",

    ]

    for pattern in patterns:

        m = re.search(
            pattern,
            text.lower()
        )

        if m:
            return int(m.group(1))

    return None


def find_segment(group):

    group = group.reset_index(
        drop=True
    )

    # ---------------------------------------------------------------
    # Find every explicit AB 2222 / Community News Act reference.
    # ---------------------------------------------------------------

    matches = []

    for i, row in group.iterrows():

        if is_ab2222(
            row["statement"]
        ):
            matches.append(i)

    if not matches:

        return None

    first_match = min(matches)

    # ---------------------------------------------------------------
    # Start slightly before the first explicit bill reference.
    #
    # This captures the chair introducing the author/bill, as happened
    # in hearing 279175.
    # ---------------------------------------------------------------

    start = max(
        0,
        first_match - 3
    )

    # ---------------------------------------------------------------
    # Determine the current file-item number if available.
    # ---------------------------------------------------------------

    current_item = None

    for i in range(
        first_match,
        max(-1, first_match - 8),
        -1
    ):

        number = extract_number(
            group.loc[i, "statement"]
        )

        if number is not None:

            current_item = number
            break

    # ---------------------------------------------------------------
    # Search forward for a new file item.
    # ---------------------------------------------------------------

    end = len(group) - 1

    if current_item is not None:

        for i in range(
            first_match + 1,
            len(group)
        ):

            number = extract_number(
                group.loc[i, "statement"]
            )

            if (
                number is not None
                and number != current_item
            ):

                end = i - 1
                break

    else:

        # -----------------------------------------------------------
        # Fallback for proceedings where file-item numbers are absent.
        #
        # We look for a strong transition into another bill.
        # -----------------------------------------------------------

        transition_patterns = [

            r"\bnext bill\b",

            r"\bnext measure\b",

            r"\bnext item\b",

            r"\bwe will now hear\b",

            r"\bwe will now consider\b",

            r"\bnext up\b",

        ]

        for i in range(
            first_match + 1,
            len(group)
        ):

            text = group.loc[
                i,
                "statement"
            ]

            lower = text.lower()

            if any(
                re.search(
                    pattern,
                    lower
                )
                for pattern in transition_patterns
            ):

                end = i - 1
                break

    segment = group.iloc[
        start:end + 1
    ].copy()

    segment["bill"] = "AB 2222"

    segment["bill_segment_start"] = start

    segment["bill_segment_end"] = end

    segment["ab2222_reference"] = segment[
        "statement"
    ].apply(is_ab2222)

    segment["statement_type"] = segment.apply(
        classify_statement,
        axis=1
    )

    return segment


# -------------------------------------------------------------------
# Main
# -------------------------------------------------------------------

def main():

    input_path = (
        PARSED /
        "all_transcript_statements.csv"
    )

    if not input_path.exists():

        raise FileNotFoundError(
            f"{input_path} not found. "
            "Run 03_parse_transcripts.py first."
        )

    df = pd.read_csv(
        input_path
    )

    print("=" * 80)
    print("EXTRACTING AB 2222 DISCUSSIONS")
    print("=" * 80)

    all_segments = []

    for hearing_id, group in df.groupby(
        "hearing_id",
        sort=False
    ):

        print()
        print("-" * 80)
        print(f"HEARING {hearing_id}")
        print("-" * 80)

        segment = extract_segment(
            group
        )

        if segment is None:

            print(
                "NO AB 2222 DISCUSSION FOUND"
            )

            continue

        print(
            f"Statements in segment: "
            f"{len(segment)}"
        )

        print(
            f"AB 2222 references: "
            f"{segment['ab2222_reference'].sum()}"
        )

        legislators = segment[
            segment["speaker_type"]
            == "Legislator"
        ]

        print(
            f"Legislator statements: "
            f"{len(legislators)}"
        )

        substantive = legislators[
            legislators["statement_type"]
            == "substantive"
        ]

        procedural = legislators[
            legislators["statement_type"]
            == "procedural"
        ]

        print(
            f"  substantive: {len(substantive)}"
        )

        print(
            f"  procedural:  {len(procedural)}"
        )

        all_segments.append(
            segment
        )

    if not all_segments:

        print()
        print(
            "No AB 2222 segments were found."
        )

        return

    result = pd.concat(
        all_segments,
        ignore_index=True
    )

    # ---------------------------------------------------------------
    # Save complete bill-discussion corpus
    # ---------------------------------------------------------------

    all_path = (
        EXTRACTED /
        "ab2222_all_statements.csv"
    )

    result.to_csv(
        all_path,
        index=False
    )

    # ---------------------------------------------------------------
    # Save legislator-only corpus
    # ---------------------------------------------------------------

    legislators = result[
        result["speaker_type"]
        == "Legislator"
    ].copy()

    legislator_path = (
        EXTRACTED /
        "ab2222_legislator_statements.csv"
    )

    legislators.to_csv(
        legislator_path,
        index=False
    )

    # ---------------------------------------------------------------
    # Save substantive legislator corpus
    # ---------------------------------------------------------------

    substantive = legislators[
        legislators["statement_type"]
        == "substantive"
    ].copy()

    substantive_path = (
        EXTRACTED /
        "ab2222_substantive_legislator_statements.csv"
    )

    substantive.to_csv(
        substantive_path,
        index=False
    )

    # ---------------------------------------------------------------
    # Print final summary
    # ---------------------------------------------------------------

    print()
    print("=" * 80)
    print("FINAL SUMMARY")
    print("=" * 80)

    print(
        f"Hearings with AB 2222: "
        f"{result['hearing_id'].nunique()}"
    )

    print(
        f"Total AB 2222 statements: "
        f"{len(result)}"
    )

    print(
        f"Legislator statements: "
        f"{len(legislators)}"
    )

    print(
        f"Substantive legislator statements: "
        f"{len(substantive)}"
    )

    print(
        f"Procedural legislator statements: "
        f"{len(legislators) - len(substantive)}"
    )

    print()
    print("Legislators:")

    for speaker in sorted(
        legislators["speaker"]
        .dropna()
        .unique()
    ):

        print(
            f"  {speaker}"
        )

    print()
    print("Saved:")
    print(
        f"  {all_path}"
    )
    print(
        f"  {legislator_path}"
    )
    print(
        f"  {substantive_path}"
    )


# Alias kept separate so it is easy to replace
# the segmentation algorithm later.
def extract_segment(group):

    return extract_segment_core(group)


def extract_segment_core(group):

    return extract_segment_impl(group)


def extract_segment_impl(group):

    return extract_bill_segment(group)


def extract_bill_segment(group):

    return extract_segment_original(group)


def extract_segment_original(group):

    return extract_segment_logic(group)


def extract_segment_logic(group):

    # The actual implementation is defined here to make the
    # segmentation function easy to replace in a later version.

    group = group.reset_index(
        drop=True
    )

    matches = []

    for i, row in group.iterrows():

        if is_ab2222(
            row["statement"]
        ):
            matches.append(i)

    if not matches:
        return None

    first_match = min(matches)

    start = max(
        0,
        first_match - 3
    )

    current_item = None

    for i in range(
        first_match,
        max(-1, first_match - 8),
        -1
    ):

        number = extract_number(
            group.loc[i, "statement"]
        )

        if number is not None:

            current_item = number
            break

    end = len(group) - 1

    if current_item is not None:

        for i in range(
            first_match + 1,
            len(group)
        ):

            number = extract_number(
                group.loc[i, "statement"]
            )

            if (
                number is not None
                and number != current_item
            ):

                end = i - 1
                break

    else:

        transition_patterns = [

            r"\bnext bill\b",
            r"\bnext measure\b",
            r"\bnext item\b",
            r"\bwe will now hear\b",
            r"\bwe will now consider\b",
            r"\bnext up\b",

        ]

        for i in range(
            first_match + 1,
            len(group)
        ):

            text = str(
                group.loc[
                    i,
                    "statement"
                ]
            )

            lower = text.lower()

            if any(
                re.search(
                    pattern,
                    lower
                )
                for pattern in transition_patterns
            ):

                end = i - 1
                break

    segment = group.iloc[
        start:end + 1
    ].copy()

    segment["bill"] = "AB 2222"

    segment["bill_segment_start"] = start

    segment["bill_segment_end"] = end

    segment["ab2222_reference"] = segment[
        "statement"
    ].apply(is_ab2222)

    segment["statement_type"] = segment.apply(
        classify_statement,
        axis=1
    )

    return segment


if __name__ == "__main__":
    main()
