import asyncio
import random
import json
from playwright.async_api import async_playwright
from datetime import datetime
import csv
from typing import List, Dict
import os

class LinkedInScraper:
    def __init__(self):
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
        ]

    async def init_browser(self):
        playwright = await async_playwright().start()
        browser = await playwright.chromium.launch(
            headless=False,
            args=[
                '--disable-blink-features=AutomationControlled',
                '--no-sandbox',
                '--disable-web-security',
                '--disable-features=IsolateOrigins,site-per-process'
            ]
        )
        context = await browser.new_context(
            user_agent=random.choice(self.user_agents),
            viewport={"width": 1920, "height": 1080},
            java_script_enabled=True,
            extra_http_headers={"Accept-Language": "en-US,en;q=0.9"},
            bypass_csp=True,
            permissions=['geolocation'],
            geolocation={'latitude': 28.6139, 'longitude': 77.2090},
        )
        await context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
            Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]});
            Object.defineProperty(navigator, 'languages', {get: () => ['en-US', 'en']};
            window.chrome = { runtime: {} };
        """)
        try:
            with open("linkedin_cookies.json", "r") as f:
                cookies = json.load(f)
                await context.add_cookies(cookies)
        except FileNotFoundError:
            print("No stored cookies found")
        return playwright, browser, context

    async def scrape_internships(self, search_url: str, max_results: int = 20) -> List[Dict]:
        playwright, browser, context = await self.init_browser()
        page = await context.new_page()
        internships = []
        try:
            page_number = 0
            while len(internships) < max_results:
                current_url = search_url
                if page_number > 0:
                    current_url = f"{search_url}&start={page_number * 25}"
                print(f"\nNavigating to page {page_number + 1}: {current_url}")
                await page.goto(current_url)
                await asyncio.sleep(random.uniform(3, 5))
                
                await page.evaluate("""
                    const container = document.querySelector('ul.ffbbjNmknqAXhulEufUCQfHWdANElJtnLXXALA');
                    if (container) {
                        container.scrollIntoView({ behavior: 'smooth', block: 'end' });
                    }
                """)
                
                for _ in range(10):
                    await asyncio.sleep(1)
                    jobs = await page.query_selector_all("div.job-card-container.relative.job-card-list")
                    if len(jobs) >= 25:
                        break
                print(f"Found {len(jobs)} job cards on current page")
                if not jobs:
                    print("No more job cards found")
                    break
                for job in jobs:
                    if len(internships) >= max_results:
                        break
                    try:
                        title_elem = await job.query_selector(".job-card-list__title--link span strong")
                        company_elem = await job.query_selector(".artdeco-entity-lockup__subtitle span")
                        location_elem = await job.query_selector(".job-card-container__metadata-wrapper li span")
                        link_elem = await job.query_selector(".job-card-list__title--link")
                        if all([title_elem, company_elem, location_elem, link_elem]):
                            job_data = {
                                "title": (await title_elem.inner_text()).strip(),
                                "company": (await company_elem.inner_text()).strip(),
                                "location": (await location_elem.inner_text()).strip(),
                                "link": await link_elem.get_attribute("href"),
                                "scraped_at": datetime.now().isoformat()
                            }
                            internships.append(job_data)
                            self.save_to_csv([job_data], "internships.csv")
                    except Exception as e:
                        continue
                page_number += 1
                total_results = await page.query_selector(".jobs-search-results-list__subtitle")
                if total_results:
                    total_text = await total_results.inner_text()
                    if "25" in total_text and page_number * 25 >= int(total_text.split()[0]):
                        break
        finally:
            cookies = await context.cookies()
            with open("linkedin_cookies.json", "w") as f:
                json.dump(cookies, f)
            await browser.close()
            await playwright.stop()
        return internships

    async def login_and_save_cookies(self):
        playwright, browser, context = await self.init_browser()
        page = await context.new_page()
        try:
            await page.goto('https://www.linkedin.com/login')
            print("Please login manually in the browser window...")
            print("After logging in, press Enter in this console to continue...")
            input()
            await asyncio.sleep(3)
            cookies = await context.cookies()
            with open("linkedin_cookies.json", "w") as f:
                json.dump(cookies, f)
        finally:
            await browser.close()
            await playwright.stop()

    def save_to_csv(self, internships: List[Dict], filename: str = "internships.csv"):
        if not internships:
            return
        try:
            file_exists = os.path.exists(filename)
            with open(filename, "a", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=internships[0].keys())
                if not file_exists:
                    writer.writeheader()
                writer.writerows(internships)
        except Exception as e:
            print(f"Error saving to CSV: {e}")

    async def monitor_internships(self, search_urls: List[str], check_interval: int = 300):
        seen_jobs = set()
        while True:
            print("\n=== Starting new monitoring cycle ===")
            for url in search_urls:
                try:
                    print(f"\nSearching URL: {url}")
                    internships = await self.scrape_internships(url, max_results=100)
                    new_jobs = 0
                    for job in internships:
                        job_id = f"{job['title']}_{job['company']}_{job['location']}"
                        if job_id not in seen_jobs:
                            seen_jobs.add(job_id)
                            new_jobs += 1
                            self.save_to_csv([job], "internships.csv")
                    print(f"Found {new_jobs} new internships in this search")
                except Exception as e:
                    continue
                await asyncio.sleep(random.uniform(5, 10))
            await asyncio.sleep(check_interval)

SEARCH_URLS = [
    "https://www.linkedin.com/jobs/search/?keywords=python%20developer%20internship&f_TPR=r604800&location=India",
    "https://www.linkedin.com/jobs/search/?keywords=django%20developer%20internship&f_TPR=r604800&location=India",
    "https://www.linkedin.com/jobs/search/?keywords=backend%20developer%20internship&f_TPR=r604800&location=India"
]

async def main():
    scraper = LinkedInScraper()
    await scraper.login_and_save_cookies()
    await scraper.monitor_internships(
        search_urls=SEARCH_URLS,
        check_interval=300
    )

if __name__ == "__main__":
    asyncio.run(main())