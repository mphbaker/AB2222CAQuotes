# Legislative Local News Statements

A reproducible workflow for identifying and extracting public statements by state legislators concerning local news, journalism, news organizations, and related policy issues.

## Current case study

The initial implementation uses California Assembly Bill 2222 (AB 2222), the Community News Act, as a test case.

The workflow collects publicly available legislative hearing transcripts and progressively narrows them from the full transcript record to statements relevant to local news and journalism.

## Workflow

1. Discover hearings associated with the bill.
2. Render and download publicly available hearing transcripts.
3. Parse individual transcript statements.
4. Identify portions of hearings associated with AB 2222.
5. Apply broad keyword and topic retrieval.
6. Split statements into individual sentences for keyword matching.
7. Filter keyword matches for local-news and journalism context.
8. Deduplicate matching sentences back to complete transcript statements.
9. Produce a legislator-only dataset for review and quotation selection.

## Directory structure

```text
scripts/
    01_discover_hearings.py
    02_download_transcripts.py
    03_parse_transcripts.py
    04_extract_ab2222.py
    05_audit_extraction.py
    06_keyword_extract.py
    06a_sentence_keyword_extract.py
    06b_context_filter.py
    06c_deduplicate_statements.py

data/
    hearings.csv
    raw_transcripts/
    parsed/
    extracted/
Data provenance

The transcript data are collected from the publicly available California Digital Democracy / CalMatters Digital Democracy hearing record.

The extracted datasets are derived from those publicly available transcripts using the scripts in this repository.

Outputs

The pipeline produces progressively refined datasets, including:

Parsed transcript statements
Keyword-coded statements
Sentence-level keyword matches
Context-relevant sentences
Deduplicated context-relevant statements
Legislator-only context-relevant statements

The final legislator-only dataset is intended for human review of statements and quotations. Keyword matching is used for retrieval and does not by itself determine substantive relevance.

Raw transcripts

Raw rendered transcript HTML and text files are excluded from version control. They can be regenerated from the public source using the download script.

Status

AB 2222 is the initial test case. The workflow is intended to be evaluated and refined before being generalized to additional bills, legislative sessions, or jurisdictions.

Reproducibility

Run the scripts in numerical order. Each stage uses the output of the preceding stage.

The complete workflow is:

01_discover_hearings.py
02_download_transcripts.py
03_parse_transcripts.py
04_extract_ab2222.py
05_audit_extraction.py
06_keyword_extract.py
06a_sentence_keyword_extract.py
06b_context_filter.py
06c_deduplicate_statements.py
