import json
from datetime import datetime
import pytz

def load_bracket_data():
    with open('bracket_data.json', 'r') as f:
        return json.load(f)

def is_selection_locked():
    est = pytz.timezone('US/Eastern')
    cutoff = est.localize(datetime(2026, 7, 4, 12, 0, 0))
    now = datetime.now(est)
    return now >= cutoff

def get_teams_for_match(match, selections):
    team_home = match['team_home']
    team_away = match['team_away']
    
    if team_home.startswith('W') or team_home.startswith('L'):
        match_id = int(team_home[1:])
        team_home = selections.get(str(match_id), '???')
    
    if team_away.startswith('W') or team_away.startswith('L'):
        match_id = int(team_away[1:])
        team_away = selections.get(str(match_id), '???')
    
    return team_home, team_away

def validate_bracket(selections):
    bracket_data = load_bracket_data()
    
    for match in bracket_data['bracket']['round_of_32']:
        match_id = str(match['match_id'])
        if match_id not in selections:
            return False, f"Missing selection for match {match_id}"
    
    for match in bracket_data['bracket']['round_of_16']:
        match_id = str(match['match_id'])
        if match_id not in selections:
            return False, f"Missing selection for match {match_id}"
    
    for match in bracket_data['bracket']['quarter_finals']:
        match_id = str(match['match_id'])
        if match_id not in selections:
            return False, f"Missing selection for match {match_id}"
    
    for match in bracket_data['bracket']['semi_finals']:
        match_id = str(match['match_id'])
        if match_id not in selections:
            return False, f"Missing selection for match {match_id}"
    
    final_match_id = str(bracket_data['bracket']['final']['match_id'])
    if final_match_id not in selections:
        return False, "Missing selection for final"
    
    return True, None

def get_available_teams_from_round32():
    bracket_data = load_bracket_data()
    teams = set()
    
    for match in bracket_data['bracket']['round_of_32']:
        teams.add(match['team_home'])
        teams.add(match['team_away'])
    
    return sorted(list(teams))
