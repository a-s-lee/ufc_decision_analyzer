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
    # strip=True trims whitespace else statement returns "" if no tag is found
    event = raw_title_tag.get_text(strip=True) if raw_title_tag else ""

    # 3. Extract event year from date text
    td = soup.find('td', class_='decision-bottom2')
    year_match = re.search(r"\b(\d{4})\b", td.text if td else "")
    # Converts to int
    year = int(year_match.group(1)) if year_match else None

    records = []

    # 4. Loop over each bout in the card
    for fight_cell in soup.select("td.list2"):
        bout_tag = fight_cell.find("b")
        bout = bout_tag.get_text(strip=True) if bout_tag else ""

        method_tag = fight_cell.find("i")
        method = method_tag.get_text(strip=True) if method_tag else ""

        # Get the next 3 judge <td> cells and stores in list
        judge_cells = fight_cell.find_next_siblings("td")[:3]

        # Loops through the <td> tags in judge_cells (judge name + score), and giving each one a position number 
        for pos, jc in enumerate(judge_cells, start=1):
            # Find the judge's name — sometimes it’s inside an <a>, sometimes a <b>.
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

    # 5. Converts dicts to dataframe
    df = pd.DataFrame(records)
    df = df.drop_duplicates(
        subset=["event", "bout", "method", "judge", "score", "pos"],
        keep="first"
    )

    return df

if __name__ == "__main__":
    df = pd.read_csv('ufc_event_urls.csv')

    all_data = []

    # iterate in CSV order from row 0 → end
    for idx, row in df.iterrows():
        url = row['url']
        year = row['year']
        title = row['title']

        print(f"Scraping row #{idx+1}: {title} ({year})")

        try:
            event_df = scrape_event(url)
            all_data.append(event_df)
        except Exception as e:
            print(f"Error scraping {url}: {e}")

    print(f"\nYou have scraped a total of {len(df)} events!")
    big_df = pd.concat(all_data, ignore_index=True)
    big_df = big_df.replace('\u00A0', ' ', regex=True)
    big_df.to_csv('ufc_scorecards.csv', index=False)
