from nba_api.stats.static import players
from nba_api.stats.endpoints import commonplayerinfo, playercareerstats
import json
import time
import os

print("Starting player data fetch...", flush=True)

# Fetch all active players
all_players = [p for p in players.get_players() if p.get('is_active')]

# Save basic player info
with open('players.json', 'w') as f:
    json.dump(all_players, f)

# Load existing details and stats if present
if os.path.exists('player_details.json'):
    with open('player_details.json') as f:
        player_details = json.load(f)
else:
    player_details = {}
if os.path.exists('player_stats.json'):
    with open('player_stats.json') as f:
        player_stats = json.load(f)
else:
    player_stats = {}

# Fetch and save detailed info for each player
for p in all_players:
    pid = str(p['id'])
    if pid in player_details and player_details[pid]:
        print(f"Skipping {p['full_name']} (already cached)", flush=True)
        continue
    try:
        info = commonplayerinfo.CommonPlayerInfo(player_id=pid).get_normalized_dict()
        player_details[pid] = info['CommonPlayerInfo'][0] if info['CommonPlayerInfo'] else {}
        stats = playercareerstats.PlayerCareerStats(player_id=pid).get_normalized_dict()
        if 'CareerStats' in stats and stats['CareerStats']:
            player_stats[pid] = stats['CareerStats'][0]
        elif 'CareerTotalsRegularSeason' in stats and stats['CareerTotalsRegularSeason']:
            player_stats[pid] = stats['CareerTotalsRegularSeason'][0]
        else:
            player_stats[pid] = {}
        print(f"Fetched {p['full_name']}", flush=True)
        time.sleep(2)  # Increased sleep to 2 seconds to avoid rate limiting
    except Exception as e:
        print(f"Error fetching {p['full_name']}: {e}", flush=True)
        player_details[pid] = {}
        player_stats[pid] = {}

with open('player_details.json', 'w') as f:
    json.dump(player_details, f)
with open('player_stats.json', 'w') as f:
    json.dump(player_stats, f)
print("Done!", flush=True)
