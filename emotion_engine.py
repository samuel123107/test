"""
Emotion Analysis Engine - ML-Powered Multi-Emotion Intelligence
Uses Scikit-Learn (TF-IDF + Logistic Regression) for professional accuracy.
Features: ML Classification, Emotional Momentum, Stability Index, Smart Prediction.
"""

import numpy as np
import collections
from datetime import datetime
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression

# ─── Training Data (Optimized for Study Assistant) ───────────────────────────
TRAINING_DATA = [
    ("I feel great today", "happy"), ("I am happy with my progress", "happy"),
    ("I'm having a wonderful day", "happy"), ("I love studying this", "happy"),
    ("This is fun", "happy"), ("I'm feeling positive", "happy"),
    ("Great results on my last quiz", "happy"), ("I feel excellent and joyful", "happy"),
    ("Everything is going smoothly", "happy"), ("I feel successful", "happy"),
    
    ("I am so stressed out", "stressed"), ("Too much work to do", "stressed"),
    ("I'm feeling overwhelmed", "stressed"), ("Under a lot of pressure", "stressed"),
    ("I have a deadline coming up", "stressed"), ("I'm swamped with assignments", "stressed"),
    ("This is too much for me to handle", "stressed"), ("I'm struggling to keep up with the material", "stressed"),
    ("I feel panicky about my workload", "stressed"), ("Busy and stressed", "stressed"),
    
    ("I'm worried about my exams", "anxious"), ("I feel panicky", "anxious"),
    ("I'm nervous for the test tomorrow", "anxious"), ("I can't stop thinking about failure", "anxious"),
    ("I feel shaky and uneasy", "anxious"), ("My heart is racing thinking about the finals", "anxious"),
    ("I'm concerned about my grades", "anxious"), ("Fretful about upcoming results", "anxious"),
    
    ("I'm so exhausted", "tired"), ("I have no energy to study", "tired"),
    ("I'm feeling very sleepy", "tired"), ("I can't keep my eyes open", "tired"),
    ("I need a nap right now", "tired"), ("I'm drained and fatigued", "tired"),
    
    ("I'm ready to tackle this", "motivated"), ("Let's get to work", "motivated"),
    ("I'm feeling productive", "motivated"), ("I want to learn more today", "motivated"),
    ("I'm focused and ready for deep study", "motivated"), ("Highly motivated today", "motivated"),
    
    ("I don't understand this concept", "confused"), ("I'm so confused by this", "confused"),
    ("This makes no sense to me", "confused"), ("I'm lost in this topic", "confused"),
    ("What does this definition mean?", "confused"), ("Puzzled by these math problems", "confused"),
    
    ("I'm so annoyed with this problem", "frustrated"), ("This is incredibly frustrating", "frustrated"),
    ("I want to give up", "frustrated"), ("Argh this is not working", "frustrated"),
    ("I'm losing my patience", "frustrated"), ("Irritated by this codebase", "frustrated"),
    
    ("I feel okay", "neutral"), ("I'm just studying", "neutral"),
    ("Nothing special today", "neutral"), ("I'm in a normal mood", "neutral"),
    ("Average day of studying", "neutral"), ("Just fine", "neutral"),
]

# ─── Model Global State ───
texts, labels = zip(*TRAINING_DATA)
tfidf = TfidfVectorizer(stop_words='english', min_df=1, sublinear_tf=True)
X_train = tfidf.fit_transform(texts)
clf = LogisticRegression(max_iter=1000)
clf.fit(X_train, labels)

EMOTIONS = clf.classes_
EMOTION_ICONS = {
    'happy': '😊', 'stressed': '😰', 'anxious': '😟', 'tired': '😴',
    'motivated': '🚀', 'confused': '🤔', 'frustrated': '😤', 'neutral': '😐'
}

# ─── Valence Mapping (for mathematical analysis) ───
EMOTION_VALENCE = {
    'happy': 1.0, 'motivated': 0.9, 'neutral': 0.1,
    'confused': -0.3, 'tired': -0.5,
    'frustrated': -0.8, 'anxious': -1.0, 'stressed': -1.2
}

EMOTION_RECOMMENDATIONS = {
    'happy': {'title': '🌟 Keep the Momentum!', 'color': '#10b981', 'study_tip': 'Perfect for deep learning.', 'suggestions': ['Tackle challenging topics']},
    'stressed': {'title': '🧘 Reduce Pressure', 'color': '#f59e0b', 'study_tip': 'Break it down.', 'suggestions': ['Short breaks']},
    'anxious': {'title': '💚 Confidence', 'color': '#8b5cf6', 'study_tip': 'Start familiar.', 'suggestions': ['Mindfulness']},
    'tired': {'title': '😴 Rest', 'color': '#6366f1', 'study_tip': 'Rest is learning.', 'suggestions': ['Power nap']},
    'motivated': {'title': '🚀 Focus', 'color': '#ec4899', 'study_tip': 'Channel energy.', 'suggestions': ['Hardest material']},
    'confused': {'title': '🤔 Clarity', 'color': '#06b6d4', 'study_tip': 'Ask questions.', 'suggestions': ['Tutorials']},
    'frustrated': {'title': '😤 Breath', 'color': '#ef4444', 'study_tip': 'Growth mindset.', 'suggestions': ['Step away']},
    'neutral': {'title': '📚 Steady', 'color': '#64748b', 'study_tip': 'Consistency counts.', 'suggestions': ['Routine study']}
}

# ─── 1. Emotional Momentum ───
def calculate_momentum(sessions):
    """
    Detects if valence is improving, stable, or declining.
    Returns: { "momentum": label, "momentum_score": -100 to 100 }
    """
    if len(sessions) < 4:
        return {"momentum": "Stable", "momentum_score": 0}
    
    # Get valence values, newest first
    valences = [EMOTION_VALENCE.get(s['emotion'], 0) for s in sessions]
    
    # Compare newest half vs oldest half
    mid = len(valences) // 2
    avg_recent = np.mean(valences[:mid])
    avg_older = np.mean(valences[mid:])
    
    diff = avg_recent - avg_older
    score = int(np.clip(diff * 50, -100, 100)) # Scale diff to -100 to 100
    
    if score > 15: label = "Improving"
    elif score < -15: label = "Declining"
    else: label = "Stable"
    
    return {"momentum": label, "momentum_score": score}

# ─── 2. Emotional Stability Index ───
def calculate_stability_index(sessions):
    """
    Calculates variance of last 10 emotions.
    Returns: { "stability_score": 0-100, "stability_label": label }
    """
    if len(sessions) < 3:
        return {"stability_score": 100, "stability_label": "Stable"}
    
    trimmed = sessions[:10]
    valences = [EMOTION_VALENCE.get(s['emotion'], 0) for s in trimmed]
    variance = np.var(valences) # High variance = unstable
    
    # Map variance (typically 0 to ~1.0) to 0-100 stability score
    # Lower variance -> Higher stability
    score = int(max(0, min(100, (1 - variance) * 100)))
    
    if score >= 75: label = "Stable"
    elif score >= 45: label = "Moderate"
    else: label = "Volatile"
    
    return {"stability_score": score, "stability_label": label}

# ─── 3. Smart Next Emotion Prediction ───
def predict_next_emotion_smart(sessions):
    """
    Weighted recency prediction. Newer sessions count more.
    """
    if not sessions: return None
    
    if len(sessions) < 2:
        pred = sessions[0]['emotion']
        return {"predicted": pred, "confidence": "Low", "probability": 100, "reason": "First session baseline."}

    # Weighting: 1/1, 1/2, 1/3... (or linear)
    emo_weights = collections.defaultdict(float)
    for i, s in enumerate(sessions[:10]):
        weight = 1.0 / (i + 1)
        emo_weights[s['emotion']] += weight
        
    # Get top weighted emotion
    predicted = max(emo_weights, key=emo_weights.get)
    total_weight = sum(emo_weights.values())
    prob = int((emo_weights[predicted] / total_weight) * 100)
    
    if prob >= 60: conf = "High"
    elif prob >= 40: conf = "Medium"
    else: conf = "Low"
    
    # Reason logic
    mom = calculate_momentum(sessions[:5])
    reason = f"Based on your {mom['momentum'].lower()} trend and weighted recency."
    
    return {
        "predicted": predicted, 
        "confidence": conf, 
        "probability": prob, 
        "reason": reason,
        "icon": EMOTION_ICONS.get(predicted, "😐")
    }

# ─── 4. AI Insight Generator ───
def generate_ai_insights(sessions):
    """
    Analyzes timestamps + patterns to generate dynamic text insights.
    """
    insights = []
    if len(sessions) < 5:
        return ["Need more data to generate advanced insights."]
        
    # Time-based analysis
    time_emotions = collections.defaultdict(list)
    for s in sessions:
        try:
            ts = s.get('timestamp', '')
            # Assuming format 'YYYY-MM-DD HH:MM:SS'
            hour = int(str(ts)[11:13])
            if 6 <= hour < 12: bucket = "morning"
            elif 12 <= hour < 17: bucket = "afternoon"
            elif 17 <= hour < 22: bucket = "evening"
            else: bucket = "night"
            time_emotions[bucket].append(s['emotion'])
        except: continue
        
    for bucket, emotes in time_emotions.items():
        if len(emotes) >= 2:
            top = collections.Counter(emotes).most_common(1)[0]
            if top[1] >= len(emotes) * 0.6: # 60% frequency
                if top[0] in ('stressed', 'anxious', 'tired'):
                    insights.append(f"Your {top[0]} levels tend to spike during the {bucket}.")
                elif top[0] in ('motivated', 'happy'):
                    insights.append(f"The {bucket} appears to be your peak output window.")

    # Consistency analysis
    stab = calculate_stability_index(sessions)
    if stab['stability_label'] == "Volatile":
        insights.append("Highly volatile shifts detected. Ensure you're taking tactical breaks.")
    
    # Default fallback
    if not insights:
        insights.append("Stay consistent with your session logging for deeper insights.")
        
    return insights[:3]

# ─── Core ML Analysis ───
def analyze_emotion(text):
    if not text or not text.strip():
        return 'neutral', 0, {'neutral': 100}
    
    X_input = tfidf.transform([text])
    probs = clf.predict_proba(X_input)[0]
    prob_dict = {em: round(p * 100) for em, p in zip(EMOTIONS, probs)}
    
    diff = 100 - sum(prob_dict.values())
    if diff != 0:
        top_em = max(prob_dict, key=prob_dict.get)
        prob_dict[top_em] += diff
        
    sorted_probs = dict(sorted(prob_dict.items(), key=lambda x: x[1], reverse=True))
    dominant = list(sorted_probs.keys())[0]
    return dominant, sorted_probs[dominant], sorted_probs

# ─── 5. Upgraded Weekly Summary ───
def generate_weekly_summary(stats, trend, sessions, productivity_score):
    """
    Returns upgraded complex summary object.
    """
    mom = calculate_momentum(sessions)
    stab = calculate_stability_index(sessions)
    
    # Calculate burnout risk
    neg_emotions = ('stressed', 'anxious', 'frustrated', 'tired')
    neg_count = sum(stats.get(e, 0) for e in neg_emotions)
    total = sum(stats.values())
    burnout_score = int((neg_count / total * 100)) if total > 0 else 0
    
    if burnout_score > 60: risk = "High"
    elif burnout_score > 30: risk = "Moderate"
    else: risk = "Low"
    
    insights = generate_ai_insights(sessions)
    
    dom = list(stats.keys())[0] if stats else 'neutral'
    
    return {
        "dominant_emotion": dom,
        "dominant_icon": EMOTION_ICONS.get(dom, "😐"),
        "productivity_score": productivity_score,
        "burnout_risk": risk,
        "burnout_score": burnout_score,
        "momentum": mom['momentum'],
        "momentum_score": mom['momentum_score'],
        "stability": stab['stability_label'],
        "stability_score": stab['stability_score'],
        "recommendation": "Maintain a balanced study-rest ratio." if risk != "High" else "Critical: Take a 24-hour digital detox.",
        "emotional_insight": insights[0] if insights else "Keep tracking to reveal patterns."
    }

# ─── Context & Plans ───
EXAM_KEYWORDS = ['exam', 'test', 'quiz', 'deadline', 'tomorrow', 'tonight', 'finals']
TIRED_KEYWORDS = ['tired', 'exhausted', 'sleepy', 'drained']

def detect_context(user_input):
    txt = user_input.lower() if user_input else ''
    return {'exam': any(k in txt for k in EXAM_KEYWORDS), 'tired': any(k in txt for k in TIRED_KEYWORDS)}

def generate_study_plan(dominant, secondary, hour=None, user_input=''):
    if hour is None: hour = datetime.now().hour
    time_label = 'morning' if 6 <= hour < 12 else 'afternoon' if 12 <= hour < 17 else 'evening' if 17 <= hour < 22 else 'night'
    ctx = detect_context(user_input)

    if ctx['exam'] and dominant in ('stressed', 'anxious'):
        return {'mode': 'exam-sprint', 'time_context': time_label, 'total_minutes': 20, 'blocks': [{'duration': 15, 'activity': 'Focused revision', 'type': 'study', 'icon': '🔥'}]}
    
    if dominant == 'motivated':
        return {'mode': 'deep-work', 'time_context': time_label, 'total_minutes': 55, 'blocks': [{'duration': 45, 'activity': 'Deep work', 'type': 'study', 'icon': '💪'}]}
    
    return {'mode': 'standard', 'time_context': time_label, 'total_minutes': 30, 'blocks': [{'duration': 25, 'activity': 'Study block', 'type': 'study', 'icon': '📖'}]}

# Legacy support helpers
def get_recommendation(emotion):
    return EMOTION_RECOMMENDATIONS.get(emotion, EMOTION_RECOMMENDATIONS['neutral'])

def calculate_stability(sessions):
    res = calculate_stability_index(sessions)
    return {'score': res['stability_score'], 'label': res['stability_label'], 'color': '#10b981' if res['stability_score'] > 70 else '#f59e0b'}

def detect_patterns(sessions):
    res = detect_patterns_internal(sessions)
    return res

def detect_patterns_internal(sessions):
    if not sessions: return {'warnings': [], 'trend': None, 'insights': []}
    emotions = [s['emotion'] for s in sessions]
    counts = collections.Counter(emotions)
    trend = counts.most_common(1)[0][0]
    insights = generate_ai_insights(sessions)
    return {'warnings': [], 'trend': trend, 'insights': insights, 'emotion_counts': dict(counts)}

def predict_next_emotion(sessions):
    return predict_next_emotion_smart(sessions)

def calculate_productivity_score(stats):
    if not stats: return 0
    total = sum(stats.values())
    w = {'happy': 2.0, 'motivated': 2.0, 'neutral': 1.0, 'stressed': -1.5, 'anxious': -1.5, 'frustrated': -1.0, 'tired': -0.5}
    score = sum(w.get(e, 0) * c for e, c in stats.items())
    return max(0, min(100, round(((score - (total*-1.5)) / (total*2 - (total*-1.5))) * 100))) if total > 0 else 0
