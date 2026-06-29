from supabase import create_client, Client
import os
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

_supabase = None

def get_supabase() -> Client:
    global _supabase
    if _supabase is None:
        url = os.getenv('SUPABASE_URL')
        key = os.getenv('SUPABASE_KEY')
        
        if not url or not key:
            raise ValueError("SUPABASE_URL and SUPABASE_KEY must be set in .env file")
        
        _supabase = create_client(url, key)
    return _supabase

def create_user(email, name):
    supabase = get_supabase()
    
    existing = supabase.table('users').select('*').eq('email', email).execute()
    if existing.data:
        return None, "User already exists"
    
    user_data = {
        'email': email,
        'name': name,
        'created_at': datetime.utcnow().isoformat()
    }
    
    result = supabase.table('users').insert(user_data).execute()
    
    if result.data:
        return result.data[0]['id'], None
    return None, "Failed to create user"

def get_user_by_email(email):
    supabase = get_supabase()
    
    result = supabase.table('users').select('*').eq('email', email).execute()
    
    if result.data:
        return result.data[0]
    return None

def save_bracket(user_id, bracket_selections, champion, final_score=None):
    supabase = get_supabase()
    
    bracket_data = {
        'user_id': user_id,
        'selections': bracket_selections,
        'champion': champion,
        'final_score': final_score or {"home": "", "away": ""},
        'updated_at': datetime.utcnow().isoformat()
    }
    
    existing = supabase.table('brackets').select('*').eq('user_id', user_id).execute()
    
    if existing.data:
        supabase.table('brackets').update(bracket_data).eq('user_id', user_id).execute()
    else:
        supabase.table('brackets').insert(bracket_data).execute()

def get_user_bracket(user_id):
    supabase = get_supabase()
    
    result = supabase.table('brackets').select('*').eq('user_id', user_id).execute()
    
    if result.data:
        return result.data[0]
    return None

def get_all_brackets():
    try:
        supabase = get_supabase()
        
        # Get all brackets with user information
        response = supabase.table('brackets').select('*, users(name, email)').execute()
        
        result = []
        for bracket in response.data:
            user_data = bracket.get('users', {})
            result.append({
                'user_name': user_data.get('name') if isinstance(user_data, dict) else 'N/A',
                'user_email': user_data.get('email') if isinstance(user_data, dict) else 'N/A',
                'champion': bracket.get('champion'),
                'selections': bracket.get('selections'),
                'final_score': bracket.get('final_score', {"home": "", "away": ""}),
                'updated_at': bracket.get('updated_at'),
                'user_id': bracket.get('user_id')
            })
        
        return result
    except Exception as e:
        print(f"Error in get_all_brackets: {str(e)}")
        return []
