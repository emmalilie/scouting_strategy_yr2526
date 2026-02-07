import requests
from bs4 import BeautifulSoup

url = "https://gopsusports.com/sports/mens-tennis/schedule/2023-24"
r = requests.get(url, timeout=5)
soup = BeautifulSoup(r.text, "html.parser")

# Find all schedule events (rows)
events = soup.find_all("li", class_="schedule-event")
print(f"Found {len(events)} schedule events\n")

for i, event in enumerate(events[:5]):
    # Get date
    date_elem = event.find("time")
    date = date_elem.get_text(strip=True) if date_elem else "NO DATE"
    
    # Get opponent from table row
    table_row = event.find("tr")
    if table_row:
        tds = table_row.find_all("td")
        opponent = tds[0].get_text(strip=True) if len(tds) > 0 else "NO OPPONENT"
        result = tds[2].get_text(strip=True) if len(tds) > 2 else "NO RESULT"
        print(f"Event {i}:")
        print(f"  Date: {date}")
        print(f"  Opponent: {opponent}")
        print(f"  Result: {result}\n")
