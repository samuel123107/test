from data.study_materials import study_materials
"""
Emotion-Aware Study Assistant - Flask Application (v5.0 Enterprise)
"""

import os
import requests
from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from datetime import datetime
from dotenv import load_dotenv
from pypdf import PdfReader
from flask_wtf.csrf import CSRFProtect

import time
from collections import defaultdict

# Simple in-memory rate limiter
user_last_request = defaultdict(float)
RATE_LIMIT_SECONDS = 2  # 1 request every 2 seconds for AI endpoints

def rate_limit(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        user_id = session.get('user_id')
        if user_id:
            now = time.time()
            if now - user_last_request[user_id] < RATE_LIMIT_SECONDS:
                return jsonify({'success': False, 'error': 'Slow down! Please wait a moment between requests.'}), 429
            user_last_request[user_id] = now
        return f(*args, **kwargs)
    return decorated


from werkzeug.utils import secure_filename
import uuid
import database
import emotion_engine
import ai_coach
import growth_engine
import ai_features

load_dotenv()

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 2 * 1024 * 1024  # 2MB Limit
UPLOAD_FOLDER = 'static/uploads/profile_photos'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

csrf = CSRFProtect(app)
@app.context_processor
def inject_user_helpers():
    return dict(get_user_by_id=database.get_user_by_id)

app.secret_key = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')

GOOGLE_CLIENT_ID = os.getenv('GOOGLE_CLIENT_ID', '')
GOOGLE_CLIENT_SECRET = os.getenv('GOOGLE_CLIENT_SECRET', '')

EMOTION_COLORS = {
    'happy': '#10b981', 'stressed': '#f59e0b', 'anxious': '#8b5cf6',
    'tired': '#6366f1', 'motivated': '#ec4899', 'confused': '#06b6d4',
    'frustrated': '#ef4444', 'neutral': '#64748b'
}

EMOTION_ICONS = {
    'focused': '◎', 'flow': '◈', 'anxious': '◇', 'confused': '○',
    'bored': '□', 'tired': '◑', 'excited': '◉', 'happy': '◉',
    'motivated': '◈', 'stressed': '◇', 'frustrated': '□', 'neutral': '○'
}

# Auth helper
def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated

database.init_db()

# ─── Main ─────────────────────────────────────────────────────────────────────
# ─── Public ──────────────────────────────────────────────────────────────────
@app.route('/')
def landing():
    if 'user_id' in session:
        return redirect(url_for('index'))
    return render_template('landing.html')

# ─── Dashboard ───────────────────────────────────────────────────────────────
@app.route('/dashboard')
@login_required
def index():
    user_id = session['user_id']
    stats = database.get_emotion_stats(user_id=user_id)
    weekly_stats = database.get_weekly_stats(user_id=user_id)
    total_sessions = sum(stats.values())
    total_hours = sum(day['hours'] for day in weekly_stats) if weekly_stats else 0
    sessions_this_week = sum(day['session_count'] for day in weekly_stats) if weekly_stats else 0
    recent_sessions = database.get_session_history(limit=5, user_id=user_id)
    saved_mats = database.get_user_materials(user_id)
    avg_score = 83 # Placeholder
    recent_session = recent_sessions[0] if recent_sessions else None
    study_plan = ai_features.generate_study_plan(recent_session['emotion'] if recent_session else 'neutral')
    return render_template('dashboard.html', 
                          study_plan=study_plan,
                          username=session.get('username', 'Student'),
                          total_sessions=total_sessions,
                          sessions_this_week=sessions_this_week,
                          total_hours=total_hours,
                          avg_score=avg_score,
                          recent_sessions=recent_sessions,
                          emotion_icons=EMOTION_ICONS,
                          saved_materials=saved_mats,
                          stats=stats,
                          weekly_stats=weekly_stats)

@app.route('/analyze', methods=['POST'])
@login_required
def analyze():
    data = request.get_json()
    if not data or 'feeling' not in data:
        return jsonify({'error': 'No input provided'}), 400
    user_input = data['feeling'].strip()
    if not user_input:
        return jsonify({'error': 'Please describe how you are feeling'}), 400

    socratic_mode = data.get('socratic_mode', False)
    dominant, confidence, probs = emotion_engine.analyze_emotion(user_input)
    prob_list = list(probs.items())
    secondary = prob_list[1][0] if len(prob_list) > 1 and prob_list[1][1] >= 10 else None
    recommendation = emotion_engine.get_recommendation(dominant)
    study_plan = emotion_engine.generate_study_plan(dominant, secondary, user_input=user_input)
    if socratic_mode:
        recommendation['title'] = "🤔 Socratic Inquiry"
        recommendation['tip'] = "I'll guide you with questions rather than answers."
        study_plan['context'] = "Socratic guidance active. Exploring concepts through inquiry."

    # AI confidence mapping
    if confidence >= 40:
        ai_confidence = {'label': 'High', 'score': confidence, 'color': '#10b981'}
    elif confidence >= 25:
        ai_confidence = {'label': 'Medium', 'score': confidence, 'color': '#f59e0b'}
    else:
        ai_confidence = {'label': 'Low', 'score': confidence, 'color': '#ef4444'}

    database.save_session(emotion=dominant, suggestion=recommendation['title'],
                          user_input=user_input, user_id=session.get('user_id'))

    return jsonify({
        'success': True,
        'emotion': dominant,
        'secondary': secondary,
        'confidence': confidence,
        'ai_confidence': ai_confidence,
        'emotion_probs': probs,
        'recommendation': recommendation,
        'study_plan': study_plan
    })

# ─── Analytics v5.0 ───────────────────────────────────────────────────────────
@app.route('/analytics')
@login_required
def analytics():
    user_id = session['user_id']
    stats = database.get_emotion_stats(user_id=user_id)
    trend_data = database.get_trend_data(user_id=user_id, days=7)
    recent_sessions = database.get_recent_sessions_raw(user_id=user_id, limit=20)
    monthly_sessions = database.get_monthly_sessions(user_id)
    
    # 1. Base Analytics
    patterns = emotion_engine.detect_patterns(recent_sessions)
    productivity_score = emotion_engine.calculate_productivity_score(stats)
    stability = emotion_engine.calculate_stability_index(recent_sessions)
    momentum = emotion_engine.calculate_momentum(recent_sessions)
    prediction = emotion_engine.predict_next_emotion_smart(recent_sessions)
    
    # 2. Growth Engine v5.0
    habit_data = growth_engine.calculate_habit_score(monthly_sessions)
    long_term_growth = growth_engine.calculate_30day_growth(monthly_sessions)
    weekly_hour_goal = database.get_user_goal(user_id)
    goal_alignment = growth_engine.calculate_goal_alignment(recent_sessions, weekly_hour_goal)
    
    # 3. AI Coach v4.0 + Burnout v2.0
    top_emotion = list(stats.keys())[0] if stats else 'neutral'
    neg_emotions = ('stressed', 'anxious', 'frustrated', 'tired')
    neg_count = sum(stats.get(e, 0) for e in neg_emotions)
    total_sess = sum(stats.values())
    burnout_score_v1 = int((neg_count / total_sess * 100)) if total_sess > 0 else 0
    
    burnout_pred = growth_engine.burnout_prediction_v2(
        burnout_score_v1, momentum.get("momentum_score", 0), stability.get("stability_score", 100)
    )
    
    growth_score = round((productivity_score + (momentum.get("momentum_score", 0) + 100) / 2 + habit_data['score']) / 3)
    
    coach_advice = ai_coach.get_coaching_advice(
        top_emotion, momentum.get("momentum_score", 0), 
        stability.get("stability_score", 100), burnout_pred['risk_score'],
        growth_score
    )
    
    return render_template('analytics.html',
        username=session.get('username', 'Student'),
        stats=stats, trend_data=trend_data, patterns=patterns,
        productivity_score=productivity_score, stability=stability, momentum=momentum,
        prediction=prediction, coach_advice=coach_advice, growth_score=growth_score, 
        habit_data=habit_data, long_term_growth=long_term_growth, goal_alignment=goal_alignment,
        burnout_pred=burnout_pred, weekly_hour_goal=weekly_hour_goal,
        total_sessions=total_sess, top_emotion=top_emotion, top_emotion_icon=emotion_engine.EMOTION_ICONS.get(top_emotion, ''),
        emotion_icons=emotion_engine.EMOTION_ICONS, emotion_colors=EMOTION_COLORS
    )

# ─── Weekly Report v5.0 ───────────────────────────────────────────────────────
@app.route('/weekly-report')
@login_required
def weekly_report():
    user_id = session['user_id']
    stats = database.get_emotion_stats(user_id=user_id)
    trend_data = database.get_trend_data(user_id=user_id, days=7)
    recent_sessions = database.get_recent_sessions_raw(user_id=user_id, limit=50)
    monthly_sessions = database.get_monthly_sessions(user_id)
    
    productivity_score = emotion_engine.calculate_productivity_score(stats)
    summary = emotion_engine.generate_weekly_summary(stats, trend_data, recent_sessions, productivity_score)
    stability = emotion_engine.calculate_stability_index(recent_sessions)
    momentum = emotion_engine.calculate_momentum(recent_sessions)
    prediction = emotion_engine.predict_next_emotion_smart(recent_sessions)
    
    # Growth & Habit Engine
    habit_data = growth_engine.calculate_habit_score(monthly_sessions)
    long_term_growth = growth_engine.calculate_30day_growth(monthly_sessions)
    weekly_hour_goal = database.get_user_goal(user_id)
    goal_alignment = growth_engine.calculate_goal_alignment(recent_sessions, weekly_hour_goal)
    
    # AI Coach v4.0 + Burnout v2.0
    top_emotion = summary.get('dominant_emotion', 'neutral')
    burnout_pred = growth_engine.burnout_prediction_v2(
        summary.get('burnout_score', 0), momentum.get("momentum_score", 0), stability.get("stability_score", 100)
    )
    growth_score = round((productivity_score + (momentum.get("momentum_score", 0) + 100) / 2 + habit_data['score']) / 3)
    
    coach_advice = ai_coach.get_coaching_advice(
        top_emotion, momentum.get("momentum_score", 0), 
        stability.get("stability_score", 100), burnout_pred['risk_score'],
        growth_score
    )
    
    reflection = ai_coach.generate_weekly_reflection(recent_sessions, stats, summary)
    weekly_stats = database.get_weekly_stats(user_id=user_id)
    
    return render_template('weekly_report.html',
        username=session.get('username', 'Student'),
        summary=summary, stability=stability, momentum=momentum, prediction=prediction, 
        coach_advice=coach_advice, growth_score=growth_score, reflection=reflection,
        habit_data=habit_data, long_term_growth=long_term_growth, goal_alignment=goal_alignment,
        burnout_pred=burnout_pred, weekly_hour_goal=weekly_hour_goal,
        trend_data=trend_data, weekly_stats=weekly_stats,
        emotion_icons=emotion_engine.EMOTION_ICONS, emotion_colors=EMOTION_COLORS,
        report_date=datetime.now().strftime('%B %d, %Y')
    )

@app.route('/update-goal', methods=['POST'])
@login_required
def update_goal():
    data = request.get_json()
    goal = data.get('goal')
    if goal is not None:
        try:
            goal = float(goal)
            if 1 <= goal <= 168:
                database.update_user_goal(session['user_id'], goal)
                return jsonify({'success': True})
        except: pass
    return jsonify({'success': False, 'message': 'Invalid goal value'}), 400

# ─── Auth (Register/Login Simplified) ────────────────────────────────────────
@app.route('/register', methods=['GET', 'POST'])
def register():
    if 'user_id' in session: return redirect(url_for('index'))
    if request.method == 'GET': return render_template('register.html')
    data = request.get_json()
    u, p, c = data.get('username', '').strip(), data.get('password', ''), data.get('confirm_password', '')
    if len(u) < 3 or len(p) < 6 or p != c: return jsonify({'success': False, 'message': 'Invalid Input'})
    uid = database.create_user(u, generate_password_hash(p))
    if uid is None: return jsonify({'success': False, 'message': 'Taken'})
    session['user_id'], session['username'] = uid, u
    return jsonify({'success': True, 'redirect': '/dashboard'})

@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session: return redirect(url_for('index'))
    if request.method == 'GET': return render_template('login.html')
    data = request.get_json()
    user = database.get_user_by_username(data.get('username', '').strip())
    if not user or not check_password_hash(user['password_hash'], data.get('password', '')):
        return jsonify({'success': False, 'message': 'Invalid'})
    session['user_id'], session['username'] = user['id'], user['username']
    return jsonify({'success': True, 'redirect': '/dashboard'})

@app.route('/login-demo', methods=['POST'])
def login_demo():
    username = "Demo Student"
    user = database.get_user_by_username(username)
    if not user:
        uid = database.create_user(username, generate_password_hash("demo-pass-123"))
        user = database.get_user_by_id(uid)
    session['user_id'], session['username'] = user['id'], user['username']
    return jsonify({'success': True, 'redirect': '/dashboard'})

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'GET': return render_template('forgot_password.html')
    data = request.get_json()
    user = database.get_user_by_username(data.get('username', '').strip())
    if not user: return jsonify({'success': False})
    token = database.create_reset_token(user['id'])
    return jsonify({'success': True, 'show_link': True, 'reset_url': url_for('reset_password', token=token, _external=True)})

@app.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    if request.method == 'GET':
        v = database.verify_reset_token(token)
        return render_template('reset_password.html', valid=v is not None, token=token)
    data = request.get_json()
    v = database.verify_reset_token(token)
    if not v: return jsonify({'success': False})
    database.update_password(v, generate_password_hash(data.get('password', '')))
    database.invalidate_reset_token(token)
    return jsonify({'success': True})

@app.route('/profile')
@login_required
def profile():
    user = database.get_user_by_id(session['user_id'])
    st = database.get_emotion_stats(session['user_id'])
    g = database.get_user_goal(session['user_id'])
    return render_template('profile.html', user=user, stats=st, weekly_hour_goal=g, total_sessions=sum(st.values()))

@app.route('/auth/google')
def auth_google():
    return render_template('oauth_coming_soon.html')

@app.route('/auth/google/callback')
def auth_google_callback():
    code = request.args.get('code')
    res = requests.post('https://oauth2.googleapis.com/token', data={'code': code, 'client_id': GOOGLE_CLIENT_ID, 'client_secret': GOOGLE_CLIENT_SECRET, 'redirect_uri': url_for('auth_google_callback', _external=True), 'grant_type': 'authorization_code'})
    tok = res.json().get('access_token')
    ui = requests.get('https://www.googleapis.com/oauth2/v2/userinfo', headers={'Authorization': f'Bearer {tok}'}).json()
    uname = f"google_{ui.get('id')}"
    user = database.get_user_by_username(uname)
    if not user:
        uid = database.create_user(uname, generate_password_hash(os.urandom(32).hex()))
        user = database.get_user_by_id(uid)
    session['user_id'], session['username'] = user['id'], user['username']
    return redirect(url_for('index'))


@app.route('/generate-flashcards', methods=['POST'])
@rate_limit
@login_required
def generate_flashcards():
    data = request.get_json()
    content = data.get('content', '')
    if not content:
        return jsonify({'success': False, 'error': 'No content provided'}), 400
    
    flashcards = ai_features.generate_flashcards(content)
    if 'error' in flashcards:
        return jsonify({'success': False, 'error': flashcards['error']}), 500
    return jsonify({'success': True, 'flashcards': flashcards.get('flashcards', [])})

@app.route('/generate-questions', methods=['POST'])
@rate_limit
@login_required
def generate_questions():
    data = request.get_json()
    content = data.get('content', '')
    if not content:
        return jsonify({'error': 'No content provided'}), 400
    
    questions = ai_features.generate_questions(content)
    return jsonify({'success': 'error' not in questions, 'quiz': questions})

@app.route('/chat', methods=['POST'])
@rate_limit
@login_required
def chat():
    data = request.get_json()
    if not data or 'message' not in data:
        return jsonify({'error': 'No message provided'}), 400
        
    user_message = data['message']
    socratic_mode = data.get('socratic_mode', False)
    context = data.get('context', '')
    history = data.get('history', [])
    
    llm_messages = []
    if context:
        llm_messages.append({"role": "user", "content": f"Here is my study material for context: \\r\n\r\n{context}"})
        llm_messages.append({"role": "assistant", "content": "Understood. I have read your materials. What would you like to discuss?"})
        
    for h in history:
        llm_messages.append(h)
    llm_messages.append({"role": "user", "content": user_message})
    
    # Check if we are in Coach Mode (which replaces/extends Socratic)
    is_coach = data.get('coach_mode', False)
    persona = data.get('persona', 'Socratic')
    
    if is_coach:
        # Get last emotion for context
        recent = database.get_session_history(limit=1, user_id=session['user_id'])
        emotion = recent[0]['emotion'] if recent else 'neutral'
        response = ai_features.study_coach_response(user_message, history, emotion, context, persona=persona)
    else:
        response = ai_coach.get_ai_chat_response(llm_messages, socratic_mode=socratic_mode)
        
    return jsonify({'response': response})

@app.route('/get-summary', methods=['POST'])
@login_required
def get_summary():
    data = request.get_json()
    if not data or 'content' not in data:
        return jsonify({'error': 'No content provided'}), 400
    summary = ai_coach.get_quick_summary(data['content'])
    return jsonify({'success': True, 'summary': summary})



@app.route('/set-emotion', methods=['POST'])
@login_required
def set_emotion():
    data = request.get_json()
    emotion = data.get('emotion', 'neutral').lower()
    
    # Save a quick session for this manual override
    database.save_session(
        emotion=emotion,
        suggestion="Manual Mood Update",
        user_input="User manually set mood to " + emotion,
        user_id=session['user_id']
    )
    
    study_plan = ai_features.generate_study_plan(emotion)
    return jsonify({'success': True, 'study_plan': study_plan, 'emotion': emotion})


@app.route('/api/materials')
def get_materials():
    page = int(request.args.get("page", 1))
    limit = int(request.args.get("limit", 50))
    start = (page - 1) * limit
    end = start + limit
    return jsonify({'success': True, 'materials': study_materials[start:end]})

@app.route('/api/materials/search')
def search_materials():
    query = request.args.get("q","").lower()
    results = [
        m for m in study_materials
        if query in m["title"].lower() or query in m["subject"].lower()
    ]
    return jsonify({'success': True, 'results': results[:50]})

@app.route('/api/user-materials', methods=['GET'])
@login_required
def get_user_materials_api():
    mats = database.get_user_materials(session['user_id'])
    return jsonify(mats)
@app.route('/save-material', methods=['POST'])
@login_required
def save_material():
    data = request.get_json()
    if not data or 'id' not in data or 'title' not in data:
        return jsonify({'error': 'Invalid data'}), 400
    
    database.save_material(
        mat_id=data['id'],
        user_id=session['user_id'],
        title=data['title'],
        source=data.get('source', 'unknown'),
        content=data.get('content', '')
    )
    return jsonify({'success': True})

@app.route('/delete-material', methods=['DELETE'])
@login_required
def delete_material():
    data = request.get_json()
    if not data or 'id' not in data:
        return jsonify({'error': 'No ID provided'}), 400
    
    success = database.delete_material(data['id'], session['user_id'])
    return jsonify({'success': success})

@app.route('/upload-material', methods=['POST'])
@login_required
def upload_material():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
    content = ""
    if file.filename.endswith('.pdf'):
        try:
            reader = PdfReader(file)
            for page in reader.pages:
                content += page.extract_text() + "\\n"
        except Exception as e:
            return jsonify({'error': f'PDF processing error: {str(e)}'}), 500
    else:
        content = file.read().decode('utf-8', errors='ignore')

    if not content.strip():
        return jsonify({'error': 'File appears to be empty'}), 400

    import uuid
    mat_id = str(uuid.uuid4())
    title = file.filename
    database.save_material(mat_id, session['user_id'], title, 'upload', content)
    
    return jsonify({
        'success': True,
        'material': {'id': mat_id, 'title': title, 'source': 'upload', 'content': content}
    })

@app.route('/update-settings', methods=['POST'])
@login_required
def update_settings():
    data = request.get_json()
    username = data.get('username')
    goal = data.get('goal')
    
    try:
        if goal:
            goal = float(goal)
        success = database.update_user_settings(session['user_id'], username, goal)
        if success and username:
            session['username'] = username
        return jsonify({'success': success})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400

@app.route('/upload-profile-photo', methods=['POST'])
@login_required
def upload_profile_photo():
    if 'photo' not in request.files:
        return jsonify({'success': False, 'message': 'No file part'}), 400
    
    file = request.files['photo']
    if file.filename == '':
        return jsonify({'success': False, 'message': 'No selected file'}), 400
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        # Unique filename to avoid collisions and caching issues
        ext = filename.rsplit('.', 1)[1].lower()
        unique_name = f"{session['user_id']}_{uuid.uuid4().hex[:8]}.{ext}"
        
        if not os.path.exists(UPLOAD_FOLDER):
            os.makedirs(UPLOAD_FOLDER)
            
        file_path = os.path.join(UPLOAD_FOLDER, unique_name)
        file.save(file_path)
        
        # Update DB
        web_path = f"/static/uploads/profile_photos/{unique_name}"
        database.update_user_photo(session['user_id'], web_path)
        
        return jsonify({'success': True, 'photo_url': web_path})
    
    return jsonify({'success': False, 'message': 'Invalid file type. Use JPG or PNG.'}), 400

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)





