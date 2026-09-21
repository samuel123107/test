// ========================================
// DOM Elements
// ========================================
const emotionForm = document.getElementById('emotionForm');
const feelingInput = document.getElementById('feelingInput');
const analyzeBtn = document.getElementById('analyzeBtn');
const charCount = document.getElementById('charCount');
const errorMessage = document.getElementById('errorMessage');
const resultsSection = document.getElementById('resultsSection');
const emotionIcon = document.getElementById('emotionIcon');
const emotionName = document.getElementById('emotionName');
const emotionSecondary = document.getElementById('emotionSecondary');
const recommendationTitle = document.getElementById('recommendationTitle');
const studyTip = document.getElementById('studyTip');
const suggestionsList = document.getElementById('suggestionsList');
const sessionsContainer = document.getElementById('sessionsContainer');
const probBars = document.getElementById('probBars');
const planBlocks = document.getElementById('planBlocks');
const planContext = document.getElementById('planContext');
const planTotal = document.getElementById('planTotal');

// ========================================
// Emotion Config
// ========================================
const EMOTION_ICONS = {
    'happy': '😊', 'stressed': '😰', 'anxious': '😟',
    'tired': '😴', 'motivated': '🚀', 'confused': '🤔',
    'frustrated': '😤', 'neutral': '😐'
};
const EMOTION_COLORS = {
    'happy': '#10b981', 'stressed': '#f59e0b', 'anxious': '#8b5cf6',
    'tired': '#6366f1', 'motivated': '#ec4899', 'confused': '#06b6d4',
    'frustrated': '#ef4444', 'neutral': '#64748b'
};
const PLAN_TYPE_COLORS = {
    'study': '#667eea', 'break': '#10b981', 'review': '#f59e0b',
    'practice': '#ec4899', 'default': '#64748b'
};

// ========================================
// Character Counter
// ========================================
feelingInput.addEventListener('input', () => {
    const length = feelingInput.value.length;
    charCount.textContent = length;
    charCount.style.color = length > 450 ? '#ef4444' : '';
});

// ========================================
// Form Submission
// ========================================
emotionForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const feeling = feelingInput.value.trim();
    if (!feeling) { showError("Please tell us how you're feeling"); return; }
    if (feeling.length > 500) { showError('Please keep your input under 500 characters'); return; }
    setLoadingState(true);
    hideError();
    try {
        const response = await fetch('/analyze', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', 'X-CSRFToken': document.querySelector('meta[name="csrf-token"]').getAttribute('content') },
            body: JSON.stringify({ feeling })
        });
        const data = await response.json();
        if (!response.ok) throw new Error(data.error || 'An error occurred');
        if (data.success) {
            displayResults(data);
            loadSessionHistory();
            setTimeout(() => resultsSection.scrollIntoView({ behavior: 'smooth', block: 'nearest' }), 100);
        }
    } catch (error) {
        showError(error.message);
    } finally {
        setLoadingState(false);
    }
});

// ========================================
// Display Results
// ========================================
function displayResults(data) {
    const { emotion, secondary, recommendation, emotion_probs, study_plan } = data;

    // Dominant emotion
    emotionIcon.textContent = EMOTION_ICONS[emotion] || '😐';
    emotionName.textContent = emotion.charAt(0).toUpperCase() + emotion.slice(1);

    // Secondary emotion
    if (secondary) {
        emotionSecondary.textContent = Secondary:  ;
        emotionSecondary.style.display = 'block';
    } else {
        emotionSecondary.style.display = 'none';
    }

    // AI Confidence Score
    if (data.ai_confidence) renderConfidenceScore(data.ai_confidence);
    // Probability bars
    renderProbBars(emotion_probs);

    // Study plan
    if (study_plan && study_plan.blocks) {
        renderStudyPlan(study_plan, emotion);
    }

    // Recommendation
    recommendationTitle.textContent = recommendation.title;
    studyTip.textContent = recommendation.study_tip;
    suggestionsList.innerHTML = '';
    recommendation.suggestions.forEach(s => {
        const li = document.createElement('li');
        li.textContent = s;
        suggestionsList.appendChild(li);
    });
    if (recommendation.color) {
        document.querySelector('.recommendations').style.borderLeftColor = recommendation.color;
        document.querySelector('.study-tip').style.borderLeftColor = recommendation.color;
    }

    resultsSection.style.display = 'block';
    resultsSection.style.animation = 'fadeIn 0.6s ease';
}

// ========================================
// Probability Bars
// ========================================
function renderProbBars(probs) {
    probBars.innerHTML = '';
    Object.entries(probs).forEach(([emotion, pct], i) => {
        const color = EMOTION_COLORS[emotion] || '#64748b';
        const icon = EMOTION_ICONS[emotion] || '😐';
        const row = document.createElement('div');
        row.className = 'prob-row';
        row.style.animationDelay = ${i * 0.08}s;
        row.innerHTML = 
            <span class="prob-label"> </span>
            <div class="prob-track">
                <div class="prob-fill" style="background:; width:0%;" data-width="%"></div>
            </div>
            <span class="prob-pct">%</span>
        ;
        probBars.appendChild(row);
    });
    // Animate bars after render
    requestAnimationFrame(() => {
        document.querySelectorAll('.prob-fill').forEach(bar => {
            bar.style.width = bar.dataset.width;
        });
    });
}

// ========================================
// Study Plan
// ========================================
function renderStudyPlan(plan, emotion) {
    const timeLabels = { morning: '🌅 Morning', afternoon: '☀️ Afternoon', evening: '🌆 Evening', night: '🌙 Night' };
    planContext.textContent = ${timeLabels[plan.time_context] || ''} plan for  state;
    planBlocks.innerHTML = '';
    plan.blocks.forEach((block, i) => {
        const color = PLAN_TYPE_COLORS[block.type] || PLAN_TYPE_COLORS.default;
        const div = document.createElement('div');
        div.className = 'plan-block';
        div.style.animationDelay = ${i * 0.1}s;
        div.innerHTML = 
            <div class="plan-block-icon"></div>
            <div class="plan-block-body">
                <div class="plan-block-activity"></div>
                <div class="plan-block-meta">
                    <span class="plan-block-type" style="background:20; color:;"></span>
                    <span class="plan-block-duration">⏱  min</span>
                </div>
            </div>
        ;
        planBlocks.appendChild(div);
    });
    planTotal.textContent = Total:  minutes;
}

// ========================================
// Session History
// ========================================
async function loadSessionHistory() {
    try {
        const response = await fetch('/dashboard');
        const data = await response.json();
        if (data.success && data.sessions.length > 0) displaySessions(data.sessions);
    } catch (error) { console.error('Error loading session history:', error); }
}

function displaySessions(sessions) {
    if (sessions.length === 0) {
        sessionsContainer.innerHTML = '<p class="empty-state">No sessions yet. Start by sharing how you\'re feeling!</p>';
        return;
    }
    sessionsContainer.innerHTML = '';
    sessions.forEach(session => {
        const item = document.createElement('div');
        item.className = 'session-item';
        const emotionSpan = document.createElement('div');
        emotionSpan.className = 'session-emotion';
        emotionSpan.innerHTML = ${EMOTION_ICONS[session.emotion] || '😐'} ;
        const timeSpan = document.createElement('div');
        timeSpan.className = 'session-time';
        timeSpan.textContent = formatTimestamp(session.timestamp);
        item.appendChild(emotionSpan);
        item.appendChild(timeSpan);
        sessionsContainer.appendChild(item);
    });
}

// ========================================
// Helpers
// ========================================
function setLoadingState(isLoading) {
    analyzeBtn.disabled = isLoading;
    feelingInput.disabled = isLoading;
    analyzeBtn.querySelector('.btn-text').style.display = isLoading ? 'none' : 'inline';
    analyzeBtn.querySelector('.btn-loader').style.display = isLoading ? 'inline-flex' : 'none';
}
function showError(message) { errorMessage.textContent = message; errorMessage.style.display = 'block'; }
function hideError() { errorMessage.style.display = 'none'; }
function formatTimestamp(timestamp) {
    const date = new Date(timestamp);
    const now = new Date();
    const diffMins = Math.floor((now - date) / 60000);
    const diffHours = Math.floor(diffMins / 60);
    const diffDays = Math.floor(diffHours / 24);
    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return ${diffMins} minute ago;
    if (diffHours < 24) return ${diffHours} hour ago;
    if (diffDays < 7) return ${diffDays} day ago;
    return date.toLocaleDateString();
}

// ========================================
// Initialize
// ========================================
document.addEventListener('DOMContentLoaded', () => { loadSessionHistory(); });

// ─── AI Confidence Score Display ──────────────────────────────────────────────
function renderConfidenceScore(aiConf) {
    const existing = document.getElementById('aiConfidenceCard');
    if (existing) existing.remove();
    const card = document.createElement('div');
    card.id = 'aiConfidenceCard';
    card.className = 'ai-confidence-card';
    card.innerHTML = 
        <span class="ai-conf-label">🤖 AI Confidence</span>
        <div class="ai-conf-bar-track">
            <div class="ai-conf-bar-fill" style="background:; width:0%;" data-width="%"></div>
        </div>
        <span class="ai-conf-pct" style="color:;">% <em>()</em></span>
    ;
    const emotionSection = document.querySelector('.emotion-result');
    if (emotionSection) emotionSection.appendChild(card);
    requestAnimationFrame(() => {
        const fill = card.querySelector('.ai-conf-bar-fill');
        if (fill) fill.style.width = fill.dataset.width;
    });
}


