"""
update_roster.py
================
Updates an existing roster CSV with fresh season stats (wins/losses)
fetched from the Sidearm static stats page. Merges by player name.
Works for any school — pass the school key as a CLI arg or edit the defaults.

Usage:
    python update_roster.py                    # updates all schools in SCHOOLS
    python update_roster.py ucla               # updates only UCLA
    python update_roster.py ucla usc michigan  # updates multiple schools

Requires:
    - rosters/<school>_roster.csv must already exist (run scrape_all_rosters.py first)
    - pip install requests beautifulsoup4 pandas
"""

import sys
import requests
from bs4 import BeautifulSoup
import pandas as pd
import re
import logging
import os

logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")
log = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    )
}

SEASON = "2025-26"

# Map school key -> stats page URL
# Pattern: https://static.<domain>/custompages/Stats/<season>/MTEN/teamcume.htm
STATS_URLS = {
    "ucla":          "https://static.uclabruins.com/custompages/Stats/2025-26/MTEN/teamcume.htm",
    "usc":           "https://static.usctrojans.com/custompages/Stats/2025-26/MTEN/teamcume.htm",
    "michigan":      "https://static.mgoblue.com/custompages/Stats/2025-26/MTEN/teamcume.htm",
    "ohio_state":    "https://static.ohiostatebuckeyes.com/custompages/Stats/2025-26/MTEN/teamcume.htm",
    "penn_state":    "https://static.gopsusports.com/custompages/Stats/2025-26/MTEN/teamcume.htm",
    "indiana":       "https://static.iuhoosiers.com/custompages/Stats/2025-26/MTEN/teamcume.htm",
    "illinois":      "https://static.fightingillini.com/custompages/Stats/2025-26/MTEN/teamcume.htm",
    "northwestern":  "https://static.nusports.com/custompages/Stats/2025-26/MTEN/teamcume.htm",
    "purdue":        "https://static.purduesports.com/custompages/Stats/2025-26/MTEN/teamcume.htm",
    "wisconsin":     "https://static.uwbadgers.com/custompages/Stats/2025-26/MTEN/teamcume.htm",
    "nebraska":      "https://static.huskers.com/custompages/Stats/2025-26/MTEN/teamcume.htm",
    "michigan_state":"https://static.msuspartans.com/custompages/Stats/2025-26/MTEN/teamcume.htm",
}


# ---------------------------------------------------------------------------
# Stats HTML parser
# ---------------------------------------------------------------------------

SINGLES_WIN_ALIASES  = {"sw", "s-w", "singles_w", "singles wins", "w", "wins"}
SINGLES_LOSS_ALIASES = {"sl", "s-l", "singles_l", "singles losses", "l", "losses"}
DOUBLES_WIN_ALIASES  = {"dw", "d-w", "doubles_w", "doubles wins"}
DOUBLES_LOSS_ALIASES = {"dl", "d-l", "doubles_l", "doubles losses"}


def _col_idx(headers: list[str], aliases: set) -> int:
    for i, h in enumerate(headers):
        if h.lower().strip() in aliases:
            return i
    return -1


def fetch_stats(url: str) -> dict[str, dict]:
    """
    Download the cumulative stats page and parse it.
    Returns {normalized_name: {Singles_W, Singles_L, Doubles_W, Doubles_L}}
    """
    try:
        r = requests.get(url, headers=HEADERS, timeout=20)
        r.raise_for_status()
    except Exception as e:
        log.error(f"Could not fetch stats page {url}: {e}")
        return {}

    soup = BeautifulSoup(r.text, "html.parser")
    result: dict[str, dict] = {}

    for table in soup.find_all("table"):
        rows = table.find_all("tr")
        if len(rows) < 2:
            continue

        # Find header row by looking for stat-like column names
        header_texts: list[str] = []
        header_row_idx = 0
        for i, row in enumerate(rows[:5]):
            cells = row.find_all(["th", "td"])
            texts = [c.get_text(strip=True).lower() for c in cells]
            if any(t in texts for t in ["w", "l", "s-w", "d-w", "sw", "dw", "singles wins"]):
                header_texts = texts
                header_row_idx = i
                break

        if not header_texts:
            continue

        sw = _col_idx(header_texts, SINGLES_WIN_ALIASES)
        sl = _col_idx(header_texts, SINGLES_LOSS_ALIASES)
        dw = _col_idx(header_texts, DOUBLES_WIN_ALIASES)
        dl = _col_idx(header_texts, DOUBLES_LOSS_ALIASES)

        # Positional fallback: Name | SW | SL | S% | DW | DL | D%
        if sw == -1 and len(header_texts) >= 6:
            sw, sl, dw, dl = 1, 2, 4, 5

        for row in rows[header_row_idx + 1:]:
            cols = [c.get_text(strip=True) for c in row.find_all("td")]
            if not cols or not cols[0]:
                continue
            name = cols[0]
            if name.lower() in {"total", "team", "totals", "", "singles", "percentage"}:
                continue

            def safe(idx):
                try:
                    v = cols[idx] if 0 <= idx < len(cols) else "0"
                    return v if v else "0"
                except Exception:
                    return "0"

            result[_norm(name)] = {
                "Singles_W": safe(sw),
                "Singles_L": safe(sl),
                "Doubles_W": safe(dw),
                "Doubles_L": safe(dl),
            }

    return result


def _norm(name: str) -> str:
    return re.sub(r"[^a-z ]", "", name.lower()).strip()


def match_stats(name: str, stats: dict) -> dict | None:
    n = _norm(name)
    if n in stats:
        return stats[n]
    # Last-name fuzzy match
    last = n.split()[-1] if n.split() else ""
    for key, val in stats.items():
        if last and last in key.split():
            return val
    return None


# ---------------------------------------------------------------------------
# Update logic
# ---------------------------------------------------------------------------

def update_school(school_key: str) -> None:
    roster_path = f"rosters/{school_key}_roster.csv"
    if not os.path.exists(roster_path):
        log.warning(f"Roster file not found: {roster_path} — run scrape_all_rosters.py first")
        return

    stats_url = STATS_URLS.get(school_key)
    if not stats_url:
        log.error(f"No stats URL configured for '{school_key}'")
        return

    log.info(f"Fetching stats for {school_key} from {stats_url}")
    stats = fetch_stats(stats_url)

    if not stats:
        log.warning(f"No stats retrieved for {school_key}")
        return

    df = pd.read_csv(roster_path)

    # Ensure stat columns exist
    for col in ["Singles_W", "Singles_L", "Singles_Record", "Doubles_W", "Doubles_L", "Doubles_Record"]:
        if col not in df.columns:
            df[col] = "0"

    updated = 0
    for idx, row in df.iterrows():
        player_stats = match_stats(str(row.get("Player", "")), stats)
        if player_stats:
            df.at[idx, "Singles_W"]      = player_stats["Singles_W"]
            df.at[idx, "Singles_L"]      = player_stats["Singles_L"]
            df.at[idx, "Singles_Record"] = f"{player_stats['Singles_W']}-{player_stats['Singles_L']}"
            df.at[idx, "Doubles_W"]      = player_stats["Doubles_W"]
            df.at[idx, "Doubles_L"]      = player_stats["Doubles_L"]
            df.at[idx, "Doubles_Record"] = f"{player_stats['Doubles_W']}-{player_stats['Doubles_L']}"
            updated += 1

    df.to_csv(roster_path, index=False)
    log.info(f"Updated {updated}/{len(df)} players in {roster_path}")

    # Print updated table
    print(f"\n{'='*60}")
    print(f"{school_key.upper().replace('_', ' ')} — Updated Records")
    print(f"{'='*60}")
    cols_to_show = ["Player", "Year_In_School", "Singles_Record", "Doubles_Record"]
    cols_to_show = [c for c in cols_to_show if c in df.columns]
    print(df[cols_to_show].to_string(index=False))


def main():
    targets = sys.argv[1:] if len(sys.argv) > 1 else list(STATS_URLS.keys())

    for school_key in targets:
        if school_key not in STATS_URLS:
            log.error(f"Unknown school: '{school_key}'. Valid options: {list(STATS_URLS.keys())}")
            continue
        update_school(school_key)


if __name__ == "__main__":
    main()