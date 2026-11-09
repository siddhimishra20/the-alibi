// THE ALIBI - Frontend Client
let currentSession = null;
let currentCase = null;
let transcriptHistory = [];
let soundEnabled = true;

// Web Audio API Synthesizer
let audioCtx = null;
function getAudioContext() {
    if (!audioCtx) {
        audioCtx = new (window.AudioContext || window.webkitAudioContext)();
    }
    return audioCtx;
}

function playSound(type) {
    if (!soundEnabled) return;
    try {
        const ctx = getAudioContext();
        if (ctx.state === 'suspended') {
            ctx.resume();
        }
        const now = ctx.currentTime;

        if (type === 'key') {
            const osc = ctx.createOscillator();
            const gain = ctx.createGain();
            osc.type = 'triangle';
            osc.frequency.setValueAtTime(600 + Math.random() * 200, now);
            gain.gain.setValueAtTime(0.04, now);
            gain.gain.exponentialRampToValueAtTime(0.001, now + 0.05);
            osc.connect(gain);
            gain.connect(ctx.destination);
            osc.start(now);
            osc.stop(now + 0.05);
        } else if (type === 'accuse') {
            // Dramatic heavy thud
            const osc = ctx.createOscillator();
            const gain = ctx.createGain();
            osc.type = 'sawtooth';
            osc.frequency.setValueAtTime(140, now);
            osc.frequency.exponentialRampToValueAtTime(35, now + 0.35);
            gain.gain.setValueAtTime(0.3, now);
            gain.gain.exponentialRampToValueAtTime(0.001, now + 0.35);
            osc.connect(gain);
            gain.connect(ctx.destination);
            osc.start(now);
            osc.stop(now + 0.35);
        } else if (type === 'win') {
            // Victorious ascending chord
            [330, 440, 554.37, 659.25].forEach((freq, idx) => {
                const osc = ctx.createOscillator();
                const gain = ctx.createGain();
                osc.type = 'sine';
                osc.frequency.setValueAtTime(freq, now + idx * 0.1);
                gain.gain.setValueAtTime(0.15, now + idx * 0.1);
                gain.gain.exponentialRampToValueAtTime(0.001, now + idx * 0.1 + 0.4);
                osc.connect(gain);
                gain.connect(ctx.destination);
                osc.start(now + idx * 0.1);
                osc.stop(now + idx * 0.1 + 0.4);
            });
        } else if (type === 'lose') {
            // Low buzzer
            const osc = ctx.createOscillator();
            const gain = ctx.createGain();
            osc.type = 'sawtooth';
            osc.frequency.setValueAtTime(95, now);
            osc.frequency.setValueAtTime(80, now + 0.2);
            gain.gain.setValueAtTime(0.2, now);
            gain.gain.exponentialRampToValueAtTime(0.001, now + 0.5);
            osc.connect(gain);
            gain.connect(ctx.destination);
            osc.start(now);
            osc.stop(now + 0.5);
        }
    } catch (e) {
        console.warn("AudioContext error:", e);
    }
}

// Retro 4-Dot Square Loading Animation
const SQUARE_DOT_FRAMES = ["┌ ● · ┐", "┌ · ● ┐", "└ · ● ┘", "└ ● · ┘"];
let spinnerInterval = null;

function startSpinner(text = "SUSPECT IS THINKING...") {
    const el = document.getElementById("loading-spinner");
    const icon = document.getElementById("spinner-art");
    const label = document.getElementById("spinner-text");
    el.classList.remove("hidden");
    label.innerText = text;
    let idx = 0;
    spinnerInterval = setInterval(() => {
        icon.innerText = SQUARE_DOT_FRAMES[idx % SQUARE_DOT_FRAMES.length];
        idx++;
    }, 250);
}

function stopSpinner() {
    if (spinnerInterval) {
        clearInterval(spinnerInterval);
        spinnerInterval = null;
    }
    document.getElementById("loading-spinner").classList.add("hidden");
}

// Live Countdown Timer
function startCountdown() {
    function update() {
        const now = new Date();
        const tomorrow = new Date(now.getFullYear(), now.getMonth(), now.getDate() + 1);
        const diff = Math.max(0, tomorrow - now);
        const hours = String(Math.floor((diff / (1000 * 60 * 60)) % 24)).padStart(2, "0");
        const minutes = String(Math.floor((diff / (1000 * 60)) % 60)).padStart(2, "0");
        const seconds = String(Math.floor((diff / 1000) % 60)).padStart(2, "0");
        document.getElementById("countdown-badge").innerText = `NEXT CASE: ${hours}:${minutes}:${seconds}`;
    }
    update();
    setInterval(update, 1000);
}

// Fetch Global Status
async function loadStatus() {
    try {
        const res = await fetch("/api/status");
        if (res.ok) {
            const data = await res.json();
            document.getElementById("streak-badge").innerText = `STREAK: ${data.current_streak} ★`;
        }
    } catch (e) {
        console.warn("Failed to fetch status:", e);
    }
}

// Start Game Session
async function startSession(date = null, practice = false) {
    const diff = document.getElementById("select-difficulty").value;
    startSpinner("INITIALIZING CRIME DOSSIER...");

    try {
        const res = await fetch("/api/session/start", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ date: date, practice: practice, difficulty: diff })
        });
        const data = await res.json();
        stopSpinner();

        currentSession = data;
        currentCase = data.case;
        transcriptHistory = [];

        renderCase(currentCase);
        renderTokens(data.remaining_tokens, data.max_tokens);
        clearTranscript();

        // Enable inputs
        document.getElementById("question-input").disabled = false;
        document.getElementById("btn-submit-question").disabled = false;
        document.getElementById("btn-open-accuse").disabled = false;
        document.getElementById("btn-use-hint").disabled = (diff === "hardboiled");
        document.getElementById("interrogation-status").innerText = "ACTIVE TRIAL";
        document.getElementById("question-input").focus();

        appendTranscript("system", `[DISPATCH] Investigation opened for case '${currentCase.title}'. You have ${data.remaining_tokens} tokens. Question the suspect or type 'A' to accuse.`);
    } catch (e) {
        stopSpinner();
        alert("Failed to start game session: " + e.message);
    }
}

// Render Case UI
function renderCase(c) {
    document.getElementById("case-title").innerText = c.title;
    document.getElementById("case-date-badge").innerText = c.date;
    document.getElementById("crime-description").innerText = c.crime_description;
    document.getElementById("crime-setting").innerText = c.setting;

    // Suspect
    document.getElementById("suspect-name").innerText = c.suspect.name;
    document.getElementById("suspect-occupation").innerText = c.suspect.occupation;
    document.getElementById("suspect-quirk").innerText = `"${c.suspect.quirk}"`;
    if (c.suspect.ascii_face) {
        document.getElementById("suspect-face").innerText = c.suspect.ascii_face;
    }

    // Dossier Facts
    const container = document.getElementById("dossier-facts-list");
    container.innerHTML = "";
    const factSelect = document.getElementById("accuse-fact-select");
    factSelect.innerHTML = '<option value="">-- Choose conflicting dossier fact --</option>';

    c.dossier.forEach((fact, idx) => {
        const div = document.createElement("div");
        div.className = "fact-card";
        div.innerHTML = `<span class="fact-id">[FACT ${idx + 1}] (${fact.id})</span>${fact.text}`;
        container.appendChild(div);

        const opt = document.createElement("option");
        opt.value = fact.text;
        opt.innerText = `[FACT ${idx + 1}] ${fact.text.substring(0, 50)}...`;
        factSelect.appendChild(opt);
    });
}

// Render Tokens HUD
function renderTokens(remaining, max) {
    const filled = "● ".repeat(remaining);
    const empty = "○ ".repeat(Math.max(0, max - remaining));
    document.getElementById("tokens-display").innerText = (filled + empty).trim();
    document.getElementById("tokens-count-text").innerText = `(${remaining} / ${max} REMAINING)`;
}

function clearTranscript() {
    const feed = document.getElementById("chat-stream");
    feed.innerHTML = "";
}

function appendTranscript(role, text, emotion = null) {
    const feed = document.getElementById("chat-stream");
    const bubble = document.createElement("div");
    bubble.className = `chat-bubble ${role}`;

    if (role === "detective") {
        bubble.innerHTML = `<span class="speaker-tag" style="color: #00ffcc;">YOU (DETECTIVE):</span>"${text}"`;
    } else if (role === "suspect") {
        const emoBadge = emotion ? `<span class="emotion-tag" style="border-color: #ff8800; color: #ffaa33;">${emotion.toUpperCase()}</span>` : "";
        bubble.innerHTML = `<span class="speaker-tag" style="color: #ff8800; font-weight: 700;">${currentCase.suspect.name}: ${emoBadge}</span>"${text}"`;
        // Allow clicking on suspect quote to directly populate accuse modal
        bubble.title = "Click to select this statement for accusation";
        bubble.addEventListener("click", () => {
            openAccuseModal(text);
        });
    } else {
        bubble.innerText = text;
    }

    feed.appendChild(bubble);
    feed.scrollTop = feed.scrollHeight;
}

// Send Question
async function submitQuestion(question) {
    if (!currentSession || !question.trim()) return;

    appendTranscript("detective", question);
    document.getElementById("question-input").value = "";
    document.getElementById("question-input").disabled = true;
    document.getElementById("btn-submit-question").disabled = true;

    playSound("key");
    startSpinner("SUSPECT IS THINKING & WEAVING LIES...");

    try {
        const res = await fetch("/api/session/interrogate", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ session_id: currentSession.session_id, question: question })
        });
        const data = await res.json();
        stopSpinner();

        if (data.success) {
            appendTranscript("suspect", data.answer, data.emotion);
            transcriptHistory.push(data.answer);
            renderTokens(data.remaining_tokens, data.max_tokens);

            if (data.game_over) {
                endGame(false, "You ran out of question tokens without uncovering the contradiction!");
            } else {
                document.getElementById("question-input").disabled = false;
                document.getElementById("btn-submit-question").disabled = false;
                document.getElementById("question-input").focus();
            }
        } else {
            appendTranscript("system", `[ERROR] ${data.error}`);
            document.getElementById("question-input").disabled = false;
            document.getElementById("btn-submit-question").disabled = false;
        }
    } catch (e) {
        stopSpinner();
        appendTranscript("system", `[NETWORK ERROR] Could not reach server: ${e.message}`);
        document.getElementById("question-input").disabled = false;
        document.getElementById("btn-submit-question").disabled = false;
    }
}

// Hint Request
async function useHint() {
    if (!currentSession) return;
    startSpinner("CALLING NOIR NARRATOR...");
    try {
        const res = await fetch("/api/session/hint", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ session_id: currentSession.session_id })
        });
        const data = await res.json();
        stopSpinner();
        if (data.success) {
            appendTranscript("system", `[NOIR NARRATOR HINT]: "${data.hint}"`);
            renderTokens(data.remaining_tokens, currentSession.max_tokens);
            document.getElementById("btn-use-hint").disabled = true;
        } else {
            alert(data.hint);
        }
    } catch (e) {
        stopSpinner();
        alert("Failed to get hint: " + e.message);
    }
}

// Accusation Flow
function openAccuseModal(preselectedQuote = null) {
    if (!currentSession) return;
    const select = document.getElementById("accuse-quote-select");
    select.innerHTML = '<option value="">-- Choose statement from transcript --</option>';

    transcriptHistory.forEach((q, idx) => {
        const opt = document.createElement("option");
        opt.value = q;
        opt.innerText = `Turn #${idx + 1}: "${q.substring(0, 60)}..."`;
        if (preselectedQuote && q === preselectedQuote) {
            opt.selected = true;
        }
        select.appendChild(opt);
    });

    document.getElementById("accuse-modal").classList.remove("hidden");
}

async function submitAccusation() {
    const quote = document.getElementById("accuse-quote-select").value;
    const fact = document.getElementById("accuse-fact-select").value;

    if (!quote || !fact) {
        alert("You must select both a suspect quote and the conflicting dossier fact!");
        return;
    }

    document.getElementById("accuse-modal").classList.add("hidden");
    playSound("accuse");
    startSpinner("JUDGE IS EVALUATING CONTRADICTION...");

    try {
        const res = await fetch("/api/session/accuse", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                session_id: currentSession.session_id,
                quote: quote,
                target_text: fact,
                is_dossier_fact: true
            })
        });
        const data = await res.json();
        stopSpinner();

        renderTokens(data.remaining_tokens, currentSession.max_tokens);

        if (data.valid) {
            playSound("win");
            endGame(true, data.explanation, data.breakdown_confession, data.share_grid);
        } else {
            playSound("lose");
            appendTranscript("system", `[ACCUSATION REJECTED]: ${data.explanation} (Penalty incurred!)`);
            if (data.game_over) {
                endGame(false, "You lost your last token on a flawed accusation. The suspect walks free!");
            }
        }
    } catch (e) {
        stopSpinner();
        alert("Accusation error: " + e.message);
    }
}

function endGame(won, explanation, confession = "", shareGrid = "") {
    document.getElementById("question-input").disabled = true;
    document.getElementById("btn-submit-question").disabled = true;
    document.getElementById("btn-open-accuse").disabled = true;
    document.getElementById("interrogation-status").innerText = won ? "CASE SOLVED" : "SUSPECT DISMISSED";

    const title = document.getElementById("result-title");
    title.innerText = won ? "⚖ GUILTY AS CHARGED! ⚖" : "✖ CASE COLD ✖";
    title.style.color = won ? "var(--accent-green)" : "var(--accent-red)";

    const badge = document.getElementById("result-badge");
    badge.innerText = won ? "★ ★ ★   CASE CLOSED: SUSPECT CONVICTED & JAILED!   ★ ★ ★" : "✖ ✖ ✖   CASE COLD: OUT OF EVIDENCE // SUSPECT WALKED FREE   ✖ ✖ ✖";
    badge.style.color = won ? "var(--accent-green)" : "var(--accent-red)";

    document.getElementById("result-explanation").innerText = explanation;

    if (confession) {
        document.getElementById("result-confession-box").classList.remove("hidden");
        document.getElementById("result-confession").innerText = confession;
    } else {
        document.getElementById("result-confession-box").classList.add("hidden");
    }

    document.getElementById("result-share-grid").innerText = shareGrid;
    document.getElementById("result-modal").classList.remove("hidden");

    loadStatus(); // refresh streak
}

// Archive Flow
async function openArchiveModal() {
    startSpinner("LOADING ARCHIVE RECORDS...");
    try {
        const res = await fetch("/api/archive");
        const list = await res.json();
        stopSpinner();

        const tbody = document.getElementById("archive-table-body");
        tbody.innerHTML = "";

        list.forEach(c => {
            const tr = document.createElement("tr");
            let badgeStyle = "color: var(--accent-cyan);";
            if (c.status === "SOLVED") badgeStyle = "color: var(--accent-green); font-weight: 700;";
            if (c.status === "FAILED") badgeStyle = "color: var(--accent-red);";
            if (c.status === "TODAY") badgeStyle = "color: var(--accent-amber); font-weight: 700;";

            tr.innerHTML = `
                <td>${c.date}</td>
                <td style="${badgeStyle}">${c.status}</td>
                <td><strong>${c.title}</strong></td>
                <td>${c.suspect_name}</td>
                <td>${c.setting}</td>
                <td><button class="btn btn-secondary btn-sm" onclick="startSession('${c.date}', false)">PLAY</button></td>
            `;
            tbody.appendChild(tr);
        });

        document.getElementById("archive-modal").classList.remove("hidden");
    } catch (e) {
        stopSpinner();
        alert("Failed to load archive: " + e.message);
    }
}

// DOM Event Listeners
document.addEventListener("DOMContentLoaded", () => {
    startCountdown();
    loadStatus();

    // Buttons
    document.getElementById("btn-today-case").addEventListener("click", () => startSession(null, false));
    document.getElementById("btn-practice-case").addEventListener("click", () => startSession(null, true));
    document.getElementById("btn-open-archive").addEventListener("click", openArchiveModal);
    document.getElementById("btn-close-archive").addEventListener("click", () => {
        document.getElementById("archive-modal").classList.add("hidden");
    });

    document.getElementById("btn-rules").addEventListener("click", () => {
        alert("THE ALIBI RULES:\n\n1. You are given 3 100% verified forensic facts.\n2. You have question tokens to interrogate the suspect.\n3. The suspect has a cover story with hidden weak points that contradict the facts.\n4. Type 'A' or click ACCUSE to highlight the lie and match it with the broken fact!");
    });

    document.getElementById("btn-use-hint").addEventListener("click", useHint);
    document.getElementById("btn-open-accuse").addEventListener("click", () => openAccuseModal());
    document.getElementById("btn-close-accuse").addEventListener("click", () => {
        document.getElementById("accuse-modal").classList.add("hidden");
    });
    document.getElementById("btn-cancel-accuse").addEventListener("click", () => {
        document.getElementById("accuse-modal").classList.add("hidden");
    });
    document.getElementById("btn-submit-accuse").addEventListener("click", submitAccusation);

    document.getElementById("btn-close-result").addEventListener("click", () => {
        document.getElementById("result-modal").classList.add("hidden");
    });
    document.getElementById("btn-result-new-game").addEventListener("click", () => {
        document.getElementById("result-modal").classList.add("hidden");
        startSession(null, true);
    });

    document.getElementById("btn-copy-share").addEventListener("click", () => {
        const grid = document.getElementById("result-share-grid").innerText;
        navigator.clipboard.writeText(grid).then(() => {
            alert("Share grid copied to clipboard!");
        });
    });

    document.getElementById("btn-sound-toggle").addEventListener("click", (e) => {
        soundEnabled = !soundEnabled;
        e.target.innerText = soundEnabled ? "🔊" : "🔇";
    });

    // Form
    document.getElementById("question-form").addEventListener("submit", (e) => {
        e.preventDefault();
        const input = document.getElementById("question-input");
        const val = input.value.trim();
        if (val.toLowerCase() === "a" || val.toLowerCase() === "/accuse") {
            openAccuseModal();
            input.value = "";
        } else if (val.toLowerCase() === "h" || val.toLowerCase() === "/hint") {
            useHint();
            input.value = "";
        } else if (val) {
            submitQuestion(val);
        }
    });

    // Keyboard Shortcuts
    document.addEventListener("keydown", (e) => {
        if (e.key === "Escape") {
            document.getElementById("accuse-modal").classList.add("hidden");
            document.getElementById("result-modal").classList.add("hidden");
            document.getElementById("archive-modal").classList.add("hidden");
        }
    });

    // Auto-load today's case briefing on startup
    fetch("/api/case/today").then(r => r.json()).then(c => renderCase(c)).catch(() => {});

    // Engine Config Modal Handling
    const engineModal = document.getElementById("engine-modal");
    const btnEngineConfig = document.getElementById("btn-engine-config");
    const btnCloseEngineModal = document.getElementById("btn-close-engine-modal");
    const btnSaveEngine = document.getElementById("btn-save-engine");
    const inputGroqKey = document.getElementById("input-groq-key");
    const alertBox = document.getElementById("engine-status-alert");

    function openEngineModal() {
        if (engineModal) {
            alertBox.classList.add("hidden");
            engineModal.classList.remove("hidden");
        }
    }

    function closeEngineModal() {
        if (engineModal) engineModal.classList.add("hidden");
    }

    if (btnEngineConfig) btnEngineConfig.addEventListener("click", openEngineModal);
    if (btnCloseEngineModal) btnCloseEngineModal.addEventListener("click", closeEngineModal);

    if (btnSaveEngine) {
        btnSaveEngine.addEventListener("click", async () => {
            const isGroq = document.getElementById("radio-groq")?.checked;
            const provider = isGroq ? "groq" : "ollama";
            const apiKey = inputGroqKey.value.trim();

            btnSaveEngine.innerText = "CONNECTING...";
            btnSaveEngine.disabled = true;

            try {
                const resp = await fetch("/api/config/llm", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({
                        provider: provider,
                        groq_api_key: apiKey || undefined
                    })
                });
                const data = await resp.json();
                alertBox.classList.remove("hidden");
                if (data.verified) {
                    alertBox.className = "engine-alert success";
                    alertBox.innerText = `CONNECTED: ${data.message}`;
                    playSound("win");
                    loadEngineStatus();
                    setTimeout(closeEngineModal, 1200);
                } else {
                    alertBox.className = "engine-alert error";
                    alertBox.innerText = `ERROR: ${data.message}`;
                    playSound("lose");
                }
            } catch (err) {
                alertBox.classList.remove("hidden");
                alertBox.className = "engine-alert error";
                alertBox.innerText = "Failed to connect to backend engine.";
            } finally {
                btnSaveEngine.innerText = "CONNECT ENGINE";
                btnSaveEngine.disabled = false;
            }
        });
    }

    loadEngineStatus();
});

// Procedural CRT Polygraph Voice-Stress Engine
const EQUALIZER_CHARS = [" ", " ", "▂", "▃", "▄", "▅", "▆", "▇", "█"];
let polygraphFrame = 0;

function updatePolygraphAnimation() {
    const el = document.getElementById("polygraph-display");
    if (!el) return;

    polygraphFrame++;
    const t = polygraphFrame * 0.35;
    
    // Wave 1 (30 chars)
    let wave1 = "";
    for (let col = 0; col < 30; col++) {
        const val = Math.sin(col * 0.28 + t) * Math.cos(col * 0.12 - t * 0.5);
        const norm = (val + 1) / 2;
        const charIdx = Math.min(EQUALIZER_CHARS.length - 1, Math.floor(norm * EQUALIZER_CHARS.length));
        wave1 += EQUALIZER_CHARS[charIdx];
    }

    // Wave 2 (30 chars)
    let wave2 = "";
    for (let col = 0; col < 30; col++) {
        const val = Math.cos(col * 0.22 - t * 0.8) * Math.sin(col * 0.35 + t * 0.4);
        const norm = (val + 1) / 2;
        const charIdx = Math.min(EQUALIZER_CHARS.length - 1, Math.floor(norm * EQUALIZER_CHARS.length));
        wave2 += EQUALIZER_CHARS[charIdx];
    }

    // Dynamic metrics
    const stress = Math.min(99, Math.max(10, Math.floor(35 + 50 * ((Math.sin(t * 0.6) + 1) / 2))));
    const bpm = Math.min(99, Math.max(60, Math.floor(68 + 26 * ((Math.cos(t * 0.4) + 1) / 2))));
    const truth = Math.min(99, Math.max(10, Math.floor(15 + 75 * ((Math.sin(t * 0.5 + 1.2) + 1) / 2))));

    // Rolling cipher digits (24 digits grouped in 4)
    let digits = "";
    for (let i = 0; i < 6; i++) {
        const grp = Math.floor(1000 + Math.random() * 9000);
        digits += (i > 0 ? " " : "") + grp;
    }

    const reg = (0x47E0 + (polygraphFrame % 16)).toString(16).toUpperCase();

    const line0 = `VOICE STRESS : [${wave1}]  STRESS: ${stress}%  BPM: ${bpm}`;
    const line1 = `FREQ RESPONSE: [${wave2}]  TRUTH : ${truth}%  REG: 0x${reg}`;
    const line2 = `CIPHER TRACK : [ ${digits} ]`;

    el.innerText = `${line0}\n${line1}\n${line2}`;
}

setInterval(updatePolygraphAnimation, 120);

async function loadEngineStatus() {
    try {
        const resp = await fetch("/api/config/llm");
        if (resp.ok) {
            const data = await resp.json();
            const badge = document.getElementById("engine-badge-text");
            if (badge) {
                if (data.provider === "groq") {
                    badge.innerText = "⚡ GROQ CLOUD";
                    badge.style.color = "var(--accent-green)";
                } else {
                    badge.innerText = "🖥️ LOCAL OLLAMA";
                    badge.style.color = "var(--accent-cyan)";
                }
            }
            if (data.provider === "groq") {
                const rGroq = document.getElementById("radio-groq");
                if (rGroq) rGroq.checked = true;
            } else {
                const rOllama = document.getElementById("radio-ollama");
                if (rOllama) rOllama.checked = true;
            }
        }
    } catch (e) {
        console.warn("Could not load LLM engine status", e);
    }
}
