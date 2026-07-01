import streamlit as st
from supabase_config import create_user, get_user_by_email, save_bracket, get_user_bracket, get_all_brackets
from bracket_logic import load_bracket_data, is_selection_locked, get_teams_for_match, validate_bracket, get_available_teams_from_round32, load_completed_matches, is_match_completed, get_completed_match_winner
from country_flags import get_flag
from country_colors import get_country_gradient
from live_match_tracker import get_live_match_from_file, format_live_match_display, update_live_match, clear_live_match
import os
from dotenv import load_dotenv
import time
from datetime import datetime, timedelta
import hashlib
import json

load_dotenv()

st.set_page_config(page_title="FIFA World Cup 2026 Bracket Challenge", layout="wide", initial_sidebar_state="collapsed")

# Session timeout: 15 minutes (in seconds)
SESSION_TIMEOUT = 15 * 60

# Create a simple session token
def create_session_token(user_id, email):
    """Create a session token"""
    timestamp = str(time.time())
    data = f"{user_id}:{email}:{timestamp}"
    return hashlib.md5(data.encode()).hexdigest()

# Store session in browser using custom component (HTML local storage)
def store_session_in_browser(user_id, email, name, is_admin=False):
    """Store session data in browser using HTML localStorage"""
    session_data = {
        'user_id': user_id,
        'email': email,
        'name': name,
        'is_admin': is_admin,
        'timestamp': time.time()
    }
    session_json = json.dumps(session_data)
    
    # Inject JavaScript to store in localStorage
    st.components.v1.html(f"""
        <script>
            localStorage.setItem('fifa_session', '{session_json}');
            console.log('Session stored');
        </script>
    """, height=0)

def get_session_from_browser():
    """Retrieve session from browser localStorage"""
    # Use HTML component to read from localStorage
    session_html = st.components.v1.html("""
        <script>
            const session = localStorage.getItem('fifa_session');
            if (session) {{
                window.parent.postMessage({{type: 'streamlit:setComponentValue', value: session}}, '*');
            }} else {{
                window.parent.postMessage({{type: 'streamlit:setComponentValue', value: null}}, '*');
            }}
        </script>
    """, height=0)
    
    return session_html

def clear_browser_session():
    """Clear session from browser localStorage"""
    st.components.v1.html("""
        <script>
            localStorage.removeItem('fifa_session');
            console.log('Session cleared');
        </script>
    """, height=0)

# Initialize session state
if 'session_initialized' not in st.session_state:
    st.session_state.session_initialized = False
    st.session_state.logged_in = False
    st.session_state.user_id = None
    st.session_state.user_email = None
    st.session_state.user_name = None
    st.session_state.last_activity = None
    st.session_state.admin_logged_in = False
    st.session_state.admin_last_activity = None
    st.session_state.selections = {}
    st.session_state.champion = None
    st.session_state.final_score = {"home": "", "away": ""}

# Try to restore session from query params (simpler approach)
if not st.session_state.session_initialized:
    query_params = st.query_params
    
    if 'user_id' in query_params and 'email' in query_params:
        user_id = query_params.get('user_id')
        email = query_params.get('email')
        timestamp = float(query_params.get('timestamp', 0))
        
        # Check if session is still valid (within 15 minutes)
        if time.time() - timestamp < SESSION_TIMEOUT:
            # Restore session
            user = get_user_by_email(email)
            if user and str(user['id']) == user_id:
                st.session_state.logged_in = True
                st.session_state.user_id = user['id']
                st.session_state.user_email = user['email']
                st.session_state.user_name = user['name']
                st.session_state.last_activity = timestamp
                
                # Load bracket
                bracket = get_user_bracket(user['id'])
                if bracket:
                    st.session_state.selections = bracket.get('selections', {})
                    st.session_state.champion = bracket.get('champion')
                    st.session_state.final_score = bracket.get('final_score', {"home": "", "away": ""})
    
    elif 'admin' in query_params:
        admin_timestamp = float(query_params.get('admin_timestamp', 0))
        if time.time() - admin_timestamp < SESSION_TIMEOUT:
            st.session_state.admin_logged_in = True
            st.session_state.admin_last_activity = admin_timestamp
    
    st.session_state.session_initialized = True

if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user_id = None
    st.session_state.user_email = None
    st.session_state.user_name = None
    st.session_state.last_activity = None

if 'admin_logged_in' not in st.session_state:
    st.session_state.admin_logged_in = False
    st.session_state.admin_last_activity = None

if 'selections' not in st.session_state:
    st.session_state.selections = {}

if 'champion' not in st.session_state:
    st.session_state.champion = None

if 'final_score' not in st.session_state:
    st.session_state.final_score = {"home": "", "away": ""}

# Update query params to persist session
def persist_session():
    """Persist session in URL query params"""
    if st.session_state.logged_in:
        st.query_params.update({
            'user_id': str(st.session_state.user_id),
            'email': st.session_state.user_email,
            'timestamp': str(time.time())
        })
    elif st.session_state.admin_logged_in:
        st.query_params.update({
            'page': 'admin',
            'admin': 'true',
            'admin_timestamp': str(time.time())
        })
    else:
        st.query_params.clear()


# Check for session timeout
def check_session_timeout():
    """Check if user session has timed out (15 min inactivity)"""
    current_time = time.time()
    
    # Check regular user session
    if st.session_state.logged_in and st.session_state.last_activity:
        if current_time - st.session_state.last_activity > SESSION_TIMEOUT:
            # Session expired
            st.session_state.logged_in = False
            st.session_state.user_id = None
            st.session_state.user_email = None
            st.session_state.user_name = None
            st.session_state.selections = {}
            st.session_state.champion = None
            st.session_state.final_score = {"home": "", "away": ""}
            st.session_state.last_activity = None
            return True
    
    # Check admin session
    if st.session_state.admin_logged_in and st.session_state.admin_last_activity:
        if current_time - st.session_state.admin_last_activity > SESSION_TIMEOUT:
            st.session_state.admin_logged_in = False
            st.session_state.admin_last_activity = None
            return True
    
    return False

def update_activity():
    """Update last activity timestamp"""
    current_time = time.time()
    if st.session_state.logged_in:
        st.session_state.last_activity = current_time
    if st.session_state.admin_logged_in:
        st.session_state.admin_last_activity = current_time

def render_live_match_navbar():
    """Render live match ticker navbar"""
    match_data = get_live_match_from_file()
    
    if match_data and match_data.get('match_id'):
        formatted = format_live_match_display(match_data)
        
        if formatted:
            # Color based on status
            status_colors = {
                'live': '#28a745',  # Green for live
                'halftime': '#ffc107',  # Yellow for halftime
                'finished': '#6c757d',  # Gray for finished
                'scheduled': '#17a2b8'  # Blue for scheduled
            }
            bg_color = status_colors.get(formatted['status'], '#17a2b8')
            
            # Animated pulse for live matches
            animation = """
                @keyframes pulse {
                    0%, 100% { opacity: 1; }
                    50% { opacity: 0.7; }
                }
            """ if formatted['status'] == 'live' else ""
            
            animation_style = "animation: pulse 2s infinite;" if formatted['status'] == 'live' else ""
            
            home_flag = get_flag(formatted['team_home'])
            away_flag = get_flag(formatted['team_away'])
            
            st.markdown(f"""
                <style>
                {animation}
                </style>
                <div style="
                    position: sticky;
                    top: 0;
                    z-index: 999;
                    background: {bg_color};
                    color: white;
                    padding: 12px 20px;
                    text-align: center;
                    font-weight: bold;
                    font-size: 16px;
                    box-shadow: 0 2px 8px rgba(0,0,0,0.2);
                    {animation_style}
                    border-bottom: 3px solid rgba(255,255,255,0.3);
                ">
                    <span style="background: rgba(255,255,255,0.2); padding: 4px 12px; border-radius: 20px; margin-right: 15px;">
                        {formatted['status_text']}
                    </span>
                    <span style="font-size: 18px;">
                        {home_flag} {formatted['team_home']} 
                        <span style="font-size: 24px; margin: 0 15px; color: #ffd700;">{formatted['score_home']} - {formatted['score_away']}</span>
                        {formatted['team_away']} {away_flag}
                    </span>
                    <span style="margin-left: 15px; font-size: 12px; opacity: 0.9;">
                        Match {formatted['match_id']}
                    </span>
                </div>
            """, unsafe_allow_html=True)


def login_page():
    st.title("⚽ FIFA World Cup 2026 Bracket Challenge")
    
    # Check if signup is locked (after deadline)
    signup_locked = is_selection_locked()
    
    if signup_locked:
        # Only show login after deadline
        st.subheader("Login to View Your Bracket")
        st.info("🔒 Signup is closed. The tournament has started! Login to view your predictions.")
        
        email = st.text_input("Email", key="login_email")
        
        if st.button("Login", key="login_btn"):
            user = get_user_by_email(email)
            if user:
                st.session_state.logged_in = True
                st.session_state.user_id = user['id']
                st.session_state.user_email = user['email']
                st.session_state.user_name = user['name']
                st.session_state.last_activity = time.time()
                
                bracket = get_user_bracket(user['id'])
                if bracket:
                    st.session_state.selections = bracket.get('selections', {})
                    st.session_state.champion = bracket.get('champion')
                    st.session_state.final_score = bracket.get('final_score', {"home": "", "away": ""})
                
                # Persist session
                persist_session()
                st.rerun()
            else:
                st.error("User not found. Signup is now closed.")
    else:
        # Show both login and signup before deadline
        tab1, tab2 = st.tabs(["Login", "Sign Up"])
        
        with tab1:
            st.subheader("Login")
            email = st.text_input("Email", key="login_email")
            
            if st.button("Login", key="login_btn"):
                user = get_user_by_email(email)
                if user:
                    st.session_state.logged_in = True
                    st.session_state.user_id = user['id']
                    st.session_state.user_email = user['email']
                    st.session_state.user_name = user['name']
                    st.session_state.last_activity = time.time()
                    
                    bracket = get_user_bracket(user['id'])
                    if bracket:
                        st.session_state.selections = bracket.get('selections', {})
                        st.session_state.champion = bracket.get('champion')
                        st.session_state.final_score = bracket.get('final_score', {"home": "", "away": ""})
                    
                    # Persist session
                    persist_session()
                    st.rerun()
                else:
                    st.error("User not found. Please sign up first.")
        
        with tab2:
            st.subheader("Sign Up")
            name = st.text_input("Full Name", key="signup_name")
            email = st.text_input("Email", key="signup_email")
            
            if st.button("Sign Up", key="signup_btn"):
                if name and email:
                    user_id, error = create_user(email, name)
                    if error:
                        st.error(error)
                    else:
                        # Auto-login after successful signup
                        st.session_state.logged_in = True
                        st.session_state.user_id = user_id
                        st.session_state.user_name = name
                        st.session_state.user_email = email
                        st.session_state.last_activity = time.time()
                        
                        # Load existing bracket if any
                        existing_bracket = get_user_bracket(user_id)
                        if existing_bracket:
                            st.session_state.selections = existing_bracket.get('selections', {})
                            st.session_state.champion = existing_bracket.get('champion')
                            st.session_state.final_score = existing_bracket.get('final_score', {"home": "", "away": ""})
                        else:
                            st.session_state.selections = {}
                            st.session_state.champion = None
                            st.session_state.final_score = {"home": "", "away": ""}
                        
                        # Persist session
                        persist_session()
                        st.success("✅ Account created successfully! Redirecting to bracket...")
                        st.rerun()
                else:
                    st.error("Please fill in all fields.")

def admin_login_page():
    """Separate admin login page accessible via /admin route"""
    st.title("🔐 Admin Login")
    
    st.info("📌 Admin access only. You must navigate to `?page=admin` to access this page.")
    
    admin_password = st.text_input("Admin Password", type="password", key="admin_password")
    
    if st.button("Admin Login", key="admin_login_btn", use_container_width=True):
        if admin_password == os.getenv('ADMIN_PASSWORD'):
            st.session_state.admin_logged_in = True
            st.session_state.admin_last_activity = time.time()
            persist_session()
            st.rerun()
        else:
            st.error("❌ Invalid admin password")
    
    st.markdown("---")
    st.caption("Unauthorized access is prohibited.")

def get_match_winner(match_id, selections):
    """Get the winner of a specific match"""
    return selections.get(str(match_id), None)

def is_team_advancing(match_id, team_name, selections, next_round_matches):
    """Check if a team from this match advances to the next round"""
    winner = get_match_winner(match_id, selections)
    return winner == team_name

def render_match_box(match, selections, locked, position_prefix):
    """Render a complete match box with both teams inside"""
    match_id = match['match_id']
    team_home = match['team_home']
    team_away = match['team_away']
    
    # Check if this match is completed (result already determined)
    is_completed = is_match_completed(match_id)
    completed_winner = get_completed_match_winner(match_id) if is_completed else None
    
    # If match is completed, use the official result
    if is_completed and completed_winner:
        selections[str(match_id)] = completed_winner
    
    # Resolve team names if they reference previous match winners
    if team_home.startswith('W'):
        prev_match_id = int(team_home[1:])
        team_home = selections.get(str(prev_match_id), 'TBD')
    if team_away.startswith('W'):
        prev_match_id = int(team_away[1:])
        team_away = selections.get(str(prev_match_id), 'TBD')
    
    winner = get_match_winner(match_id, selections)
    
    # Disable selection if match is completed OR locked OR teams not determined
    can_select = team_home != 'TBD' and team_away != 'TBD' and not locked and not is_completed
    
    flag_home = get_flag(team_home)
    flag_away = get_flag(team_away)
    
    # Match header with completed badge
    match_header = f"Match {match_id} • {match.get('date', '')}"
    if is_completed:
        match_header = f"✅ {match_header} • FINAL"
    
    # Render match container
    st.markdown(f"""
        <div style="background: white; border: 2px solid {'#28a745' if is_completed else '#dee2e6'}; border-radius: 8px; 
                    padding: 8px; margin: 5px 0;">
            <div style="text-align: center; font-size: 10px; color: {'#28a745' if is_completed else '#666'}; 
                        font-weight: bold; margin-bottom: 5px; border-bottom: 1px solid #eee; padding-bottom: 5px;">
                {match_header}
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    # Team buttons
    if team_home == 'TBD':
        st.markdown(f"""
            <div style="padding: 8px; margin: 2px 0; background: #f0f0f0; 
                        border: 1px solid #ddd; border-radius: 5px; text-align: center; color: #999; font-size: 13px;">
                {flag_home} {team_home}
            </div>
        """, unsafe_allow_html=True)
    else:
        is_winner = winner == team_home
        is_loser = is_completed and winner != team_home
        
        # Show disabled/grayed out for losers in completed matches
        if is_loser:
            st.markdown(f"""
                <div style="padding: 8px; margin: 2px 0; background: #f0f0f0; 
                            border: 1px solid #ddd; border-radius: 5px; text-align: center; 
                            color: #999; font-size: 13px; text-decoration: line-through;">
                    {flag_home} {team_home} ❌
                </div>
            """, unsafe_allow_html=True)
        else:
            if st.button(
                f"{flag_home} {team_home} {'🏆' if is_completed and is_winner else ''}",
                key=f"{position_prefix}_home_{match_id}_{team_home[:3]}",
                disabled=not can_select,
                use_container_width=True,
                type="primary" if is_winner else "secondary"
            ):
                if can_select:
                    st.session_state.selections[str(match_id)] = team_home
                    st.rerun()
    
    if team_away == 'TBD':
        st.markdown(f"""
            <div style="padding: 8px; margin: 2px 0; background: #f0f0f0; 
                        border: 1px solid #ddd; border-radius: 5px; text-align: center; color: #999; font-size: 13px;">
                {flag_away} {team_away}
            </div>
        """, unsafe_allow_html=True)
    else:
        is_winner = winner == team_away
        is_loser = is_completed and winner != team_away
        
        if is_loser:
            st.markdown(f"""
                <div style="padding: 8px; margin: 2px 0; background: #f0f0f0; 
                            border: 1px solid #ddd; border-radius: 5px; text-align: center; 
                            color: #999; font-size: 13px; text-decoration: line-through;">
                    {flag_away} {team_away} ❌
                </div>
            """, unsafe_allow_html=True)
        else:
            if st.button(
                f"{flag_away} {team_away} {'🏆' if is_completed and is_winner else ''}",
                key=f"{position_prefix}_away_{match_id}_{team_away[:3]}",
                disabled=not can_select,
                use_container_width=True,
                type="primary" if is_winner else "secondary"
            ):
                if can_select:
                    st.session_state.selections[str(match_id)] = team_away
                    st.rerun()

def render_team_button(team_name, is_winner, can_select, match_id, position, locked):
    """Render a team selection button with proper styling"""
    flag = get_flag(team_name)
    
    if team_name == 'TBD':
        st.markdown(f"""
            <div style="padding: 10px; margin: 3px 0; background: #f0f0f0; 
                        border: 1px solid #ddd; border-radius: 5px; text-align: center; color: #999;">
                {flag} {team_name}
            </div>
        """, unsafe_allow_html=True)
    else:
        if st.button(
            f"{flag} {team_name}",
            key=f"{position}_{match_id}_{team_name[:3]}",
            disabled=not can_select,
            use_container_width=True,
            type="primary" if is_winner else "secondary"
        ):
            if can_select:
                st.session_state.selections[str(match_id)] = team_name
                st.rerun()

def render_connector_for_pair(match1_id, match2_id, team1_home, team1_away, team2_home, team2_away, selections, is_left_side=True):
    """Render simple bracket connector lines for a PAIR of matches feeding into next round"""
    winner1 = get_match_winner(match1_id, selections)
    winner2 = get_match_winner(match2_id, selections)
    
    # Colors - green if team selected, gray if not
    m1_color = "#28a745" if winner1 else "#d0d0d0"
    m2_color = "#28a745" if winner2 else "#d0d0d0"
    winner_color = "#28a745" if (winner1 or winner2) else "#d0d0d0"
    line_width = "2px"
    
    if is_left_side:
        return f"""
<div style="height: 200px; position: relative; margin: 0; padding: 0;">
    <div style="position: absolute; top: 25%; left: 0; width: 50%; border-top: {line_width} solid {m1_color};"></div>
    <div style="position: absolute; top: 25%; left: 50%; height: 50%; border-left: {line_width} solid {winner_color};"></div>
    <div style="position: absolute; bottom: 25%; left: 0; width: 50%; border-top: {line_width} solid {m2_color};"></div>
    <div style="position: absolute; top: 50%; left: 50%; width: 50%; border-top: {line_width} solid {winner_color};"></div>
</div>
"""
    else:
        return f"""
<div style="height: 200px; position: relative; margin: 0; padding: 0;">
    <div style="position: absolute; top: 25%; right: 0; width: 50%; border-top: {line_width} solid {m1_color};"></div>
    <div style="position: absolute; top: 25%; right: 50%; height: 50%; border-left: {line_width} solid {winner_color};"></div>
    <div style="position: absolute; bottom: 25%; right: 0; width: 50%; border-top: {line_width} solid {m2_color};"></div>
    <div style="position: absolute; top: 50%; right: 50%; width: 50%; border-top: {line_width} solid {winner_color};"></div>
</div>
"""

def bracket_page():
    st.markdown("""
        <style>
        .bracket-header {
            text-align: center;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 20px;
            border-radius: 10px;
            margin-bottom: 20px;
        }
        .bracket-header h1 {
            color: white;
            margin: 0;
            font-size: clamp(1.5rem, 4vw, 2.5rem);
        }
        .bracket-header h3 {
            color: white;
            font-size: clamp(1rem, 2.5vw, 1.5rem);
        }
        .match-box {
            background: white;
            border: 2px solid #dee2e6;
            border-radius: 8px;
            padding: 10px;
            margin: 10px 0;
        }
        .match-title {
            text-align: center;
            font-size: 11px;
            color: #666;
            margin-bottom: 8px;
            font-weight: bold;
        }
        .round-title {
            text-align: center;
            font-weight: bold;
            font-size: 16px;
            padding: 8px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border-radius: 8px;
            margin-bottom: 15px;
        }
        
        /* Responsive adjustments */
        @media (max-width: 1200px) {
            .stColumn {
                min-width: 100px !important;
            }
            .round-title {
                font-size: 12px;
                padding: 5px;
            }
            .match-title {
                font-size: 9px;
            }
        }
        
        @media (max-width: 768px) {
            .bracket-header h1 {
                font-size: 1.2rem;
            }
            .bracket-header h3 {
                font-size: 0.9rem;
            }
            .stColumn {
                min-width: 80px !important;
            }
            .round-title {
                font-size: 10px;
                padding: 4px;
            }
            .match-title {
                font-size: 8px;
            }
            .match-box {
                padding: 5px;
                margin: 5px 0;
            }
        }
        
        /* Hide elements on very small screens */
        @media (max-width: 480px) {
            .stColumn > div {
                padding: 0 2px !important;
            }
        }
        
        /* Make the app scrollable horizontally on small screens */
        .main > div {
            overflow-x: auto;
        }
        
        /* Ensure buttons remain readable */
        button {
            font-size: clamp(0.7rem, 2vw, 1rem) !important;
        }
        </style>
    """, unsafe_allow_html=True)
    
    # Add a warning for small screens
    st.markdown("""
        <script>
        if (window.innerWidth < 768) {
            const warningDiv = document.createElement('div');
            warningDiv.style.cssText = 'background: #fff3cd; border: 1px solid #ffc107; padding: 10px; margin: 10px 0; border-radius: 5px; text-align: center;';
            warningDiv.innerHTML = '📱 <strong>Tip:</strong> For the best experience, view on a larger screen or rotate your device to landscape mode.';
            const main = document.querySelector('.main');
            if (main) main.insertBefore(warningDiv, main.firstChild);
        }
        </script>
    """, unsafe_allow_html=True)
    
    # Render live match navbar at the top
    render_live_match_navbar()
    
    st.markdown(f"""
        <div class="bracket-header">
            <h1>⚽ FIFA World Cup 2026 Bracket Challenge</h1>
            <h3>Welcome, {st.session_state.user_name}!</h3>
        </div>
    """, unsafe_allow_html=True)
    
    # Top action bar with Logout and Save buttons
    top_col1, top_col2, top_col3 = st.columns([1, 2, 1])
    with top_col1:
        if st.button("🚪 Logout", use_container_width=True):
            st.session_state.logged_in = False
            st.session_state.user_id = None
            st.session_state.selections = {}
            st.session_state.champion = None
            st.session_state.final_score = {"home": "", "away": ""}
            st.session_state.last_activity = None
            st.query_params.clear()
            st.rerun()
    
    with top_col2:
        # Session info
        if st.session_state.last_activity:
            elapsed = time.time() - st.session_state.last_activity
            remaining = max(0, SESSION_TIMEOUT - elapsed)
            remaining_minutes = int(remaining / 60)
            st.info(f"🕐 Session active - Auto-logout in {remaining_minutes} min if inactive")
    
    with top_col3:
        locked = is_selection_locked()
        if not locked:
            if st.button("💾 Save Bracket", type="primary", use_container_width=True, key="save_top"):
                is_valid, error = validate_bracket(st.session_state.selections)
                if is_valid and st.session_state.champion:
                    save_bracket(
                        st.session_state.user_id,
                        st.session_state.selections,
                        st.session_state.champion,
                        st.session_state.final_score
                    )
                    st.success("✅ Bracket saved successfully!")
                    st.balloons()
                else:
                    st.error(f"❌ Please complete all selections. {error if error else 'Missing champion selection.'}")
        else:
            # Show view-only badge instead of save button after deadline
            st.markdown("""
                <div style="padding: 8px; background: #dc3545; color: white; border-radius: 5px; text-align: center; font-weight: bold;">
                    👁️ VIEW ONLY
                </div>
            """, unsafe_allow_html=True)
    
    locked = is_selection_locked()
    
    if locked:
        st.error("🔒 Bracket is now VIEW ONLY. The deadline was July 4, 2026 at 12:00 PM EST.")
    else:
        st.info("⏰ You can modify your bracket until July 4, 2026 at 12:00 PM EST")
    
    # Mobile-friendly tip
    st.markdown("""
        <div style="text-align: center; margin: 10px 0; padding: 8px; background: #e7f3ff; border-radius: 5px; font-size: 14px;">
            💡 <strong>Tip:</strong> Best viewed on desktop or landscape mode
        </div>
    """, unsafe_allow_html=True)
    
    bracket_data = load_bracket_data()
    selections = st.session_state.selections
    
    st.markdown("---")
    
    
    # Split bracket with correct match order for proper paths
    # LEFT SIDE leads to M101, RIGHT SIDE leads to M102, both meet in FINAL (M104)
    all_r32 = bracket_data['bracket']['round_of_32']
    all_r16 = bracket_data['bracket']['round_of_16']
    all_qf = bracket_data['bracket']['quarter_finals']
    all_sf = bracket_data['bracket']['semi_finals']
    
    # Create lookup dictionary for matches by ID
    r32_dict = {m['match_id']: m for m in all_r32}
    r16_dict = {m['match_id']: m for m in all_r16}
    qf_dict = {m['match_id']: m for m in all_qf}
    sf_dict = {m['match_id']: m for m in all_sf}
    
    # LEFT SIDE R32: M74, M77, M73, M75, M83, M84, M81, M82
    left_r32 = [r32_dict[mid] for mid in [74, 77, 73, 75, 83, 84, 81, 82]]
    # RIGHT SIDE R32: M76, M78, M79, M80, M86, M88, M85, M87
    right_r32 = [r32_dict[mid] for mid in [76, 78, 79, 80, 86, 88, 85, 87]]
    
    # LEFT SIDE R16: M89, M90, M93, M94
    left_r16 = [r16_dict[mid] for mid in [89, 90, 93, 94]]
    # RIGHT SIDE R16: M91, M92, M95, M96
    right_r16 = [r16_dict[mid] for mid in [91, 92, 95, 96]]
    
    # LEFT SIDE QF: M97, M98
    left_qf = [qf_dict[mid] for mid in [97, 98]]
    # RIGHT SIDE QF: M99, M100
    right_qf = [qf_dict[mid] for mid in [99, 100]]
    
    # LEFT SIDE SF: M101
    left_sf = [sf_dict[101]]
    # RIGHT SIDE SF: M102
    right_sf = [sf_dict[102]]
    
    # Wrap bracket in scrollable container
    st.markdown('<div style="overflow-x: auto; min-width: 100%;">', unsafe_allow_html=True)
    
    # Create the bracket layout
    r32_left, conn1, r16_left, conn2, qf_left, conn3, sf_left, final_col, sf_right, conn4, qf_right, conn5, r16_right, conn6, r32_right = st.columns(
        [3, 0.3, 3, 0.3, 3, 0.3, 3, 3, 3, 0.3, 3, 0.3, 3, 0.3, 3]
    )
    
    # LEFT SIDE - ROUND OF 32
    with r32_left:
        st.markdown('<div class="round-title">Round of 32</div>', unsafe_allow_html=True)
        for i, match in enumerate(left_r32):
            render_match_box(match, selections, locked, 'r32_left')
            # Add spacing after every odd match (after 1st, 3rd, 5th, 7th)
            if i % 2 == 1:
                st.markdown('<div style="height: 20px;"></div>', unsafe_allow_html=True)
        # Add bottom padding to ensure everything renders
        st.markdown('<div style="height: 50px;"></div>', unsafe_allow_html=True)

    
    with conn1:
        st.markdown('<div class="round-title" style="opacity: 0;">.</div>', unsafe_allow_html=True)
        # Render connectors for PAIRS of Round of 32 matches
        for i in range(0, len(left_r32), 2):
            if i+1 < len(left_r32):
                match1 = left_r32[i]
                match2 = left_r32[i+1]
                st.markdown(render_connector_for_pair(
                    match1['match_id'], match2['match_id'],
                    match1['team_home'], match1['team_away'],
                    match2['team_home'], match2['team_away'],
                    selections, True
                ), unsafe_allow_html=True)
                st.markdown('<div style="height: 20px;"></div>', unsafe_allow_html=True)
        # Add bottom padding
        st.markdown('<div style="height: 50px;"></div>', unsafe_allow_html=True)
    
    with r16_left:
        st.markdown('<div class="round-title">Round of 16</div>', unsafe_allow_html=True)
        st.markdown('<div style="height: 50px;"></div>', unsafe_allow_html=True)
        for i, match in enumerate(left_r16):
            render_match_box(match, selections, locked, 'r16_left')
            st.markdown('<div style="height: 100px;"></div>', unsafe_allow_html=True)

    
    with conn2:
        st.markdown('<div class="round-title" style="opacity: 0;">.</div>', unsafe_allow_html=True)
        st.markdown('<div style="height: 50px;"></div>', unsafe_allow_html=True)
        # Render connectors for PAIRS of R16 matches
        for i in range(0, len(left_r16), 2):
            if i+1 < len(left_r16):
                match1 = left_r16[i]
                match2 = left_r16[i+1]
                
                # Get team names for match1
                team1_home = match1['team_home']
                team1_away = match1['team_away']
                if team1_home.startswith('W'):
                    team1_home = selections.get(str(int(team1_home[1:])), 'TBD')
                if team1_away.startswith('W'):
                    team1_away = selections.get(str(int(team1_away[1:])), 'TBD')
                
                # Get team names for match2
                team2_home = match2['team_home']
                team2_away = match2['team_away']
                if team2_home.startswith('W'):
                    team2_home = selections.get(str(int(team2_home[1:])), 'TBD')
                if team2_away.startswith('W'):
                    team2_away = selections.get(str(int(team2_away[1:])), 'TBD')
                
                st.markdown(render_connector_for_pair(
                    match1['match_id'], match2['match_id'],
                    team1_home, team1_away,
                    team2_home, team2_away,
                    selections, True
                ), unsafe_allow_html=True)
                st.markdown('<div style="height: 100px;"></div>', unsafe_allow_html=True)
    
    with qf_left:
        st.markdown('<div class="round-title">Quarter Finals</div>', unsafe_allow_html=True)
        st.markdown("<br>" * 4, unsafe_allow_html=True)
        for match in left_qf:
            render_match_box(match, selections, locked, 'qf_left')
            st.markdown("<br>" * 5, unsafe_allow_html=True)

    
    with conn3:
        st.markdown('<div class="round-title" style="opacity: 0;">.</div>', unsafe_allow_html=True)
        st.markdown("<br>" * 8, unsafe_allow_html=True)
        # Connector for QF pair leading to SF (M97 and M98 -> M101)
        if len(left_qf) >= 2:
            match1 = left_qf[0]  # M97
            match2 = left_qf[1]  # M98
            
            # Get team names for match1
            team1_home = match1['team_home']
            team1_away = match1['team_away']
            if team1_home.startswith('W'):
                team1_home = selections.get(str(int(team1_home[1:])), 'TBD')
            if team1_away.startswith('W'):
                team1_away = selections.get(str(int(team1_away[1:])), 'TBD')
            
            # Get team names for match2
            team2_home = match2['team_home']
            team2_away = match2['team_away']
            if team2_home.startswith('W'):
                team2_home = selections.get(str(int(team2_home[1:])), 'TBD')
            if team2_away.startswith('W'):
                team2_away = selections.get(str(int(team2_away[1:])), 'TBD')
            
            st.markdown(render_connector_for_pair(
                match1['match_id'], match2['match_id'],
                team1_home, team1_away,
                team2_home, team2_away,
                selections, True
            ), unsafe_allow_html=True)
    
    with sf_left:
        st.markdown('<div class="round-title">Semi Finals</div>', unsafe_allow_html=True)
        st.markdown("<br>" * 10, unsafe_allow_html=True)
        match = left_sf[0]  # M101
        render_match_box(match, selections, locked, 'sf_left')

    
    # CENTER - FINAL
    with final_col:
        st.markdown('<div class="round-title">🏆 FINAL 🏆</div>', unsafe_allow_html=True)
        st.markdown("<br>" * 12, unsafe_allow_html=True)
        
        final_match = bracket_data['bracket']['final']
        match_id = str(final_match['match_id'])
        team_home = final_match['team_home']
        team_away = final_match['team_away']
        
        if team_home.startswith('W'):
            prev_match_id = int(team_home[1:])
            team_home = selections.get(str(prev_match_id), 'TBD')
        if team_away.startswith('W'):
            prev_match_id = int(team_away[1:])
            team_away = selections.get(str(prev_match_id), 'TBD')
        
        winner = get_match_winner(match_id, selections)
        can_select = team_home != 'TBD' and team_away != 'TBD' and not locked
        
        home_flag = get_flag(team_home)
        away_flag = get_flag(team_away)
        
        st.markdown(f"""
            <div style="background: linear-gradient(135deg, #FFD700 0%, #FFA500 100%); 
                        padding: 15px; border-radius: 10px; border: 3px solid gold; margin: 10px 0;">
                <div style="text-align: center; color: white; font-size: 11px; margin-bottom: 10px; font-weight: bold;">
                    Match {final_match['match_id']} • {final_match['date']}
                </div>
        """, unsafe_allow_html=True)
        
        if team_home != 'TBD' and team_away != 'TBD':
            if st.button(
                f"{home_flag} {team_home}",
                key=f"final_home",
                disabled=not can_select,
                use_container_width=True,
                type="primary" if winner == team_home else "secondary"
            ):
                if can_select:
                    st.session_state.selections[match_id] = team_home
                    st.session_state.champion = team_home
                    st.rerun()
            
            score_col1, vs_col, score_col2 = st.columns([2, 1, 2])
            with score_col1:
                home_score = st.text_input(
                    "Score",
                    value=st.session_state.final_score.get('home', ''),
                    key="final_home_score",
                    disabled=locked,
                    max_chars=2
                )
                st.session_state.final_score['home'] = home_score
            
            with vs_col:
                st.markdown("<div style='text-align: center; padding: 20px 0; color: white; font-weight: bold; font-size: 16px;'>VS</div>", unsafe_allow_html=True)
            
            with score_col2:
                away_score = st.text_input(
                    "Score",
                    value=st.session_state.final_score.get('away', ''),
                    key="final_away_score",
                    disabled=locked,
                    max_chars=2
                )
                st.session_state.final_score['away'] = away_score
            
            if st.button(
                f"{away_flag} {team_away}",
                key=f"final_away",
                disabled=not can_select,
                use_container_width=True,
                type="primary" if winner == team_away else "secondary"
            ):
                if can_select:
                    st.session_state.selections[match_id] = team_away
                    st.session_state.champion = team_away
                    st.rerun()
        else:
            st.markdown(f"""
                <div style="text-align: center; padding: 20px; color: white;">
                    <div>{home_flag} {team_home}</div>
                    <div style="margin: 10px 0;">VS</div>
                    <div>{away_flag} {team_away}</div>
                </div>
            """, unsafe_allow_html=True)
        
        st.markdown("</div>", unsafe_allow_html=True)
    
    # RIGHT SIDE - BOTTOM BRACKET (reversed order)
    with sf_right:
        st.markdown('<div class="round-title">Semi Finals</div>', unsafe_allow_html=True)
        st.markdown("<br>" * 10, unsafe_allow_html=True)
        match = right_sf[0]  # M102
        render_match_box(match, selections, locked, 'sf_right')

    
    with conn4:
        st.markdown('<div class="round-title" style="opacity: 0;">.</div>', unsafe_allow_html=True)
        st.markdown("<br>" * 8, unsafe_allow_html=True)
        # Connector for QF pair leading to SF (M99 and M100 -> M102)
        if len(right_qf) >= 2:
            match1 = right_qf[0]  # M99
            match2 = right_qf[1]  # M100
            
            # Get team names for match1
            team1_home = match1['team_home']
            team1_away = match1['team_away']
            if team1_home.startswith('W'):
                team1_home = selections.get(str(int(team1_home[1:])), 'TBD')
            if team1_away.startswith('W'):
                team1_away = selections.get(str(int(team1_away[1:])), 'TBD')
            
            # Get team names for match2
            team2_home = match2['team_home']
            team2_away = match2['team_away']
            if team2_home.startswith('W'):
                team2_home = selections.get(str(int(team2_home[1:])), 'TBD')
            if team2_away.startswith('W'):
                team2_away = selections.get(str(int(team2_away[1:])), 'TBD')
            
            st.markdown(render_connector_for_pair(
                match1['match_id'], match2['match_id'],
                team1_home, team1_away,
                team2_home, team2_away,
                selections, False
            ), unsafe_allow_html=True)
    
    with qf_right:
        st.markdown('<div class="round-title">Quarter Finals</div>', unsafe_allow_html=True)
        st.markdown("<br>" * 4, unsafe_allow_html=True)
        for match in right_qf:
            render_match_box(match, selections, locked, 'qf_right')
            st.markdown("<br>" * 5, unsafe_allow_html=True)

    
    with conn5:
        st.markdown('<div class="round-title" style="opacity: 0;">.</div>', unsafe_allow_html=True)
        st.markdown('<div style="height: 50px;"></div>', unsafe_allow_html=True)
        # Render connectors for PAIRS of R16 matches (right side)
        for i in range(0, len(right_r16), 2):
            if i+1 < len(right_r16):
                match1 = right_r16[i]
                match2 = right_r16[i+1]
                
                # Get team names for match1
                team1_home = match1['team_home']
                team1_away = match1['team_away']
                if team1_home.startswith('W'):
                    team1_home = selections.get(str(int(team1_home[1:])), 'TBD')
                if team1_away.startswith('W'):
                    team1_away = selections.get(str(int(team1_away[1:])), 'TBD')
                
                # Get team names for match2
                team2_home = match2['team_home']
                team2_away = match2['team_away']
                if team2_home.startswith('W'):
                    team2_home = selections.get(str(int(team2_home[1:])), 'TBD')
                if team2_away.startswith('W'):
                    team2_away = selections.get(str(int(team2_away[1:])), 'TBD')
                
                st.markdown(render_connector_for_pair(
                    match1['match_id'], match2['match_id'],
                    team1_home, team1_away,
                    team2_home, team2_away,
                    selections, False
                ), unsafe_allow_html=True)
                st.markdown('<div style="height: 100px;"></div>', unsafe_allow_html=True)
    
    with r16_right:
        st.markdown('<div class="round-title">Round of 16</div>', unsafe_allow_html=True)
        st.markdown('<div style="height: 50px;"></div>', unsafe_allow_html=True)
        for i, match in enumerate(right_r16):
            render_match_box(match, selections, locked, 'r16_right')
            st.markdown('<div style="height: 100px;"></div>', unsafe_allow_html=True)

    
    with conn6:
        st.markdown('<div class="round-title" style="opacity: 0;">.</div>', unsafe_allow_html=True)
        # Render connectors for PAIRS of Round of 32 matches (right side)
        for i in range(0, len(right_r32), 2):
            if i+1 < len(right_r32):
                match1 = right_r32[i]
                match2 = right_r32[i+1]
                st.markdown(render_connector_for_pair(
                    match1['match_id'], match2['match_id'],
                    match1['team_home'], match1['team_away'],
                    match2['team_home'], match2['team_away'],
                    selections, False
                ), unsafe_allow_html=True)
                st.markdown('<div style="height: 20px;"></div>', unsafe_allow_html=True)
        # Add bottom padding
        st.markdown('<div style="height: 50px;"></div>', unsafe_allow_html=True)
    
    with r32_right:
        st.markdown('<div class="round-title">Round of 32</div>', unsafe_allow_html=True)
        for i, match in enumerate(right_r32):
            render_match_box(match, selections, locked, 'r32_right')
            # Add spacing after every odd match (after 1st, 3rd, 5th, 7th)
            if i % 2 == 1:
                st.markdown('<div style="height: 20px;"></div>', unsafe_allow_html=True)
        # Add bottom padding
        st.markdown('<div style="height: 50px;"></div>', unsafe_allow_html=True)

    # Close scrollable container
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Champion Display and Save Button
    st.markdown("---")
    
    if st.session_state.champion:
        champion_flag = get_flag(st.session_state.champion)
        primary_color, secondary_color = get_country_gradient(st.session_state.champion)
        st.markdown(f"""
            <div style="text-align: center; margin-top: 30px; padding: 30px; 
                        background: linear-gradient(135deg, {primary_color} 0%, {secondary_color} 100%); 
                        border-radius: 15px; border: 5px solid {primary_color}; box-shadow: 0 4px 20px rgba(0,0,0,0.3);">
                <h1 style="color: white; font-size: 48px; margin: 0; text-shadow: 2px 2px 4px rgba(0,0,0,0.5);">🏆</h1>
                <h2 style="color: white; margin: 10px 0; text-shadow: 2px 2px 4px rgba(0,0,0,0.5);">YOUR CHAMPION</h2>
                <h1 style="color: white; font-size: 42px; margin: 10px 0; text-shadow: 2px 2px 4px rgba(0,0,0,0.5);">{champion_flag} {st.session_state.champion}</h1>
            </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Bottom Save Button (for convenience after scrolling)
    if not locked:
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("💾 Save Bracket", type="primary", use_container_width=True, key="save_bottom"):
                is_valid, error = validate_bracket(st.session_state.selections)
                if is_valid and st.session_state.champion:
                    save_bracket(
                        st.session_state.user_id,
                        st.session_state.selections,
                        st.session_state.champion,
                        st.session_state.final_score
                    )
                    st.success("✅ Bracket saved successfully!")
                    st.balloons()
                else:
                    st.error(f"❌ Please complete all selections. {error if error else 'Missing champion selection.'}")

def calculate_bracket_score(selections, completed_matches):
    """Calculate score for a bracket based on completed matches"""
    # Point system: R32=1, R16=2, QF=4, SF=8, Final=16, Champion=32
    score = 0
    round_points = {
        'round_of_32': 1,
        'round_of_16': 2,
        'quarter_finals': 4,
        'semi_finals': 8,
        'final': 16
    }
    
    bracket_data = load_bracket_data()
    
    for round_name, points in round_points.items():
        if round_name == 'final':
            match = bracket_data['bracket']['final']
            match_id = str(match['match_id'])
            if match_id in completed_matches:
                if selections.get(match_id) == completed_matches[match_id]:
                    score += points
        else:
            for match in bracket_data['bracket'][round_name]:
                match_id = str(match['match_id'])
                if match_id in completed_matches:
                    if selections.get(match_id) == completed_matches[match_id]:
                        score += points
    
    return score

def admin_page():
    st.title("🔐 Admin Dashboard")
    
    col1, col2 = st.columns([5, 1])
    
    with col2:
        if st.button("Logout", use_container_width=True):
            st.session_state.admin_logged_in = False
            st.session_state.admin_last_activity = None
            st.query_params.clear()
            st.rerun()
    
    # Admin tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["📊 Statistics", "👥 User Brackets", "⚽ Match Results", "🏆 Leaderboard", "📡 Live Match"])
    
    try:
        brackets = get_all_brackets()
        completed_matches = load_completed_matches()
        
        # TAB 1: Statistics Dashboard
        with tab1:
            st.header("📊 User Statistics")
            
            if brackets:
                total_users = len(brackets)
                unique_emails = set(b['user_email'] for b in brackets)
                complete_brackets = sum(1 for b in brackets if b.get('champion'))
                
                # Metrics
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Total Registered Users", total_users)
                with col2:
                    st.metric("Complete Brackets", complete_brackets)
                with col3:
                    st.metric("Incomplete Brackets", total_users - complete_brackets)
                
                st.markdown("---")
                
                # Champion picks analysis
                st.subheader("🏆 Champion Predictions")
                champion_counts = {}
                for bracket in brackets:
                    champ = bracket.get('champion')
                    if champ:
                        champion_counts[champ] = champion_counts.get(champ, 0) + 1
                
                if champion_counts:
                    sorted_champs = sorted(champion_counts.items(), key=lambda x: x[1], reverse=True)
                    
                    champ_cols = st.columns(min(3, len(sorted_champs)))
                    for idx, (champ, count) in enumerate(sorted_champs[:3]):
                        with champ_cols[idx]:
                            percentage = (count / total_users) * 100
                            flag = get_flag(champ)
                            st.metric(
                                f"{flag} {champ}",
                                f"{count} picks",
                                f"{percentage:.1f}%"
                            )
                    
                    st.markdown("**All Champion Picks:**")
                    for champ, count in sorted_champs:
                        percentage = (count / total_users) * 100
                        flag = get_flag(champ)
                        st.write(f"{flag} **{champ}**: {count} picks ({percentage:.1f}%)")
                
                st.markdown("---")
                
                # Completed matches statistics
                if completed_matches:
                    st.subheader("⚽ Completed Matches")
                    st.write(f"**Total Completed:** {len(completed_matches)} matches")
                    
                    for match_id, winner in completed_matches.items():
                        flag = get_flag(winner)
                        correct_picks = sum(1 for b in brackets if b.get('selections', {}).get(match_id) == winner)
                        total_picks = sum(1 for b in brackets if b.get('selections', {}).get(match_id))
                        
                        if total_picks > 0:
                            accuracy = (correct_picks / total_picks) * 100
                            st.write(f"**Match {match_id}:** {flag} {winner} - {correct_picks}/{total_picks} correct ({accuracy:.1f}%)")
            else:
                st.info("No brackets submitted yet.")
        
        # TAB 2: Individual Bracket Viewer
        with tab2:
            st.header("👥 View User Brackets")
            
            if brackets:
                # Search by email
                user_emails = [b['user_email'] for b in brackets]
                selected_email = st.selectbox("Select User", [""] + user_emails)
                
                if selected_email:
                    user_bracket = next((b for b in brackets if b['user_email'] == selected_email), None)
                    
                    if user_bracket:
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.write(f"**👤 Name:** {user_bracket['user_name']}")
                            st.write(f"**📧 Email:** {user_bracket['user_email']}")
                        
                        with col2:
                            champion_flag = get_flag(user_bracket.get('champion', 'Not selected'))
                            st.write(f"**🏆 Champion:** {champion_flag} {user_bracket.get('champion', 'Not selected')}")
                            st.write(f"**🕐 Last Updated:** {user_bracket.get('updated_at', 'N/A')}")
                        
                        final_score = user_bracket.get('final_score', {})
                        if final_score and (final_score.get('home') or final_score.get('away')):
                            st.write(f"**⚽ Final Score Prediction:** {final_score.get('home', '?')} - {final_score.get('away', '?')}")
                        
                        # Calculate current score
                        if completed_matches:
                            current_score = calculate_bracket_score(user_bracket.get('selections', {}), completed_matches)
                            st.metric("Current Score", current_score)
                        
                        st.markdown("---")
                        
                        if user_bracket.get('selections'):
                            st.subheader("Match Selections")
                            
                            bracket_data = load_bracket_data()
                            
                            st.write("**Round of 32:**")
                            r32_cols = st.columns(4)
                            for idx2, match in enumerate(bracket_data['bracket']['round_of_32']):
                                match_id = str(match['match_id'])
                                winner = user_bracket['selections'].get(match_id, 'Not selected')
                                flag = get_flag(winner)
                                
                                # Check if correct
                                is_correct = match_id in completed_matches and completed_matches[match_id] == winner
                                status = "✅" if is_correct else ("❌" if match_id in completed_matches else "")
                                
                                with r32_cols[idx2 % 4]:
                                    st.write(f"M{match_id}: {flag} {winner} {status}")
                            
                            st.write("**Round of 16:**")
                            r16_cols = st.columns(4)
                            for idx2, match in enumerate(bracket_data['bracket']['round_of_16']):
                                match_id = str(match['match_id'])
                                winner = user_bracket['selections'].get(match_id, 'Not selected')
                                flag = get_flag(winner)
                                
                                is_correct = match_id in completed_matches and completed_matches[match_id] == winner
                                status = "✅" if is_correct else ("❌" if match_id in completed_matches else "")
                                
                                with r16_cols[idx2 % 4]:
                                    st.write(f"M{match_id}: {flag} {winner} {status}")
                            
                            st.write("**Quarter Finals:**")
                            qf_cols = st.columns(4)
                            for idx2, match in enumerate(bracket_data['bracket']['quarter_finals']):
                                match_id = str(match['match_id'])
                                winner = user_bracket['selections'].get(match_id, 'Not selected')
                                flag = get_flag(winner)
                                
                                is_correct = match_id in completed_matches and completed_matches[match_id] == winner
                                status = "✅" if is_correct else ("❌" if match_id in completed_matches else "")
                                
                                with qf_cols[idx2 % 4]:
                                    st.write(f"M{match_id}: {flag} {winner} {status}")
                            
                            st.write("**Semi Finals:**")
                            sf_cols = st.columns(2)
                            for idx2, match in enumerate(bracket_data['bracket']['semi_finals']):
                                match_id = str(match['match_id'])
                                winner = user_bracket['selections'].get(match_id, 'Not selected')
                                flag = get_flag(winner)
                                
                                is_correct = match_id in completed_matches and completed_matches[match_id] == winner
                                status = "✅" if is_correct else ("❌" if match_id in completed_matches else "")
                                
                                with sf_cols[idx2]:
                                    st.write(f"M{match_id}: {flag} {winner} {status}")
                            
                            st.write("**Final:**")
                            final_match_id = str(bracket_data['bracket']['final']['match_id'])
                            final_winner = user_bracket['selections'].get(final_match_id, 'Not selected')
                            final_flag = get_flag(final_winner)
                            
                            is_correct = final_match_id in completed_matches and completed_matches[final_match_id] == final_winner
                            status = "✅" if is_correct else ("❌" if final_match_id in completed_matches else "")
                            
                            st.write(f"M{final_match_id}: {final_flag} {final_winner} {status}")
            else:
                st.info("No brackets submitted yet.")
        
        # TAB 3: Match Results Management
        with tab3:
            st.header("⚽ Match Results Management")
            
            st.subheader("Add/Update Match Result")
            
            col1, col2 = st.columns(2)
            with col1:
                match_id_input = st.text_input("Match ID", placeholder="e.g., 73")
            with col2:
                winner_input = st.text_input("Winner Team", placeholder="e.g., Canada")
            
            if st.button("Update Match Result", type="primary"):
                if match_id_input and winner_input:
                    # Load current completed matches
                    completed = load_completed_matches()
                    completed[match_id_input] = winner_input
                    
                    # Save to file
                    import json
                    with open('completed_matches.json', 'w') as f:
                        json.dump(completed, f, indent=2)
                    
                    st.success(f"✅ Match {match_id_input} result updated: {winner_input} wins!")
                    st.rerun()
                else:
                    st.error("Please fill in both Match ID and Winner")
            
            st.markdown("---")
            
            st.subheader("Current Completed Matches")
            if completed_matches:
                for match_id, winner in sorted(completed_matches.items(), key=lambda x: int(x[0])):
                    flag = get_flag(winner)
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        st.write(f"**Match {match_id}:** {flag} {winner}")
                    with col2:
                        if st.button("Delete", key=f"del_{match_id}"):
                            completed = load_completed_matches()
                            del completed[match_id]
                            
                            import json
                            with open('completed_matches.json', 'w') as f:
                                json.dump(completed, f, indent=2)
                            
                            st.success(f"Match {match_id} result deleted")
                            st.rerun()
            else:
                st.info("No completed matches yet")
        
        # TAB 4: Leaderboard
        with tab4:
            st.header("🏆 Leaderboard")
            
            if brackets and completed_matches:
                # Calculate scores for all users
                leaderboard = []
                for bracket in brackets:
                    score = calculate_bracket_score(bracket.get('selections', {}), completed_matches)
                    leaderboard.append({
                        'rank': 0,
                        'name': bracket['user_name'],
                        'email': bracket['user_email'],
                        'champion': bracket.get('champion', 'Not selected'),
                        'score': score
                    })
                
                # Sort by score
                leaderboard.sort(key=lambda x: x['score'], reverse=True)
                
                # Assign ranks
                for idx, entry in enumerate(leaderboard):
                    entry['rank'] = idx + 1
                
                # Display leaderboard
                st.markdown(f"**Total Matches Completed:** {len(completed_matches)}")
                st.markdown(f"**Maximum Possible Score:** Varies by matches completed")
                st.markdown("---")
                
                # Top 3
                if len(leaderboard) >= 1:
                    st.subheader("🥇 Top 3")
                    top_cols = st.columns(min(3, len(leaderboard)))
                    
                    medals = ["🥇", "🥈", "🥉"]
                    for idx in range(min(3, len(leaderboard))):
                        with top_cols[idx]:
                            entry = leaderboard[idx]
                            champion_flag = get_flag(entry['champion'])
                            st.markdown(f"""
                                <div style="text-align: center; padding: 20px; background: #f8f9fa; border-radius: 10px; border: 2px solid #ddd;">
                                    <h1>{medals[idx]}</h1>
                                    <h3>{entry['name']}</h3>
                                    <p><strong>Score: {entry['score']}</strong></p>
                                    <p>Champion: {champion_flag} {entry['champion']}</p>
                                </div>
                            """, unsafe_allow_html=True)
                
                st.markdown("---")
                
                # Full leaderboard
                st.subheader("Full Rankings")
                for entry in leaderboard:
                    champion_flag = get_flag(entry['champion'])
                    
                    # Highlight top 3
                    bg_color = "#fff3cd" if entry['rank'] <= 3 else "#ffffff"
                    
                    st.markdown(f"""
                        <div style="padding: 10px; margin: 5px 0; background: {bg_color}; border-radius: 5px; border: 1px solid #ddd;">
                            <strong>#{entry['rank']}</strong> | <strong>{entry['name']}</strong> | Score: <strong>{entry['score']}</strong> | Champion: {champion_flag} {entry['champion']}
                        </div>
                    """, unsafe_allow_html=True)
                
                # Export button
                st.markdown("---")
                if st.button("📥 Export Leaderboard as CSV"):
                    import csv
                    from io import StringIO
                    
                    output = StringIO()
                    writer = csv.DictWriter(output, fieldnames=['rank', 'name', 'email', 'score', 'champion'])
                    writer.writeheader()
                    writer.writerows(leaderboard)
                    
                    st.download_button(
                        label="Download CSV",
                        data=output.getvalue(),
                        file_name="leaderboard.csv",
                        mime="text/csv"
                    )
            elif not completed_matches:
                st.info("No matches completed yet. Leaderboard will appear once matches are finished.")
            else:
                st.info("No brackets submitted yet.")
        
        # TAB 5: Live Match Management
        with tab5:
            st.header("📡 Live Match Management")
            
            st.subheader("Update Live Match Display")
            st.info("This will update the live match ticker shown to all users at the top of the bracket page.")
            
            # Current live match display
            current_match = get_live_match_from_file()
            if current_match and current_match.get('match_id'):
                st.success("✅ Live match is currently active")
                formatted = format_live_match_display(current_match)
                if formatted:
                    st.markdown(f"""
                        **Current Display:**  
                        {formatted['status_text']} | {get_flag(formatted['team_home'])} {formatted['team_home']} 
                        **{formatted['score_home']} - {formatted['score_away']}** 
                        {formatted['team_away']} {get_flag(formatted['team_away'])} | Match {formatted['match_id']}
                    """)
            else:
                st.info("No live match currently displayed")
            
            st.markdown("---")
            
            # Form to update live match
            with st.form("live_match_form"):
                col1, col2 = st.columns(2)
                
                with col1:
                    match_id = st.text_input("Match ID", placeholder="e.g., 73")
                    team_home = st.text_input("Home Team", placeholder="e.g., Canada")
                    score_home = st.number_input("Home Score", min_value=0, value=0, step=1)
                
                with col2:
                    status = st.selectbox("Status", ["live", "halftime", "finished", "scheduled"])
                    team_away = st.text_input("Away Team", placeholder="e.g., South Africa")
                    score_away = st.number_input("Away Score", min_value=0, value=0, step=1)
                
                minute = st.text_input("Minute (optional, for live matches)", placeholder="e.g., 67")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    submitted = st.form_submit_button("🔴 Update Live Match", type="primary", use_container_width=True)
                
                with col2:
                    clear_button = st.form_submit_button("🗑️ Clear Live Match", use_container_width=True)
                
                if submitted:
                    if match_id and team_home and team_away:
                        success = update_live_match(
                            match_id=match_id,
                            team_home=team_home,
                            team_away=team_away,
                            score_home=int(score_home),
                            score_away=int(score_away),
                            status=status,
                            minute=minute if minute else None
                        )
                        
                        if success:
                            st.success("✅ Live match updated! Users will see this at the top of the page.")
                            st.rerun()
                        else:
                            st.error("Failed to update live match")
                    else:
                        st.error("Please fill in Match ID, Home Team, and Away Team")
                
                if clear_button:
                    if clear_live_match():
                        st.success("✅ Live match cleared!")
                        st.rerun()
                    else:
                        st.error("Failed to clear live match")
            
            st.markdown("---")
            
            st.subheader("📝 Instructions")
            st.markdown("""
            1. **Match ID**: Enter the official match number (e.g., 73)
            2. **Teams**: Enter the team names exactly as they appear in the bracket
            3. **Scores**: Enter current scores (0-0 for scheduled matches)
            4. **Status**:
               - **live**: Match is currently being played (shows animated ticker)
               - **halftime**: Match is at halftime
               - **finished**: Match has ended
               - **scheduled**: Match hasn't started yet
            5. **Minute**: Optional field for live matches (e.g., "45+2" for injury time)
            6. Click "Update Live Match" to activate the ticker
            7. Click "Clear Live Match" to remove the ticker from display
            
            **Note**: The ticker appears at the very top of the bracket page for all users.
            """)
                
    except Exception as e:
        st.error(f"Error loading admin data: {str(e)}")

def main():
    # Check for admin route
    query_params = st.query_params
    is_admin_route = 'page' in query_params and query_params.get('page') == 'admin'
    
    # Check for session timeout
    timed_out = check_session_timeout()
    
    if timed_out:
        st.query_params.clear()
        st.warning("⏱️ Your session has expired due to inactivity. Please login again.")
        if is_admin_route:
            admin_login_page()
        else:
            login_page()
    elif is_admin_route:
        # Admin route - show admin login or dashboard
        if st.session_state.admin_logged_in:
            update_activity()
            persist_session()
            admin_page()
        else:
            admin_login_page()
    elif st.session_state.logged_in:
        # Regular user logged in
        update_activity()
        persist_session()
        bracket_page()
    else:
        # No one logged in, show login page
        login_page()

if __name__ == "__main__":
    main()
