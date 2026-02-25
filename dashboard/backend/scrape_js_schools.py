"""
scrape_js_schools.py
====================
Handles schools whose roster pages are fully JavaScript-rendered
(Penn State / gopsusports.com, Purdue / purduesports.com, Nebraska / huskers.com).
These use Nuxt.js or similar frameworks — requests+BeautifulSoup only gets
a "Javascript is required" shell.

TWO STRATEGIES (tried in order):
  1. Playwright headless browser — renders JS and extracts full DOM.
     Install: pip install playwright && playwright install chromium
  2. Table-format fallback — many Sidearm/Nuxt sites expose a printable
     table version at /roster?view=table or embed data in a <script> tag.

Also handles schools whose roster pages use a <table> layout instead of
the card/grid layout (which caused undercounting on some Sidearm schools).

Usage:
    python scrape_js_schools.py                    # all JS schools
    python scrape_js_schools.py penn_state purdue  # specific schools

Output: rosters/<school>_roster.csv
"""

import sys
import os
import re
import time
import json
import logging
import requests
from urllib.parse import urljoin
import pandas as pd

logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")
log = logging.getLogger(__name__)

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROSTERS_DIR = os.path.join(SCRIPT_DIR, "rosters")
os.makedirs(ROSTERS_DIR, exist_ok=True)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}

SEASON = "2025-26"

# ---------------------------------------------------------------------------
# Schools configuration
# ---------------------------------------------------------------------------
# These three use Nuxt.js (fully JS-rendered, player URL = /roster/player/slug)
NUXT_SCHOOLS = {
    "penn_state": {
        "display":    "Penn State Nittany Lions",
        "roster_url": "https://gopsusports.com/sports/mens-tennis/roster",
        "stats_url":  "https://static.gopsusports.com/custompages/Stats/2025-26/MTEN/teamcume.htm",
        "base_url":   "https://gopsusports.com",
        # Known players from search results / manual lookup (slug format)
        # Fill in as you find them — the Playwright path will auto-discover all
        "known_player_slugs": [
            "michael-wright-tennis",
            "david-lindsay",
            "jaden-brady",
            "eyal-shyovitz",
            "emil-matikainen",
        ],
    },
    "purdue": {
        "display":    "Purdue Boilermakers",
        "roster_url": "https://purduesports.com/sports/mens-tennis/roster",
        "stats_url":  "https://static.purduesports.com/custompages/Stats/2025-26/MTEN/teamcume.htm",
        "base_url":   "https://purduesports.com",
        "known_player_slugs": [],
    },
    "nebraska": {
        "display":    "Nebraska Cornhuskers",
        "roster_url": "https://huskers.com/sports/mens-tennis/roster",
        "stats_url":  "https://static.huskers.com/custompages/Stats/2025-26/MTEN/teamcume.htm",
        "base_url":   "https://huskers.com",
        "known_player_slugs": [],
    },
}

# These use Sidearm but with a TABLE layout — the card scraper misses most players.
# Adding explicit table-row parsing for these.
TABLE_LAYOUT_SIDEARM_SCHOOLS = {
    # Add any other Sidearm school here if it shows <1 player per card page
}

# ---------------------------------------------------------------------------
# Stats parser (reused from main scraper)
# ---------------------------------------------------------------------------

def _norm(name: str) -> str:
    return re.sub(r"[^a-z ]", "", name.lower()).strip()

def parse_stats(html: str) -> dict[str, dict]:
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(html, "html.parser")
    result: dict[str, dict] = {}
    SINGLES_WIN  = {"sw", "s-w", "w", "wins", "singles wins"}
    SINGLES_LOSS = {"sl", "s-l", "l", "losses", "singles losses"}
    DOUBLES_WIN  = {"dw", "d-w", "doubles wins"}
    DOUBLES_LOSS = {"dl", "d-l", "doubles losses"}

    def col_idx(hdrs, aliases):
        for i, h in enumerate(hdrs):
            if h.lower().strip() in aliases:
                return i
        return -1

    for table in soup.find_all("table"):
        rows = table.find_all("tr")
        header_texts, header_idx = [], 0
        for i, row in enumerate(rows[:5]):
            texts = [c.get_text(strip=True).lower() for c in row.find_all(["th", "td"])]
            if any(t in texts for t in ["w", "l", "s-w", "d-w", "sw"]):
                header_texts, header_idx = texts, i
                break
        if not header_texts:
            continue
        sw = col_idx(header_texts, SINGLES_WIN)
        sl = col_idx(header_texts, SINGLES_LOSS)
        dw = col_idx(header_texts, DOUBLES_WIN)
        dl = col_idx(header_texts, DOUBLES_LOSS)
        if sw == -1 and len(header_texts) >= 6:
            sw, sl, dw, dl = 1, 2, 4, 5
        for row in rows[header_idx + 1:]:
            cols = [c.get_text(strip=True) for c in row.find_all("td")]
            if not cols or not cols[0]:
                continue
            if cols[0].lower() in {"total", "team", "totals", ""}:
                continue
            def safe(idx):
                try: return cols[idx] if 0 <= idx < len(cols) and cols[idx] else "0"
                except: return "0"
            result[_norm(cols[0])] = {
                "Singles_W": safe(sw), "Singles_L": safe(sl),
                "Doubles_W": safe(dw), "Doubles_L": safe(dl),
            }
    return result

def match_stats(name: str, stats: dict) -> dict:
    n = _norm(name)
    if n in stats:
        return stats[n]
    last = n.split()[-1] if n.split() else ""
    for k, v in stats.items():
        if last and last in k.split():
            return v
    return {"Singles_W": "0", "Singles_L": "0", "Doubles_W": "0", "Doubles_L": "0"}

# ---------------------------------------------------------------------------
# UTR lookup
# ---------------------------------------------------------------------------

def get_utr(name: str, school: str = "") -> tuple[str, str]:
    ep = "https://api.utrsports.net/v2/search/players"
    queries = [name, f"{name} {school}"] if school else [name]
    for q in queries:
        try:
            r = requests.get(ep, headers=HEADERS, params={"query": q, "top": 5}, timeout=10)
            if r.status_code != 200:
                continue
            hits = r.json().get("hits") or []
            for hit in hits:
                if "college" in str(hit.get("membership", "")).lower():
                    pid = hit.get("id", "")
                    utr = hit.get("singlesUtr", "N/A")
                    return str(utr), f"https://app.utrsports.net/profiles/{pid}"
            if hits:
                pid = hits[0].get("id", "")
                utr = hits[0].get("singlesUtr", "N/A")
                return str(utr), f"https://app.utrsports.net/profiles/{pid}"
        except Exception as e:
            log.debug(f"UTR error for '{q}': {e}")
    return "N/A", "N/A"

# ---------------------------------------------------------------------------
# Strategy 1: Playwright (headless Chrome)
# ---------------------------------------------------------------------------

def scrape_with_playwright(roster_url: str, base_url: str) -> list[dict]:
    """Render JS, extract player cards and table rows."""
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        log.warning("Playwright not installed. Run: pip install playwright && playwright install chromium")
        return []

    players: list[dict] = []
    from bs4 import BeautifulSoup

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(extra_http_headers=HEADERS)

        try:
            log.info(f"  Playwright loading: {roster_url}")
            page.goto(roster_url, wait_until="networkidle", timeout=30000)
            # Wait for player data to load
            try:
                page.wait_for_selector(
                    "a[href*='/roster/player/'], table tr, .s-person-details",
                    timeout=15000
                )
            except Exception:
                pass  # Continue anyway with whatever loaded
            time.sleep(2)  # Extra buffer for lazy-loaded content

            html = page.content()
        except Exception as e:
            log.error(f"  Playwright navigation error: {e}")
            browser.close()
            return []

        browser.close()

    soup = BeautifulSoup(html, "html.parser")

    # --- Method A: Player card links ---
    # Nuxt schools use: /sports/mens-tennis/roster/player/player-slug
    player_link_re = re.compile(r"/sports/mens-tennis/roster/player/([^/?#]+)", re.I)
    # Also handles Nebraska/Purdue which may use /sports/X/roster/player/Y
    player_link_re2 = re.compile(r"/sports/[^/]+/roster/player/([^/?#]+)", re.I)

    seen: set[str] = set()

    for link in soup.find_all("a", href=True):
        href = link.get("href", "")
        m = player_link_re.search(href) or player_link_re2.search(href)
        if not m:
            continue
        slug = m.group(1)
        if slug in seen or "staff" in href:
            continue
        seen.add(slug)

        profile_url = href if href.startswith("http") else urljoin(base_url, href)

        # Extract name from the link
        name = _extract_name_from_card(link, slug)
        year = _extract_field_from_card(link, r"class|year|eligib")
        hometown = _extract_field_from_card(link, r"hometown|city|high.school")

        if name:
            players.append({
                "Name": name, "Slug": slug,
                "Year_In_School": _map_year(year),
                "Hometown": hometown or "N/A",
                "Profile_URL": profile_url,
            })

    # --- Method B: Table rows (some Nuxt schools use list/table view) ---
    if not players:
        players = _parse_table_roster(soup, base_url)

    log.info(f"  Playwright found {len(players)} players")
    return players


def _extract_name_from_card(link, slug: str) -> str:
    """Pull name from link element or nearby DOM."""
    for tag in ("h2", "h3", "h4", "h5"):
        h = link.find(tag)
        if h:
            t = h.get_text(" ", strip=True)
            if t and len(t) > 2:
                return t

    for cls_pattern in ("name", "title", "person"):
        elem = link.find(class_=re.compile(cls_pattern, re.I))
        if elem:
            t = elem.get_text(" ", strip=True)
            if t and len(t) > 2:
                return t

    # Check parent card
    card = link.parent
    for _ in range(4):
        if card is None:
            break
        for tag in ("h2", "h3", "h4"):
            h = card.find(tag)
            if h:
                t = h.get_text(" ", strip=True)
                if t and len(t) > 2 and not t.isdigit():
                    return t
        card = card.parent

    # Link text
    t = link.get_text(" ", strip=True)
    if t and len(t) > 2 and not t.isdigit():
        return t

    # Slug fallback
    return slug.replace("-", " ").title()


def _extract_field_from_card(link, pattern: str) -> str:
    """Look for a field matching a CSS class pattern in the surrounding card."""
    card = link.parent
    for _ in range(6):
        if card is None:
            break
        elem = card.find(class_=re.compile(pattern, re.I))
        if elem:
            return elem.get_text(" ", strip=True)
        card = card.parent
    return ""


YEAR_MAP = {
    "freshman": "Fr", "fr": "Fr",
    "sophomore": "So", "so": "So",
    "junior": "Jr", "jr": "Jr",
    "senior": "Sr", "sr": "Sr",
    "graduate": "Grad", "grad": "Grad",
    "5th year": "Grad", "fifth year": "Grad",
    "redshirt freshman": "RS Fr", "redshirt sophomore": "RS So",
}

def _map_year(text: str) -> str:
    if not text:
        return "N/A"
    t = text.lower().strip().rstrip(".")
    return YEAR_MAP.get(t, text.title())


def _parse_table_roster(soup, base_url: str) -> list[dict]:
    """Parse a table-formatted roster (some schools use list/table view)."""
    from bs4 import BeautifulSoup
    players = []
    player_link_re = re.compile(r"/roster/player/([^/?#]+)", re.I)

    for table in soup.find_all("table"):
        rows = table.find_all("tr")
        if len(rows) < 2:
            continue

        # Check if this looks like a roster table
        first_text = rows[0].get_text(" ", strip=True).lower()
        if not any(kw in first_text for kw in ("name", "year", "class", "hometown")):
            continue

        headers = [th.get_text(strip=True).lower() for th in rows[0].find_all(["th", "td"])]
        name_idx = next((i for i, h in enumerate(headers) if "name" in h), 0)
        year_idx = next((i for i, h in enumerate(headers) if "year" in h or "class" in h), -1)
        home_idx = next((i for i, h in enumerate(headers) if "hometown" in h or "city" in h), -1)

        for row in rows[1:]:
            cols = row.find_all("td")
            if not cols:
                continue

            # Get name
            name_cell = cols[name_idx] if name_idx < len(cols) else cols[0]
            name = name_cell.get_text(" ", strip=True)
            if not name or len(name) < 2 or name.isdigit():
                continue

            # Get profile URL from link in row
            link = row.find("a", href=player_link_re)
            if link:
                href = link.get("href", "")
                profile_url = href if href.startswith("http") else urljoin(base_url, href)
                m = player_link_re.search(href)
                slug = m.group(1) if m else _norm(name).replace(" ", "-")
            else:
                slug = _norm(name).replace(" ", "-")
                profile_url = f"{base_url}/sports/mens-tennis/roster/player/{slug}"

            year = cols[year_idx].get_text(strip=True) if year_idx >= 0 and year_idx < len(cols) else "N/A"
            hometown = cols[home_idx].get_text(strip=True) if home_idx >= 0 and home_idx < len(cols) else "N/A"

            players.append({
                "Name": name, "Slug": slug,
                "Year_In_School": _map_year(year),
                "Hometown": hometown,
                "Profile_URL": profile_url,
            })

    return players


# ---------------------------------------------------------------------------
# Strategy 2: Nuxt JSON API (/_nuxt/data or /api/ endpoints)
# ---------------------------------------------------------------------------

def scrape_via_nuxt_api(roster_url: str, base_url: str) -> list[dict]:
    """
    Nuxt apps often expose data via /_nuxt/data/<build-id>/path.json.
    We try to find the build ID from the page source, then hit the API.
    """
    r = requests.get(roster_url, headers=HEADERS, timeout=15)
    if not r.ok:
        return []

    html = r.text

    # Find Nuxt build ID from script tags
    # Pattern: /_nuxt/XXXX.js or __NUXT_DATA__ JSON embed
    build_id = None
    m = re.search(r'/_nuxt/([a-f0-9]{8,})/manifest', html)
    if m:
        build_id = m.group(1)

    # Try to find embedded __NUXT_DATA__ JSON
    nuxt_data_match = re.search(r'<script[^>]*>\s*window\.__NUXT__\s*=\s*(\{.*?\})\s*</script>', html, re.S)
    if nuxt_data_match:
        try:
            data = json.loads(nuxt_data_match.group(1))
            players = _extract_players_from_nuxt_data(data, base_url)
            if players:
                log.info(f"  Nuxt embedded data: found {len(players)} players")
                return players
        except Exception as e:
            log.debug(f"  Nuxt data parse error: {e}")

    # Try inline JSON arrays in script tags
    for script in re.findall(r'<script[^>]*>(.*?)</script>', html, re.S):
        if '"name"' not in script or '"roster"' not in script.lower():
            continue
        # Try to find JSON with player arrays
        for m in re.finditer(r'\{[^{}]*"name"\s*:\s*"([^"]{3,})"[^{}]*\}', script):
            log.debug(f"  Found potential player object in script: {m.group(0)[:100]}")

    return []


def _extract_players_from_nuxt_data(data: dict, base_url: str) -> list[dict]:
    """Recursively search Nuxt data blob for player objects."""
    players = []
    seen = set()

    def search(obj):
        if isinstance(obj, dict):
            name = obj.get("name") or obj.get("fullName") or obj.get("playerName")
            slug = obj.get("slug") or obj.get("urlSlug") or obj.get("identifier")
            if name and isinstance(name, str) and len(name) > 3 and name not in seen:
                seen.add(name)
                pid = obj.get("id") or obj.get("playerId") or ""
                year_raw = obj.get("academicYear") or obj.get("classYear") or obj.get("year") or ""
                hometown = obj.get("hometown") or obj.get("homeCity") or obj.get("city") or "N/A"
                profile = (
                    obj.get("profileUrl") or
                    (f"{base_url}/sports/mens-tennis/roster/player/{slug}" if slug else
                     f"{base_url}/sports/mens-tennis/roster/player/{pid}" if pid else "N/A")
                )
                players.append({
                    "Name": name,
                    "Slug": slug or str(pid),
                    "Year_In_School": _map_year(str(year_raw)),
                    "Hometown": hometown,
                    "Profile_URL": profile,
                })
            for v in obj.values():
                search(v)
        elif isinstance(obj, list):
            for item in obj:
                search(item)

    search(data)
    return players


# ---------------------------------------------------------------------------
# Strategy 3: Individual profile pages from known slugs
# ---------------------------------------------------------------------------

def scrape_via_known_slugs(slugs: list[str], base_url: str, sport_path: str = "sports/mens-tennis") -> list[dict]:
    """
    For schools where we know player slugs (from Google/manual lookup),
    fetch each profile page and extract data.
    """
    from bs4 import BeautifulSoup
    players = []

    for slug in slugs:
        url = f"{base_url}/{sport_path}/roster/player/{slug}"
        r = requests.get(url, headers=HEADERS, timeout=15)
        if not r.ok:
            log.warning(f"  Profile 404: {url}")
            continue

        soup = BeautifulSoup(r.content, "html.parser")

        # Extract name from page title or h1
        name = ""
        title = soup.find("title")
        if title:
            # "Player Name - 2025-26 Men's Tennis - School"
            name = title.get_text(strip=True).split(" - ")[0].strip()

        if not name:
            h1 = soup.find("h1")
            name = h1.get_text(strip=True) if h1 else slug.replace("-", " ").title()

        # Extract year and hometown from bio
        year, hometown = "N/A", "N/A"
        for dt in soup.find_all("dt"):
            label = dt.get_text(strip=True).lower()
            dd = dt.find_next_sibling("dd")
            val = dd.get_text(strip=True) if dd else ""
            if any(kw in label for kw in ("year", "class", "eligib")):
                year = _map_year(val)
            if any(kw in label for kw in ("hometown", "city", "home")):
                hometown = val

        # Fallback: search all elements
        if year == "N/A":
            for elem in soup.find_all(class_=re.compile(r"year|class|eligib", re.I)):
                t = elem.get_text(strip=True)
                y = _map_year(t)
                if y != t.title():  # matched a known year
                    year = y
                    break

        players.append({
            "Name": name,
            "Slug": slug,
            "Year_In_School": year,
            "Hometown": hometown,
            "Profile_URL": url,
        })
        log.info(f"    Got profile: {name} ({year}) from {url}")
        time.sleep(0.5)

    return players


# ---------------------------------------------------------------------------
# Main per-school scraper
# ---------------------------------------------------------------------------

def scrape_nuxt_school(school_key: str, cfg: dict) -> pd.DataFrame:
    display = cfg["display"]
    log.info(f"\n{'='*70}")
    log.info(f"Scraping JS school: {display}")

    players: list[dict] = []

    # Try Playwright first (best results)
    playwright_available = True
    try:
        import importlib
        importlib.import_module("playwright")
    except ImportError:
        playwright_available = False

    if playwright_available:
        players = scrape_with_playwright(cfg["roster_url"], cfg["base_url"])

    # Fallback: Nuxt JSON API
    if not players:
        log.info("  Trying Nuxt API fallback...")
        players = scrape_via_nuxt_api(cfg["roster_url"], cfg["base_url"])

    # Fallback: known slugs from manual lookup / previous runs
    if not players and cfg.get("known_player_slugs"):
        log.info("  Trying known player slugs...")
        players = scrape_via_known_slugs(cfg["known_player_slugs"], cfg["base_url"])

    if not players:
        log.error(f"  Could not scrape {display}. Options:")
        log.error(f"    1. Install Playwright: pip install playwright && playwright install chromium")
        log.error(f"    2. Add known player slugs to NUXT_SCHOOLS['{school_key}']['known_player_slugs']")
        log.error(f"    3. Find and add slugs from: {cfg['roster_url']}")
        return pd.DataFrame()

    # Fetch stats
    stats: dict[str, dict] = {}
    try:
        r = requests.get(cfg["stats_url"], headers=HEADERS, timeout=15)
        if r.ok:
            stats = parse_stats(r.text)
            log.info(f"  Loaded stats for {len(stats)} players")
    except Exception as e:
        log.warning(f"  Stats fetch error: {e}")

    # Build rows
    rows = []
    for p in players:
        name = p["Name"]
        log.info(f"    Processing: {name}")

        s = match_stats(name, stats)
        utr_r, utr_url = get_utr(name, display)
        time.sleep(0.75)

        rows.append({
            "School":         display,
            "Season":         SEASON,
            "Player":         name,
            "Player_Slug":    p.get("Slug", ""),
            "Year_In_School": p.get("Year_In_School", "N/A"),
            "Hometown":       p.get("Hometown", "N/A"),
            "Profile_URL":    p.get("Profile_URL", "N/A"),
            "UTR_Rating":     utr_r,
            "UTR_URL":        utr_url,
            "Singles_W":      s["Singles_W"],
            "Singles_L":      s["Singles_L"],
            "Singles_Record": f"{s['Singles_W']}-{s['Singles_L']}",
            "Doubles_W":      s["Doubles_W"],
            "Doubles_L":      s["Doubles_L"],
            "Doubles_Record": f"{s['Doubles_W']}-{s['Doubles_L']}",
        })

    COLS = ["Player", "Year", "Hometown", "UTR", "Singles_Record", "Doubles_Record", "Profile_URL", "UTR_URL"]
    return pd.DataFrame(rows, columns=COLS)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    targets = sys.argv[1:] if len(sys.argv) > 1 else list(NUXT_SCHOOLS.keys())

    all_frames = []
    for school_key in targets:
        if school_key not in NUXT_SCHOOLS:
            log.error(f"Unknown school '{school_key}'. Options: {list(NUXT_SCHOOLS.keys())}")
            continue
        try:
            df = scrape_nuxt_school(school_key, NUXT_SCHOOLS[school_key])
            if not df.empty:
                path = os.path.join(ROSTERS_DIR, f"{school_key}_roster.csv")
                df.to_csv(path, index=False)
                log.info(f"  Saved {len(df)} rows -> {path}")
                all_frames.append(df)
        except Exception as e:
            log.exception(f"Error scraping {school_key}: {e}")
        time.sleep(2)

    if len(all_frames) > 1:
        combined = pd.concat(all_frames, ignore_index=True)
        combined.to_csv(os.path.join(ROSTERS_DIR, "js_schools_rosters.csv"), index=False)
        log.info(f"\nCombined JS schools: rosters/js_schools_rosters.csv ({len(combined)} rows)")

    print("\n" + "="*70)
    print("NEXT STEPS if Playwright is not installed:")
    print("  pip install playwright")
    print("  playwright install chromium")
    print("  python scrape_js_schools.py")
    print()
    print("OR manually add player slugs to NUXT_SCHOOLS config above.")
    print("Find slugs by visiting the roster page in your browser and")
    print("hovering over each player card — the URL shows the slug.")


if __name__ == "__main__":
    main()