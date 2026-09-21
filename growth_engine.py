"""
Growth Engine v5.0 - Intelligent Behavioral Platform
Handles long-term modeling, habit scoring, and goal alignment.
"""

import collections
import numpy as np
from datetime import datetime, timedelta

def calculate_habit_score(sessions):
    """
    Consistency score (0-100). Rewards streaks, penalizes instability.
    """
    if not sessions:
        return {"score": 0, "streak": 0, "label": "No Data"}
    
    # 1. Consistency (Days with sessions in last 30)
    timestamps = []
    for s in sessions:
        try:
            ts = datetime.strptime(str(s['timestamp']), '%Y-%m-%d %H:%M:%S')
            timestamps.append(ts.date())
        except: continue
    
    unique_days = sorted(list(set(timestamps)), reverse=True)
    if not unique_days:
        return {"score": 0, "streak": 0, "label": "No Data"}

    # 2. Streak Detection
    streak = 0
    today = datetime.now().date()
    current = today
    
    # Check if they had a session today or yesterday to continue streak
    if unique_days and (unique_days[0] == today or unique_days[0] == today - timedelta(days=1)):
        for day in unique_days:
            if day == current:
                streak += 1
                current -= timedelta(days=1)
            elif day > current:
                continue
            else:
                break

    # 3. Frequency Score (sessions in last 30 days)
    # Ideal: 20+ days of sessions
    freq_score = min(100, (len(unique_days) / 20) * 100)
    
    # 4. Reward Streak
    streak_bonus = min(20, streak * 2)
    
    final_score = int(min(100, (freq_score * 0.8) + streak_bonus))
    
    if final_score >= 80: label = "Elite"
    elif final_score >= 60: label = "Consistent"
    elif final_score >= 40: label = "Building"
    else: label = "Developing"
    
    return {
        "score": final_score,
        "streak": streak,
        "label": label,
        "active_days": len(unique_days)
    }

def calculate_30day_growth(sessions):
    """
    Track emotional trend over 30 days.
    """
    if len(sessions) < 10:
        return {"status": "Stable", "insight": "Accumulating long-term data..."}
    
    # Map to valence
    valence_map = {
        'happy': 1.0, 'motivated': 0.9, 'neutral': 0.1,
        'confused': -0.3, 'tired': -0.5,
        'frustrated': -0.8, 'anxious': -1.0, 'stressed': -1.2
    }
    
    valences = [valence_map.get(s['emotion'], 0) for s in sessions]
    
    # Split into 3 segments (Older, Mid, Recent)
    n = len(valences)
    seg = n // 3
    recent_av = np.mean(valences[:seg])
    older_av = np.mean(valences[-seg:])
    
    diff = recent_av - older_av
    
    if diff > 0.2: status = "Improving"
    elif diff < -0.2: status = "Declining"
    else: status = "Stable"
    
    insight = "Your emotional resilience is trending upwards." if status == "Improving" else \
              "Consistency is your focus right now." if status == "Stable" else \
              "Detecting long-term fatigue baseline shifts."
              
    return {"status": status, "diff": round(diff, 2), "insight": insight}

def calculate_goal_alignment(sessions, weekly_goal_hours):
    """
    Compare actual behavior vs goal.
    Assuming average session is 45 minutes (0.75 hours).
    """
    if weekly_goal_hours <= 0: weekly_goal_hours = 10
    
    # Filter sessions for last 7 days
    now = datetime.now()
    week_ago = now - timedelta(days=7)
    
    current_week_sessions = 0
    for s in sessions:
        try:
            ts = datetime.strptime(str(s['timestamp']), '%Y-%m-%d %H:%M:%S')
            if ts >= week_ago:
                current_week_sessions += 1
        except: continue
        
    actual_hours = current_week_sessions * 0.75 # Estimated 45m per session
    alignment = min(100, int((actual_hours / weekly_goal_hours) * 100))
    
    return {
        "score": alignment,
        "actual_hours": round(actual_hours, 1),
        "target_hours": weekly_goal_hours,
        "status": "On Track" if alignment >= 90 else "Behind" if alignment < 50 else "Gaining"
    }

def burnout_prediction_v2(burnout_score_v1, momentum_score, stability_score):
    """
    Multi-factor risk modeling.
    """
    # Inverse stability/momentum
    # Low momentum + Low stability + high baseline burnout = V2 Risk
    risk_factors = 0
    if burnout_score_v1 > 50: risk_factors += 1
    if momentum_score < -10: risk_factors += 1
    if stability_score < 40: risk_factors += 1
    
    prediction_score = int((burnout_score_v1 * 0.5) + (abs(min(0, momentum_score)) * 0.3) + ((100 - stability_score) * 0.2))
    
    if prediction_score > 70:
        level = "High"
        intervention = "Mandatory 48h rest. Cognitive overload detected."
    elif prediction_score > 40:
        level = "Moderate"
        intervention = "Switch to micro-learning. Reduce session duration."
    else:
        level = "Low"
        intervention = "Maintain current intensity. Sustainable pace detected."
        
    return {
        "risk_level": level,
        "risk_score": prediction_score,
        "intervention": intervention,
        "trigger_count": risk_factors
    }
