# LinkedIn Internship Scraper

A Python-based scraper that monitors LinkedIn for new internship postings and saves them to a CSV file. Built with Playwright for reliable web automation.

## Features

- Monitors multiple search URLs simultaneously
- Saves results to CSV with deduplication
- Handles LinkedIn authentication via cookies
- Uses rotating user agents and anti-detection measures
- Configurable search intervals and result limits

## Prerequisites

- Python 3.8+
- pip

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd linkedin-internship-scraper
```

2. Create and activate a virtual environment:
```bash
python -m venv venv

# On Windows
venv\Scripts\activate

# On macOS/Linux
source venv/bin/activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Install Playwright browsers:
```bash
playwright install chromium
```

## Configuration

1. Edit the `SEARCH_URLS` list in `linkedin_scraper.py` to customize your search queries:
```python
SEARCH_URLS = [
    "https://www.linkedin.com/jobs/search/?keywords=python%20developer%20internship&f_TPR=r604800&location=India",
    "https://www.linkedin.com/jobs/search/?keywords=django%20developer%20internship&f_TPR=r604800&location=India",
]
```

## Usage

1. First-time setup (login to LinkedIn):
```bash
python linkedin_scraper.py
```
- A browser window will open
- Log in to your LinkedIn account
- Press Enter in the console to save your login cookies

2. The scraper will automatically:
- Monitor the configured search URLs
- Check for new internships every 5 minutes
- Save results to `internships.csv`
- Skip duplicate listings

## Output Format

The scraper saves internships to `internships.csv` with the following fields:
- title
- company
- location
- link
- scraped_at

## Notes

- The script uses a non-headless browser to avoid detection
- Login cookies are saved locally in `linkedin_cookies.json`
- Default check interval is 300 seconds (5 minutes)
- Adjust `max_results` in `monitor_internships()` to control the number of listings to fetch

