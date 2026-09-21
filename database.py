"""
Database module for Emotion-Aware Study Assistant — Supabase Backend
"""

import os
from datetime import datetime, timedelta
import uuid
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()

SUPABASE_URL = os.getenv('SUPABASE_URL', '')
SUPABASE_KEY = os.getenv('SUPABASE_SERVICE_KEY', '')  # Use service role key to bypass RLS

_client: Client = None

def _get_client() -> Client:
    global _client
    if _client is None:
        _client = create_client(SUPABASE_URL, SUPABASE_KEY)
    return _client

def init_db():
    """Test connection to Supabase."""
    try:
        sb = _get_client()
        # Quick connectivity check
        sb.table('users').select('id').limit(1).execute()
        print('[OK] Supabase database connected successfully')
    except Exception as e:
        print(f'[WARN] Supabase connection issue: {e}')
        print('[INFO] Make sure tables exist. Run the SQL in Supabase Dashboard.')

# ─── Users ────────────────────────────────────────────────────────────────────

def create_user(username, password_hash):
    sb = _get_client()
    try:
        result = sb.table('users').insert({
            'username': username,
            'password_hash': password_hash
        }).execute()
        if result.data:
            return result.data[0]['id']
        return None
    except Exception:
        return None  # Username already taken (unique constraint)

def get_user_by_username(username):
    sb = _get_client()
    result = sb.table('users').select(
        'id, username, password_hash, profile_photo, created_at'
    ).eq('username', username).limit(1).execute()
    if result.data:
        row = result.data[0]
        return {
            'id': row['id'],
            'username': row['username'],
            'password_hash': row['password_hash'],
            'profile_photo': row.get('profile_photo'),
            'created_at': row.get('created_at')
        }
    return None

def get_user_by_id(user_id):
    if user_id is None:
        return None
    sb = _get_client()
    result = sb.table('users').select(
        'id, username, profile_photo, created_at'
    ).eq('id', user_id).limit(1).execute()
    if result.data:
        row = result.data[0]
        return {
            'id': row['id'],
            'username': row['username'],
            'profile_photo': row.get('profile_photo'),
            'created_at': row.get('created_at')
        }
    return None

def update_password(user_id, new_password_hash):
    sb = _get_client()
    result = sb.table('users').update({
        'password_hash': new_password_hash
    }).eq('id', user_id).execute()
    return bool(result.data)

def update_username(user_id, new_username):
    sb = _get_client()
    try:
        result = sb.table('users').update({
            'username': new_username
        }).eq('id', user_id).execute()
        return bool(result.data)
    except Exception:
        return False  # Unique constraint violation

# ─── Reset Tokens ─────────────────────────────────────────────────────────────

def create_reset_token(user_id):
    token = str(uuid.uuid4())
    expires_at = (datetime.now() + timedelta(hours=1)).isoformat()
    sb = _get_client()
    # Invalidate old tokens
    sb.table('reset_tokens').update({'used': True}).eq('user_id', user_id).execute()
    # Create new token
    sb.table('reset_tokens').insert({
        'token': token,
        'user_id': user_id,
        'expires_at': expires_at
    }).execute()
    return token

def verify_reset_token(token):
    sb = _get_client()
    result = sb.table('reset_tokens').select(
        'user_id, expires_at, used'
    ).eq('token', token).limit(1).execute()
    if not result.data:
        return None
    row = result.data[0]
    if row['used']:
        return None
    expires_at = datetime.fromisoformat(row['expires_at'].replace('Z', '+00:00'))
    if datetime.now(expires_at.tzinfo) > expires_at:
        return None
    return row['user_id']

def invalidate_reset_token(token):
    sb = _get_client()
    sb.table('reset_tokens').update({'used': True}).eq('token', token).execute()

# ─── Sessions ─────────────────────────────────────────────────────────────────

def save_session(emotion, suggestion, user_input, user_id=None):
    sb = _get_client()
    data = {
        'emotion': emotion,
        'suggestion': suggestion,
        'user_input': user_input,
    }
    if user_id is not None:
        data['user_id'] = user_id
    result = sb.table('sessions').insert(data).execute()
    if result.data:
        return result.data[0]['id']
    return None

def get_session_history(limit=10, user_id=None):
    sb = _get_client()
    query = sb.table('sessions').select('id, emotion, timestamp, suggestion')
    if user_id:
        query = query.eq('user_id', user_id)
    result = query.order('timestamp', desc=True).limit(limit).execute()
    return [
        {
            'id': r['id'],
            'emotion': r['emotion'],
            'timestamp': r['timestamp'],
            'suggestion': r['suggestion']
        }
        for r in (result.data or [])
    ]

def get_recent_sessions_raw(user_id, limit=20):
    """Get raw sessions with timestamps for pattern detection."""
    sb = _get_client()
    result = sb.table('sessions').select(
        'emotion, timestamp'
    ).eq('user_id', user_id).order(
        'timestamp', desc=True
    ).limit(limit).execute()
    return [
        {'emotion': r['emotion'], 'timestamp': r['timestamp']}
        for r in (result.data or [])
    ]

def get_trend_data(user_id, days=7):
    """Get emotion counts grouped by day for the last N days."""
    sb = _get_client()
    since = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%dT00:00:00')
    result = sb.table('sessions').select(
        'emotion, timestamp'
    ).eq('user_id', user_id).gte(
        'timestamp', since
    ).order('timestamp').execute()

    # Group by day and emotion
    trend = {}
    for r in (result.data or []):
        day = r['timestamp'][:10]  # Extract YYYY-MM-DD
        if day not in trend:
            trend[day] = {}
        emotion = r['emotion']
        trend[day][emotion] = trend[day].get(emotion, 0) + 1

    # Fill missing days
    output = []
    for i in range(days):
        day = (datetime.now() - timedelta(days=days - 1 - i)).strftime('%Y-%m-%d')
        output.append({'day': day, 'emotions': trend.get(day, {})})
    return output

def get_emotion_stats(user_id=None):
    sb = _get_client()
    query = sb.table('sessions').select('emotion')
    if user_id:
        query = query.eq('user_id', user_id)
    result = query.execute()

    # Count emotions
    stats = {}
    for r in (result.data or []):
        e = r['emotion']
        stats[e] = stats.get(e, 0) + 1
    # Sort by count descending
    return dict(sorted(stats.items(), key=lambda x: x[1], reverse=True))

def get_weekly_stats(user_id):
    """Get detailed stats for the weekly report (last 7 days)."""
    sb = _get_client()
    since = (datetime.now() - timedelta(days=6)).strftime('%Y-%m-%dT00:00:00')
    result = sb.table('sessions').select(
        'timestamp'
    ).eq('user_id', user_id).gte('timestamp', since).execute()

    # Group by day
    rows = {}
    for r in (result.data or []):
        day = r['timestamp'][:10]
        rows[day] = rows.get(day, 0) + 1

    output = []
    for i in range(7):
        date_obj = datetime.now() - timedelta(days=6 - i)
        day_str = date_obj.strftime('%Y-%m-%d')
        day_name = date_obj.strftime('%a')
        count = rows.get(day_str, 0)
        output.append({
            'day': day_str,
            'day_name': day_name,
            'session_count': count,
            'hours': round(count * 0.5, 1)
        })
    return output

def get_monthly_sessions(user_id):
    sb = _get_client()
    since = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%dT00:00:00')
    result = sb.table('sessions').select(
        'emotion, timestamp'
    ).eq('user_id', user_id).gte(
        'timestamp', since
    ).order('timestamp', desc=True).execute()
    return [
        {'emotion': r['emotion'], 'timestamp': r['timestamp']}
        for r in (result.data or [])
    ]

# ─── Goals ────────────────────────────────────────────────────────────────────

def update_user_goal(user_id, goal):
    sb = _get_client()
    sb.table('users').update({'weekly_hour_goal': goal}).eq('id', user_id).execute()
    return True

def get_user_goal(user_id):
    sb = _get_client()
    result = sb.table('users').select('weekly_hour_goal').eq('id', user_id).limit(1).execute()
    if result.data:
        return result.data[0].get('weekly_hour_goal', 10.0)
    return 10.0

# ─── Materials ────────────────────────────────────────────────────────────────

def save_material(mat_id, user_id, title, source, content):
    sb = _get_client()
    try:
        sb.table('materials').upsert({
            'id': mat_id,
            'user_id': user_id,
            'title': title,
            'source': source,
            'content': content
        }).execute()
        return True
    except Exception as e:
        print(f"Error saving material: {e}")
        return False

def delete_material(mat_id, user_id):
    sb = _get_client()
    result = sb.table('materials').delete().eq(
        'id', mat_id
    ).eq('user_id', user_id).execute()
    return bool(result.data)

def get_user_materials(user_id):
    sb = _get_client()
    result = sb.table('materials').select(
        'id, title, source, content'
    ).eq('user_id', user_id).order('created_at', desc=True).execute()
    return [
        {'id': r['id'], 'title': r['title'], 'source': r['source'], 'content': r['content']}
        for r in (result.data or [])
    ]

# ─── Settings ─────────────────────────────────────────────────────────────────

def update_user_settings(user_id, username=None, goal=None, profile_photo=None):
    sb = _get_client()
    updates = {}
    if username:
        updates['username'] = username
    if goal:
        updates['weekly_hour_goal'] = goal
    if profile_photo:
        updates['profile_photo'] = profile_photo
    if not updates:
        return False
    try:
        result = sb.table('users').update(updates).eq('id', user_id).execute()
        return bool(result.data)
    except Exception:
        return False

def update_user_photo(user_id, photo_path):
    sb = _get_client()
    result = sb.table('users').update({
        'profile_photo': photo_path
    }).eq('id', user_id).execute()
    return bool(result.data)
