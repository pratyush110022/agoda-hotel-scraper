import time
import json
import math
import os
import pandas as pd
import requests
from seleniumwire import webdriver
from urllib.parse import urlparse, parse_qs

# =========================================================
# 🔧 CONFIG — CHANGE ONLY THIS URL
# =========================================================
URL = "https://www.agoda.com/en-in/search?city=30375&checkIn=2026-03-25&checkOut=2026-03-26&rooms=1&adults=2"


OUTPUT_FILE = "Agoda_Patnitop.xlsx"
GRAPHQL_URL = "https://www.agoda.com/graphql/search"

# =========================================================
# 🧠 Detect search type (city / area / region)
# =========================================================
params = parse_qs(urlparse(URL).query)

SEARCH_TYPE = "city"
SEARCH_ID = None

if "region" in params:
    SEARCH_TYPE = "region"
    SEARCH_ID = int(params["region"][0])
elif "area" in params:
    SEARCH_TYPE = "area"
    SEARCH_ID = int(params["area"][0])
elif "city" in params:
    SEARCH_TYPE = "city"
    SEARCH_ID = int(params["city"][0])

print(f"\n🔎 Search type detected: {SEARCH_TYPE.upper()} ({SEARCH_ID})")

# =========================================================
# 🚀 Step 1: Capture GraphQL request via browser
# =========================================================
print("\nOpening Agoda to capture GraphQL request...\n")

driver = webdriver.Chrome()
driver.get(URL)
driver.requests.clear()

time.sleep(6)
driver.execute_script("window.scrollBy(0, 1200);")
time.sleep(4)

graphql_request = None

for _ in range(30):
    for r in driver.requests:
        if r.response and "graphql/search" in r.url:
            graphql_request = r
            break
    if graphql_request:
        break
    time.sleep(1)

driver.quit()

if not graphql_request:
    print("❌ GraphQL request not found.")
    exit()

print("✅ GraphQL request captured!\n")

# =========================================================
# 📦 Extract headers + payload
# =========================================================
headers = dict(graphql_request.headers)
headers.pop("Content-Length", None)
headers.pop("Host", None)

body = json.loads(graphql_request.body.decode("utf-8"))

# =========================================================
# 🧠 Normalize payload (city / area / region)
# =========================================================
variables = body["variables"]

if SEARCH_TYPE == "region":
    variables.pop("CitySearchRequest", None)
    variables["RegionSearchRequest"]["regionId"] = SEARCH_ID
    ROOT_KEY = "regionSearch"
elif SEARCH_TYPE == "area":
    variables["CitySearchRequest"]["areaId"] = SEARCH_ID
    variables["CitySearchRequest"].pop("cityId", None)
    ROOT_KEY = "citySearch"
else:
    variables["CitySearchRequest"]["cityId"] = SEARCH_ID
    ROOT_KEY = "citySearch"

# =========================================================
# 🔐 Requests session
# =========================================================
session = requests.Session()

# =========================================================
# 🛡 Safe getter
# =========================================================
def safe_get(d, keys, default="N/A"):
    try:
        for k in keys:
            if d is None:
                return default
            if isinstance(k, int):
                if isinstance(d, list) and len(d) > k:
                    d = d[k]
                else:
                    return default
            else:
                d = d.get(k)
        return d if d is not None else default
    except:
        return default

# =========================================================
# 📊 First call → total hotels
# =========================================================
print("Fetching total hotels...\n")

r = session.post(GRAPHQL_URL, headers=headers, json=body)
data = r.json()

total_hotels = safe_get(
    data,
    ["data", ROOT_KEY, "searchResult", "searchInfo", "totalFilteredHotels"],
    default=0
)

page_size = safe_get(
    body,
    ["variables", list(variables.keys())[0], "searchRequest", "page", "pageSize"],
    default=45
)

total_pages = math.ceil(total_hotels / page_size)

print(f"✅ Total Hotels Found: {total_hotels}")
print(f"✅ Total Pages: {total_pages}")

# =========================================================
# 🏨 Scrape all pages
# =========================================================
all_hotels = []

for page in range(1, total_pages + 1):
    print(f"\nScraping Page {page}...")

    variables[list(variables.keys())[0]]["searchRequest"]["page"]["pageNumber"] = page

    resp = session.post(GRAPHQL_URL, headers=headers, json=body)
    page_data = resp.json()

    hotels = safe_get(page_data, ["data", ROOT_KEY, "properties"], default=[])

    for h in hotels:
        info = safe_get(h, ["content", "informationSummary"], default={})

        latitude = safe_get(info, ["geoInfo", "latitude"])
        longitude = safe_get(info, ["geoInfo", "longitude"])

        all_hotels.append({
            "Hotel ID": h.get("propertyId"),
            "Hotel Name": info.get("displayName"),
            "Stars": info.get("rating"),
            "Area": safe_get(info, ["address", "area", "name"]),
            "City": safe_get(info, ["address", "city", "name"]),
            "Latitude": latitude,
            "Longitude": longitude,
            "Google Maps": (
                f"https://maps.google.com/?q={latitude},{longitude}"
                if latitude != "N/A" and longitude != "N/A"
                else "N/A"
            ),
            "Review Score": safe_get(h, ["content", "reviews", "cumulative", "score"]),
            "Review Count": safe_get(h, ["content", "reviews", "cumulative", "reviewCount"]),
            "Price Per Night": safe_get(
                h,
                ["pricing", "offers", "roomOffers", 0,
                 "room", "pricing", "price",
                 "perRoomPerNight", "exclusive", "display"]
            ),
            "Hotel URL": (
                "https://www.agoda.com" +
                safe_get(info, ["propertyLinks", "propertyPage"])
                if safe_get(info, ["propertyLinks", "propertyPage"]) != "N/A"
                else "N/A"
            )
        })

# =========================================================
# 💾 Save Excel safely
# =========================================================
os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)

df = pd.DataFrame(all_hotels)
df.to_excel(OUTPUT_FILE, index=False)

print("\n✅ DONE SUCCESSFULLY!")
print("✅ Hotels scraped:", len(df))
print("✅ File saved:", OUTPUT_FILE)
