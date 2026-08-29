"""
Playwright scraper skeleton for an OTA site (example structure — you MUST
inspect the actual site in DevTools > Network tab first and adjust selectors
and/or switch to calling their internal JSON API directly if you find one).

Before running: pip install playwright && playwright install chromium
"""

import asyncio
from datetime import date, timedelta
from playwright.async_api import async_playwright

ROUTES = [("DEL", "BOM"), ("DEL", "BLR")]
ADVANCE_DAYS = [1, 7, 15, 30, 45]


async def scrape_route(page, origin, destination, travel_date):
    """
    Example flow — adjust selectors to match the actual site's HTML/DOM.
    Step 1: Always check DevTools > Network tab for a JSON API call first.
    If found, skip browser automation entirely and call that endpoint with
    httpx/requests — it's faster and far more stable than DOM scraping.
    """
    url = f"https://example-ota.com/flights/{origin}-{destination}?date={travel_date}"
    await page.goto(url, wait_until="networkidle")

    # Ethical scraping: respect a reasonable delay between actions
    await page.wait_for_timeout(2000)

    # Example selector — REPLACE with the real site's structure after inspecting it
    fare_cards = await page.query_selector_all(".flight-result-card")

    results = []
    for card in fare_cards:
        try:
            carrier = await (await card.query_selector(".airline-name")).inner_text()
            total_fare_text = await (await card.query_selector(".fare-amount")).inner_text()
            total_fare = float(total_fare_text.replace("₹", "").replace(",", "").strip())

            results.append({
                "origin": origin,
                "destination": destination,
                "travel_date": travel_date,
                "carrier": carrier.strip(),
                "total_fare": total_fare,
                "source_site": "example_ota",
            })
        except Exception:
            continue  # skip malformed cards (sold out, ads, etc.)

    return results


async def main():
    search_date = date.today()
    all_results = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        # Rotate a realistic user agent — basic anti-bot courtesy, not full evasion
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        )
        page = await context.new_page()

        for origin, destination in ROUTES:
            for advance_days in ADVANCE_DAYS:
                travel_date = search_date + timedelta(days=advance_days)
                try:
                    results = await scrape_route(page, origin, destination, travel_date)
                    all_results.extend(results)
                    print(f"Scraped {len(results)} fares: {origin}-{destination} T+{advance_days}")
                except Exception as e:
                    print(f"Failed: {origin}-{destination} T+{advance_days}: {e}")

                # Rate limiting between requests — ethical scraping requirement from PS
                await page.wait_for_timeout(3000)

        await browser.close()

    # TODO: save all_results to Postgres using the same save_to_db pattern
    # as fetch_amadeus.py, adding advance_purchase_days + search_date + base/tax split
    return all_results


if __name__ == "__main__":
    asyncio.run(asyncio.get_event_loop().run_until_complete(main()) if False else main())
