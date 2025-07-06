import re                                    # for regular expression matching
import requests                              # to download HTML from the web
from bs4 import BeautifulSoup                # to parse the downloaded HTML
import pandas as pd                          # to build and write out our table

def scrape_event(url):
    """
    Download an MMA Decisions event page and extract:
      - event name (truncated to the first number)
      - each fight's bout text
      - method of victory (Unanimous/Split/Majority)
      - each judge's name and score
    Returns a pandas DataFrame with columns:
      event, bout, method, judge, score
    """

    # --- 1) Download the page ---
    resp = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
    resp.encoding = "UTF-8"

    # Parse HTML into a BeautifulSoup "soup" object
    soup = BeautifulSoup(resp.text, "lxml")


    # --- 2) Extract and normalize the event title ---
    # The full title lives in a <td class="decision-top2"><b>…</b> element
    raw_title_tag = soup.select_one("td.decision-top2 b") # select_one () selects first instance of td.decision-t..
    raw_title = raw_title_tag.get_text(strip=True) if raw_title_tag else "" # Get the tag’s text (trimmed of extra whitespace) if it exists, otherwise set as empty string

    # Use a regex to keep everything up through the first digit sequence:
    #   r"^.*?\d+" means "from start, lazily match chars until a digit, then consume all digits"
    m = re.match(r"^.*?\d+", raw_title)
    event = m.group(0) if m else raw_title
    # Examples:
    #   "UFC on ABC 8: Hill vs..."  → "UFC on ABC 8"
    #   "UFC 317: Topuria vs..."    → "UFC 317"
    #   "UFC on ESPN 69: Usman vs." → "UFC on ESPN 69"


    records = []  # we'll accumulate one dict per (bout, judge) row here


    # --- 3) Loop over every fight in the card ---
    # Each fight/bout is in a <td class="list2"> cell
    for fight_cell in soup.select("td.list2"):

        # a) Bout description = the <b>…</b> inside the cell
        bout_tag = fight_cell.find("b")
        bout = bout_tag.get_text(strip=True) if bout_tag else ""

        # b) Method (Unanimous/Split/Majority) = the <i>…</i> inside the cell
        method_tag = fight_cell.find("i")
        method = method_tag.get_text(strip=True) if method_tag else ""


        # --- 4) Grab the three judge cells for *this* fight row ---
        # They sit immediately after the <td class="list2">, as <td> siblings.
        # Some pages mark one of them with class="selected" instead of "list",
        # so we just grab the next three <td> tags, regardless of class.
        judge_cells = fight_cell.find_next_siblings("td")[:3]

        for jc in judge_cells:
            # Judge name is in the <a>…</a> inside that cell
            name = jc.find("a").get_text(strip=True)

            # Score text is in the <span>…</span>. It may contain extra
            # spaces or newlines, so we split on any whitespace and re-join.
            raw_score = jc.find("span").get_text()
            score = " ".join(raw_score.split())

            # Add our row to the list
            records.append({
                "event":  event,
                "bout":   bout,
                "method": method,
                "judge":  name,
                "score":  score
            })


    # --- 5) Build a DataFrame and clean up duplicates ---
    df = pd.DataFrame(records)

    # In case the same judge+ bout ever got recorded twice, drop duplicates:
    df = df.drop_duplicates(
        subset=["event", "bout", "method", "judge"],
        keep="first"
    )

    return df


if __name__ == "__main__":
    # Example usage: point at any MMADecisions event page
    df = pd.read_csv('ufc_event_urls.csv')
    all_data = []
    # Scrape into a DataFrame    
    for year, group in df.groupby("year"):
        print(f"\nStarting year {year} ( {len(group)} events )")

        for event_index, url in enumerate(group['url'], start=1):
            try: 
                event_df = scrape_event(url)
                all_data.append(event_df)
                print(f"Scraped Event #{event_index} Out Of {len(group)}")
            except Exception as e:
                print(f"Errpr scraping {url}: {e}")
    
    print(f"You have scraped a total of {len(df)} events!")    
    big_df = pd.concat(all_data, ignore_index=False)
    big_df = big_df.replace('\u00A0', ' ', regex=True)
    big_df.to_csv('ufc_scorecards.csv', index=False)
