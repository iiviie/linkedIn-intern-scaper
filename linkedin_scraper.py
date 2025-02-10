import asyncio
import random
import json
from playwright.async_api import async_playwright
from datetime import datetime
import csv
from typing import List, Dict
import time
import os

class LinkedInScraper:
    def __init__(self):
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
        ]

    async def init_browser(self):
        """Initialize browser with stealth settings"""
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
            geolocation={'latitude': 28.6139, 'longitude': 77.2090},  #New Delhi coordinates
        )

        await context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
            Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]});
            Object.defineProperty(navigator, 'languages', {get: () => ['en-US', 'en']});
            window.chrome = { runtime: {} };
        """)

        try:
            with open("linkedin_cookies.json", "r") as f:
                cookies = json.load(f)
                await context.add_cookies(cookies)
        except FileNotFoundError:
            print("No stored cookies found")

        return playwright, browser, context

    async def simulate_human_behavior(self, page):
        """Simulate realistic user behavior"""
        await page.evaluate("""
            window.scrollTo({
                top: Math.floor(Math.random() * window.innerHeight),
                behavior: 'smooth'
            });
        """)
        
        await asyncio.sleep(random.uniform(2, 5))

        for _ in range(random.randint(3, 7)):
            await page.mouse.move(
                random.randint(0, 1920),
                random.randint(0, 1080)
            )
            await asyncio.sleep(random.uniform(0.1, 0.3))

    async def scrape_internships(self, search_url: str, max_results: int = 20) -> List[Dict]:
        """Main scraping function"""
        playwright, browser, context = await self.init_browser()
        page = await context.new_page()
        
        internships = []
        try:
            await page.goto(search_url)
            await asyncio.sleep(random.uniform(3, 5))

            while len(internships) < max_results:
                await self.simulate_human_behavior(page)

                # Updated selector for job cards
                jobs = await page.query_selector_all("div.job-card-container.relative.job-card-list")
                print(f"Found {len(jobs)} job cards on current page")
                
                for job in jobs:
                    if len(internships) >= max_results:
                        break
                        
                    try:
                        print("\nAttempting to extract job data...")
                        # Updated selectors to match exact HTML structure
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
                            print(f"Found job: {job_data['title']} at {job_data['company']}")
                    except Exception as e:
                        print(f"Error extracting job data: {e}")
                        continue

                next_button = await page.query_selector("button[aria-label='Next']")
                if not next_button:
                    print("No more pages to scrape")
                    break
                    
                await asyncio.sleep(random.uniform(2, 4))
                await next_button.click()

        finally:
            cookies = await context.cookies()
            with open("linkedin_cookies.json", "w") as f:
                json.dump(cookies, f)

            await browser.close()
            await playwright.stop()

        return internships

    async def login_and_save_cookies(self):
        """Open browser and wait for manual login"""
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
                print("Cookies saved successfully!")
                
        finally:
            await browser.close()
            await playwright.stop()

    def save_to_csv(self, internships: List[Dict], filename: str = "internships.csv"):
        """Save results to CSV file in append mode"""
        if not internships:
            print("No internships to save")
            return

        try:
            print(f"Attempting to save to {os.path.abspath(filename)}")  # Debug print
            file_exists = os.path.exists(filename)
            
            with open(filename, "a", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=internships[0].keys())
                if not file_exists:
                    writer.writeheader()
                    print(f"Created new CSV file: {filename}")
                writer.writerows(internships)
                print(f"Saved {len(internships)} new internships to {filename}")
                
        except Exception as e:
            print(f"Error saving to CSV: {e}")

    async def monitor_internships(self, search_urls: List[str], check_interval: int = 300):
        """Continuously monitor for new internships"""
        seen_jobs = set()  
        
        while True:
            print("\n=== Starting new monitoring cycle ===")
            for url in search_urls:
                try:
                    print(f"\nSearching URL: {url}")
                    internships = await self.scrape_internships(url, max_results=100)
                    print(f"Found {len(internships)} total internships on this search")
                    
                    new_jobs = 0
                    for job in internships:
                        job_id = f"{job['title']}_{job['company']}_{job['location']}"
                        if job_id not in seen_jobs:
                            seen_jobs.add(job_id)
                            new_jobs += 1
                            print("\n🆕 New Internship Found!")
                            print(f"Title: {job['title']}")
                            print(f"Company: {job['company']}")
                            print(f"Location: {job['location']}")
                            print(f"Link: {job['link']}")
                            print("=" * 50)
                            
                            self.save_to_csv([job], "internships.csv")
                    
                    print(f"Found {new_jobs} new internships in this search")
                    
                except Exception as e:
                    print(f"Error during scraping: {e}")
                    continue
                
                await asyncio.sleep(random.uniform(5, 10))
                
            print(f"\nWaiting {check_interval/60} minutes before next check...")
            await asyncio.sleep(check_interval)

SEARCH_URLS = [
    "https://www.linkedin.com/jobs/search/?keywords=django%20developer%20internship&f_TPR=r604800&location=India",
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