function getCsrfToken() {
    return document.querySelector('meta[name="csrf-token"]')?.getAttribute('content');
}
let chatHistory = [];
let socraticMode = false;
/* ═══════════════════════════════════════════════════════
   DATA & CONFIG
   ═══════════════════════════════════════════════════════ */
const EMOTIONS = {
  focused:  { label: "Focused",  icon: "◎", color: "#a8ff3e" },
  flow:     { label: "In Flow",  icon: "◈", color: "#60a5fa" },
  anxious:  { label: "Anxious",  icon: "◇", color: "#fbbf24" },
  confused: { label: "Confused", icon: "○", color: "#c084fc" },
  bored:    { label: "Bored",    icon: "□", color: "#94a3b8" },
  tired:    { label: "Tired",    icon: "◑", color: "#f472b6" },
  excited:  { label: "Excited",  icon: "◉", color: "#fb923c" },
};

const LIBRARY = {};

const SUBJECTS = [];

let currentEmotion = 'focused';
let currentSubject = 'Mathematics';
let messages = [];
let sessionRunning = false;
let sessionSeconds = 0;
let timerInterval = null;
let chatLoading = false;
let flashcardsList = [];
let flashcardIndex = 0;
let materials = [];
let orbInterval = null;
let activeOrb = 0;

function updateMaterialsUI() {
  const badge = document.getElementById('mat-badge');
  const homeCount = document.getElementById('home-mat-count');
  const activeList = document.getElementById('active-mat-list');
  
  const count = materials.length;
  if (badge) { badge.textContent = count; badge.style.display = count > 0 ? 'inline' : 'none'; }
  if (homeCount) homeCount.textContent = count;
  
  const sessionList = document.getElementById('session-mat-list');
  if (sessionList) {
    if (count === 0) sessionList.innerHTML = '<div style="font-size:12px;color:#2a3045;text-align:center;padding:8px 0">No context loaded</div>';
    else sessionList.innerHTML = materials.map(m => `<div style="font-size:11px;padding:6px 9px;border-radius:4px;background:rgba(168,255,62,.06);border:1px solid rgba(168,255,62,.1);color:#8891a4;margin-bottom:4px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">📚 ${m.title}</div>`).join('');
  }

  if (activeList) {
    if (count === 0) {
      activeList.innerHTML = '<div style="font-size:13px;color:#3a4055;text-align:center;padding:40px 0;">No active materials. Use the library or paste a note.</div>';
    } else {
      activeList.innerHTML = materials.map(m => `
        <div style="padding:11px 13px;background:rgba(168,255,62,.05);border:1px solid rgba(168,255,62,.15);border-radius:10px;position:relative;margin-bottom:8px">
          <div style="font-size:12.5px;font-weight:600;color:#c8d0e0;margin-bottom:3px;padding-right:18px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">${m.title}</div>
          <div style="font-size:11px;color:#4a5270">${m.source} · ${m.content.length.toLocaleString()} chars</div>
          <button onclick="removeMaterial('${m.id}')" style="position:absolute;top:9px;right:9px;background:none;border:none;color:#4a5270;cursor:pointer;font-size:15px;">×</button>
        </div>`).join('');
    }
  }
}

async function removeMaterial(id) {
  materials = materials.filter(m => m.id !== id);
  updateMaterialsUI();
  if (typeof buildLibCards === 'function') buildLibCards();
  const csrfToken = document.querySelector('meta[name="csrf-token"]')?.getAttribute('content');
  try {
    await fetch('/delete-material', { 
        method: 'DELETE', 
        headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrfToken },
        body: JSON.stringify({ id })
    });
  } catch (e) { console.error('Sync error:', e); }
}

async function syncMaterial(mat) {
  const csrfToken = document.querySelector('meta[name="csrf-token"]')?.getAttribute('content');
  try {
    await fetch('/save-material', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrfToken },
        body: JSON.stringify(mat)
    });
  } catch (e) { console.error('Sync error:', e); }
}

function toggleLibMat(subject, title) {
  const mat = (LIBRARY[subject]||[]).find(m=>m.title===title);
  if (!mat) return;
  const id = `lib-${subject}-${title}`;
  if (materials.some(m=>m.id===id)) {
    removeMaterial(id);
  } else {
    const newMat = { id, title:mat.title, source:'library', content:mat.content };
    materials.push(newMat);
    syncMaterial(newMat);
  }
  updateMaterialsUI();
  if (typeof buildLibCards === 'function') buildLibCards();
}



async function updateMood(mood) {
    if (!mood) return;
    
    // Update display badge
    const displayMood = document.getElementById('display-mood');
    if (displayMood) displayMood.textContent = mood;
    
    // Show loading state in study plan
    const details = document.getElementById('study-plan-details');
    if (details) details.style.opacity = '0.5';
    
    try {
        const resp = await fetch('/set-emotion', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCsrfToken() },
            body: JSON.stringify({ emotion: mood })
        });
        const data = await resp.json();
        
        if (data.success && data.study_plan) {
            const plan = data.study_plan;
            if (details) {
                details.innerHTML = `
                    <div style="display:grid; grid-template-columns: 1fr 1fr; gap:20px;">
                      <div>
                        <div style="font-size:11px; color:#4a5270; text-transform:uppercase; margin-bottom:4px;">Focus Task</div>
                        <div style="font-size:16px; font-weight:700; color:#e8eaf0;">${plan.task}</div>
                      </div>
                      <div>
                        <div style="font-size:11px; color:#4a5270; text-transform:uppercase; margin-bottom:4px;">Target Duration</div>
                        <div style="font-size:16px; font-weight:700; color:#e8eaf0;">${plan.duration}</div>
                      </div>
                    </div>
                    <div style="margin-top:15px; padding-top:15px; border-top: 1px solid rgba(255,255,255,0.05); font-size:13px; color:#c0cce0; font-style: italic;">
                      "${plan.recommendation}"
                    </div>
                `;
                details.style.opacity = '1';
            }
            
            // Also update the global currentEmotion for chat context
            currentEmotion = mood;
            
            // Update sidebar/mood chips if they exist
            if (typeof selectEmotion === 'function') {
                selectEmotion(mood);
            }
        }
    } catch (e) {
        console.error('Error updating mood:', e);
        if (details) details.style.opacity = '1';
    }
}

async function loadNote() {
    try {
        const resp = await fetch('/api/user-materials');
        const mats = await resp.json();
        
        if (!mats || mats.length === 0) {
            alert("No saved notes found!");
            return;
        }
        
        // Filter for pasted notes
        const notes = mats.filter(m => m.source === 'pasted-note');
        if (notes.length === 0) {
            alert("No pasted notes found to load!");
            return;
        }
        
        // For simplicity, let's show a prompt with titles
        let msg = "Select a note to load (enter number):\n";
        notes.forEach((n, i) => msg += `${i+1}. ${n.title}\n`);
        
        const idx = prompt(msg);
        if (idx && !isNaN(idx)) {
            const selected = notes[parseInt(idx) - 1];
            if (selected) {
                const el = document.getElementById('note-editor');
                el.value = selected.content;
                el.style.height = 'auto';
                el.style.height = Math.min(el.scrollHeight, 150) + 'px';
            }
        }
    } catch (e) {
        console.error('Error loading notes:', e);
        alert("Failed to fetch notes.");
    }
}
function addPastedNote() {
  const el = document.getElementById('note-editor');
  const txt = el.value.trim();
  if (!txt) return;
  const title = txt.split('\n\\n')[0].substring(0,30) + (txt.length>30?'...':'');
  const newMat = { id:Date.now().toString(), title, source:'pasted-note', content:txt };
  materials.push(newMat);
  syncMaterial(newMat);
  el.value = '';
  updateMaterialsUI();
}

function updateSendBtn() {
  const btn = document.getElementById('send-btn');
  const input = document.getElementById('chat-input');
  if (!btn || !input) return;
  const e = EMOTIONS[currentEmotion];
  const active = input.value.trim() && !chatLoading;
  btn.style.background = active ? e.color : 'rgba(255,255,255,.06)';
  btn.style.color = active ? '#0a0a0f' : '#3a4055';
  btn.style.cursor = active ? 'pointer' : 'not-allowed';
  btn.style.boxShadow = active ? `0 4px 16px -4px ${e.color}88` : 'none';
}

function renderMessages() {
  const el = document.getElementById('chat-messages');
  if (!el) return;
  el.innerHTML = '';
  messages.forEach(msg => {
    const e = EMOTIONS[currentEmotion];
    const row = document.createElement('div');
    row.style.cssText = `display:flex;gap:9px;flex-direction:${msg.role==='user'?'row-reverse':'row'}`;
    if (msg.role === 'assistant') {
      const av = document.createElement('div');
      av.style.cssText = `width:26px;height:26px;border-radius:7px;background:${e.color}18;border:1px solid ${e.color}30;display:flex;align-items:center;justify-content:center;font-size:11px;color:${e.color};flex-shrink:0`;
      av.textContent = e.icon;
      row.appendChild(av);
    }
    const bubble = document.createElement('div');
    bubble.className = 'chat-bubble' + (msg.role==='user'?' user':'');
    bubble.textContent = msg.content;
    row.appendChild(bubble);
    el.appendChild(row);
  });
  el.scrollTop = el.scrollHeight;
}
async function sendMessage() {
    const input = document.getElementById('chat-input');
    const msg = input.value.trim();
    if (!msg || chatLoading) return;
    
    // Add user message to UI
    appendMessage('user', msg);
    input.value = '';
    input.style.height = 'auto';
    chatLoading = true;
    updateSendBtn();
    
    // Show typing indicator
    const typingId = 'typing-' + Date.now();
    addTypingIndicator(typingId);
    
    // Prepare context from active materials
    const context = materials.map(m => m.content).join('\\n\\n');
    
    try {
        const res = await fetch('/chat', {
            method: 'POST',
            headers: {'Content-Type': 'application/json', 'X-CSRFToken': getCsrfToken()},
            body: JSON.stringify({
                message: msg,
                socratic_mode: socraticMode, persona: document.getElementById('persona-select')?.value || 'Socratic',
                context: context,
                history: chatHistory.slice(-6),
                coach_mode: document.getElementById('socratic-toggle').checked
            })
        });
        const data = await res.json();
        
        removeTypingIndicator(typingId);
        if (data.response) {
            appendMessage('assistant', data.response);
            chatHistory.push({role: 'user', content: msg});
            chatHistory.push({role: 'assistant', content: data.response});
        }
    } catch (err) {
        removeTypingIndicator(typingId);
        appendMessage('assistant', "Sorry, I lost my connection. Check your internet!");
    } finally {
        chatLoading = false;
        updateSendBtn();
    }
}

function appendMessage(role, text, id = null) {
    const container = document.getElementById('chat-messages');
    if (!container) return;
    const msgDiv = document.createElement('div');
    msgDiv.className = "chat-msg";
    if (id) msgDiv.id = id;
    
    // Robust Markdown parsing with marked.js
    const formatted = typeof marked !== "undefined" ? marked.parse(text) : text.replace(/\n/g, '<br>');
    msgDiv.innerHTML = `<div class="msg-bubble">${formatted}</div>`;
    container.appendChild(msgDiv);
    container.scrollTop = container.scrollHeight;
}

function addTypingIndicator(id) {
    const container = document.getElementById('chat-messages');
    if (!container) return;
    const typingDiv = document.createElement('div');
    typingDiv.className = 'chat-msg assistant typing';
    typingDiv.id = id;
    typingDiv.innerHTML = '<div class="msg-bubble"><div class="typing-dots"><span></span><span></span><span></span></div></div>';
    container.appendChild(typingDiv);
    container.scrollTop = container.scrollHeight;
}

function removeTypingIndicator(id) {
    const el = document.getElementById(id);
    if (el) el.remove();
}

function showSessionSummary() {
  const overlay = document.getElementById('summary-overlay');
  if (!overlay) return;
  const timeDisp = document.getElementById('summary-time');
  const moodDisp = document.getElementById('summary-mood');
  const e = EMOTIONS[currentEmotion];
  
  const m = Math.floor(sessionSeconds/60);
  const s = sessionSeconds%60;
  if (timeDisp) timeDisp.textContent = `${m}:${String(s).padStart(2,'0')}`;
  if (moodDisp) {
    moodDisp.innerHTML = `<div style="font-size:32px;margin-bottom:8px">${e.icon}</div><div style="font-size:16px;font-weight:800;color:${e.color}">${e.label}</div>`;
  }
  overlay.style.display = 'flex';
}

function closeSummary() {
  document.getElementById('summary-overlay').style.display = 'none';
  resetTimer();
}

function toggleTimer() {
  sessionRunning = !sessionRunning;
  const btn = document.getElementById('timer-btn');
  const disp = document.getElementById('timer-display');
  if (!btn || !disp) return;
  if (sessionRunning) {
    timerInterval = setInterval(() => {
      sessionSeconds++;
      const m = String(Math.floor(sessionSeconds/60)).padStart(2,'0');
      const s = String(sessionSeconds%60).padStart(2,'0');
      disp.textContent=`${m}:${s}`; 
      disp.style.color='#a8ff3e';
    }, 1000);
    btn.innerHTML = '⏸ Pause';
  } else {
    clearInterval(timerInterval);
    btn.innerHTML = '▶ Start';
    disp.style.color='#2a3045';
    if (sessionSeconds > 5) showSessionSummary();
  }
}

function resetTimer() {
  clearInterval(timerInterval);
  sessionRunning = false;
  sessionSeconds = 0;
  const btn = document.getElementById('timer-btn');
  const disp = document.getElementById('timer-display');
  if (btn) btn.innerHTML = '▶ Start';
  if (disp) { disp.textContent='00:00'; disp.style.color='#2a3045'; }
}

async function updateProfile() {
    const username = document.getElementById('profile-username')?.value;
    const goal = document.getElementById('profile-goal')?.value;
    const btn = document.getElementById('profile-save-btn');
    const csrfToken = document.querySelector('meta[name="csrf-token"]')?.getAttribute('content');
    
    if (btn) btn.innerHTML = 'Saving...';
    try {
        const resp = await fetch('/update-settings', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrfToken },
            body: JSON.stringify({ username, goal })
        });
        const data = await resp.json();
        if (data.success) {
            if (btn) btn.innerHTML = '✓ Saved';
            setTimeout(() => { if (btn) btn.innerHTML = 'Save Changes'; }, 2000);
        }
    } catch (e) { console.error(e); if (btn) btn.innerHTML = 'Error'; }
}

function toggleSocratic() {
  socraticMode = document.getElementById('socratic-toggle').checked;
  const meta = document.getElementById('chat-meta');
  if (meta) {
    const e = EMOTIONS[currentEmotion];
    meta.innerHTML = `· ${currentSubject} · ${e.label} ${socraticMode ? '<span style="color:#a8ff3e;margin-left:5px">· Socratic</span>' : ''}`;
  }
}

async function handleFileUpload(event) {
  const file = event.target.files[0];
  if (!file) return;
  
  const formData = new FormData();
  formData.append('file', file);
  const csrfToken = document.querySelector('meta[name="csrf-token"]')?.getAttribute('content');
  
  const grid = document.getElementById('library-container');
  if (!grid) return;
  const original = grid.innerHTML;
  grid.innerHTML = '<div style="padding:40px;text-align:center;color:#a8ff3e">Processing file...</div>';

  try {
    const resp = await fetch('/upload-material', {
      method: 'POST',
      headers: { 'X-CSRFToken': csrfToken },
      body: formData
    });
    const data = await resp.json();
    if (data.success) {
      materials.push(data.material);
      updateMaterialsUI();
      showDashTab('materials');
    } else {
      alert(data.error || 'Upload failed');
    }
  } catch (e) { console.error(e); }
  finally { grid.innerHTML = original; }
}

function renderHeatmap() {
    const grid = document.getElementById('heatmap-grid');
    if (!grid) return;
    grid.innerHTML = '';
    for (let i = 0; i < 35; i++) {
        const opacity = Math.random() > 0.7 ? (0.2 + (Math.random() * 0.7)) : 0.05;
        const cell = document.createElement('div');
        cell.style.background = `rgba(168, 255, 62, ${opacity})`;
        cell.style.borderRadius = '3px';
        cell.style.transition = 'all 0.3s';
        if (opacity > 0.1) cell.style.boxShadow = `0 0 8px rgba(168, 255, 62, ${opacity * 0.3})`;
        grid.appendChild(cell);
    }
}

function initLandingOrbs() {
  const container = document.getElementById('orbs-container');
  if (!container) return;
  container.innerHTML = '';
  const entries = Object.entries(EMOTIONS);
  entries.forEach(([key, e], i) => {
    const angle = (i / entries.length) * Math.PI * 2;
    const x = Math.cos(angle) * 280;
    const y = Math.sin(angle) * 155;
    const div = document.createElement('div');
    div.className = 'orb';
    div.id = 'orb-' + i;
    div.style.cssText = `left:calc(50% + ${x}px);top:calc(50% + ${y}px);width:42px;height:42px;background:rgba(255,255,255,.03);border:1px solid rgba(255,255,255,.06);color:#3a4055;font-size:15px;animation:float ${4+i*0.7}s ease-in-out infinite;animation-delay:${i*0.4}s`;
    div.textContent = e.icon;
    container.appendChild(div);
  });
  clearInterval(orbInterval);
  orbInterval = setInterval(() => {
    const prev = document.getElementById('orb-' + activeOrb);
    if (prev) { prev.style.width='42px'; prev.style.height='42px'; prev.style.background='rgba(255,255,255,.03)'; prev.style.border='1px solid rgba(255,255,255,.06)'; prev.style.color='#3a4055'; prev.style.fontSize='15px'; prev.style.boxShadow='none'; }
    activeOrb = (activeOrb + 1) % entries.length;
    const curr = document.getElementById('orb-' + activeOrb);
    const e = entries[activeOrb][1];
    if (curr) { curr.style.width='56px'; curr.style.height='56px'; curr.style.background=`radial-gradient(circle, ${e.color}33, ${e.color}0a)`; curr.style.border=`1px solid ${e.color}88`; curr.style.color=e.color; curr.style.fontSize='20px'; curr.style.boxShadow=`0 0 30px -5px ${e.color}55`; }
  }, 2200);
}

window.addEventListener('load', () => {
  if (document.getElementById('orbs-container')) initLandingOrbs();
  updateMaterialsUI();
  if (document.getElementById('heatmap-grid')) renderHeatmap();
});


async function generateQuizFromMaterials() {
    if (materials.length === 0) {
        alert("Please add some study materials first!");
        return;
    }
    
    const btn = document.getElementById('gen-quiz-btn');
    const placeholder = document.getElementById('quiz-placeholder');
    const content = document.getElementById('quiz-content');
    
    btn.disabled = true;
    btn.textContent = "Generating...";
    placeholder.innerHTML = '<div style="color:#a8ff3e">AI is reading your materials...</div>';
    
    const allContent = materials.map(m => m.content).join('\\n\\n');
    
    try {
        const resp = await fetch('/generate-questions', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCsrfToken() },
            body: JSON.stringify({ content: allContent })
        });
        const data = await resp.json();
        
        if (data.error) throw new Error(data.error);
        
        placeholder.style.display = 'none';
        content.style.display = 'block';
        renderQuiz(data);
        
    } catch (e) {
        placeholder.innerHTML = '<div style="color:#ef4444">Error generating quiz. Try again.</div>';
        console.error(e);
    } finally {
        btn.disabled = false;
        btn.textContent = "Regenerate";
    }
}

function renderQuiz(data) {
    const container = document.getElementById('quiz-content');
    let html = '<div style="display:flex; flex-direction:column; gap:15px;">';
    
    if (data.mcqs) {
        data.mcqs.forEach((q, i) => {
            html += `
                <div class="quiz-q" style="background:rgba(255,255,255,0.02); padding:12px; border-radius:8px;">
                    <div style="font-size:12px; font-weight:600; color:#c0cce0; margin-bottom:8px;">Q${i+1}: ${q.question}</div>
                    <div style="display:grid; grid-template-columns:1fr 1fr; gap:6px;">
                        ${q.options.map(opt => `<button class="btn-sm quiz-opt" style="font-size:10px; text-align:left; background:rgba(255,255,255,0.05);" onclick="checkAnswer(this, '${q.answer}', '${opt}')">${opt}</button>`).join('')}
                    </div>
                </div>
            `;
        });
    }
    
    html += '</div>';
    container.innerHTML = html;
}

function checkAnswer(btn, correct, selected) {
    const parent = btn.parentElement;
    const btns = parent.querySelectorAll('button');
    btns.forEach(b => b.disabled = true);
    
    if (selected === correct) {
        btn.style.background = 'rgba(168, 255, 62, 0.2)';
        btn.style.borderColor = '#a8ff3e';
        btn.innerHTML += ' ✓';
    } else {
        btn.style.background = 'rgba(239, 68, 68, 0.2)';
        btn.style.borderColor = '#ef4444';
        btn.innerHTML += ' ✗';
        btns.forEach(b => {
            if (b.textContent === correct) b.style.background = 'rgba(168, 255, 62, 0.1)';
        });
    }
}

// Global Exports
window.generateQuizFromMaterials = generateQuizFromMaterials;
window.renderQuiz = renderQuiz;
window.checkAnswer = checkAnswer;

// Global Exports
window.updateProfile = updateProfile;
window.closeSummary = closeSummary;
window.toggleSocratic = toggleSocratic;
window.handleFileUpload = handleFileUpload;
window.renderHeatmap = renderHeatmap;
window.sendMessage = sendMessage;
window.toggleTimer = toggleTimer;
window.resetTimer = resetTimer;
window.updateSendBtn = updateSendBtn;
window.updateMaterialsUI = updateMaterialsUI;
window.toggleLibMat = toggleLibMat;
window.removeMaterial = removeMaterial;
window.addPastedNote = addPastedNote;
window.loadNote = loadNote;
window.updateMood = updateMood;
window.initLandingOrbs = initLandingOrbs;





// ─── Library Logic ──────────────────────────────────────────────────────────
let currentPage = 1;
let currentSearchQuery = "";

async function loadLibrary(page = 1, query = "") {
    if (page < 1) page = 1;
    currentPage = page;
    currentSearchQuery = query;
    
    const container = document.getElementById("library-container");
    if (!container) return;
    
    container.innerHTML = '<div style="padding:20px; text-align:center; color:#a8ff3e">Loading library...</div>';
    
    try {
        let url = `/api/materials?page=${page}&limit=50`;
        if (query) {
            url = `/api/materials/search?q=${encodeURIComponent(query)}`;
        }
        
        const res = await fetch(url);
        const rawData = await res.json();
        // API returns {success, materials} or {success, results}
        const materialsData = rawData.materials || rawData.results || (Array.isArray(rawData) ? rawData : []);
        
        container.innerHTML = "";
        
        if (!materialsData || materialsData.length === 0) {
            container.innerHTML = '<div style="padding:20px; text-align:center; color:#4a5270">No materials found.</div>';
            return;
        }

        materialsData.forEach(m => {
            const item = document.createElement("div");
            item.className = "library-item";
            // Styled via CSS class .library-item
            item.innerHTML = `
                <div class="lib-item-row">
                    <div class="lib-item-info">
                        <div class="lib-item-title">${m.title}</div>
                        <div class="lib-item-meta">${m.language || ''} · ${m.subject || ''}</div>
                    </div>
                    <button class="btn-link-mat">
                        <span>+</span> Link
                    </button>
                </div>
            `;
            // Click handlers via JS for safety
            const linkBtn = item.querySelector('.btn-link-mat');
            linkBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                linkMaterial(m.id, m.title, m.content, e);
            });

            item.addEventListener('click', () => {
                const editor = document.getElementById("note-editor");
                if (editor) {
                    editor.value = m.content;
                    editor.style.height = 'auto';
                    editor.style.height = Math.min(editor.scrollHeight, 150) + 'px';
                }
            };

            container.appendChild(item);
        });
    } catch (e) {
        console.error("Library fetch error:", e);
        container.innerHTML = '<div style="padding:20px; text-align:center; color:#ef4444">Failed to load library.</div>';
    }
}

function nextPage() {
    currentPage++;
    loadLibrary(currentPage, currentSearchQuery);
}

function prevPage() {
    if (currentPage > 1) {
        currentPage--;
        loadLibrary(currentPage, currentSearchQuery);
    }
}

// Auto-load library
document.addEventListener("DOMContentLoaded", () => {
    loadLibrary(1);
});


function showDashTab(tabId) {
    console.log("Switching to tab:", tabId);
    // Hide all tabs
    document.querySelectorAll('[id^="tab-"]').forEach(t => {
        t.style.display = 'none';
    });
    
    // Show target tab
    const target = document.getElementById(`tab-${tabId}`);
    if (target) {
        target.style.display = 'block';
        if (tabId === 'materials') {
            loadLibrary(1);
        }
    }
    
    // Update sidebar active state
    document.querySelectorAll('.sidebar-item').forEach(b => {
        b.classList.remove('active');
    });
    const sbItem = document.getElementById(`sb-${tabId}`);
    if (sbItem) sbItem.classList.add('active');
}

window.showDashTab = showDashTab;

function linkMaterial(id, title, content, event) {
    const matId = `lib-${id}`;
    if (materials.some(m => m.id === matId)) {
        alert("This material is already in your session.");
        return;
    }
    const newMat = { id: matId, title, source: 'library', content };
    materials.push(newMat);
    syncMaterial(newMat);
    updateMaterialsUI();
    
    // Visual feedback
    const target = event ? event.target : (window.event ? window.event.target : null);
    if (target) {
        target.textContent = "Linked ✓";
        target.style.background = "rgba(168,255,62,0.3)";
        setTimeout(() => {
            target.textContent = "Link +";
            target.style.background = "rgba(168,255,62,0.1)";
        }, 2000);
    }
}
window.linkMaterial = linkMaterial;
// Final Exports
window.nextPage = nextPage;
window.prevPage = prevPage;
window.loadLibrary = loadLibrary;

// --- Theme Switcher ---
function initTheme() {
    const saved = localStorage.getItem('theme') || 'dark';
    document.documentElement.setAttribute('data-theme', saved);
    updateThemeIcon(saved);
}

function toggleTheme() {
    const current = document.documentElement.getAttribute('data-theme');
    const target = current === 'dark' ? 'light' : 'dark';
    document.documentElement.setAttribute('data-theme', target);
    localStorage.setItem('theme', target);
    updateThemeIcon(target);
}

function updateThemeIcon(theme) {
    const btn = document.getElementById('theme-toggle-btn');
    if (btn) btn.innerHTML = theme === 'dark' ? '<span>🌙</span> Dark' : '<span>☀️</span> Light';
}

window.toggleTheme = toggleTheme;
document.addEventListener('DOMContentLoaded', initTheme);

async function generateFlashcards() {
    const btn = document.getElementById('gen-flashcards-btn');
    const display = document.getElementById('flashcards-display');
    const placeholder = document.getElementById('flashcards-placeholder');
    
    if (materials.length === 0) {
        alert("Please link some materials first to generate flashcards.");
        return;
    }
    
    const context = materials.map(m => m.content).join("\n\n");
    btn.disabled = true;
    btn.textContent = "Generating...";
    
    try {
        const resp = await fetch('/generate-flashcards', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCsrfToken() },
            body: JSON.stringify({ content: context })
        });
        const data = await resp.json();
        if (data.success && data.flashcards) {
            flashcardsList = data.flashcards;
            flashcardIndex = 0;
            updateFlashcardUI();
            display.style.display = 'flex';
            placeholder.style.display = 'none';
        } else {
            alert(data.error || "Failed to generate flashcards.");
        }
    } catch (e) {
        console.error(e);
        alert("Error connecting to AI service.");
    } finally {
        btn.disabled = false;
        btn.textContent = "Generate from Context";
    }
}

function updateFlashcardUI() {
    if (flashcardsList.length === 0) return;
    const card = flashcardsList[flashcardIndex];
    document.getElementById('flash-front').textContent = card.front;
    document.getElementById('flash-back').textContent = card.back;
    document.getElementById('flashcard-counter').textContent = `${flashcardIndex + 1} / ${flashcardsList.length}`;
    document.getElementById('active-flashcard').classList.remove('flipped');
}

function nextFlashcard() {
    if (flashcardsList.length === 0) return;
    flashcardIndex = (flashcardIndex + 1) % flashcardsList.length;
    updateFlashcardUI();
}

function prevFlashcard() {
    if (flashcardsList.length === 0) return;
    flashcardIndex = (flashcardIndex - 1 + flashcardsList.length) % flashcardsList.length;
    updateFlashcardUI();
}

window.generateFlashcards = generateFlashcards;
window.nextFlashcard = nextFlashcard;
window.prevFlashcard = prevFlashcard;
