print("Hello, World! ")
from playwright.sync_api import sync_playwright
import time
   
"""
W1D3 Playwright Assignment
Demonstrates the four core Playwright actions on a practice website
built for scraping (quotes.toscrape.com):

    1. Load browser   - launch Chromium and open the site
    2. Typewriting    - type username and password key by key
    3. Clicking       - click Login, then click "Next" to change page
    4. Waiting        - wait for selectors before reading the page
    5. Extracting     - read quotes, authors and tags, save them to CSV
    6. Screenshot     - save screenshots as proof of each stage
"""

import csv
import os
from playwright.sync_api import sync_playwright

BASE_URL = os.environ.get("BASE_URL", "https://quotes.toscrape.com")
HEADLESS = os.environ.get("HEADLESS", "0") == "1"
PAGES_TO_READ = 2


def extract_quotes(page):
    """Return a list of dicts with text, author and tags for every quote on the page."""
    results = []
    for card in page.locator("div.quote").all():
        results.append({
            "text": card.locator("span.text").inner_text().strip("“”\""),
            "author": card.locator("small.author").inner_text(),
            "tags": ", ".join(card.locator("a.tag").all_inner_texts()),
        })
    return results


def main():
    with sync_playwright() as p:
        # 1. LOAD BROWSER
        print("1. Launching browser...")
        browser = p.chromium.launch(headless=HEADLESS, slow_mo=300)
        page = browser.new_page(viewport={"width": 1280, "height": 800})
        page.goto(f"{BASE_URL}/login", wait_until="domcontentloaded")
        page.wait_for_selector("#username")  # make sure the form is ready
        print("   Opened:", page.title())

        # 2. TYPEWRITING (one key at a time, like a person typing)
        print("2. Typing login details...")
        page.locator("#username").press_sequentially("selvakumar", delay=120)
        page.locator("#password").press_sequentially("password123", delay=120)
        page.screenshot(path="1_login_typed.png")

        # 3. CLICKING
        print("3. Clicking Login...")
        page.locator("input[type='submit']").click()

        # 4. WAITING FOR SELECTOR
        print("4. Waiting for the page to show the Logout link...")
        page.wait_for_selector("a[href='/logout']", state="visible", timeout=10000)
        print("   Logged in successfully.")

        # 5. EXTRACTING
        all_quotes = []
        for page_no in range(1, PAGES_TO_READ + 1):
            page.wait_for_selector("div.quote", state="visible", timeout=10000)
            quotes = extract_quotes(page)
            print(f"5. Extracted {len(quotes)} quotes from page {page_no}")
            all_quotes.extend(quotes)
            # 6. SCREENSHOT
            page.screenshot(path=f"{page_no + 1}_quotes_page{page_no}.png", full_page=True)

            next_link = page.locator("li.next a")
            if page_no < PAGES_TO_READ and next_link.count():
                next_link.click()  # another click: go to the next page
            else:
                break

        with open("quotes.csv", "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=["text", "author", "tags"])
            writer.writeheader()
            writer.writerows(all_quotes)

        print(f"\nSaved {len(all_quotes)} quotes to quotes.csv. First three:")
        for q in all_quotes[:3]:
            print(f'  - "{q["text"][:60]}..." by {q["author"]}  [{q["tags"]}]')

        browser.close()
        print("Done. Screenshots saved as *.png")


if __name__ == "__main__":
    main()