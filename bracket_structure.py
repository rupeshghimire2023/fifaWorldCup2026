def get_bracket_structure():
    """
    Returns the bracket structure with matches organized by their position
    Left side leads to Final via top path
    Right side leads to Final via bottom path
    """
    return {
        'left_r16': [74, 77, 73, 75, 83, 84, 81, 82],  # Left side Round of 16
        'right_r16': [76, 78, 79, 80, 86, 88, 85, 87],  # Right side Round of 16
        'left_qf': [90, 89, 93, 94],  # Left side Quarter Finals
        'right_qf': [91, 92, 95, 96],  # Right side Quarter Finals
        'left_sf': [97, 99],  # Left side Semi Finals
        'right_sf': [98, 100],  # Right side Semi Finals
        'left_ff': [101],  # Left Final Four (top bracket winner)
        'right_ff': [102],  # Right Final Four (bottom bracket winner)
    }

def get_match_by_id(match_id, bracket_data):
    """Get match data by match_id"""
    all_matches = (
        bracket_data['bracket']['round_of_16'] +
        bracket_data['bracket']['quarter_finals'] +
        bracket_data['bracket']['semi_finals'] +
        bracket_data['bracket']['final_four']
    )
    for match in all_matches:
        if match['match_id'] == match_id:
            return match
    return None
