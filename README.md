# Agoda Hotel Search Scraper

Python automation for collecting structured hotel-search results from Agoda and exporting them to Excel.

## How it works

1. Opens the configured search URL in Chrome through Selenium Wire.
2. Captures the browser's GraphQL search request and reuses its headers and payload with a requests session.
3. Detects whether the URL is configured for a city, area, or region search.
4. Reads the total result count and paginates through the available search results.
5. Collects hotel-level attributes and writes the combined dataset to an Excel workbook.

## Data collected

The output records may include:

- Hotel/property ID and display name
- Star rating, area, and city fields returned by Agoda
- Latitude and longitude, plus a Google Maps query link
- Review score and review count
- Displayed price per room per night
- Hotel property-page URL

Values that are not present in the response are represented as N/A by the script's safe getter.

## Files

- Agoda Scraper.py — scraper entry point
- requirements.txt — Python package list
- README.md — project documentation

## Requirements

- Python 3.10 or a compatible version
- Google Chrome installed
- A Selenium/Selenium Wire-compatible ChromeDriver setup
- Packages in requirements.txt

## Setup

Create and activate a virtual environment in PowerShell:

    python -m venv .venv
    .venv/Scripts/Activate.ps1
    pip install -r requirements.txt

## Configuration and run

At the top of Agoda Scraper.py, review:

- URL — the Agoda search URL, including search target and check-in/check-out parameters
- OUTPUT_FILE — the Excel output path

Run:

    python "Agoda Scraper.py"

The script writes the workbook to the configured OUTPUT_FILE.

**Output-path note:** the current script calls os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True). If OUTPUT_FILE is only a filename with no directory, os.path.dirname is empty; configure a directory in OUTPUT_FILE or guard the directory-creation call before running.

## Operational notes

- Agoda's page behavior, GraphQL payload, and response schema can change; a captured request or expected field may no longer be available.
- Search URL dates and location parameters are configuration values, not a guarantee of data availability.
- Use browser automation and collected data only in ways permitted by the target site's terms and applicable policies.
- Do not commit browser cookies, private session data, or credentials.

## Synthetic sample data

[`sample_synthetic_12_records.csv`](sample_synthetic_12_records.csv) contains **12 synthetic test records** with the output columns used by this scraper. The rows were generated for schema inspection and portfolio/demo purposes; they were not collected from the source website or API. Names and addresses are fictional, contact details and example.com links are placeholders, coordinates are illustrative, and any ratings/prices/amenities are not real or current. Do not use these records for navigation, operational decisions, or market/pricing analysis.
