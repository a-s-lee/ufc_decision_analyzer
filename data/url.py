import re                              # for working with regular expressions
import requests                        # to download web pages
from bs4 import BeautifulSoup          # to parse HTML and navigate the document
from urllib.parse import urljoin       # to build full URLs from relative paths
import csv                             # to write our results into a CSV file

def get_ufc_event_urls_for_year(year):
    """
    Fetches the archive page for a given year and returns a list of
    (event title, full event URL) for every UFC event listed.
    """
    base = "https://mmadecisions.com"  # root URL of the site
    archive_url = f"{base}/decisions-by-event/{year}/"  
    # e.g. "https://mmadecisions.com/decisions-by-event/2025/"

    # -- Download the page --
    resp = requests.get(
        archive_url,
        headers={"User-Agent": "Mozilla/5.0"}  # pretend to be a normal browser
    )

    # -- Determine and set the correct character encoding --
    # Look for "charset=XYZ" in the HTTP response headers
    ctype = resp.headers.get("Content-Type", "")
    match = re.search(r"charset=([^;]+)", ctype)
    if match:
        # If the server told us the charset, use it
        resp.encoding = match.group(1)
    else:
        # Otherwise let requests guess the best encoding
        resp.encoding = resp.apparent_encoding

    # -- Parse the downloaded HTML --
    soup = BeautifulSoup(resp.text, "lxml")

    results = []  # will hold our (title, url) pairs

    # -- Loop over each table row that represents an event --
    for row in soup.select("tr.decision"):
        # Inside that row, find the link in the "Event" column
        link = row.select_one("td.list a")
        if not link:
            # If for some reason there's no <a> tag, skip this row
            continue

        title = link.get_text(strip=True)  # e.g. "UFC 317: Topuria vs. Oliveira"
        href = link["href"]                # e.g. "event/1559/UFC-317-Topuria-vs-Oliveira"

        # Only keep events whose title starts with "UFC"
        if title.startswith("UFC"):
            # Convert the relative path into a full URL
            full_url = urljoin(base, href)
            results.append((title, full_url))

    # Remove duplicates while preserving order
    return list(dict.fromkeys(results))


if __name__ == "__main__":
    # -- Configuration: years you want to scrape --
    years = range(2024, 2026)  # change this range as needed

    # -- Open (or create) the CSV file for writing --
    with open("ufc_event_urls.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        # Write the header row
        writer.writerow(["year", "title", "url"])

        # For each year, fetch its UFC event URLs and write them out
        for yr in years:
            for title, url in get_ufc_event_urls_for_year(yr):
                writer.writerow([yr, title, url])

    # Print a simple confirmation
    print(f"Saved UFC event URLs for years {years.start}-{years.stop - 1} to ufc_event_urls.csv")
