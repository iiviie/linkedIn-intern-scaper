import asyncio
import random
import json
from playwright.async_api import async_playwright
from datetime import datetime
import csv
from typing import List, Dict
import time

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
            geolocation={'latitude': 40.7128, 'longitude': -74.0060},  # New York coordinates
        )

        # Additional stealth settings
        await context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
            Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]});
            Object.defineProperty(navigator, 'languages', {get: () => ['en-US', 'en']});
            window.chrome = { runtime: {} };
        """)

        # Load stored cookies if available
        try:
            with open("linkedin_cookies.json", "r") as f:
                cookies = json.load(f)
                await context.add_cookies(cookies)
        except FileNotFoundError:
            print("No stored cookies found")

        return playwright, browser, context

    async def simulate_human_behavior(self, page):
        """Simulate realistic user behavior"""
        # Random scroll
        await page.evaluate("""
            window.scrollTo({
                top: Math.floor(Math.random() * window.innerHeight),
                behavior: 'smooth'
            });
        """)
        
        await asyncio.sleep(random.uniform(2, 5))

        # Random mouse movements
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
        
        # Enable stealth mode
        await page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
        """)

        internships = []
        try:
            await page.goto(search_url)
            await asyncio.sleep(random.uniform(3, 5))

            while len(internships) < max_results:
                await self.simulate_human_behavior(page)

                # Extract job listings
                jobs = await page.query_selector_all(".job-card-container")
                
                for job in jobs:
                    if len(internships) >= max_results:
                        break
                        
                    job_data = {
                        "title": await job.query_selector(".job-title").inner_text(),
                        "company": await job.query_selector(".company-name").inner_text(),
                        "location": await job.query_selector(".job-location").inner_text(),
                        "link": await job.query_selector("a").get_attribute("href"),
                        "scraped_at": datetime.now().isoformat()
                    }
                    internships.append(job_data)

                # Click next page with random delay
                next_button = await page.query_selector("button.next-page")
                if not next_button:
                    break
                    
                await asyncio.sleep(random.uniform(2, 4))
                await next_button.click()

        finally:
            # Save cookies for future use
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
            # Go to LinkedIn login page
            await page.goto('https://www.linkedin.com/login')
            print("Please login manually in the browser window...")
            print("After logging in, press Enter in this console to continue...")
            
            # Wait for user input
            input()
            
            # Give extra time for session to establish
            await asyncio.sleep(3)
            
            # Save cookies
            cookies = await context.cookies()
            with open("linkedin_cookies.json", "w") as f:
                json.dump(cookies, f)
                print("Cookies saved successfully!")
                
        finally:
            await browser.close()
            await playwright.stop()

    def save_to_csv(self, internships: List[Dict], filename: str = "internships.csv"):
        """Save results to CSV file"""
        if not internships:
            return

        with open(filename, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=internships[0].keys())
            writer.writeheader()
            writer.writerows(internships)

async def main():
    scraper = LinkedInScraper()
    
    # First time setup - wait for manual login
    await scraper.login_and_save_cookies()
    
    # Now run the scraper
    search_url = "https://www.linkedin.com/jobs/search/?keywords=internship&location=United%20States"
    internships = await scraper.scrape_internships(search_url, max_results=50)
    scraper.save_to_csv(internships)

if __name__ == "__main__":
    asyncio.run(main()) 