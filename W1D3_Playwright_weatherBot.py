"""
Weather Report Bot - W1D3 Playwright Assignment

Steps:
    1. Launch Chromium
    2. Open a weather report website (timeanddate.com) for the chosen city
    3. Wait for the weather section, then extract the data
    4. Report the weather: print it, save a text report, append to a CSV
       history file, and save a screenshot of the page

If the main site's layout changes or it blocks the bot, the script falls back
to wttr.in, a simple weather site, so the report is still produced.

Run:  python weather_bot.py            (default city: Chennai)
      python weather_bot.py Bangalore
"""

import csv
import json
import os
import sys
from datetime import datetime
from playwright.sync_api import sync_playwright, Error as PWError

CITY = sys.argv[1] if len(sys.argv) > 1 else "Chennai"
COUNTRY = "india"
HEADLESS = os.environ.get("HEADLESS", "0") == "1"
MAIN_URL = os.environ.get("MAIN_URL", "https://www.timeanddate.com/weather/{country}/{city}")
BACKUP_URL = os.environ.get("BACKUP_URL", "https://wttr.in/{city}?format=j1")

REPORT_TXT = "weather_report.txt"
HISTORY_CSV = "weather_history.csv"
SCREENSHOT = "weather_page.png"


def clean(text):
    return " ".join(text.replace("\xa0", " ").split())


def from_timeanddate(page):
    """Extract weather from timeanddate.com's 'quick look' section."""
    url = MAIN_URL.format(country=COUNTRY, city=CITY.lower().replace(" ", "-"))
    print(f"2. Opening weather website: {url}")
    page.goto(url, wait_until="domcontentloaded", timeout=30000)

    print("3. Waiting for the weather section...")
    page.wait_for_selector("#qlook", state="visible", timeout=15000)
    page.screenshot(path=SCREENSHOT, full_page=False)

    qlook = page.locator("#qlook")
    lines = [clean(t) for t in qlook.locator("p").all_inner_texts() if clean(t)]
    data = {
        "temperature": clean(qlook.locator(".h2").first.inner_text()),
        "condition": lines[0].rstrip(".") if lines else "N/A",
        "feels_like": next((l.split(":", 1)[1].strip().split(" Forecast")[0]
                            for l in lines if l.startswith("Feels Like")), "N/A"),
    }

    # Facts table: Humidity, Pressure, Visibility, Dew Point...
    for row in page.locator("table.table--left tr").all():
        th, td = row.locator("th"), row.locator("td")
        if th.count() and td.count():
            key = clean(th.first.inner_text()).rstrip(":").lower()
            if key in ("humidity", "pressure", "visibility", "dew point"):
                data[key.replace(" ", "_")] = clean(td.first.inner_text())

    data["source"] = "timeanddate.com"
    return data


def from_wttr(page):
    """Backup: wttr.in returns weather as JSON, which the browser displays as text."""
    url = BACKUP_URL.format(city=CITY.replace(" ", "+"))
    print(f"   Trying backup weather website: {url}")
    page.goto(url, wait_until="domcontentloaded", timeout=30000)
    page.wait_for_selector("body", timeout=15000)
    page.screenshot(path=SCREENSHOT)
    w = json.loads(page.inner_text("body"))["current_condition"][0]
    return {
        "temperature": f'{w["temp_C"]} °C',
        "condition": w["weatherDesc"][0]["value"],
        "feels_like": f'{w["FeelsLikeC"]} °C',
        "humidity": f'{w["humidity"]}%',
        "pressure": f'{w["pressure"]} mbar',
        "visibility": f'{w["visibility"]} km',
        "wind": f'{w["windspeedKmph"]} km/h {w["winddir16Point"]}',
        "source": "wttr.in",
    }


def save_report(data):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    fields = ["temperature", "condition", "feels_like", "humidity",
              "pressure", "visibility", "dew_point", "wind"]

    lines = [
        "=" * 44,
        f"  WEATHER REPORT - {CITY.upper()}",
        f"  Generated: {now}",
        "=" * 44,
    ]
    for f in fields:
        if f in data:
            lines.append(f"  {f.replace('_', ' ').title():<12}: {data[f]}")
    lines += [f"  {'Source':<12}: {data['source']}", "=" * 44]
    report = "\n".join(lines)

    print("\n" + report)
    with open(REPORT_TXT, "w", encoding="utf-8") as fh:
        fh.write(report + "\n")

    new_file = not os.path.exists(HISTORY_CSV)
    with open(HISTORY_CSV, "a", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=["timestamp", "city"] + fields + ["source"])
        if new_file:
            writer.writeheader()
        writer.writerow({"timestamp": now, "city": CITY, **{f: data.get(f, "") for f in fields},
                         "source": data["source"]})

    print(f"\n4. Saved: {REPORT_TXT}, {HISTORY_CSV} (appended), {SCREENSHOT}")


def main():
    print(f"Weather Report Bot - city: {CITY}")
    with sync_playwright() as p:
        print("1. Launching Chromium...")
        browser = p.chromium.launch(headless=HEADLESS, slow_mo=200)
        page = browser.new_page(viewport={"width": 1366, "height": 900}, locale="en-IN")

        try:
            data = from_timeanddate(page)
        except (PWError, IndexError, ValueError) as err:
            print(f"   Main site did not work ({type(err).__name__}).")
            try:
                data = from_wttr(page)
            except (PWError, KeyError, ValueError) as err2:
                browser.close()
                print(f"\nCould not get the weather from either website ({type(err2).__name__}).")
                print("Check your internet connection and the city name, then try again.")
                sys.exit(1)

        browser.close()

    save_report(data)


if __name__ == "__main__":
    main()