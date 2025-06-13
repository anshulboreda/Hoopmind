from flask import Flask, render_template, request, session, redirect, url_for, jsonify
import random
import json
from datetime import datetime
from nba_api.stats.static import players
from nba_api.stats.endpoints import commonplayerinfo, playercareerstats
import os

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'dev')

# Load all active players once
ALL_PLAYERS = [p for p in players.get_players() if p.get('is_active')]

# Helper to get conference/division from TEAM_ABBREVIATION
def get_conf_div(team_abbr):
    nba_teams = {
        'ATL': ('East', 'Southeast'), 'BOS': ('East', 'Atlantic'), 'BKN': ('East', 'Atlantic'), 'CHA': ('East', 'Southeast'),
        'CHI': ('East', 'Central'), 'CLE': ('East', 'Central'), 'DAL': ('West', 'Southwest'), 'DEN': ('West', 'Northwest'),
        'DET': ('East', 'Central'), 'GSW': ('West', 'Pacific'), 'HOU': ('West', 'Southwest'), 'IND': ('East', 'Central'),
        'LAC': ('West', 'Pacific'), 'LAL': ('West', 'Pacific'), 'MEM': ('West', 'Southwest'), 'MIA': ('East', 'Southeast'),
        'MIL': ('East', 'Central'), 'MIN': ('West', 'Northwest'), 'NOP': ('West', 'Southwest'), 'NYK': ('East', 'Atlantic'),
        'OKC': ('West', 'Northwest'), 'ORL': ('East', 'Southeast'), 'PHI': ('East', 'Atlantic'), 'PHX': ('West', 'Pacific'),
        'POR': ('West', 'Northwest'), 'SAC': ('West', 'Pacific'), 'SAS': ('West', 'Southwest'), 'TOR': ('East', 'Atlantic'),
        'UTA': ('West', 'Northwest'), 'WAS': ('East', 'Southeast')
    }
    return nba_teams.get(team_abbr, ('N/A', 'N/A'))

def get_player_info(player_id):
    info = commonplayerinfo.CommonPlayerInfo(player_id=player_id).get_normalized_dict()
    return info['CommonPlayerInfo'][0] if info['CommonPlayerInfo'] else None

def get_player_clue(player_id):
    try:
        stats = playercareerstats.PlayerCareerStats(player_id=player_id).get_normalized_dict()
        if 'CareerStats' in stats and stats['CareerStats']:
            career = stats['CareerStats'][0]
        elif 'CareerTotalsRegularSeason' in stats and stats['CareerTotalsRegularSeason']:
            career = stats['CareerTotalsRegularSeason'][0]
        else:
            return "No stats available."
        gp = float(career.get('GP', 0))
        ppg = float(career.get('PTS', 0)) / gp if gp else 0
        rpg = float(career.get('REB', 0)) / gp if gp else 0
        apg = float(career.get('AST', 0)) / gp if gp else 0
        return f"Career averages - PPG: {ppg:.1f}, RPG: {rpg:.1f}, APG: {apg:.1f}"
    except Exception as e:
        return f"Clue unavailable."

def compare_guess(guessed, target):
    guessed_conf, guessed_div = get_conf_div(guessed.get('TEAM_ABBREVIATION'))
    target_conf, target_div = get_conf_div(target.get('TEAM_ABBREVIATION'))
    return {
        'name': guessed['DISPLAY_FIRST_LAST'],
        'team': guessed['TEAM_ABBREVIATION'] or 'N/A',
        'position': guessed['POSITION'] or 'N/A',
        'height': guessed['HEIGHT'] or 'N/A',
        'weight': int(guessed['WEIGHT']) if guessed['WEIGHT'] else 0,
        'conference': guessed_conf,
        'division': guessed_div,
        'team_match': guessed['TEAM_ID'] == target['TEAM_ID'],
        'position_match': guessed['POSITION'] and target['POSITION'] and guessed['POSITION'].lower() == target['POSITION'].lower(),
        'height_match': guessed['HEIGHT'] == target['HEIGHT'],
        'weight_match': abs(int(guessed['WEIGHT'] or 0) - int(target['WEIGHT'] or 0)) <= 10 if guessed['WEIGHT'] and target['WEIGHT'] else False,
        'conference_match': guessed_conf == target_conf and guessed_conf != 'N/A',
        'division_match': guessed_div == target_div and guessed_div != 'N/A',
    }

def check_win(guessed, target):
    return guessed['DISPLAY_FIRST_LAST'].lower() == target['DISPLAY_FIRST_LAST'].lower()

def get_silhouette_url(person_id):
    from PIL import Image
    import requests
    from io import BytesIO
    import base64
    resolutions = [
        None,  # 0: blank
        '52x40',  # 1: very blurry
        '104x76', # 2: blurry
        '260x190', # 3: low-res
        '520x380', # 4: mid-res
        '1040x760' # 5: full-res
    ]
    res = resolutions[min(session.get('reveal_level', 0), len(resolutions)-1)]
    if res is None:
        return ''
    url = f"https://cdn.nba.com/headshots/nba/latest/{res}/{person_id}.png"
    try:
        resp = requests.get(url, timeout=3)
        if resp.status_code == 200:
            img = Image.open(BytesIO(resp.content)).convert("RGBA")
            gray = img.convert("L")
            mask = gray.point(lambda x: 0 if x > 40 else 255, mode='1')
            silhouette = Image.new("RGBA", img.size, (255,255,255,0))
            for y in range(img.size[1]):
                for x in range(img.size[0]):
                    if mask.getpixel((x, y)) == 255:
                        silhouette.putpixel((x, y), (0,0,0,255))
                    else:
                        silhouette.putpixel((x, y), (255,255,255,0))
            buf = BytesIO()
            silhouette.save(buf, format='PNG')
            buf.seek(0)
            b64 = base64.b64encode(buf.read()).decode('utf-8')
            return f"data:image/png;base64,{b64}"
        else:
            return ''
    except Exception:
        return ''

@app.route('/', methods=['GET', 'POST'])
def index():
    if 'target_player' not in session:
        player = random.choice(ALL_PLAYERS)
        info = get_player_info(player['id'])
        session['target_player'] = info
        session['guesses'] = []
        session['reveal_level'] = 0
    target = session['target_player']
    guesses = session.get('guesses', [])
    message = ''
    clue = get_player_clue(target['PERSON_ID'])
    silhouette_url = get_silhouette_url(target['PERSON_ID'])
    if request.method == 'POST':
        guess_name = request.form['guess'].strip()
        found = [p for p in ALL_PLAYERS if guess_name.lower() in p['full_name'].lower()]
        if not found:
            message = 'Player not found. Try again.'
        else:
            guessed = get_player_info(found[0]['id'])
            if not guessed:
                message = 'Player data not found. Try again.'
            else:
                feedback = compare_guess(guessed, target)
                guesses.append(feedback)
                session['guesses'] = guesses
                if check_win(guessed, target):
                    message = f'🎉 Correct! The player was {target["DISPLAY_FIRST_LAST"]}!'
                    session.pop('target_player')
                elif len(guesses) >= 6:
                    message = f'❌ Game Over! The player was {target["DISPLAY_FIRST_LAST"]}!'
                    session.pop('target_player')
                else:
                    session['reveal_level'] = session.get('reveal_level', 0) + 1
                silhouette_url = get_silhouette_url(target['PERSON_ID'])
    return render_template('index.html', guesses=guesses, message=message, clue=clue, silhouette_url=silhouette_url)

@app.route('/reset')
def reset():
    session.pop('target_player', None)
    session.pop('guesses', None)
    session.pop('reveal_level', None)
    return redirect(url_for('index'))

@app.route('/player_suggestions')
def player_suggestions():
    query = request.args.get('q', '').strip().lower()
    if not query or len(query) < 2:
        return jsonify([])
    matches = [p['full_name'] for p in ALL_PLAYERS if query in p['full_name'].lower()][:10]
    return jsonify(matches)

if __name__ == '__main__':
    app.run(debug=True)
