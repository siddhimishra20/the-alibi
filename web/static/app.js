// ==========================================================================
// THE ALIBI: RETRO CRT NOIR TERMINAL JAVASCRIPT
// Multi-Screen Architecture • Authentic Sound Effects • Zero Emojis
// ==========================================================================

let currentSession = null;
let currentCase = null;
let currentDifficulty = "classic";
let soundEnabled = true;
let audioContextUnlocked = false;
let audioCache = {};

// --------------------------------------------------------------------------
// 1. AUDIO ENGINE (WAV Asset Loader & Web Audio Unlocking)
// --------------------------------------------------------------------------
const AUDIO_FILES = {
    key: "/audio/key_click.wav",
    token: "/audio/token_spent.wav",
    accuse: "/audio/accuse_stamp.wav",
    nervous: "/audio/suspect_nervous.wav",
    win: "/audio/win.wav",
    lose: "/audio/lose.wav"
};

function unlockAudio() {
    if (audioContextUnlocked) return;
    audioContextUnlocked = true;
    // Preload audio elements
    for (const [key, path] of Object.entries(AUDIO_FILES)) {
        try {
            const a = new Audio(path);
            a.volume = 0.45;
            audioCache[key] = a;
        } catch (e) {
            console.warn("Audio load error for", key, e);
        }
    }
}

function playSound(name) {
    if (!soundEnabled) return;
    unlockAudio();
    try {
        const audio = audioCache[name];
        if (audio) {
            audio.currentTime = 0;
            audio.play().catch(() => {});
        } else if (AUDIO_FILES[name]) {
            const temp = new Audio(AUDIO_FILES[name]);
            temp.volume = 0.45;
            temp.play().catch(() => {});
        }
    } catch (e) {
        console.warn("Audio play error", name, e);
    }
}

// --------------------------------------------------------------------------
// 2. SCREEN NAVIGATION (True Multi-Screen Flow)
// --------------------------------------------------------------------------
function navigateTo(screenId) {
    const screens = document.querySelectorAll(".game-screen");
    screens.forEach(s => s.classList.remove("active-screen"));

    const target = document.getElementById(screenId);
    if (target) {
        target.classList.add("active-screen");
        window.scrollTo(0, 0);
    }
}

// --------------------------------------------------------------------------
// 3. PROCEDURAL CRT VOICE-STRESS POLYGRAPH & AUDIO CIPHER
// --------------------------------------------------------------------------
const EQUALIZER_CHARS = [" ", " ", "▂", "▃", "▄", "▅", "▆", "▇", "█"];
let polygraphFrame = 0;

function updatePolygraphStream() {
    const el = document.getElementById("polygraph-display");
    if (!el) return;

    polygraphFrame++;
    const t = polygraphFrame * 0.35;

    // Sine wave 1 (30 characters)
    let wave1 = "";
    for (let col = 0; col < 30; col++) {
        const val = Math.sin(col * 0.28 + t) * Math.cos(col * 0.12 - t * 0.5);
        const norm = (val + 1) / 2;
        const charIdx = Math.min(EQUALIZER_CHARS.length - 1, Math.floor(norm * EQUALIZER_CHARS.length));
        wave1 += EQUALIZER_CHARS[charIdx];
    }

    // Sine wave 2 (30 characters)
    let wave2 = "";
    for (let col = 0; col < 30; col++) {
        const val = Math.cos(col * 0.22 - t * 0.8) * Math.sin(col * 0.35 + t * 0.4);
        const norm = (val + 1) / 2;
        const charIdx = Math.min(EQUALIZER_CHARS.length - 1, Math.floor(norm * EQUALIZER_CHARS.length));
        wave2 += EQUALIZER_CHARS[charIdx];
    }

    // Live metrics
    const stress = Math.min(99, Math.max(10, Math.floor(35 + 50 * ((Math.sin(t * 0.6) + 1) / 2))));
    const bpm = Math.min(99, Math.max(60, Math.floor(68 + 26 * ((Math.cos(t * 0.4) + 1) / 2))));
    const truth = Math.min(99, Math.max(10, Math.floor(15 + 75 * ((Math.sin(t * 0.5 + 1.2) + 1) / 2))));

    // Rolling 24 random digits in blocks of 4
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

setInterval(updatePolygraphStream, 110);

// --------------------------------------------------------------------------
// 4. SUSPECT ASCII ART EXPRESSIONS
// --------------------------------------------------------------------------
const ASCII_FACES = {
    calm: "   _____  \n  /     \\ \n | () () |\n  \\  ^  / \n   |||||  ",
    smug: "   _____  \n  /     \\ \n | ¬) ¬) |\n  \\  -  / \n   \\___/  ",
    nervous: "   _____  \n  / o o \\ \n |  ---  |\n  \\  ~  / \n   ;;;;;  ",
    rattled: "  \\\\\\\\\\// \n  | X X | \n  |  O  | \n  /  ~  \\ \n  ;;;;;;; "
};

function getFaceForEmotion(emotion = "calm") {
    const e = emotion.toLowerCase();
    if (e.includes("nervous") || e.includes("sweat")) return ASCII_FACES.nervous;
    if (e.includes("smug") || e.includes("arrogant")) return ASCII_FACES.smug;
    if (e.includes("angry") || e.includes("rattled") || e.includes("cornered")) return ASCII_FACES.rattled;
    return ASCII_FACES.calm;
}

// --------------------------------------------------------------------------
// 5. GAME INITIALIZATION & SESSION MANAGEMENT
// --------------------------------------------------------------------------
async function startCaseFlow(isPractice = false, targetDate = null) {
    unlockAudio();
    playSound("key");

    // Read selected difficulty
    const checkedDiff = document.querySelector('input[name="difficulty-select"]:checked');
    currentDifficulty = checkedDiff ? checkedDiff.value : "classic";

    try {
        const resp = await fetch("/api/session/start", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                date: targetDate,
                practice: isPractice,
                difficulty: currentDifficulty
            })
        });

        if (!resp.ok) {
            alert("Could not initialize game session. Please check connection.");
            return;
        }

        const data = await resp.json();
        currentSession = {
            id: data.session_id,
            remainingTokens: data.remaining_tokens,
            maxTokens: data.max_tokens,
            difficulty: data.difficulty,
            turn: 0,
            statements: []
        };
        currentCase = data.case;

        // Populate Briefing Screen
        renderBriefingScreen(currentCase);
        navigateTo("screen-briefing");
    } catch (err) {
        console.error("Session start error", err);
        alert("Failed to start session.");
    }
}

function renderBriefingScreen(caseObj) {
    document.getElementById("briefing-title").innerText = caseObj.title.toUpperCase();
    document.getElementById("briefing-date-badge").innerText = `DATE: ${caseObj.date}`;
    document.getElementById("briefing-description").innerText = caseObj.crime_description;
    document.getElementById("briefing-setting").innerText = caseObj.setting.toUpperCase();

    // Suspect
    document.getElementById("briefing-suspect-name").innerText = caseObj.suspect.name.toUpperCase();
    document.getElementById("briefing-suspect-occupation").innerText = `OCCUPATION: ${caseObj.suspect.occupation.toUpperCase()}`;
    document.getElementById("briefing-suspect-quirk").innerText = `"${caseObj.suspect.quirk}"`;
    document.getElementById("briefing-suspect-mugshot").innerText = caseObj.suspect.ascii_face || ASCII_FACES.calm;

    // Dossier Facts Preview
    const factsContainer = document.getElementById("briefing-dossier-list");
    factsContainer.innerHTML = "";
    caseObj.dossier.forEach((fact, idx) => {
        const card = document.createElement("div");
        card.className = "preview-fact-card";
        card.innerHTML = `
            <span class="preview-fact-tag">[ FACT #${idx + 1} — VERIFIED EVIDENCE ]</span>
            <p class="preview-fact-text">${escapeHtml(fact.text)}</p>
        `;
        factsContainer.appendChild(card);
    });
}

function enterInterrogationRoom() {
    if (!currentCase || !currentSession) return;
    playSound("key");

    // Populate HUD
    document.getElementById("room-case-title").innerText = currentCase.title.toUpperCase();
    document.getElementById("room-suspect-name").innerText = currentCase.suspect.name.toUpperCase();
    document.getElementById("room-sidebar-quirk").innerText = `"${currentCase.suspect.quirk}"`;
    document.getElementById("room-suspect-face").innerText = currentCase.suspect.ascii_face || ASCII_FACES.calm;
    document.getElementById("room-suspect-mood").innerText = "[MOOD: CALM]";
    document.getElementById("room-suspect-mood").className = "mood-badge mood-calm";

    // Populate Dossier
    const dossierList = document.getElementById("room-dossier-facts");
    dossierList.innerHTML = "";
    currentCase.dossier.forEach((fact, idx) => {
        const c = document.createElement("div");
        c.className = "side-fact-card";
        c.innerHTML = `
            <span class="side-fact-tag">[ FACT #${idx + 1} ]</span>
            <p class="side-fact-text">${escapeHtml(fact.text)}</p>
        `;
        dossierList.appendChild(c);
    });

    // Populate Tokens HUD
    updateTokensUI();

    // Reset Transcript
    const transcript = document.getElementById("interrogation-transcript");
    transcript.innerHTML = `
        <div class="transcript-msg system-msg">
            <span class="msg-sender">[DISPATCH]:</span>
            <span class="msg-text">Interrogation room audio wire opened. Suspect ${escapeHtml(currentCase.suspect.name)} is seated across the table. You hold ${currentSession.remainingTokens} tokens. Make every question count.</span>
        </div>
    `;

    document.getElementById("console-turn-counter").innerText = "TURN #0";
    document.getElementById("input-interrogate-question").value = "";

    navigateTo("screen-interrogation");
    setTimeout(() => {
        document.getElementById("input-interrogate-question").focus();
    }, 200);
}

function updateTokensUI() {
    const pipsContainer = document.getElementById("room-tokens-pips");
    const label = document.getElementById("room-tokens-count");
    if (!currentSession) return;

    pipsContainer.innerHTML = "";
    for (let i = 0; i < currentSession.maxTokens; i++) {
        const span = document.createElement("span");
        if (i < currentSession.remainingTokens) {
            span.className = "token-pip active" + (currentSession.remainingTokens <= 2 ? " critical" : "");
            span.innerText = "[O]";
        } else {
            span.className = "token-pip";
            span.innerText = "[X]";
        }
        pipsContainer.appendChild(span);
    }

    label.innerText = `(${currentSession.remainingTokens} / ${currentSession.maxTokens})`;
}

// --------------------------------------------------------------------------
// 6. QUESTION TRANSMISSION & INTERROGATION LOG
// --------------------------------------------------------------------------
async function submitQuestion(questionText) {
    if (!currentSession || !questionText.trim()) return;
    const text = questionText.trim();

    playSound("token");
    const transcript = document.getElementById("interrogation-transcript");
    const input = document.getElementById("input-interrogate-question");
    input.value = "";
    input.disabled = true;

    // Append Detective Question
    const qMsg = document.createElement("div");
    qMsg.className = "transcript-msg detective-msg";
    qMsg.innerHTML = `
        <span class="msg-sender">[DETECTIVE]:</span>
        <span class="msg-text">"${escapeHtml(text)}"</span>
    `;
    transcript.appendChild(qMsg);
    transcript.scrollTop = transcript.scrollHeight;

    // Show Thinking Spinner
    const spinner = document.getElementById("transcript-spinner");
    spinner.classList.remove("hidden");

    try {
        const resp = await fetch("/api/session/interrogate", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                session_id: currentSession.id,
                question: text
            })
        });

        spinner.classList.add("hidden");
        input.disabled = false;
        input.focus();

        if (!resp.ok) {
            alert("Error communicating with interrogation room.");
            return;
        }

        const data = await resp.json();
        currentSession.remainingTokens = data.remaining_tokens;
        currentSession.turn = data.turn_number;
        updateTokensUI();
        document.getElementById("console-turn-counter").innerText = `TURN #${data.turn_number}`;

        if (!data.success) {
            // Out of tokens or error
            const errDiv = document.createElement("div");
            errDiv.className = "transcript-msg alert-msg";
            errDiv.innerHTML = `<span class="msg-sender">[ALERT]:</span> <span class="msg-text">${escapeHtml(data.error || "Turn rejected.")}</span>`;
            transcript.appendChild(errDiv);
            if (data.game_over) {
                handleGameOver(false, "You ran out of Question Tokens without extracting a formal contradiction.");
            }
            return;
        }

        // Suspect Response
        currentSession.statements.push({
            turn: data.turn_number,
            question: text,
            answer: data.answer,
            claims: data.extracted_claims || []
        });

        // Update Mood & Art
        const mood = data.emotion || "calm";
        const moodBadge = document.getElementById("room-suspect-mood");
        moodBadge.innerText = `[MOOD: ${mood.toUpperCase()}]`;
        if (mood.toLowerCase().includes("nervous") || mood.toLowerCase().includes("sweat")) {
            moodBadge.className = "mood-badge mood-nervous";
            playSound("nervous");
        } else if (mood.toLowerCase().includes("rattled") || mood.toLowerCase().includes("cornered")) {
            moodBadge.className = "mood-badge mood-rattled";
            playSound("nervous");
        } else {
            moodBadge.className = "mood-badge mood-calm";
        }
        document.getElementById("room-suspect-face").innerText = getFaceForEmotion(mood);

        // Append Suspect Reply
        const sMsg = document.createElement("div");
        sMsg.className = "transcript-msg suspect-msg";
        let claimsHtml = "";
        if (data.extracted_claims && data.extracted_claims.length > 0) {
            claimsHtml = `<div class="suspect-claim-tags">` + data.extracted_claims.map(c => 
                `<span class="claim-tag">[CLAIM: ${escapeHtml(c.subject)} ${escapeHtml(c.predicate)} ${escapeHtml(c.object_value)}]</span>`
            ).join("") + `</div>`;
        }

        sMsg.innerHTML = `
            <span class="msg-sender">[${escapeHtml(currentCase.suspect.name.toUpperCase())}]:</span>
            <span class="msg-text">"${escapeHtml(data.answer)}"</span>
            ${claimsHtml}
        `;
        transcript.appendChild(sMsg);
        transcript.scrollTop = transcript.scrollHeight;

        // Check if out of tokens
        if (data.game_over && !data.won) {
            handleGameOver(false, "You exhausted your final question token without lodging an indictment.");
        }

    } catch (e) {
        spinner.classList.add("hidden");
        input.disabled = false;
        console.error("Interrogation error", e);
    }
}

// --------------------------------------------------------------------------
// 7. NOIR NARRATOR HINT
// --------------------------------------------------------------------------
async function requestHint() {
    if (!currentSession) return;
    playSound("key");

    try {
        const resp = await fetch("/api/session/hint", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ session_id: currentSession.id })
        });

        const data = await resp.json();
        const transcript = document.getElementById("interrogation-transcript");

        if (data.success) {
            currentSession.remainingTokens = data.remaining_tokens;
            updateTokensUI();

            const hMsg = document.createElement("div");
            hMsg.className = "transcript-msg hint-msg";
            hMsg.innerHTML = `
                <span class="msg-sender">[NOIR NARRATOR]:</span>
                <span class="msg-text">${escapeHtml(data.hint)}</span>
            `;
            transcript.appendChild(hMsg);
            transcript.scrollTop = transcript.scrollHeight;
        } else {
            const hMsg = document.createElement("div");
            hMsg.className = "transcript-msg alert-msg";
            hMsg.innerHTML = `<span class="msg-sender">[ALERT]:</span> <span class="msg-text">${escapeHtml(data.hint || "No hints available.")}</span>`;
            transcript.appendChild(hMsg);
        }
    } catch (e) {
        console.error("Hint error", e);
    }
}

// --------------------------------------------------------------------------
// 8. FORMAL ACCUSATION INDICTMENT FLOW
// --------------------------------------------------------------------------
function openAccuseModal() {
    if (!currentSession || !currentCase) return;
    playSound("key");

    if (currentSession.statements.length === 0) {
        alert("You have not questioned the suspect yet. Inquire first before indicting.");
        return;
    }

    const quotesList = document.getElementById("accuse-quotes-list");
    const factsList = document.getElementById("accuse-facts-list");
    quotesList.innerHTML = "";
    factsList.innerHTML = "";

    // 1. Populate Suspect Statements
    currentSession.statements.forEach((st, idx) => {
        const div = document.createElement("label");
        div.className = "accuse-option-card";
        div.innerHTML = `
            <input type="radio" name="accuse-quote-pick" value="${escapeHtml(st.answer)}" ${idx === currentSession.statements.length - 1 ? "checked" : ""}>
            <span class="option-quote-text">"${escapeHtml(st.answer)}"</span>
        `;
        div.addEventListener("click", () => {
            document.querySelectorAll("#accuse-quotes-list .accuse-option-card").forEach(c => c.classList.remove("selected"));
            div.classList.add("selected");
        });
        if (idx === currentSession.statements.length - 1) div.classList.add("selected");
        quotesList.appendChild(div);
    });

    // 2. Populate Dossier Facts
    currentCase.dossier.forEach((fact, idx) => {
        const div = document.createElement("label");
        div.className = "accuse-option-card";
        div.innerHTML = `
            <input type="radio" name="accuse-fact-pick" value="${escapeHtml(fact.text)}" ${idx === 0 ? "checked" : ""}>
            <span class="option-quote-text">[FACT #${idx + 1}]: ${escapeHtml(fact.text)}</span>
        `;
        div.addEventListener("click", () => {
            document.querySelectorAll("#accuse-facts-list .accuse-option-card").forEach(c => c.classList.remove("selected"));
            div.classList.add("selected");
        });
        if (idx === 0) div.classList.add("selected");
        factsList.appendChild(div);
    });

    document.getElementById("accuse-judging-spinner").classList.add("hidden");
    document.getElementById("btn-submit-indictment").disabled = false;
    document.getElementById("btn-submit-indictment").innerText = "[ DELIVER INDICTMENT TO JUDGE ]";

    document.getElementById("modal-accuse").classList.remove("hidden");
}

function closeAccuseModal() {
    document.getElementById("modal-accuse").classList.add("hidden");
}

async function submitIndictment() {
    if (!currentSession) return;

    const pickedQuoteRadio = document.querySelector('input[name="accuse-quote-pick"]:checked');
    const pickedFactRadio = document.querySelector('input[name="accuse-fact-pick"]:checked');

    if (!pickedQuoteRadio || !pickedFactRadio) {
        alert("Please select both a suspect quote and a contradictory dossier fact.");
        return;
    }

    const quote = pickedQuoteRadio.value;
    const factText = pickedFactRadio.value;

    playSound("accuse");
    const spinner = document.getElementById("accuse-judging-spinner");
    const btn = document.getElementById("btn-submit-indictment");
    spinner.classList.remove("hidden");
    btn.disabled = true;
    btn.innerText = "JUDGE DELIBERATING...";

    try {
        const resp = await fetch("/api/session/accuse", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                session_id: currentSession.id,
                quote: quote,
                target_text: factText,
                is_dossier_fact: true
            })
        });

        spinner.classList.add("hidden");
        closeAccuseModal();

        if (!resp.ok) {
            alert("Error delivering accusation to judge.");
            return;
        }

        const data = await resp.json();
        currentSession.remainingTokens = data.remaining_tokens;
        updateTokensUI();

        if (data.valid) {
            // CONVICTED!
            playSound("win");
            handleGameOver(true, data.explanation, data.breakdown_confession, data.share_grid);
        } else {
            // Failed accusation
            playSound("nervous");
            const transcript = document.getElementById("interrogation-transcript");
            const alertDiv = document.createElement("div");
            alertDiv.className = "transcript-msg alert-msg";
            alertDiv.innerHTML = `
                <span class="msg-sender">[CONTRADICTION JUDGE]:</span>
                <span class="msg-text">INSUFFICIENT CONTRADICTION! ${escapeHtml(data.explanation || "The statement does not directly refute this fact.")} Penalty applied. Remaining tokens: ${data.remaining_tokens}.</span>
            `;
            transcript.appendChild(alertDiv);
            transcript.scrollTop = transcript.scrollHeight;

            if (data.game_over) {
                handleGameOver(false, "Your accusation failed and exhausted all remaining interrogation tokens.");
            }
        }

    } catch (e) {
        spinner.classList.add("hidden");
        btn.disabled = false;
        btn.innerText = "[ DELIVER INDICTMENT TO JUDGE ]";
        console.error("Accusation error", e);
    }
}

// --------------------------------------------------------------------------
// 9. GAME OVER & RESULT SCREEN
// --------------------------------------------------------------------------
function handleGameOver(won, explanation, confession = "", shareGrid = "") {
    const banner = document.getElementById("result-status-banner");
    const heading = document.getElementById("result-main-heading");
    const explBox = document.getElementById("result-explanation-text");
    const confessionSec = document.getElementById("result-confession-section");
    const confessionQuote = document.getElementById("result-confession-quote");
    const gridPre = document.getElementById("result-share-grid-text");

    if (won) {
        banner.className = "result-banner banner-win";
        heading.innerText = "★★★★★ CASE CLOSED: SUSPECT CONVICTED! ★★★★★";
        explBox.innerText = explanation || "Airtight contradiction established. Suspect broke down under interrogation.";
        
        if (confession) {
            confessionSec.classList.remove("hidden");
            confessionQuote.innerText = `"${confession}"`;
        } else {
            confessionSec.classList.add("hidden");
        }
    } else {
        playSound("lose");
        banner.className = "result-banner banner-lose";
        heading.innerText = "✖✖✖✖✖ CASE DISMISSED: SUSPECT WALKED FREE ✖✖✖✖✖";
        explBox.innerText = explanation || "You ran out of interrogation tokens. Without a validated contradiction, the police chief was forced to release the suspect.";
        confessionSec.classList.add("hidden");
    }

    gridPre.innerText = shareGrid || `THE ALIBI [${won ? "CONVICTED" : "DISMISSED"}]\nTokens Used: ${currentSession ? currentSession.maxTokens - currentSession.remainingTokens : 5}\nStatus: ${won ? "WON" : "LOST"}`;

    navigateTo("screen-result");
    refreshGlobalStatus();
}

// --------------------------------------------------------------------------
// 10. ARCHIVE & RULES SCREENS
// --------------------------------------------------------------------------
async function loadArchivesScreen() {
    playSound("key");
    navigateTo("screen-archive");
    const tbody = document.getElementById("archive-table-rows");
    tbody.innerHTML = `<tr><td colspan="6" style="text-align:center; padding:20px; color:var(--color-slate);">RETRIEVING COLD CASE EVIDENCE REPOSITORY...</td></tr>`;

    try {
        const resp = await fetch("/api/archive");
        if (!resp.ok) return;
        const data = await resp.json();
        tbody.innerHTML = "";

        if (!data || data.length === 0) {
            tbody.innerHTML = `<tr><td colspan="6" style="text-align:center; padding:20px;">No archived cases found.</td></tr>`;
            return;
        }

        data.forEach(item => {
            const tr = document.createElement("tr");
            const statusTag = item.solved ? `<span style="color:var(--color-green); font-weight:700;">[CONVICTED]</span>` : `<span style="color:var(--color-slate);">[COLD CASE]</span>`;
            tr.innerHTML = `
                <td>${escapeHtml(item.date)}</td>
                <td>${statusTag}</td>
                <td style="color:var(--color-amber); font-weight:700;">${escapeHtml(item.title)}</td>
                <td style="color:var(--color-cyan);">${escapeHtml(item.suspect_name)}</td>
                <td>${escapeHtml(item.setting)}</td>
                <td>
                    <button class="action-btn back-btn" style="padding:4px 10px; font-size:0.75rem;" onclick="startCaseFlow(false, '${item.date}')">
                        [ REPLAY ]
                    </button>
                </td>
            `;
            tbody.appendChild(tr);
        });
    } catch (e) {
        console.error("Archive error", e);
    }
}

// --------------------------------------------------------------------------
// 11. ENGINE CONFIGURATION & STATUS
// --------------------------------------------------------------------------
async function refreshGlobalStatus() {
    try {
        const resp = await fetch("/api/status");
        if (resp.ok) {
            const data = await resp.json();
            document.getElementById("streak-badge-text").innerText = data.current_streak || 0;
        }

        const cResp = await fetch("/api/config/llm");
        if (cResp.ok) {
            const cData = await cResp.json();
            const badge = document.getElementById("engine-badge-text");
            if (cData.provider === "groq") {
                badge.innerText = "GROQ CLOUD";
                badge.style.color = "var(--color-green)";
            } else {
                badge.innerText = "LOCAL OLLAMA";
                badge.style.color = "var(--color-cyan)";
            }
        }
    } catch (e) {
        console.warn("Status refresh error", e);
    }
}

function openEngineModal() {
    playSound("key");
    document.getElementById("engine-feedback-box").classList.add("hidden");
    document.getElementById("modal-engine").classList.remove("hidden");
}

function closeEngineModal() {
    document.getElementById("modal-engine").classList.add("hidden");
}

async function saveEngineConfig() {
    const isGroq = document.getElementById("radio-groq")?.checked;
    const provider = isGroq ? "groq" : "ollama";
    const apiKey = document.getElementById("input-groq-key").value.trim();
    const alertBox = document.getElementById("engine-feedback-box");
    const btn = document.getElementById("btn-save-engine-config");

    btn.disabled = true;
    btn.innerText = "[ CONNECTING... ]";

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
            alertBox.className = "feedback-alert success";
            alertBox.innerText = `[SUCCESS]: ${data.message}`;
            playSound("win");
            refreshGlobalStatus();
            setTimeout(closeEngineModal, 1200);
        } else {
            alertBox.className = "feedback-alert error";
            alertBox.innerText = `[ERROR]: ${data.message}`;
            playSound("lose");
        }
    } catch (e) {
        alertBox.classList.remove("hidden");
        alertBox.className = "feedback-alert error";
        alertBox.innerText = "[ERROR]: Failed to connect to server engine.";
    } finally {
        btn.disabled = false;
        btn.innerText = "[ CONNECT INFERENCE ENGINE ]";
    }
}

// --------------------------------------------------------------------------
// 12. UTILITIES & KEYBOARD EVENT HANDLERS
// --------------------------------------------------------------------------
function escapeHtml(text) {
    if (!text) return "";
    return String(text)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}

// Midnight Countdown Timer
function updateCountdown() {
    const now = new Date();
    const midnight = new Date(now);
    midnight.setHours(24, 0, 0, 0);
    const diff = midnight - now;

    const hours = Math.floor(diff / (1000 * 60 * 60));
    const mins = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));
    const secs = Math.floor((diff % (1000 * 60)) / 1000);

    const pad = n => String(n).padStart(2, '0');
    const el = document.getElementById("countdown-text");
    if (el) el.innerText = `${pad(hours)}:${pad(mins)}:${pad(secs)}`;
}
setInterval(updateCountdown, 1000);
updateCountdown();

// DOM Ready Bindings
document.addEventListener("DOMContentLoaded", () => {
    // Unmute on first body interaction
    document.body.addEventListener("click", unlockAudio, { once: true });

    // Header buttons
    document.getElementById("btn-engine-config").addEventListener("click", openEngineModal);
    document.getElementById("btn-close-engine-modal").addEventListener("click", closeEngineModal);
    document.getElementById("btn-save-engine-config").addEventListener("click", saveEngineConfig);

    document.getElementById("btn-audio-toggle").addEventListener("click", () => {
        soundEnabled = !soundEnabled;
        const btn = document.getElementById("audio-btn-text");
        btn.innerText = soundEnabled ? "[AUDIO: ON]" : "[AUDIO: MUTED]";
        btn.className = soundEnabled ? "hud-val-green" : "hud-label";
    });

    // Menu Screen buttons
    document.querySelectorAll(".arcade-menu-item").forEach(item => {
        item.addEventListener("mouseenter", () => playSound("key"));
    });
    document.getElementById("btn-menu-today").addEventListener("click", () => startCaseFlow(false));
    document.getElementById("btn-menu-practice").addEventListener("click", () => startCaseFlow(true));
    document.getElementById("btn-menu-archive").addEventListener("click", loadArchivesScreen);
    document.getElementById("btn-menu-rules").addEventListener("click", () => {
        playSound("key");
        navigateTo("screen-rules");
    });

    // Briefing Screen buttons
    document.getElementById("btn-start-interrogation").addEventListener("click", enterInterrogationRoom);
    document.getElementById("btn-briefing-back").addEventListener("click", () => {
        playSound("key");
        navigateTo("screen-menu");
    });

    // Interrogation Screen buttons
    document.getElementById("btn-request-hint").addEventListener("click", requestHint);
    document.getElementById("btn-open-accuse").addEventListener("click", openAccuseModal);
    document.getElementById("btn-close-accuse-modal").addEventListener("click", closeAccuseModal);
    document.getElementById("btn-submit-indictment").addEventListener("click", submitIndictment);

    document.getElementById("form-interrogate").addEventListener("submit", (e) => {
        e.preventDefault();
        const input = document.getElementById("input-interrogate-question");
        const val = input.value.trim();
        if (val.toLowerCase() === "a" || val.toLowerCase() === "/accuse") {
            input.value = "";
            openAccuseModal();
        } else if (val.toLowerCase() === "h" || val.toLowerCase() === "/hint") {
            input.value = "";
            requestHint();
        } else if (val) {
            submitQuestion(val);
        }
    });

    // Keystroke sound on interrogation input
    document.getElementById("input-interrogate-question").addEventListener("keydown", (e) => {
        if (e.key !== "Enter" && e.key !== "Escape" && e.key.length === 1) {
            playSound("key");
        }
    });

    // Result Screen buttons
    document.getElementById("btn-result-play-again").addEventListener("click", () => startCaseFlow(true));
    document.getElementById("btn-result-to-menu").addEventListener("click", () => {
        playSound("key");
        navigateTo("screen-menu");
    });

    document.getElementById("btn-copy-dossier").addEventListener("click", () => {
        const text = document.getElementById("result-share-grid-text").innerText;
        navigator.clipboard.writeText(text).then(() => {
            playSound("key");
            const alert = document.getElementById("copy-status-indicator");
            alert.classList.remove("hidden");
            setTimeout(() => alert.classList.add("hidden"), 1500);
        });
    });

    // Archive & Rules Return Buttons
    document.getElementById("btn-archive-back").addEventListener("click", () => {
        playSound("key");
        navigateTo("screen-menu");
    });
    document.getElementById("btn-rules-back").addEventListener("click", () => {
        playSound("key");
        navigateTo("screen-menu");
    });

    // Global Keyboard Navigation
    document.addEventListener("keydown", (e) => {
        // If typing in input field, don't trigger global shortcuts
        const activeTag = document.activeElement ? document.activeElement.tagName.toLowerCase() : "";
        if (activeTag === "input" && e.key !== "Escape") return;

        if (e.key === "Escape") {
            closeAccuseModal();
            closeEngineModal();
        } else if (e.key === "1" && document.getElementById("screen-menu").classList.contains("active-screen")) {
            startCaseFlow(false);
        } else if (e.key === "2" && document.getElementById("screen-menu").classList.contains("active-screen")) {
            startCaseFlow(true);
        } else if (e.key === "3" && document.getElementById("screen-menu").classList.contains("active-screen")) {
            loadArchivesScreen();
        } else if (e.key === "4" && document.getElementById("screen-menu").classList.contains("active-screen")) {
            navigateTo("screen-rules");
        } else if ((e.key === "a" || e.key === "A") && document.getElementById("screen-interrogation").classList.contains("active-screen")) {
            e.preventDefault();
            openAccuseModal();
        } else if ((e.key === "h" || e.key === "H") && document.getElementById("screen-interrogation").classList.contains("active-screen")) {
            e.preventDefault();
            requestHint();
        } else if (e.key === "Enter" && document.getElementById("screen-briefing").classList.contains("active-screen")) {
            enterInterrogationRoom();
        }
    });

    refreshGlobalStatus();
});
