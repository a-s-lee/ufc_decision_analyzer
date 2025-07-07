import re
import requests
from bs4 import BeautifulSoup
import pandas as pd

def scrape_event(url):
    """
    Scrape an MMA Decisions event page and extract:
    - Event name
    - Each fight's result
    - Method of decision
    - All 3 judges' names (even if unknown) and scores
    Returns a DataFrame.
    """
    # 1. Download the event page
    resp = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
    resp.encoding = "UTF-8"
    soup = BeautifulSoup(resp.text, "lxml")

    # 2. Extract event name (e.g., "UFC 107")
    raw_title_tag = soup.select_one("td.decision-top2 b")
    raw_title = raw_title_tag.get_text(strip=True) if raw_title_tag else ""
    m = re.match(r"^.*?\d+", raw_title)
    event = m.group(0) if m else raw_title

    # 3. Extract event year from date text
    td = soup.find('td', class_='decision-bottom2')
    year_match = re.search(r"\b(\d{4})\b", td.text if td else "")
    year = int(year_match.group(1)) if year_match else None

    records = []

    # 4. Loop over each bout in the card
    for fight_cell in soup.select("td.list2"):
        bout_tag = fight_cell.find("b")
        bout = bout_tag.get_text(strip=True) if bout_tag else ""

        method_tag = fight_cell.find("i")
        method = method_tag.get_text(strip=True) if method_tag else ""

        # Get the next 3 judge <td> cells
        judge_cells = fight_cell.find_next_siblings("td")[:3]

        for pos, jc in enumerate(judge_cells, start=1):
            name_tag = jc.find(["a", "b"])
            name = name_tag.get_text(strip=True) if name_tag else "Unknown"

            # Get score (normalize whitespace)
            raw_score = jc.find("span").get_text()
            score = " ".join(raw_score.split())

            records.append({
                "year":   year,
                "event":  event,
                "bout":   bout,
                "method": method,
                "judge":  name,
                "score":  score,
                "pos":    pos
            })

    # 5. Build DataFrame and deduplicate
    df = pd.DataFrame(records)
    df = df.drop_duplicates(
        subset=["event", "bout", "method", "judge", "score", "pos"],
        keep="first"
    )

    return df

if __name__ == "__main__":
    df = pd.read_csv('ufc_event_urls.csv')
    all_data = []

    for year, group in df.groupby("year"):
        print(f"\nStarting year {year} ({len(group)} events)")
        for event_index, url in enumerate(group['url'], start=1):
            try:
                event_df = scrape_event(url)
                all_data.append(event_df)
                print(f"Scraped Event #{event_index} Out Of {len(group)}")
            except Exception as e:
                print(f"Error scraping {url}: {e}")

    print(f"\nYou have scraped a total of {len(df)} events!")
    big_df = pd.concat(all_data, ignore_index=True)
    big_df = big_df.replace('\u00A0', ' ', regex=True)
    big_df.to_csv('ufc_scorecards.csv', index=False)
