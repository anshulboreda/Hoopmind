import json
import os
from flask import Flask, render_template, request, session, redirect, url_for, jsonify
import random
from datetime import datetime

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'dev')

# Load all cached data
with open(os.path.join(os.path.dirname(__file__), 'players.json')) as f:
    ALL_PLAYERS = json.load(f)
with open(os.path.join(os.path.dirname(__file__), 'player_details.json')) as f:
    PLAYER_DETAILS = json.load(f)
with open(os.path.join(os.path.dirname(__file__), 'player_stats.json')) as f:
    PLAYER_STATS = json.load(f)

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
    return PLAYER_DETAILS.get(str(player_id), {})

def get_player_clue(player_id):
    stats = PLAYER_STATS.get(str(player_id), {})
    if not stats:
        return "No stats available."
    try:
        gp = float(stats.get('GP', 0))
        ppg = float(stats.get('PTS', 0)) / gp if gp else 0
        rpg = float(stats.get('REB', 0)) / gp if gp else 0
        apg = float(stats.get('AST', 0)) / gp if gp else 0
        return f"Career averages - PPG: {ppg:.1f}, RPG: {rpg:.1f}, APG: {apg:.1f}"
    except Exception:
        return "Clue unavailable."

def compare_guess(guessed, target):
    guessed_conf, guessed_div = get_conf_div(guessed.get('TEAM_ABBREVIATION'))
    target_conf, target_div = get_conf_div(target.get('TEAM_ABBREVIATION'))
    # Height arrow logic
    def to_inches(h):
        if isinstance(h, int): return h
        if not h or h == 'N/A': return None
        if '-' in h:
            ft, inch = h.split('-')
            return int(ft)*12 + int(inch)
        return int(h)
    g_h = to_inches(guessed.get('HEIGHT'))
    t_h = to_inches(target.get('HEIGHT'))
    height_arrow = ''
    if g_h is not None and t_h is not None:
        if g_h < t_h:
            height_arrow = '↑'
        elif g_h > t_h:
            height_arrow = '↓'
    # Weight arrow logic
    guessed_weight = guessed.get('WEIGHT')
    target_weight = target.get('WEIGHT')
    weight_arrow = ''
    try:
        gw = int(guessed_weight) if guessed_weight else None
        tw = int(target_weight) if target_weight else None
        if gw is not None and tw is not None and abs(gw - tw) > 10:
            if gw < tw:
                weight_arrow = '↑'
            elif gw > tw:
                weight_arrow = '↓'
    except Exception:
        weight_arrow = ''
    feedback = {
        'name': guessed.get('DISPLAY_FIRST_LAST', guessed.get('full_name', 'Unknown')),
        'team': guessed.get('TEAM_ABBREVIATION', 'N/A'),
        'position': guessed.get('POSITION', 'N/A'),
        'height': guessed.get('HEIGHT', 'N/A'),
        'weight': int(guessed.get('WEIGHT', 0)) if guessed.get('WEIGHT') else 0,
        'conference': guessed_conf,
        'division': guessed_div,
        'team_match': guessed.get('TEAM_ID') == target.get('TEAM_ID'),
        'position_match': guessed.get('POSITION') and target.get('POSITION') and guessed.get('POSITION').lower() == target.get('POSITION').lower(),
        'height_match': guessed.get('HEIGHT') == target.get('HEIGHT'),
        'weight_match': abs(int(guessed.get('WEIGHT') or 0) - int(target.get('WEIGHT') or 0)) <= 10 if guessed.get('WEIGHT') and target.get('WEIGHT') else False,
        'conference_match': guessed_conf == target_conf and guessed_conf != 'N/A',
        'division_match': guessed_div == target_div and guessed_div != 'N/A',
        'height_arrow': height_arrow,
        'weight_arrow': weight_arrow,
    }
    return feedback

def check_win(guessed, target):
    return guessed.get('DISPLAY_FIRST_LAST', guessed.get('full_name', '')).lower() == target.get('DISPLAY_FIRST_LAST', target.get('full_name', '')).lower()

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
    clue = get_player_clue(target.get('PERSON_ID', target.get('id')))
    silhouette_url = ''  # You can add silhouette logic here if needed
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
                    message = f'🎉 Correct! The player was {target.get("DISPLAY_FIRST_LAST", target.get("full_name", ""))}!'
                    session.pop('target_player')
                elif len(guesses) >= 6:
                    message = f'❌ Game Over! The player was {target.get("DISPLAY_FIRST_LAST", target.get("full_name", ""))}!'
                    session.pop('target_player')
                else:
                    session['reveal_level'] = session.get('reveal_level', 0) + 1
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
