"""
Live match tracking for FIFA World Cup 2026
Fetches live match data from a secure API source
"""

import json
import os
from datetime import datetime
import pytz

def get_live_match_from_file():
    """
    Get live match data from local JSON file
    This can be updated by admin or external script
    """
    try:
        if os.path.exists('live_match.json'):
            with open('live_match.json', 'r') as f:
                data = json.load(f)
                return data
        return None
    except Exception as e:
        print(f"Error loading live match: {str(e)}")
        return None

def update_live_match(match_id, team_home, team_away, score_home, score_away, status, minute=None):
    """
    Update live match data (Admin function)
    Status: 'live', 'halftime', 'finished', 'scheduled'
    """
    data = {
        'match_id': match_id,
        'team_home': team_home,
        'team_away': team_away,
        'score_home': score_home,
        'score_away': score_away,
        'status': status,
        'minute': minute,
        'updated_at': datetime.now(pytz.timezone('US/Eastern')).isoformat()
    }
    
    try:
        with open('live_match.json', 'w') as f:
            json.dump(data, f, indent=2)
        return True
    except Exception as e:
        print(f"Error updating live match: {str(e)}")
        return False

def clear_live_match():
    """Clear live match data"""
    try:
        if os.path.exists('live_match.json'):
            os.remove('live_match.json')
        return True
    except Exception as e:
        print(f"Error clearing live match: {str(e)}")
        return False

def format_live_match_display(match_data):
    """Format match data for display"""
    if not match_data:
        return None
    
    status = match_data.get('status', '')
    minute = match_data.get('minute', '')
    
    status_text = {
        'live': f"⚽ LIVE {minute}'" if minute else "⚽ LIVE",
        'halftime': "⏸️ HALFTIME",
        'finished': "✅ FINAL",
        'scheduled': "📅 UPCOMING"
    }.get(status, status)
    
    return {
        'match_id': match_data.get('match_id'),
        'team_home': match_data.get('team_home'),
        'team_away': match_data.get('team_away'),
        'score_home': match_data.get('score_home'),
        'score_away': match_data.get('score_away'),
        'status_text': status_text,
        'status': status
    }
