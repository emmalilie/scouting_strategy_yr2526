import requests
from bs4 import BeautifulSoup

url = "https://gopsusports.com/sports/mens-tennis/schedule/2023-24"
r = requests.get(url, timeout=5)
soup = BeautifulSoup(r.text, "html.parser")

# Get all time elements in order
all_times = soup.find_all("time")
print(f"Total time elements: {len(all_times)}")

# Get table rows
table = soup.find("table")
rows = table.find_all("tr")[1:]  # Skip header
print(f"Total table rows: {len(rows)}")

# Find each row's corresponding time element
for i, row in enumerate(rows[:5]):
    tds = row.find_all("td")
    opponent = tds[0].get_text(strip=True) if len(tds) > 0 else ""
    result = tds[2].get_text(strip=True) if len(tds) > 2 else ""
    
    # Find the closest preceding time element
    time_elem = None
    for elem in row.find_all_previous():
        if elem.name == "time":
            time_elem = elem
            break
    
    date = time_elem.get_text(strip=True) if time_elem else "NO DATE"
    print(f"Row {i}: {date} | {opponent[:30]} | {result}")
