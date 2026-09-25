from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
from pathlib import Path
import pandas as pd
import re
import time


BASE = "https://calmatters.digitaldemocracy.org"
BILL_URL = f"{BASE}/bills/ca_202520260ab2222"

OUT = Path("data")
OUT.mkdir(exist_ok=True)


def main():

    print("=" * 80)
    print("AB 2222 HEARING DISCOVERY")
    print("=" * 80)
    print()
    print(f"Bill page: {BILL_URL}")
    print()

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

        print("Loading bill page...")

        page.goto(
            BILL_URL,
            wait_until="domcontentloaded",
            timeout=60000
        )

        page.wait_for_timeout(5000)

        html = page.content()

        browser.close()

    soup = BeautifulSoup(html, "html.parser")

    hearings = {}

    for a in soup.find_all("a", href=True):

        href = a["href"]

        if "/hearings/" not in href:
            continue

        if href.startswith("/"):
            url = BASE + href
        elif href.startswith("http"):
            url = href
        else:
            continue

        hearing_id_match = re.search(r"/hearings/(\d+)", url)

        if not hearing_id_match:
            continue

        hearing_id = hearing_id_match.group(1)

        text = a.get_text(" ", strip=True)

        hearings[hearing_id] = {
            "hearing_id": hearing_id,
            "url": url,
            "link_text": text,
        }

    hearings = list(hearings.values())

    print(f"Found {len(hearings)} unique hearing links")
    print()

    for h in hearings:
        print(
            f"{h['hearing_id']}: "
            f"{h['link_text'][:100]} "
            f"{h['url']}"
        )

    df = pd.DataFrame(hearings)

    path = OUT / "hearings.csv"

    df.to_csv(path, index=False)

    print()
    print(f"Saved: {path}")
    print()

    if len(df) == 0:
        print("WARNING: No hearing links were found.")
        print("Inspect the saved/rendered bill page if necessary.")


if __name__ == "__main__":
    main()

