"""
Cricket Live Score Bot - W1D3 Playwright Assignment

Steps:
    1. Launch Chromium
    2. Open Cricbuzz live scores and wait for the match list
    3. Extract every match listed (teams, series, status)
    4. Click the match you chose (or the first one) and wait for it to load
    5. Extract the live score: innings scores, status, run rates
    6. Report it: print, save a text report, append to a CSV history,
       and save a screenshot. With --watch, refresh every 30 seconds, 10 times.

The bot finds matches by their web address (/live-cricket-scores/) and scores
by their text pattern (e.g. "IND 245-6 (48.2)"), not by CSS class names, so it
keeps working when Cricbuzz changes its page design.

Run:
    python cricket_bot.py                 # first match on the list
    python cricket_bot.py India           # first match with "India" in it
    python cricket_bot.py India --watch   # 10 updates, 30 s apart (Ctrl+C to stop early)
"""

import csv
import os
import re
import sys
import time
from datetime import datetime
from playwright.sync_api import sync_playwright, Error as PWError

ARGS = [a for a in sys.argv[1:] if not a.startswith("--")]
KEYWORD = " ".join(ARGS).strip().lower()
WATCH = "--watch" in sys.argv
REFRESH_SECONDS = int(os.environ.get("REFRESH_SECONDS", "30"))
WATCH_UPDATES = 10          # with --watch: 10 updates, 30 s apart (about 5 minutes)
HEADLESS = os.environ.get("HEADLESS", "0") == "1"
BASE = os.environ.get("CRICBUZZ_BASE", "https://www.cricbuzz.com")
LIVE_URL = BASE + "/cricket-match/live-scores"

REPORT_TXT = "cricket_report.txt"
HISTORY_CSV = "cricket_history.csv"
SCREENSHOT = "cricket_match.png"

# "IND 245-6 (48.2)", "AUS 312/8 (50 Ov)", "ENG 156 & 89-2 (23)"
SCORE_RE = re.compile(
    r"\b([A-Z][A-Z0-9]{1,4})\s+(\d{1,3}(?:[-/]\d{1,2})?(?:\s*d)?"
    r"(?:\s*&\s*\d{1,3}(?:[-/]\d{1,2})?(?:\s*d)?)?)\s*\((\d{1,3}(?:\.\d)?)(?:\s*(?:Ov|ovs|overs))?\)"
)
STATUS_WORDS = ("won by", "need", "require", "lead by", "trail by", "opt to", "elected to",
                "stumps", "innings break", "match drawn", "match tied", "no result",
                "rain", "delayed", "starts at", "toss", "day ", "lunch", "tea", "abandoned")
RATE_RE = re.compile(r"\b(CRR|RRR|REQ|Run Rate)\s*[:\-]?\s*(\d{1,2}\.\d{1,2})", re.I)


def clean(t):
    return " ".join(t.replace("\xa0", " ").split())


def list_matches(page):
    """Return unique matches on the live-scores page as dicts {title, text, href}.

    The same match is often linked several times (menu, card, ticker), so the
    details from every copy are combined and the most descriptive title is kept.
    """
    links = page.locator("a[href*='/live-cricket-scores/']")
    by_id, order = {}, []
    for i in range(links.count()):
        a = links.nth(i)
        href = a.get_attribute("href") or ""
        m = re.search(r"/live-cricket-scores/(\d+)", href)
        if not m:
            continue
        mid = m.group(1)
        title = clean(a.get_attribute("title") or "")
        title = re.sub(r"\s*-\s*Live Cricket Score.*$", "", title, flags=re.I)
        text = clean(a.inner_text())
        if mid not in by_id:
            slug = href.rstrip("/").split("/")[-1].replace("-", " ")
            by_id[mid] = {"title": "", "text": "", "href": href, "slug": slug}
            order.append(mid)
        entry = by_id[mid]
        if len(title) > len(entry["title"]):
            entry["title"] = title
        if text and text not in entry["text"]:
            entry["text"] = (entry["text"] + " " + text).strip()
    matches = []
    for mid in order:
        e = by_id[mid]
        if not e["title"]:
            e["title"] = e["slug"].upper().replace(" VS ", " vs ")
        matches.append(e)
    return matches


def extract_score(page):
    """Read the live score from the match page using text patterns."""
    body = page.inner_text("body")
    lines = [clean(l) for l in body.splitlines() if clean(l)]
    top = "\n".join(lines[:120])  # the scoreboard is near the top of the page

    scores = []
    for team, runs, overs in SCORE_RE.findall(top):
        entry = f"{team} {runs} ({overs} ov)"
        if entry not in scores:
            scores.append(entry)

    status = next((l for l in lines[:120]
                   if any(w in l.lower() for w in STATUS_WORDS) and len(l) < 160), "N/A")
    rates = {k.upper(): v for k, v in RATE_RE.findall(top)}

    title = clean(page.title()).split(" - Cricbuzz")[0].split("| Cricbuzz")[0]
    title = re.sub(r"\s*(Live Cricket Score|Cricket Scorecard|Commentary).*$", "", title, flags=re.I)
    return {
        "match": title,
        "scores": " | ".join(scores[:4]) if scores else "Not started / no score yet",
        "status": status,
        "crr": rates.get("CRR", ""),
        "rrr": rates.get("RRR", rates.get("REQ", "")),
    }


def save_report(data):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    lines = [
        "=" * 56,
        "  CRICKET LIVE SCORE REPORT",
        f"  Generated: {now}",
        "=" * 56,
        f"  Match  : {data['match']}",
        f"  Score  : {data['scores']}",
        f"  Status : {data['status']}",
    ]
    if data["crr"]:
        lines.append(f"  CRR    : {data['crr']}")
    if data["rrr"]:
        lines.append(f"  RRR    : {data['rrr']}")
    lines += ["  Source : cricbuzz.com", "=" * 56]
    report = "\n".join(lines)

    print("\n" + report)
    with open(REPORT_TXT, "w", encoding="utf-8") as fh:
        fh.write(report + "\n")

    new = not os.path.exists(HISTORY_CSV)
    with open(HISTORY_CSV, "a", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=["timestamp", "match", "scores", "status", "crr", "rrr"])
        if new:
            w.writeheader()
        w.writerow({"timestamp": now, **data})
    print(f"Saved: {REPORT_TXT}, {HISTORY_CSV} (appended), {SCREENSHOT}")


def main():
    with sync_playwright() as p:
        print("1. Launching Chromium...")
        browser = p.chromium.launch(headless=HEADLESS, slow_mo=200)
        page = browser.new_page(viewport={"width": 1366, "height": 900}, locale="en-IN")

        try:
            print(f"2. Opening {LIVE_URL}")
            page.goto(LIVE_URL, wait_until="domcontentloaded", timeout=45000)
            page.wait_for_selector("a[href*='/live-cricket-scores/']", state="attached", timeout=20000)

            matches = list_matches(page)
            print(f"3. Found {len(matches)} matches:")
            for i, m in enumerate(matches[:15], 1):
                print(f"   {i:>2}. {m['title']}")
            if not matches:
                raise ValueError("no matches listed")

            chosen = matches[0]
            if KEYWORD:
                hits = [m for m in matches
                        if KEYWORD in (m["title"] + " " + m["text"] + " " + m["slug"]).lower()]
                if not hits:
                    print(f"   No match found for '{KEYWORD}'. Using the first match instead.")
                else:
                    chosen = hits[0]
            print(f"4. Opening match: {chosen['title']}")

            link = page.locator(f"a[href='{chosen['href']}']:visible").first
            if link.count():
                link.click()
            else:  # link hidden in a menu: open its address directly
                page.goto(BASE + chosen["href"] if chosen["href"].startswith("/") else chosen["href"],
                          wait_until="domcontentloaded")
            page.wait_for_url("**/live-cricket-scores/**", timeout=20000)
            page.wait_for_load_state("domcontentloaded")
            page.wait_for_timeout(2000)  # let the live score widget fill in

            for update in range(1, (WATCH_UPDATES if WATCH else 1) + 1):
                print(f"5. Extracting live score{f' (update {update}/{WATCH_UPDATES})' if WATCH else ''}...")
                data = extract_score(page)
                page.screenshot(path=SCREENSHOT)
                save_report(data)
                if not WATCH or update == WATCH_UPDATES:
                    break
                print(f"\n   Refreshing in {REFRESH_SECONDS} s (Ctrl+C to stop)...")
                time.sleep(REFRESH_SECONDS)
                page.reload(wait_until="domcontentloaded")
                page.wait_for_timeout(2000)

        except KeyboardInterrupt:
            # Ctrl+C also stops Playwright's helper process, so closing the browser
            # normally would hang. Exit straight away instead.
            print("\nStopped by user.")
            os._exit(0)
        except (PWError, ValueError) as err:
            print(f"\nCould not read scores from Cricbuzz ({type(err).__name__}): {str(err).splitlines()[0]}")
            print("Check your internet connection, or there may be no matches listed right now.")
            page.screenshot(path="cricket_error.png")
            print("Saved what the browser saw to cricket_error.png")
        finally:
            browser.close()


if __name__ == "__main__":
    main()