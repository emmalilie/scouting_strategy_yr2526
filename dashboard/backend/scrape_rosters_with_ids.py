import requests
from bs4 import BeautifulSoup
import pandas as pd
import re
import time
import logging
from urllib.parse import urljoin

logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")
log = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    )
}

# Matches Sidearm card URLs:  /sports/mens-tennis/roster/name/12345
#                              /sport/mten/roster/name/12345
PROFILE_RE = re.compile(r"/(?:sports/mens-tennis|sport/mten)/roster/([^/]+)/(\d+)", re.I)

YEAR_ABBREVS = {
    "freshman": "Fr", "fr": "Fr",
    "sophomore": "So", "so": "So",
    "junior": "Jr", "jr": "Jr",
    "senior": "Sr", "sr": "Sr",
    "graduate": "Grad", "grad": "Grad",
    "5th year": "Grad", "fifth year": "Grad",
}

SCHOOLS = {
    "ucla":          ("https://uclabruins.com",       "https://uclabruins.com/sports/mens-tennis/roster"),
    "usc":           ("https://usctrojans.com",        "https://usctrojans.com/sports/mens-tennis/roster"),
    "michigan":      ("https://mgoblue.com",           "https://mgoblue.com/sports/mens-tennis/roster"),
    "ohio_state":    ("https://ohiostatebuckeyes.com", "https://ohiostatebuckeyes.com/sports/mens-tennis/roster"),
    "indiana":       ("https://iuhoosiers.com",        "https://iuhoosiers.com/sports/mens-tennis/roster"),
    "illinois":      ("https://fightingillini.com",    "https://fightingillini.com/sports/mens-tennis/roster"),
    "northwestern":  ("https://nusports.com",          "https://nusports.com/sports/mens-tennis/roster"),
    "wisconsin":     ("https://uwbadgers.com",         "https://uwbadgers.com/sports/mens-tennis/roster"),
    "michigan_state":("https://msuspartans.com",       "https://msuspartans.com/sports/mens-tennis/roster"),
}

import os
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROSTERS_DIR = os.path.join(SCRIPT_DIR, "rosters")
os.makedirs(ROSTERS_DIR, exist_ok=True)


def fetch_html(url):
    for attempt in range(3):
        try:
            r = requests.get(url, headers=HEADERS, timeout=15)
            r.raise_for_status()
            return r.text
        except Exception as e:
            log.warning(f"Attempt {attempt+1} failed for {url}: {e}")
            time.sleep(2 ** attempt)
    return None


def extract_name(link, slug):
    for tag in ("h2", "h3", "h4"):
        h = link.find(tag)
        if h:
            text = h.get_text(" ", strip=True)
            if text and len(text) > 2:
                return text
    for elem in link.find_all(True):
        cls = " ".join(elem.get("class", []))
        if "name" in cls.lower():
            text = elem.get_text(" ", strip=True)
            if text and len(text) > 2:
                return text
    text = link.get_text(" ", strip=True)
    if text and len(text) > 2 and not text.isdigit():
        return text
    return slug.replace("-", " ").title()


def extract_year(card):
    if card is None:
        return "N/A"
    year_re = re.compile(r"academic.year|class.year|eligibility|year.in.school", re.I)
    elem = card.find(class_=year_re)
    if elem:
        text = elem.get_text(strip=True).lower().rstrip(".")
        return YEAR_ABBREVS.get(text, text.title())
    return "N/A"


def extract_hometown(card):
    if card is None:
        return "N/A"
    ht_re = re.compile(r"hometown|home.city|high.school", re.I)
    elem = card.find(class_=ht_re)
    if elem:
        return elem.get_text(strip=True)
    return "N/A"


def find_card(link):
    card_re = re.compile(r"roster.player|player.card|athlete|s-person", re.I)
    node = link.parent
    for _ in range(6):
        if node is None:
            break
        cls = " ".join(node.get("class", []))
        if card_re.search(cls):
            return node
        node = node.parent
    return link.parent


def scrape_roster(school_key, base_url, roster_url):
    html = fetch_html(roster_url)
    if not html:
        return []

    soup = BeautifulSoup(html, "html.parser")
    players = []
    seen = set()

    # --- Strategy 1: Card/grid layout (standard Sidearm) ---
    for link in soup.find_all("a", href=PROFILE_RE):
        href = link.get("href", "")
        m = PROFILE_RE.search(href)
        if not m:
            continue
        slug, player_id = m.group(1), m.group(2)
        if player_id in seen:
            continue
        seen.add(player_id)

        profile_url = href if href.startswith("http") else urljoin(base_url, href)
        card = find_card(link)

        players.append({
            "Player":         extract_name(link, slug),
            "Year":           extract_year(card),
            "Hometown":       extract_hometown(card),
            "UTR":            "N/A",
            "Singles_Record": "0-0",
            "Doubles_Record": "0-0",
            "Profile_URL":    profile_url,
            "UTR_URL":        "N/A",
        })

    # --- Strategy 2: Table layout fallback ---
    if len(players) <= 2:
        log.warning(f"  Only {len(players)} found via cards for {school_key}, trying table fallback...")
        for table in soup.find_all("table"):
            rows = table.find_all("tr")
            if len(rows) < 3:
                continue
            for row in rows[1:]:
                link = row.find("a", href=PROFILE_RE)
                if not link:
                    continue
                href = link.get("href", "")
                m = PROFILE_RE.search(href)
                if not m:
                    continue
                slug, player_id = m.group(1), m.group(2)
                if player_id in seen:
                    continue
                seen.add(player_id)

                profile_url = href if href.startswith("http") else urljoin(base_url, href)
                name = extract_name(link, slug)

                cols = [td.get_text(strip=True) for td in row.find_all("td")]
                year = "N/A"
                hometown = "N/A"
                for col in cols:
                    mapped = YEAR_ABBREVS.get(col.lower().rstrip("."), "")
                    if mapped:
                        year = mapped
                    if re.match(r'^[A-Za-z\s]+,\s*[A-Z]{2}', col):
                        hometown = col

                players.append({
                    "Player":         name,
                    "Year":           year,
                    "Hometown":       hometown,
                    "UTR":            "N/A",
                    "Singles_Record": "0-0",
                    "Doubles_Record": "0-0",
                    "Profile_URL":    profile_url,
                    "UTR_URL":        "N/A",
                })

    return players


def main():
    summary = []
    for school_key, (base_url, roster_url) in SCHOOLS.items():
        log.info(f"\n{'='*60}")
        log.info(f"Scraping {school_key.upper().replace('_', ' ')} ...")
        log.info(f"URL: {roster_url}")

        try:
            players = scrape_roster(school_key, base_url, roster_url)

            if players:
                log.info(f"Found {len(players)} players:")
                for p in players:
                    log.info(f"  {p['Player']} ({p['Year']}) - {p['Profile_URL']}")

                df = pd.DataFrame(players, columns=[
                    "Player", "Year", "Hometown", "UTR",
                    "Singles_Record", "Doubles_Record", "Profile_URL", "UTR_URL"
                ])
                path = os.path.join(ROSTERS_DIR, f"{school_key}_roster.csv")
                df.to_csv(path, index=False)
                log.info(f"Saved -> {path}")
                summary.append((school_key, len(players)))
            else:
                log.warning(f"No players found for {school_key}")
                summary.append((school_key, 0))

        except Exception as e:
            log.exception(f"Error scraping {school_key}: {e}")
            summary.append((school_key, 0))

        time.sleep(1.5)

    log.info(f"\n{'='*60}")
    log.info("SUMMARY:")
    for school, count in summary:
        log.info(f"  {school:<20} {count} players")


if __name__ == "__main__":
    main()