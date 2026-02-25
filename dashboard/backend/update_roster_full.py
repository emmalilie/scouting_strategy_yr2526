"""
update_roster_full.py
=====================
Full update pass for an existing roster CSV:
  1. Re-scrapes the stats page for current W/L records
  2. Re-scrapes each player's profile page for Year_In_School and Hometown
  3. Refreshes UTR ratings and profile URLs
  4. Saves updated CSV

This is slower than update_roster.py because it hits UTR for each player.
Run periodically to keep the roster fresh throughout the season.

Usage:
    python update_roster_full.py             # updates all schools
    python update_roster_full.py ucla usc    # updates specific schools

Environment variable (optional):
    UTR_COOKIE=<your session cookie from utrsports.net>
    Setting this improves UTR data quality if the public API is rate-limited.
"""

import sys
import os
import re
import time
import logging
import requests
from bs4 import BeautifulSoup
import pandas as pd
from urllib.parse import urljoin

logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")
log = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}

SEASON = "2025-26"

SCHOOL_CFG = {
    "ucla": {
        "display":    "UCLA Bruins",
        "roster_url": "https://uclabruins.com/sports/mens-tennis/roster",
        "stats_url":  "https://static.uclabruins.com/custompages/Stats/2025-26/MTEN/teamcume.htm",
        "base_url":   "https://uclabruins.com",
    },
    "usc": {
        "display":    "USC Trojans",
        "roster_url": "https://usctrojans.com/sports/mens-tennis/roster",
        "stats_url":  "https://static.usctrojans.com/custompages/Stats/2025-26/MTEN/teamcume.htm",
        "base_url":   "https://usctrojans.com",
    },
    "michigan": {
        "display":    "Michigan Wolverines",
        "roster_url": "https://mgoblue.com/sports/mens-tennis/roster",
        "stats_url":  "https://static.mgoblue.com/custompages/Stats/2025-26/MTEN/teamcume.htm",
        "base_url":   "https://mgoblue.com",
    },
    "ohio_state": {
        "display":    "Ohio State Buckeyes",
        "roster_url": "https://ohiostatebuckeyes.com/sport/mten/roster/",
        "stats_url":  "https://static.ohiostatebuckeyes.com/custompages/Stats/2025-26/MTEN/teamcume.htm",
        "base_url":   "https://ohiostatebuckeyes.com",
    },
    "penn_state": {
        "display":    "Penn State Nittany Lions",
        "roster_url": "https://gopsusports.com/sports/mens-tennis/roster",
        "stats_url":  "https://static.gopsusports.com/custompages/Stats/2025-26/MTEN/teamcume.htm",
        "base_url":   "https://gopsusports.com",
    },
    "indiana": {
        "display":    "Indiana Hoosiers",
        "roster_url": "https://iuhoosiers.com/sports/mens-tennis/roster",
        "stats_url":  "https://static.iuhoosiers.com/custompages/Stats/2025-26/MTEN/teamcume.htm",
        "base_url":   "https://iuhoosiers.com",
    },
    "illinois": {
        "display":    "Illinois Fighting Illini",
        "roster_url": "https://fightingillini.com/sports/mens-tennis/roster",
        "stats_url":  "https://static.fightingillini.com/custompages/Stats/2025-26/MTEN/teamcume.htm",
        "base_url":   "https://fightingillini.com",
    },
    "northwestern": {
        "display":    "Northwestern Wildcats",
        "roster_url": "https://nusports.com/sports/mens-tennis/roster",
        "stats_url":  "https://static.nusports.com/custompages/Stats/2025-26/MTEN/teamcume.htm",
        "base_url":   "https://nusports.com",
    },
    "purdue": {
        "display":    "Purdue Boilermakers",
        "roster_url": "https://purduesports.com/sports/mens-tennis/roster",
        "stats_url":  "https://static.purduesports.com/custompages/Stats/2025-26/MTEN/teamcume.htm",
        "base_url":   "https://purduesports.com",
    },
    "wisconsin": {
        "display":    "Wisconsin Badgers",
        "roster_url": "https://uwbadgers.com/sports/mens-tennis/roster",
        "stats_url":  "https://static.uwbadgers.com/custompages/Stats/2025-26/MTEN/teamcume.htm",
        "base_url":   "https://uwbadgers.com",
    },
    "nebraska": {
        "display":    "Nebraska Cornhuskers",
        "roster_url": "https://huskers.com/sports/mens-tennis/roster",
        "stats_url":  "https://static.huskers.com/custompages/Stats/2025-26/MTEN/teamcume.htm",
        "base_url":   "https://huskers.com",
    },
    "michigan_state": {
        "display":    "Michigan State Spartans",
        "roster_url": "https://msuspartans.com/sports/mens-tennis/roster",
        "stats_url":  "https://static.msuspartans.com/custompages/Stats/2025-26/MTEN/teamcume.htm",
        "base_url":   "https://msuspartans.com",
    },
}

PROFILE_RE = re.compile(r"/(?:sports/mens-tennis|sport/mten)/roster/([^/]+)/(\d+)", re.I)

os.makedirs("rosters", exist_ok=True)


# ---------------------------------------------------------------------------
# HTTP
# ---------------------------------------------------------------------------

def fetch(url: str, timeout: int = 20) -> requests.Response | None:
    for attempt in range(3):
        try:
            r = requests.get(url, headers=HEADERS, timeout=timeout)
            r.raise_for_status()
            return r
        except Exception as e:
            log.warning(f"Attempt {attempt+1} failed for {url}: {e}")
            time.sleep(2 ** attempt)
    return None


# ---------------------------------------------------------------------------
# UTR lookup  (tries multiple endpoint variants)
# ---------------------------------------------------------------------------

def get_utr(name: str, school_display: str = "") -> tuple[str, str]:
    """Returns (rating_str, profile_url)."""
    endpoints = [
        "https://api.utrsports.net/v2/search/players",
        "https://app.utrsports.net/api/v1/search/players",
    ]
    queries = [name]
    if school_display:
        queries.append(f"{name} {school_display}")

    utr_headers = {**HEADERS, "Accept": "application/json"}
    cookie = os.environ.get("UTR_COOKIE", "")
    if cookie:
        utr_headers["Cookie"] = cookie

    for query in queries:
        for ep in endpoints:
            try:
                r = requests.get(
                    ep,
                    headers=utr_headers,
                    params={"query": query, "top": 5},
                    timeout=10,
                )
                if r.status_code != 200:
                    continue
                data = r.json()
                hits = data.get("hits") or data.get("players") or []
                if not hits:
                    continue

                # Prefer results with 'college' membership
                for hit in hits:
                    membership = str(hit.get("membership", "") or hit.get("membershipType", "")).lower()
                    if "college" in membership or "ncaa" in membership:
                        pid  = hit.get("id", "")
                        utr  = hit.get("singlesUtr") or hit.get("singles_utr") or "N/A"
                        return str(utr), f"https://app.utrsports.net/profiles/{pid}" if pid else "N/A"

                hit = hits[0]
                pid = hit.get("id", "")
                utr = hit.get("singlesUtr") or hit.get("singles_utr") or "N/A"
                return str(utr), f"https://app.utrsports.net/profiles/{pid}" if pid else "N/A"

            except Exception as e:
                log.debug(f"UTR API error ({ep}, '{query}'): {e}")

    return "N/A", "N/A"


# ---------------------------------------------------------------------------
# Stats parser
# ---------------------------------------------------------------------------

def _norm(name: str) -> str:
    return re.sub(r"[^a-z ]", "", name.lower()).strip()

SINGLES_WIN_ALIASES  = {"sw", "s-w", "singles_w", "singles wins", "w", "wins"}
SINGLES_LOSS_ALIASES = {"sl", "s-l", "singles_l", "singles losses", "l", "losses"}
DOUBLES_WIN_ALIASES  = {"dw", "d-w", "doubles_w", "doubles wins"}
DOUBLES_LOSS_ALIASES = {"dl", "d-l", "doubles_l", "doubles losses"}


def _col_idx(headers: list[str], aliases: set) -> int:
    for i, h in enumerate(headers):
        if h.lower().strip() in aliases:
            return i
    return -1


def parse_stats(html: str) -> dict[str, dict]:
    soup = BeautifulSoup(html, "html.parser")
    result: dict[str, dict] = {}

    for table in soup.find_all("table"):
        rows = table.find_all("tr")
        if len(rows) < 2:
            continue

        header_texts: list[str] = []
        header_idx = 0
        for i, row in enumerate(rows[:5]):
            texts = [c.get_text(strip=True).lower() for c in row.find_all(["th", "td"])]
            if any(t in texts for t in ["w", "l", "s-w", "d-w", "sw", "dw"]):
                header_texts = texts
                header_idx = i
                break

        if not header_texts:
            continue

        sw = _col_idx(header_texts, SINGLES_WIN_ALIASES)
        sl = _col_idx(header_texts, SINGLES_LOSS_ALIASES)
        dw = _col_idx(header_texts, DOUBLES_WIN_ALIASES)
        dl = _col_idx(header_texts, DOUBLES_LOSS_ALIASES)

        if sw == -1 and len(header_texts) >= 6:
            sw, sl, dw, dl = 1, 2, 4, 5

        for row in rows[header_idx + 1:]:
            cols = [c.get_text(strip=True) for c in row.find_all("td")]
            if not cols or not cols[0]:
                continue
            if cols[0].lower() in {"total", "team", "totals", "singles", "percentage"}:
                continue

            def safe(idx):
                try:
                    return cols[idx] if 0 <= idx < len(cols) and cols[idx] else "0"
                except Exception:
                    return "0"

            result[_norm(cols[0])] = {
                "Singles_W": safe(sw),
                "Singles_L": safe(sl),
                "Doubles_W": safe(dw),
                "Doubles_L": safe(dl),
            }

    return result


def match_stats(name: str, stats: dict) -> dict:
    n = _norm(name)
    if n in stats:
        return stats[n]
    last = n.split()[-1] if n.split() else ""
    for key, val in stats.items():
        if last and last in key.split():
            return val
    return {"Singles_W": "0", "Singles_L": "0", "Doubles_W": "0", "Doubles_L": "0"}


# ---------------------------------------------------------------------------
# Roster page parser
# ---------------------------------------------------------------------------

YEAR_MAP = {
    "freshman": "Fr", "fr": "Fr", "fr.": "Fr",
    "sophomore": "So", "so": "So", "so.": "So",
    "junior": "Jr", "jr": "Jr", "jr.": "Jr",
    "senior": "Sr", "sr": "Sr", "sr.": "Sr",
    "graduate": "Grad", "grad": "Grad",
    "5th year": "Grad", "fifth year": "Grad",
    "redshirt freshman": "RS Fr", "redshirt sophomore": "RS So",
    "redshirt junior": "RS Jr", "redshirt senior": "RS Sr",
}


def _extract_year(text: str) -> str:
    t = text.lower().strip().rstrip(".")
    return YEAR_MAP.get(t, text.title() if text else "N/A")


def _find_card(link):
    card_re = re.compile(r"roster.player|player.card|athlete|s-person|sidearm-roster", re.I)
    node = link.parent
    for _ in range(7):
        if node is None:
            break
        cls = " ".join(node.get("class", []))
        if card_re.search(cls):
            return node
        node = node.parent
    return link.parent


def _get_text_by_class(container, pattern: str) -> str:
    if container is None:
        return ""
    elem = container.find(class_=re.compile(pattern, re.I))
    return elem.get_text(" ", strip=True) if elem else ""


def _extract_name(link, slug: str) -> str:
    for tag in ("h2", "h3", "h4"):
        h = link.find(tag)
        if h:
            t = h.get_text(" ", strip=True)
            if t and len(t) > 2:
                return t

    name_div = link.find(class_=re.compile(r"name", re.I))
    if name_div:
        t = name_div.get_text(" ", strip=True)
        if t and len(t) > 2:
            return t

    t = link.get_text(" ", strip=True)
    if t and len(t) > 2 and not t.isdigit():
        return t

    return slug.replace("-", " ").title()


def parse_roster(html: str, base_url: str) -> list[dict]:
    soup = BeautifulSoup(html, "html.parser")
    players: list[dict] = []
    seen: set[str] = set()

    for link in soup.find_all("a", href=PROFILE_RE):
        href = link.get("href", "")
        m = PROFILE_RE.search(href)
        if not m:
            continue
        slug, pid = m.group(1), m.group(2)
        if pid in seen:
            continue
        seen.add(pid)

        profile_url = href if href.startswith("http") else urljoin(base_url, href)
        card = _find_card(link)
        name = _extract_name(link, slug)
        if not name:
            continue

        year_raw = _get_text_by_class(card, r"academic.year|class.year|eligibility|year")
        year = _extract_year(year_raw) if year_raw else "N/A"

        hometown = _get_text_by_class(card, r"hometown|home.city|high.school")

        players.append({
            "Name":           name,
            "Player_ID":      pid,
            "Year_In_School": year,
            "Hometown":       hometown or "N/A",
            "Profile_URL":    profile_url,
        })

    return players


# ---------------------------------------------------------------------------
# Player profile page (individual page enrichment)
# ---------------------------------------------------------------------------

def enrich_from_profile(profile_url: str) -> dict:
    """Fetch individual player page and extract Year_In_School + Hometown."""
    r = fetch(profile_url)
    if not r:
        return {}

    soup = BeautifulSoup(r.content, "html.parser")
    result = {}

    # Sidearm bio blocks use <dt>/<dd> pairs or labeled <li> items
    for item in soup.find_all(["li", "div", "span"]):
        label_text = item.get_text(strip=True).lower()

        # Year
        if any(kw in label_text for kw in ("year", "class", "eligibility", "academic")):
            sibling = item.find_next_sibling()
            val = sibling.get_text(strip=True) if sibling else label_text
            if not result.get("Year_In_School") and val:
                result["Year_In_School"] = _extract_year(val)

        # Hometown
        if any(kw in label_text for kw in ("hometown", "home city", "high school")):
            sibling = item.find_next_sibling()
            val = sibling.get_text(strip=True) if sibling else ""
            if not result.get("Hometown") and val:
                result["Hometown"] = val

    # Also try definition lists
    for dt in soup.find_all("dt"):
        dd = dt.find_next_sibling("dd")
        if not dd:
            continue
        label = dt.get_text(strip=True).lower()
        value = dd.get_text(strip=True)
        if any(kw in label for kw in ("year", "class", "eligibility")) and not result.get("Year_In_School"):
            result["Year_In_School"] = _extract_year(value)
        if any(kw in label for kw in ("hometown", "city")) and not result.get("Hometown"):
            result["Hometown"] = value

    return result


# ---------------------------------------------------------------------------
# Main update logic
# ---------------------------------------------------------------------------

def update_school_full(school_key: str, cfg: dict) -> None:
    display = cfg["display"]
    roster_path = f"rosters/{school_key}_roster.csv"

    log.info(f"\n{'='*70}")
    log.info(f"Full update: {display}")

    # ---- Load existing roster or start fresh ----
    if os.path.exists(roster_path):
        df = pd.read_csv(roster_path)
        log.info(f"  Loaded {len(df)} existing rows from {roster_path}")
        existing_names = set(df["Player"].str.lower().str.strip())
    else:
        df = pd.DataFrame()
        existing_names = set()
        log.info(f"  No existing roster — will build from scratch")

    # ---- Re-scrape roster page to catch new players ----
    r_roster = fetch(cfg["roster_url"])
    fresh_players: list[dict] = []
    if r_roster:
        fresh_players = parse_roster(r_roster.text, cfg["base_url"])
        log.info(f"  Found {len(fresh_players)} players on live roster page")

    # Merge: add players not in existing roster
    new_rows = []
    for p in fresh_players:
        if p["Name"].lower().strip() not in existing_names:
            new_rows.append({
                "School":         display,
                "Season":         SEASON,
                "Player":         p["Name"],
                "Player_ID":      p["Player_ID"],
                "Year_In_School": p["Year_In_School"],
                "Hometown":       p["Hometown"],
                "Profile_URL":    p["Profile_URL"],
                "UTR_Rating":     "N/A",
                "UTR_URL":        "N/A",
                "Singles_W":      "0",
                "Singles_L":      "0",
                "Singles_Record": "0-0",
                "Doubles_W":      "0",
                "Doubles_L":      "0",
                "Doubles_Record": "0-0",
            })

    if new_rows:
        log.info(f"  Adding {len(new_rows)} new players")
        df = pd.concat([df, pd.DataFrame(new_rows)], ignore_index=True)

    # ---- Fetch updated stats ----
    stats: dict[str, dict] = {}
    r_stats = fetch(cfg["stats_url"])
    if r_stats:
        stats = parse_stats(r_stats.text)
        log.info(f"  Loaded stats for {len(stats)} players")
    else:
        log.warning(f"  Stats page not available")

    # ---- Update each row ----
    for idx, row in df.iterrows():
        name = str(row.get("Player", ""))
        log.info(f"    Updating: {name}")

        # Stats update
        player_stats = match_stats(name, stats)
        df.at[idx, "Singles_W"]      = player_stats["Singles_W"]
        df.at[idx, "Singles_L"]      = player_stats["Singles_L"]
        df.at[idx, "Singles_Record"] = f"{player_stats['Singles_W']}-{player_stats['Singles_L']}"
        df.at[idx, "Doubles_W"]      = player_stats["Doubles_W"]
        df.at[idx, "Doubles_L"]      = player_stats["Doubles_L"]
        df.at[idx, "Doubles_Record"] = f"{player_stats['Doubles_W']}-{player_stats['Doubles_L']}"

        # Profile enrichment (only if year/hometown missing)
        year = str(row.get("Year_In_School", "N/A"))
        hometown = str(row.get("Hometown", "N/A"))
        profile_url = str(row.get("Profile_URL", ""))

        if (year in {"N/A", "", "nan"} or hometown in {"N/A", "", "nan"}) and profile_url.startswith("http"):
            log.info(f"      Fetching profile page: {profile_url}")
            profile_data = enrich_from_profile(profile_url)
            if year in {"N/A", "", "nan"} and profile_data.get("Year_In_School"):
                df.at[idx, "Year_In_School"] = profile_data["Year_In_School"]
            if hometown in {"N/A", "", "nan"} and profile_data.get("Hometown"):
                df.at[idx, "Hometown"] = profile_data["Hometown"]
            time.sleep(0.5)

        # UTR update
        log.info(f"      UTR lookup: {name}")
        utr_rating, utr_url = get_utr(name, display)
        df.at[idx, "UTR_Rating"] = utr_rating
        df.at[idx, "UTR_URL"]    = utr_url
        time.sleep(0.75)

    # Ensure Season column is set
    df["Season"] = SEASON
    if "School" not in df.columns:
        df["School"] = display

    df.to_csv(roster_path, index=False)
    log.info(f"  Saved {len(df)} players -> {roster_path}")

    # Print summary
    print(f"\n{'='*60}")
    print(f"{display}  ({SEASON})")
    print(f"{'='*60}")
    show_cols = [c for c in ["Player", "Year_In_School", "UTR_Rating", "Singles_Record", "Doubles_Record", "Hometown"] if c in df.columns]
    print(df[show_cols].to_string(index=False))


def main():
    targets = sys.argv[1:] if len(sys.argv) > 1 else list(SCHOOL_CFG.keys())

    for school_key in targets:
        if school_key not in SCHOOL_CFG:
            log.error(f"Unknown school: '{school_key}'. Valid: {list(SCHOOL_CFG.keys())}")
            continue
        try:
            update_school_full(school_key, SCHOOL_CFG[school_key])
            time.sleep(2)
        except Exception as e:
            log.exception(f"Error updating {school_key}: {e}")

    # Rebuild combined file
    frames = []
    for school_key in targets:
        path = f"rosters/{school_key}_roster.csv"
        if os.path.exists(path):
            frames.append(pd.read_csv(path))

    if frames:
        combined = pd.concat(frames, ignore_index=True)
        combined.to_csv("rosters/all_rosters.csv", index=False)
        log.info(f"\nCombined: rosters/all_rosters.csv ({len(combined)} total rows)")


if __name__ == "__main__":
    main()