"""
scrape_all_rosters.py
=====================
Scrapes men's tennis rosters for UCLA, USC, and Big Ten schools.
For each player collects:
  - Name
  - Year in school (Fr / So / Jr / Sr / Grad)
  - Season year (e.g. 2025-26)
  - School profile URL (with numeric ID)
  - UTR profile URL
  - UTR rating (singles)
  - Season singles record (W-L)
  - Season doubles record (W-L)
  - Hometown / High School

All schools use the Sidearm Sports CMS, so one robust parser handles them all.
UCLA and USC stats pages are on static subdomains; the rest follow the same pattern.

Usage:
    python scrape_all_rosters.py

Output:
    rosters/<school>_roster.csv  for each school
    rosters/all_rosters.csv      combined file
"""

import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import re
import json
import os
import logging
from urllib.parse import urljoin, urlparse

logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")
log = logging.getLogger(__name__)

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROSTERS_DIR = os.path.join(SCRIPT_DIR, "rosters")
os.makedirs(ROSTERS_DIR, exist_ok=True)

SEASON = "2025-26"
SEASON_STATS_YEAR = "2025-26"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}

# ---------------------------------------------------------------------------
# School configuration
# Each entry: school_key -> dict with:
#   roster_url  : main roster page
#   stats_url   : cumulative stats HTML (Sidearm static page)
#   base_url    : domain root used for building absolute URLs
# ---------------------------------------------------------------------------
SCHOOLS = {
    "ucla": {
        "display": "UCLA Bruins",
        "roster_url": "https://uclabruins.com/sports/mens-tennis/roster",
        "stats_url": "https://static.uclabruins.com/custompages/Stats/2025-26/MTEN/teamcume.htm",
        "base_url": "https://uclabruins.com",
    },
    "usc": {
        "display": "USC Trojans",
        "roster_url": "https://usctrojans.com/sports/mens-tennis/roster",
        "stats_url": "https://static.usctrojans.com/custompages/Stats/2025-26/MTEN/teamcume.htm",
        "base_url": "https://usctrojans.com",
    },
    "michigan": {
        "display": "Michigan Wolverines",
        "roster_url": "https://mgoblue.com/sports/mens-tennis/roster",
        "stats_url": "https://static.mgoblue.com/custompages/Stats/2025-26/MTEN/teamcume.htm",
        "base_url": "https://mgoblue.com",
    },
    "ohio_state": {
        "display": "Ohio State Buckeyes",
        "roster_url": "https://ohiostatebuckeyes.com/sport/mten/roster/",
        "stats_url": "https://static.ohiostatebuckeyes.com/custompages/Stats/2025-26/MTEN/teamcume.htm",
        "base_url": "https://ohiostatebuckeyes.com",
    },
    "penn_state": {
        "display": "Penn State Nittany Lions",
        "roster_url": "https://gopsusports.com/sports/mens-tennis/roster",
        "stats_url": "https://static.gopsusports.com/custompages/Stats/2025-26/MTEN/teamcume.htm",
        "base_url": "https://gopsusports.com",
    },
    "indiana": {
        "display": "Indiana Hoosiers",
        "roster_url": "https://iuhoosiers.com/sports/mens-tennis/roster",
        "stats_url": "https://static.iuhoosiers.com/custompages/Stats/2025-26/MTEN/teamcume.htm",
        "base_url": "https://iuhoosiers.com",
    },
    "illinois": {
        "display": "Illinois Fighting Illini",
        "roster_url": "https://fightingillini.com/sports/mens-tennis/roster",
        "stats_url": "https://static.fightingillini.com/custompages/Stats/2025-26/MTEN/teamcume.htm",
        "base_url": "https://fightingillini.com",
    },
    "northwestern": {
        "display": "Northwestern Wildcats",
        "roster_url": "https://nusports.com/sports/mens-tennis/roster",
        "stats_url": "https://static.nusports.com/custompages/Stats/2025-26/MTEN/teamcume.htm",
        "base_url": "https://nusports.com",
    },
    "purdue": {
        "display": "Purdue Boilermakers",
        "roster_url": "https://purduesports.com/sports/mens-tennis/roster",
        "stats_url": "https://static.purduesports.com/custompages/Stats/2025-26/MTEN/teamcume.htm",
        "base_url": "https://purduesports.com",
    },
    "wisconsin": {
        "display": "Wisconsin Badgers",
        "roster_url": "https://uwbadgers.com/sports/mens-tennis/roster",
        "stats_url": "https://static.uwbadgers.com/custompages/Stats/2025-26/MTEN/teamcume.htm",
        "base_url": "https://uwbadgers.com",
    },
    "nebraska": {
        "display": "Nebraska Cornhuskers",
        "roster_url": "https://huskers.com/sports/mens-tennis/roster",
        "stats_url": "https://static.huskers.com/custompages/Stats/2025-26/MTEN/teamcume.htm",
        "base_url": "https://huskers.com",
    },
    "michigan_state": {
        "display": "Michigan State Spartans",
        "roster_url": "https://msuspartans.com/sports/mens-tennis/roster",
        "stats_url": "https://static.msuspartans.com/custompages/Stats/2025-26/MTEN/teamcume.htm",
        "base_url": "https://msuspartans.com",
    },
    "minnesota": {
        "display": "Minnesota Gophers",
        "roster_url": "https://gophersports.com/sports/mens-tennis/roster",
        "stats_url": "https://static.gophersports.com/custompages/Stats/2025-26/MTEN/teamcume.htm",
        "base_url": "https://gophersports.com",
    },
    "iowa": {
        "display": "Iowa Hawkeyes",
        "roster_url": "https://hawkeyesports.com/sports/mens-tennis/roster",
        "stats_url": "https://static.hawkeyesports.com/custompages/Stats/2025-26/MTEN/teamcume.htm",
        "base_url": "https://hawkeyesports.com",
    },
    "rutgers": {
        "display": "Rutgers Scarlet Knights",
        "roster_url": "https://scarletknights.com/sports/mens-tennis/roster",
        "stats_url": "https://static.scarletknights.com/custompages/Stats/2025-26/MTEN/teamcume.htm",
        "base_url": "https://scarletknights.com",
    },
    "maryland": {
        "display": "Maryland Terrapins",
        "roster_url": "https://umterps.com/sports/mens-tennis/roster",
        "stats_url": "https://static.umterps.com/custompages/Stats/2025-26/MTEN/teamcume.htm",
        "base_url": "https://umterps.com",
    },
}


# ---------------------------------------------------------------------------
# HTTP helper
# ---------------------------------------------------------------------------

def fetch(url: str, timeout: int = 20) -> requests.Response | None:
    """GET with retry logic and polite delays."""
    for attempt in range(3):
        try:
            r = requests.get(url, headers=HEADERS, timeout=timeout)
            r.raise_for_status()
            return r
        except requests.RequestException as e:
            log.warning(f"Attempt {attempt+1} failed for {url}: {e}")
            time.sleep(2 ** attempt)
    log.error(f"All attempts failed for {url}")
    return None


# ---------------------------------------------------------------------------
# UTR lookup
# ---------------------------------------------------------------------------

def get_utr_data(player_name: str, school: str = "") -> tuple[str, str]:
    """Returns (rating_str, profile_url)."""
    search_url = "https://api.utrsports.net/v2/search/players"
    queries = [player_name]
    if school:
        queries.append(f"{player_name} {school}")

    for query in queries:
        try:
            r = requests.get(
                search_url,
                headers={**HEADERS, "Accept": "application/json"},
                params={"query": query, "top": 5},
                timeout=10,
            )
            if r.status_code != 200:
                continue
            
            data = r.json()
            hits = data.get("hits", [])
            if not hits:
                continue

            # Prefer college players
            for hit in hits:
                source = hit.get("source", {})
                player_college = source.get("playerCollege", {})
                
                # Check if this is a college player
                if player_college and player_college.get("name"):
                    pid = source.get("id", "")
                    utr = source.get("singlesUtr")
                    # Convert 0.0 or None to "Unrated"
                    if utr is None or utr == 0 or utr == 0.0:
                        utr = "Unrated"
                    url = f"https://app.utrsports.net/profiles/{pid}" if pid else "N/A"
                    return str(utr), url

            # Fall back to first result
            hit = hits[0]
            source = hit.get("source", {})
            pid = source.get("id", "")
            utr = source.get("singlesUtr")
            # Convert 0.0 or None to "Unrated"
            if utr is None or utr == 0 or utr == 0.0:
                utr = "Unrated"
            url = f"https://app.utrsports.net/profiles/{pid}" if pid else "N/A"
            return str(utr), url

        except Exception as e:
            log.debug(f"UTR API error for '{query}': {e}")

    return "N/A", "N/A"


# ---------------------------------------------------------------------------
# Stats page parser (cumulative team stats HTML)
# ---------------------------------------------------------------------------

# Columns in the Sidearm stats page:
#   Name | S-W | S-L | S-% | D-W | D-L | D-%   (order may vary)
# We detect column positions from the header row.

SINGLES_WIN_ALIASES  = {"sw", "s-w", "singles_w", "singles wins", "w", "wins"}
SINGLES_LOSS_ALIASES = {"sl", "s-l", "singles_l", "singles losses", "l", "losses"}
DOUBLES_WIN_ALIASES  = {"dw", "d-w", "doubles_w", "doubles wins"}
DOUBLES_LOSS_ALIASES = {"dl", "d-l", "doubles_l", "doubles losses"}


def _col_index(headers_text: list[str], aliases: set) -> int:
    for i, h in enumerate(headers_text):
        if h.lower().strip() in aliases:
            return i
    return -1


def parse_stats_page(html: str) -> dict[str, dict]:
    """
    Parse the cumulative stats HTML page.
    Returns dict: normalized_name -> {singles_w, singles_l, doubles_w, doubles_l}
    """
    soup = BeautifulSoup(html, "html.parser")
    result: dict[str, dict] = {}

    tables = soup.find_all("table")
    for table in tables:
        rows = table.find_all("tr")
        if not rows:
            continue

        # Find header row
        header_row = None
        header_texts: list[str] = []
        for row in rows[:4]:
            cells = row.find_all(["th", "td"])
            texts = [c.get_text(strip=True).lower() for c in cells]
            # Look for rows that contain stat-like headers
            if any(t in texts for t in ["w", "l", "s-w", "d-w", "sw", "dw"]):
                header_row = row
                header_texts = texts
                break

        if not header_texts:
            continue

        # Detect column positions
        sw_idx = _col_index(header_texts, SINGLES_WIN_ALIASES)
        sl_idx = _col_index(header_texts, SINGLES_LOSS_ALIASES)
        dw_idx = _col_index(header_texts, DOUBLES_WIN_ALIASES)
        dl_idx = _col_index(header_texts, DOUBLES_LOSS_ALIASES)

        # Fallback: many pages have Name | SW | SL | S% | DW | DL | D%
        if sw_idx == -1 and len(header_texts) >= 6:
            # assume positional: col0=name, 1=SW, 2=SL, 3=S%, 4=DW, 5=DL
            sw_idx, sl_idx, dw_idx, dl_idx = 1, 2, 4, 5

        data_rows = rows[rows.index(header_row) + 1:] if header_row else rows[1:]

        for row in data_rows:
            cols = [c.get_text(strip=True) for c in row.find_all("td")]
            if not cols:
                continue
            name = cols[0]
            if not name or name.lower() in {"total", "team", "totals", ""}:
                continue

            def safe(idx):
                try:
                    return cols[idx] if idx >= 0 and idx < len(cols) else "0"
                except Exception:
                    return "0"

            result[_norm(name)] = {
                "Singles_W": safe(sw_idx) or "0",
                "Singles_L": safe(sl_idx) or "0",
                "Doubles_W": safe(dw_idx) or "0",
                "Doubles_L": safe(dl_idx) or "0",
            }

    return result


def _norm(name: str) -> str:
    """Normalize player name for fuzzy matching (lowercase, strip punctuation)."""
    return re.sub(r"[^a-z ]", "", name.lower()).strip()


def match_stats(norm_name: str, stats_dict: dict) -> dict:
    """Find matching stats entry using exact then partial matching."""
    if norm_name in stats_dict:
        return stats_dict[norm_name]
    # Try last-name match
    last = norm_name.split()[-1] if norm_name.split() else ""
    for key, val in stats_dict.items():
        if last and last in key:
            return val
    return {"Singles_W": "0", "Singles_L": "0", "Doubles_W": "0", "Doubles_L": "0"}


# ---------------------------------------------------------------------------
# Roster page parser (Sidearm Sports)
# ---------------------------------------------------------------------------

# Sidearm player card structure (simplified):
# <li class="sidearm-roster-player">
#   <a href="/sports/mens-tennis/roster/firstname-lastname/12345">
#     <div class="sidearm-roster-player-name"><h3>Full Name</h3></div>
#     <div class="sidearm-roster-player-academic-year">Junior</div>
#     <div class="sidearm-roster-player-hometown">City, ST</div>
#   </a>
# </li>
#
# The exact class names differ slightly between schools but the patterns below
# are broad enough to catch all variants observed on Sidearm sites.

YEAR_KEYWORDS = {
    "freshman": "Fr", "fr": "Fr", "fr.": "Fr",
    "sophomore": "So", "so": "So", "so.": "So",
    "junior": "Jr", "jr": "Jr", "jr.": "Jr",
    "senior": "Sr", "sr": "Sr", "sr.": "Sr",
    "graduate": "Grad", "grad": "Grad", "5th year": "Grad",
    "fifth year": "Grad", "redshirt": "RS",
}

PROFILE_LINK_RE = re.compile(r"/(?:sports/mens-tennis|sport/mten)/roster/[^/]+/(\d+)", re.I)


def _extract_year(text: str) -> str:
    if not text or len(text) > 30:  # Skip if too long
        return "N/A"
    t = text.lower().strip().rstrip(".")
    return YEAR_KEYWORDS.get(t, "N/A")


def parse_roster_page(html: str, base_url: str) -> list[dict]:
    """
    Parse a Sidearm roster page HTML. Returns list of player dicts.
    Each dict contains: name, year_in_school, profile_url, hometown.
    """
    soup = BeautifulSoup(html, "html.parser")
    players: list[dict] = []
    seen_ids: set[str] = set()

    # Strategy 1: Find all links matching the player profile URL pattern
    all_links = soup.find_all("a", href=PROFILE_LINK_RE)

    for link in all_links:
        href = link.get("href", "")
        m = PROFILE_LINK_RE.search(href)
        if not m:
            continue
        player_id = m.group(1)
        if player_id in seen_ids:
            continue

        # Build absolute profile URL
        profile_url = urljoin(base_url, href)

        # --- Extract name ---
        name = _extract_name_from_link(link)
        if not name:
            continue

        # --- Walk up DOM to find the player card container ---
        card = _find_card(link)

        # --- Extract year in school ---
        year = _extract_field(card, [
            r"academic.year", r"class.year", r"eligibility", r"year"
        ])
        year = _extract_year(year) if year else "N/A"

        # --- Extract hometown ---
        hometown = _extract_field(card, [
            r"hometown", r"city", r"high.school"
        ])

        seen_ids.add(player_id)
        players.append({
            "Name": name,
            "Year_In_School": year,
            "Profile_URL": profile_url,
            "Hometown": hometown or "N/A",
        })

    # Strategy 2 (fallback): JSON-LD or script data embed
    if not players:
        players = _parse_json_roster(soup, base_url)

    return players


def _extract_name_from_link(link: BeautifulSoup) -> str:
    """Pull player name from inside a profile <a> tag."""
    # Try heading tags first
    for tag in ("h2", "h3", "h4", "span", "div"):
        elem = link.find(tag, class_=re.compile(r"name", re.I))
        if elem:
            return elem.get_text(" ", strip=True)

    # Try any heading inside the link
    for tag in ("h2", "h3", "h4"):
        elem = link.find(tag)
        if elem:
            t = elem.get_text(" ", strip=True)
            if len(t) > 2:
                return t

    # Fall back to visible text of the link itself
    # Filter out links whose text is just a jersey number or punctuation
    text = link.get_text(" ", strip=True)
    if text and len(text) > 2 and not text.isdigit():
        return text

    return ""


def _find_card(link: BeautifulSoup) -> BeautifulSoup | None:
    """Walk up the DOM to find the enclosing player card element."""
    card_classes = re.compile(r"roster.player|player.card|athlete|s-person", re.I)
    node = link.parent
    for _ in range(6):  # search up to 6 levels
        if node is None:
            break
        cls = " ".join(node.get("class", []))
        if card_classes.search(cls):
            return node
        node = node.parent
    # Return closest parent we found even if not a card
    return link.parent


def _extract_field(card, class_patterns: list[str]) -> str:
    """Search a card element for text matching any of the CSS class patterns."""
    if card is None:
        return ""
    
    # Try class-based search
    combined = re.compile("|".join(class_patterns), re.I)
    elem = card.find(class_=combined)
    if elem:
        text = elem.get_text(" ", strip=True)
        # Skip if text is too long (likely scraped wrong content)
        if text and len(text) > 1 and len(text) < 100:
            return text

    # Try data attributes / aria-labels
    for attr in ("data-label", "aria-label", "data-hometown", "data-city"):
        for child in card.find_all(attrs={attr: combined}):
            text = child.get_text(" ", strip=True)
            if text and len(text) > 1 and len(text) < 100:
                return text
    
    # Try searching all text in card for hometown-like patterns
    if "hometown" in "|".join(class_patterns).lower():
        # Look for text that looks like "City, State" or "City, Country"
        all_text = card.get_text(" ", strip=True)
        # Match patterns like "Los Angeles, CA" or "Paris, France"
        match = re.search(r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*,\s*[A-Z]{2,})', all_text)
        if match:
            return match.group(1)

    return ""


def _parse_json_roster(soup: BeautifulSoup, base_url: str) -> list[dict]:
    """Some Sidearm pages embed roster JSON in a <script> tag."""
    players = []
    for script in soup.find_all("script"):
        text = script.string or ""
        if "roster" not in text.lower():
            continue
        # Try to find JSON array
        try:
            m = re.search(r'\[(\{.*?"name".*?\})\]', text, re.S)
            if m:
                arr = json.loads("[" + m.group(1) + "]")
                for p in arr:
                    name = p.get("name") or p.get("fullName", "")
                    pid = str(p.get("id", ""))
                    players.append({
                        "Name": name,
                        "Year_In_School": p.get("academicYear") or p.get("year", "N/A"),
                        "Profile_URL": f"{base_url}/sports/mens-tennis/roster/{pid}" if pid else "N/A",
                        "Hometown": p.get("hometown") or p.get("city", "N/A"),
                    })
        except Exception:
            pass
    return players


# ---------------------------------------------------------------------------
# Individual player profile page
# ---------------------------------------------------------------------------

def scrape_player_profile(profile_url: str) -> dict:
    """
    Fetch a player's individual Sidearm profile page and extract
    Year_In_School and Hometown if not already found on the roster page.
    """
    r = fetch(profile_url)
    if not r:
        return {}

    soup = BeautifulSoup(r.content, "html.parser")

    # Sidearm profile bio section
    bio = soup.find(class_=re.compile(r"player.bio|athlete.bio|s-person|bio", re.I))
    if not bio:
        bio = soup  # fallback: search whole page

    year = ""
    hometown = ""

    # Strategy 1: Look for dt/dd pairs
    for dt in bio.find_all(["dt", "span", "li", "div"]):
        label_text = dt.get_text(strip=True).lower()
        sibling = dt.find_next_sibling()
        sibling_text = sibling.get_text(strip=True) if sibling else ""

        if any(kw in label_text for kw in ["year", "class", "eligibility"]) and len(sibling_text) < 30:
            year = sibling_text or label_text

        if any(kw in label_text for kw in ["hometown", "city", "home"]) and len(sibling_text) < 100:
            hometown = sibling_text or label_text
    
    # Strategy 2: Look for specific class names
    if not hometown:
        hometown_elem = soup.find(class_=re.compile(r"hometown|city|location", re.I))
        if hometown_elem:
            ht = hometown_elem.get_text(strip=True)
            if len(ht) < 100:
                hometown = ht
    
    if not year:
        year_elem = soup.find(class_=re.compile(r"year|class|eligibility", re.I))
        if year_elem:
            yt = year_elem.get_text(strip=True)
            if len(yt) < 30:
                year = yt
    
    # Strategy 3: Search all text for hometown pattern
    if not hometown:
        all_text = soup.get_text()
        match = re.search(r'Hometown[:\s]+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*,\s*[A-Z]{2,})', all_text, re.I)
        if match:
            hometown = match.group(1)

    return {"Year_In_School": _extract_year(year) if year else "N/A", "Hometown": hometown or "N/A"}


# ---------------------------------------------------------------------------
# Main scraper per school
# ---------------------------------------------------------------------------

def scrape_school(school_key: str, cfg: dict) -> pd.DataFrame:
    display = cfg["display"]
    log.info(f"\n{'='*70}")
    log.info(f"Scraping {display} ...")

    # ---- 1. Fetch roster page ----
    r = fetch(cfg["roster_url"])
    if not r:
        log.error(f"Could not fetch roster page for {display}")
        return pd.DataFrame()

    roster_players = parse_roster_page(r.text, cfg["base_url"])
    log.info(f"  Found {len(roster_players)} players on roster page")

    # ---- 2. Fetch stats page ----
    stats_dict: dict[str, dict] = {}
    r_stats = fetch(cfg["stats_url"])
    if r_stats:
        stats_dict = parse_stats_page(r_stats.text)
        log.info(f"  Loaded stats for {len(stats_dict)} players")
    else:
        log.warning(f"  Could not fetch stats page (may not exist yet for this season)")

    # ---- 3. Enrich each player ----
    rows = []
    for p in roster_players:
        name = p["Name"]
        log.info(f"    Processing: {name}")

        # Get year and hometown from roster page
        year = p.get("Year_In_School", "N/A")
        hometown = p.get("Hometown", "N/A")

        # Always try to fetch profile page for missing data
        if year == "N/A" or not hometown or hometown == "N/A" or len(year) > 30 or len(hometown) > 100:
            log.info(f"      Fetching profile page for missing data...")
            profile_data = scrape_player_profile(p["Profile_URL"])
            if year == "N/A" or len(year) > 30:
                year = profile_data.get("Year_In_School", "N/A")
            if (not hometown or hometown == "N/A" or len(hometown) > 100) and profile_data.get("Hometown") != "N/A":
                hometown = profile_data.get("Hometown", "N/A")
            time.sleep(0.5)

        # Match stats
        stats = match_stats(_norm(name), stats_dict)

        # UTR lookup
        log.info(f"      Looking up UTR for {name}...")
        utr_rating, utr_url = get_utr_data(name, school=display)
        log.info(f"      UTR: {utr_rating}")
        time.sleep(0.75)  # be polite to UTR API

        rows.append({
            "Player":         name,
            "Year":           year,
            "Hometown":       hometown,
            "UTR":            utr_rating,
            "Singles_Record": f"{stats['Singles_W']}-{stats['Singles_L']}",
            "Doubles_Record": f"{stats['Doubles_W']}-{stats['Doubles_L']}",
            "Profile_URL":    p["Profile_URL"],
            "UTR_URL":        utr_url,
        })

    COLS = ["Player","Year","Hometown","UTR","Singles_Record","Doubles_Record","Profile_URL","UTR_URL"]
    df = pd.DataFrame(rows, columns=COLS)
    return df


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    all_frames = []

    for school_key, cfg in SCHOOLS.items():
        try:
            df = scrape_school(school_key, cfg)
            if not df.empty:
                path = os.path.join(ROSTERS_DIR, f"{school_key}_roster.csv")
                df.to_csv(path, index=False)
                log.info(f"  Saved {len(df)} rows -> {path}")
                all_frames.append(df)
            time.sleep(2)  # pause between schools
        except Exception as e:
            log.exception(f"Fatal error scraping {school_key}: {e}")

    if all_frames:
        combined = pd.concat(all_frames, ignore_index=True)
        combined.to_csv(os.path.join(ROSTERS_DIR, "all_rosters.csv"), index=False)
        log.info(f"\nCombined file: rosters/all_rosters.csv ({len(combined)} total rows)")
        print("\nSummary:")
        print(f"Total players scraped: {len(combined)}")
    else:
        log.warning("No data collected.")


if __name__ == "__main__":
    main()