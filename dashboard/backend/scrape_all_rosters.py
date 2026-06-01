"""
scrape_all_rosters.py  —  Playwright edition
Requires: pip install playwright beautifulsoup4 pandas
          playwright install chromium
"""

import asyncio
import re
import os
import time
import json
import logging
from urllib.parse import urljoin

import pandas as pd
import requests
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright, TimeoutError as PWTimeout

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
}

SCHOOLS = {
    "ucla":          {"display": "UCLA Bruins",              "roster_url": "https://uclabruins.com/sports/mens-tennis/roster",         "base_url": "https://uclabruins.com"},
    "usc":           {"display": "USC Trojans",              "roster_url": "https://usctrojans.com/sports/mens-tennis/roster",          "base_url": "https://usctrojans.com"},
    "michigan":      {"display": "Michigan Wolverines",      "roster_url": "https://mgoblue.com/sports/mens-tennis/roster",            "base_url": "https://mgoblue.com"},
    "ohio_state":    {"display": "Ohio State Buckeyes",      "roster_url": "https://ohiostatebuckeyes.com/sport/mten/roster/",         "base_url": "https://ohiostatebuckeyes.com"},
    "indiana":       {"display": "Indiana Hoosiers",         "roster_url": "https://iuhoosiers.com/sports/mens-tennis/roster",         "base_url": "https://iuhoosiers.com"},
    "northwestern":  {"display": "Northwestern Wildcats",    "roster_url": "https://nusports.com/sports/mens-tennis/roster",           "base_url": "https://nusports.com"},
    "wisconsin":     {"display": "Wisconsin Badgers",        "roster_url": "https://uwbadgers.com/sports/mens-tennis/roster",          "base_url": "https://uwbadgers.com"},
    "michigan_state":{"display": "Michigan State Spartans",  "roster_url": "https://msuspartans.com/sports/mens-tennis/roster",        "base_url": "https://msuspartans.com"},
    "minnesota":     {"display": "Minnesota Gophers",        "roster_url": "https://gophersports.com/sports/mens-tennis/roster",       "base_url": "https://gophersports.com"},
    "iowa":          {"display": "Iowa Hawkeyes",            "roster_url": "https://hawkeyesports.com/sports/mens-tennis/roster",      "base_url": "https://hawkeyesports.com"},
    "rutgers":       {"display": "Rutgers Scarlet Knights",  "roster_url": "https://scarletknights.com/sports/mens-tennis/roster",     "base_url": "https://scarletknights.com"},
    "maryland":      {"display": "Maryland Terrapins",       "roster_url": "https://umterps.com/sports/mens-tennis/roster",            "base_url": "https://umterps.com"},
    "penn_state":    {"display": "Penn State Nittany Lions", "roster_url": "https://gopsusports.com/sports/mens-tennis/roster",        "base_url": "https://gopsusports.com"},
    "nebraska":      {"display": "Nebraska Cornhuskers",     "roster_url": "https://huskers.com/sports/mens-tennis/roster",            "base_url": "https://huskers.com"},
    "purdue":        {"display": "Purdue Boilermakers",      "roster_url": "https://purduesports.com/sports/mens-tennis/roster",       "base_url": "https://purduesports.com"},
    "illinois":      {"display": "Illinois Fighting Illini", "roster_url": "https://fightingillini.com/sports/mens-tennis/roster",     "base_url": "https://fightingillini.com"},
}

YEAR_KEYWORDS = {
    "freshman": "Fr", "fr": "Fr", "fr.": "Fr",
    "sophomore": "So", "so": "So", "so.": "So",
    "junior": "Jr", "jr": "Jr", "jr.": "Jr",
    "senior": "Sr", "sr": "Sr", "sr.": "Sr",
    "graduate": "Grad", "grad": "Grad", "5th year": "Grad",
    "fifth year": "Grad", "redshirt": "RS",
}

def _extract_year(text: str) -> str:
    if not text or len(text) > 30:
        return "N/A"
    return YEAR_KEYWORDS.get(text.lower().strip().rstrip("."), "N/A")

def _norm(name: str) -> str:
    return re.sub(r"[^a-z ]", "", name.lower()).strip()


# ---------------------------------------------------------------------------
# Playwright page fetcher — renders JS then returns HTML
# ---------------------------------------------------------------------------

async def fetch_rendered(url: str, browser, wait_for: str = ".sidearm-roster-player, .s-person, article, tr") -> str:
    """
    Load a page with Playwright, wait for player content to appear,
    return the fully rendered HTML.
    """
    page = await browser.new_page()
    try:
        await page.goto(url, wait_until="domcontentloaded", timeout=30000)
        # Wait for any known player element to appear
        try:
            await page.wait_for_selector(wait_for, timeout=10000)
        except PWTimeout:
            pass  # Continue anyway — maybe the selector just didn't match
        await page.wait_for_timeout(2000)  # Extra buffer for lazy-loaded content
        html = await page.content()
        return html
    finally:
        await page.close()


# ---------------------------------------------------------------------------
# UTR lookup (unchanged — uses requests, not Playwright)
# ---------------------------------------------------------------------------

def get_utr_data(player_name: str, school: str = "") -> tuple[str, str]:
    queries = [player_name, f"{player_name} {school}"] if school else [player_name]
    for query in queries:
        try:
            data = requests.get(
                f"https://app.universaltennis.com/api/v2/search/players?query={query}&top=1",
                headers=HEADERS, timeout=10,
            ).json()
            key = "hits" if "hits" in data else "Hits"
            hit = data[key][0]
            pid = hit.get("id") or hit.get("Id")
            player = requests.get(
                f"https://app.universaltennis.com/api/v1/player/{pid}",
                headers=HEADERS, timeout=10,
            ).json()
            utr = player.get("singlesUtr") or "Unrated"
            return str(utr), f"https://app.utrsports.net/profiles/{pid}"
        except Exception as e:
            log.debug(f"UTR error for '{query}': {e}")
    return "N/A", "N/A"


# ---------------------------------------------------------------------------
# Roster HTML parser — works on rendered HTML from any Sidearm variant
# ---------------------------------------------------------------------------

# Broad profile link pattern covers all school URL formats
PROFILE_RE = re.compile(r"/(?:sports/mens-tennis|sport/mten)/roster/[^/]+/(\d+)", re.I)

def parse_roster_html(html: str, base_url: str) -> list[dict]:
    soup = BeautifulSoup(html, "html.parser")
    players: list[dict] = []
    seen: set[str] = set()

    # --- Strategy A: find all profile links (works for most Sidearm sites) ---
    for link in soup.find_all("a", href=PROFILE_RE):
        href = link["href"]
        m = PROFILE_RE.search(href)
        if not m:
            continue
        pid = m.group(1)
        if pid in seen:
            continue
        seen.add(pid)

        profile_url = urljoin(base_url, href)
        name = _extract_name(link)
        if not name:
            continue

        card = _find_card(link)
        year = _extract_year(_field_text(card, r"academic.year|class.year|eligibility|year"))
        hometown = _field_text(card, r"hometown|city|high.school") or "N/A"

        players.append({"Name": name, "Year_In_School": year, "Profile_URL": profile_url, "Hometown": hometown})

    if players:
        return players

    # --- Strategy B: generic profile link pattern (Penn State / Nebraska / Purdue / Illinois variants) ---
    GENERIC_RE = re.compile(r"/roster/[^/]+/\d+", re.I)
    for link in soup.find_all("a", href=GENERIC_RE):
        href = link["href"]
        pid_m = re.search(r"/(\d+)/?$", href)
        if not pid_m:
            continue
        pid = pid_m.group(1)
        if pid in seen:
            continue
        seen.add(pid)

        profile_url = urljoin(base_url, href)
        name = _extract_name(link)
        if not name or len(name) < 3:
            continue

        card = _find_card(link)
        year = _extract_year(_field_text(card, r"year|class|eligibility|academic"))
        hometown = _field_text(card, r"hometown|city|location") or "N/A"

        players.append({"Name": name, "Year_In_School": year, "Profile_URL": profile_url, "Hometown": hometown})

    if players:
        return players

    # --- Strategy C: s-person cards (some newer Sidearm layouts) ---
    for card in soup.find_all(class_=re.compile(r"s-person|roster-player|player-card", re.I)):
        name_tag = (card.find(class_=re.compile(r"name", re.I)) or card.find(["h2", "h3", "h4"]))
        if not name_tag:
            continue
        name = name_tag.get_text(" ", strip=True)
        if not name or len(name) < 3:
            continue

        link = card.find("a", href=True)
        href = link["href"] if link else ""
        pid_m = re.search(r"/(\d+)/?$", href)
        pid = pid_m.group(1) if pid_m else ""
        if pid in seen:
            continue
        if pid:
            seen.add(pid)

        profile_url = urljoin(base_url, href) if href else "N/A"
        year = _extract_year(_field_text(card, r"year|class|eligibility|academic"))
        hometown = _field_text(card, r"hometown|city|location") or "N/A"

        players.append({"Name": name, "Year_In_School": year, "Profile_URL": profile_url, "Hometown": hometown})

    return players


def _extract_name(link) -> str:
    for tag in ("h2", "h3", "h4", "span", "div"):
        elem = link.find(tag, class_=re.compile(r"name", re.I))
        if elem:
            return elem.get_text(" ", strip=True)
    for tag in ("h2", "h3", "h4"):
        elem = link.find(tag)
        if elem:
            t = elem.get_text(" ", strip=True)
            if len(t) > 2:
                return t
    t = link.get_text(" ", strip=True)
    return t if t and len(t) > 2 and not t.isdigit() else ""


def _find_card(link):
    rx = re.compile(r"roster.player|player.card|athlete|s-person", re.I)
    node = link.parent
    for _ in range(6):
        if node is None:
            break
        if rx.search(" ".join(node.get("class", []))):
            return node
        node = node.parent
    return link.parent


def _field_text(card, pattern: str) -> str:
    if card is None:
        return ""
    elem = card.find(class_=re.compile(pattern, re.I))
    if elem:
        t = elem.get_text(" ", strip=True)
        if 1 < len(t) < 100:
            return t
    return ""


# ---------------------------------------------------------------------------
# Individual player profile page
# ---------------------------------------------------------------------------

async def scrape_player_profile(url: str, browser) -> dict:
    try:
        html = await fetch_rendered(url, browser, wait_for="body")
    except Exception:
        return {}

    soup = BeautifulSoup(html, "html.parser")
    bio = soup.find(class_=re.compile(r"player.bio|athlete.bio|s-person|bio", re.I)) or soup

    year = hometown = ""

    for dt in bio.find_all(["dt", "span", "li", "div"]):
        label = dt.get_text(strip=True).lower()
        sib = dt.find_next_sibling()
        val = sib.get_text(strip=True) if sib else ""
        if any(k in label for k in ["year", "class", "eligibility"]) and len(val) < 30:
            year = val or label
        if any(k in label for k in ["hometown", "city", "home"]) and len(val) < 100:
            hometown = val or label

    if not hometown:
        elem = soup.find(class_=re.compile(r"hometown|city|location", re.I))
        if elem:
            ht = elem.get_text(strip=True)
            if len(ht) < 100:
                hometown = ht

    if not year:
        elem = soup.find(class_=re.compile(r"year|class|eligibility", re.I))
        if elem:
            yt = elem.get_text(strip=True)
            if len(yt) < 30:
                year = yt

    if not hometown:
        m = re.search(r'Hometown[:\s]+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*,\s*[A-Z]{2,})', soup.get_text(), re.I)
        if m:
            hometown = m.group(1)

    return {"Year_In_School": _extract_year(year) if year else "N/A", "Hometown": hometown or "N/A"}


# ---------------------------------------------------------------------------
# Per-school scraper
# ---------------------------------------------------------------------------

async def scrape_school(school_key: str, cfg: dict, browser) -> pd.DataFrame:
    display = cfg["display"]
    log.info(f"\n{'='*60}\nScraping {display} ...")

    html = await fetch_rendered(cfg["roster_url"], browser)
    if not html:
        log.error(f"Could not fetch {display}")
        return pd.DataFrame()

    players = parse_roster_html(html, cfg["base_url"])
    log.info(f"  Found {len(players)} players")

    if not players:
        # Dump a snippet to help debug
        soup = BeautifulSoup(html, "html.parser")
        log.warning(f"  DEBUG — page title: {soup.title.string if soup.title else 'N/A'}")
        log.warning(f"  DEBUG — all <a href> containing 'roster': {[a['href'] for a in soup.find_all('a', href=re.compile(r'roster', re.I))[:5]]}")

    rows = []
    for p in players:
        name     = p["Name"]
        year     = p.get("Year_In_School", "N/A")
        hometown = p.get("Hometown", "N/A")

        if year == "N/A" or hometown == "N/A":
            log.info(f"    Profile fetch: {name}")
            extra = await scrape_player_profile(p["Profile_URL"], browser)
            if year == "N/A":
                year = extra.get("Year_In_School", "N/A")
            if hometown == "N/A":
                hometown = extra.get("Hometown", "N/A")
            await asyncio.sleep(0.5)

        log.info(f"    UTR: {name}")
        utr_rating, utr_url = get_utr_data(name, school=display)
        await asyncio.sleep(0.75)

        rows.append({
            "School":      display,
            "Player":      name,
            "Year":        year,
            "Hometown":    hometown,
            "UTR":         utr_rating,
            "Profile_URL": p["Profile_URL"],
            "UTR_URL":     utr_url,
        })

    cols = ["School", "Player", "Year", "Hometown", "UTR", "Profile_URL", "UTR_URL"]
    return pd.DataFrame(rows, columns=cols)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

async def main():
    all_frames = []

    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True)

        for school_key, cfg in SCHOOLS.items():
            try:
                df = await scrape_school(school_key, cfg, browser)
                if not df.empty:
                    path = os.path.join(ROSTERS_DIR, f"{school_key}_roster.csv")
                    df.to_csv(path, index=False)
                    log.info(f"  Saved {len(df)} rows -> {path}")
                    all_frames.append(df)
                await asyncio.sleep(2)
            except Exception as e:
                log.exception(f"Fatal error on {school_key}: {e}")

        await browser.close()

    if all_frames:
        combined = pd.concat(all_frames, ignore_index=True)
        out = os.path.join(ROSTERS_DIR, "all_rosters.csv")
        combined.to_csv(out, index=False)
        log.info(f"\nCombined -> {out} ({len(combined)} total rows)")
        print(f"\nTotal players scraped: {len(combined)}")
    else:
        log.warning("No data collected.")


if __name__ == "__main__":
    asyncio.run(main())