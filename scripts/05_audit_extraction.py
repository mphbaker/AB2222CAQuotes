from pathlib import Path
import pandas as pd


PATH = Path(
    "data/extracted/ab2222_all_statements.csv"
)


def main():

    df = pd.read_csv(PATH)

    print("=" * 100)
    print("AB 2222 EXTRACTION AUDIT")
    print("=" * 100)

    for hearing_id, g in df.groupby(
        "hearing_id",
        sort=False
    ):

        print()
        print("#" * 100)
        print(f"HEARING: {hearing_id}")
        print("#" * 100)

        total_statements = len(g)

        legislator_statements = (
            g["speaker_type"] == "Legislator"
        ).sum()

        substantive_legislators = (
            (g["speaker_type"] == "Legislator")
            & (g["statement_type"] == "substantive")
        ).sum()

        procedural_legislators = (
            (g["speaker_type"] == "Legislator")
            & (g["statement_type"] == "procedural")
        ).sum()

        print(
            f"Statements: {total_statements}"
        )

        print(
            f"Legislator statements: "
            f"{legislator_statements}"
        )

        print(
            f"Substantive legislator statements: "
            f"{substantive_legislators}"
        )

        print(
            f"Procedural legislator statements: "
            f"{procedural_legislators}"
        )

        print()

        legislators = g[
            g["speaker_type"] == "Legislator"
        ]

        for _, row in legislators.iterrows():

            print(
                f"[{row['statement_index']}] "
                f"{row['speaker']} "
                f"({row['statement_type']})"
            )

            print(
                "  " + str(row["statement"])[:500]
            )

            print()


if __name__ == "__main__":
    main()
