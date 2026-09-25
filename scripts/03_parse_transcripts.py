from bs4 import BeautifulSoup
from pathlib import Path
import pandas as pd
import re


OUT = Path("data")
RAW = OUT / "raw_transcripts"
PARSED = OUT / "parsed"

PARSED.mkdir(parents=True, exist_ok=True)


def clean_text(text):

    if text is None:
        return ""

    text = re.sub(r"\s+", " ", text)

    return text.strip()


def extract_speaker_and_role(li):

    """
    Extract speaker name and role without depending
    primarily on generated CSS class names.
    """

    role_labels = [
        "Legislator",
        "Person",
        "Lobbyist",
        "Staff",
        "Reporter",
        "Moderator",
        "Organization",
    ]

    role = None
    speaker = None

    # Look for the visible role label.
    for tag in li.find_all(["p", "div", "span"]):

        txt = clean_text(tag.get_text(" ", strip=True))

        if txt in role_labels:
            role = txt

            # In the current Digital Democracy structure,
            # the speaker name is immediately before the role.
            parent = tag.parent

            if parent is not None:

                previous = parent.find_previous_sibling()

                if previous is not None:

                    candidate = clean_text(
                        previous.get_text(" ", strip=True)
                    )

                    if candidate and candidate not in role_labels:
                        speaker = candidate

            break

    # Fallback using the currently observed Digital Democracy
    # transcript structure.
    if speaker is None:

        speaker_div = li.find(
            "div",
            class_=re.compile(r"lu93s7f")
        )

        if speaker_div:
            speaker = clean_text(
                speaker_div.get_text(" ", strip=True)
            )

    if role is None:

        role_p = li.find(
            "p",
            class_=re.compile(r"lu93s7g")
        )

        if role_p:
            role = clean_text(
                role_p.get_text(" ", strip=True)
            )

    return speaker, role


def extract_statement(li):

    """
    Extract the transcript statement.

    Prefer the observed transcript paragraph structure,
    but fall back to text inside the li.
    """

    # Current Digital Democracy transcript statement.
    statement_p = li.find(
        "p",
        class_=re.compile(r"lu93s7k")
    )

    if statement_p:

        return clean_text(
            statement_p.get_text(" ", strip=True)
        )

    # Generic fallback:
    # Find the largest paragraph in the transcript item.
    paragraphs = []

    for p in li.find_all("p"):

        txt = clean_text(
            p.get_text(" ", strip=True)
        )

        if not txt:
            continue

        if txt in {
            "Legislator",
            "Person",
            "Lobbyist",
            "Staff",
            "Reporter",
            "Moderator",
            "Organization",
        }:
            continue

        paragraphs.append(txt)

    if paragraphs:

        return max(
            paragraphs,
            key=len
        )

    return ""


def parse_hearing(hearing_id):

    html_path = RAW / f"{hearing_id}.html"

    if not html_path.exists():
        print(f"Missing: {html_path}")
        return []

    html = html_path.read_text(
        encoding="utf-8"
    )

    soup = BeautifulSoup(
        html,
        "html.parser"
    )

    records = []

    # Transcript entries currently appear as <li>
    # elements containing "View Transcript".
    lis = []

    for li in soup.find_all("li"):

        text = clean_text(
            li.get_text(" ", strip=True)
        )

        if "View Transcript" in text:
            lis.append(li)

    for index, li in enumerate(lis):

        speaker, role = extract_speaker_and_role(li)

        statement = extract_statement(li)

        dom_id = li.get("id", "")

        records.append({
            "hearing_id": hearing_id,
            "statement_index": index,
            "dom_id": dom_id,
            "speaker": speaker or "",
            "speaker_type": role or "",
            "statement": statement,
        })

    return records


def main():

    print("=" * 80)
    print("PARSING DIGITAL DEMOCRACY TRANSCRIPTS")
    print("=" * 80)

    html_files = sorted(
        RAW.glob("*.html")
    )

    print(
        f"HTML files found: {len(html_files)}"
    )

    all_records = []

    for html_path in html_files:

        hearing_id = html_path.stem

        print()
        print(
            f"Parsing hearing {hearing_id}..."
        )

        records = parse_hearing(
            hearing_id
        )

        print(
            f"  Statements: {len(records)}"
        )

        all_records.extend(records)

    df = pd.DataFrame(
        all_records
    )

    output = PARSED / "all_transcript_statements.csv"

    df.to_csv(
        output,
        index=False
    )

    print()
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)

    print(
        f"Total statements: {len(df):,}"
    )

    print(
        f"Hearings: "
        f"{df['hearing_id'].nunique()}"
    )

    print()
    print("Statements by speaker type:")

    print(
        df["speaker_type"]
        .value_counts(dropna=False)
        .to_string()
    )

    print()
    print(f"Saved: {output}")


if __name__ == "__main__":
    main()
