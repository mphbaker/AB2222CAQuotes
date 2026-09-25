from playwright.sync_api import sync_playwright
from pathlib import Path
import pandas as pd
import time


OUT = Path("data")
RAW = OUT / "raw_transcripts"

RAW.mkdir(parents=True, exist_ok=True)


def download_hearing(page, hearing_id, url):

    html_path = RAW / f"{hearing_id}.html"
    text_path = RAW / f"{hearing_id}.txt"

    print()
    print("-" * 80)
    print(f"HEARING {hearing_id}")
    print("-" * 80)
    print(url)

    try:

        page.goto(
            url,
            wait_until="domcontentloaded",
            timeout=60000
        )

        # Allow the transcript to render.
        page.wait_for_timeout(5000)

        html = page.content()

        try:
            text = page.locator("body").inner_text()
        except Exception:
            text = ""

        html_path.write_text(
            html,
            encoding="utf-8"
        )

        text_path.write_text(
            text,
            encoding="utf-8"
        )

        print(f"HTML: {len(html):,} characters")
        print(f"Text: {len(text):,} characters")

        return True

    except Exception as e:

        print(f"ERROR: {e}")

        return False


def main():

    hearings_path = OUT / "hearings.csv"

    if not hearings_path.exists():
        raise FileNotFoundError(
            f"{hearings_path} not found. "
            "Run 01_discover_hearings.py first."
        )

    hearings = pd.read_csv(hearings_path)

    print("=" * 80)
    print("DOWNLOADING AB 2222 TRANSCRIPTS")
    print("=" * 80)

    print(f"Proceedings: {len(hearings)}")

    success = []
    failed = []

    with sync_playwright() as p:

        browser = p.chromium.launch(headless=True)

        page = browser.new_page(
            viewport={"width": 1440, "height": 1200},
            user_agent=(
                "Mozilla/5.0 "
                "(Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 "
                "(KHTML, like Gecko) "
                "Chrome/153.0.0.0 Safari/537.36"
            )
        )

        for _, row in hearings.iterrows():

            hearing_id = str(row["hearing_id"])
            url = row["url"]

            ok = download_hearing(
                page,
                hearing_id,
                url
            )

            if ok:
                success.append(hearing_id)
            else:
                failed.append(hearing_id)

            time.sleep(1)

        browser.close()

    print()
    print("=" * 80)
    print("DOWNLOAD SUMMARY")
    print("=" * 80)

    print(f"Successful: {len(success)}")
    print(f"Failed:     {len(failed)}")

    if failed:
        print()
        print("Failed hearings:")
        for hearing_id in failed:
            print(f"  {hearing_id}")


if __name__ == "__main__":
    main()
