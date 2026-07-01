import os
import requests
from dotenv import load_dotenv

load_dotenv()

league_id = os.getenv("LEAGUE_ID")
year = os.getenv("YEAR")
url = f"https://lm-api-reads.fantasy.espn.com/apis/v3/games/ffl/seasons/{year}/segments/0/leagues/{league_id}"

r = requests.get(
    url,
    cookies={"SWID": os.getenv("SWID"), "espn_s2": os.getenv("ESPN_S2")},
)
print("Status code:", r.status_code)
print(r.text[:300])
