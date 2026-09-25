#!/usr/bin/env python3

import pandas as pd

INPUT = "data/extracted/ab2222_keyword_relevant_sentences.csv"
OUTPUT = "data/extracted/ab2222_context_relevant_sentences.csv"

# Categories that establish a local-news/journalism context
NEWS_CONTEXT = {
    "bill_reference",
    "local_news",
    "journalists_reporters",
    "news_organizations",
    "news_decline",
}

# Policy/workforce categories that need contextual support
POLICY_CATEGORIES = {
    "employment_workforce",
    "tax_credit",
    "editorial_independence",
    "nonprofit_small_outlets",
    "civic_effects",
    "information_effects",
}


def get_groups(value):
    if pd.isna(value) or not str(value).strip():
        return set()

    return {
        x.strip()
        for x in str(value).split(";")
        if x.strip()
    }


df = pd.read_csv(INPUT)

df["groups_set"] = df["matched_groups"].apply(get_groups)

def is_context_relevant(groups):
    # Direct local-news/bill reference
    if groups & NEWS_CONTEXT:
        return True

    # Policy terms alone are not enough
    # unless another news-context term is present.
    if groups & POLICY_CATEGORIES and groups & NEWS_CONTEXT:
        return True

    return False


df["context_relevant"] = df["groups_set"].apply(is_context_relevant)

# Remove temporary helper column
df = df.drop(columns=["groups_set"])

relevant = df[df["context_relevant"]].copy()

relevant.to_csv(OUTPUT, index=False)

print("=" * 70)
print("AB 2222 CONTEXT-RELEVANT SENTENCE FILTER")
print("=" * 70)

print(f"\nBroad keyword sentences:       {len(df):,}")
print(f"Context-relevant sentences:    {len(relevant):,}")

print("\nSAVED")
print("-" * 70)
print(OUTPUT)

print("\nBY CATEGORY")
print("-" * 70)

category_counts = {}

for category in NEWS_CONTEXT | POLICY_CATEGORIES:
    count = relevant["matched_groups"].fillna("").apply(
        lambda x: category in {
            item.strip()
            for item in str(x).split(";")
            if item.strip()
        }
    ).sum()

    category_counts[category] = int(count)

for category, count in sorted(
    category_counts.items(),
    key=lambda x: (-x[1], x[0])
):
    print(f"{category:<30} {count:>6}")

print("\nDone.")
