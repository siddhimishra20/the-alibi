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
let currentBgm = null;
let bgmTitle = null;
let bgmInterrogation = null;

// --------------------------------------------------------------------------
// 1. AUDIO ENGINE (WAV Music Loops, Sound FX & Web Audio Unlocking)
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

    // Background Music Loops (705KB WAV ambient loops)
    bgmTitle = new Audio("/audio/title.wav");
    bgmTitle.loop = true;
    bgmTitle.volume = 0.35;

    bgmInterrogation = new Audio("/audio/interrogation.wav");
    bgmInterrogation.loop = true;
    bgmInterrogation.volume = 0.35;

    // Preload SFX
    for (const [key, path] of Object.entries(AUDIO_FILES)) {
        try {
            const a = new Audio(path);
            a.volume = 0.45;
            audioCache[key] = a;
        } catch (e) {
            console.warn("Audio load error for", key, e);
        }
    }

    // Auto-play menu title music if currently on menu screen
    const menuScreen = document.getElementById("screen-menu");
    if (menuScreen && menuScreen.classList.contains("active-screen")) {
        playBGM("title");
    }
}

function playBGM(track) {
    if (!soundEnabled) return;
    if (!audioContextUnlocked) unlockAudio();
    if (track === currentBgm) return;

    if (bgmTitle) bgmTitle.pause();
    if (bgmInterrogation) bgmInterrogation.pause();

    currentBgm = track;
    if (track === "title" && bgmTitle) {
        bgmTitle.currentTime = 0;
        bgmTitle.play().catch(e => console.warn("Title BGM play error", e));
    } else if (track === "interrogation" && bgmInterrogation) {
        bgmInterrogation.currentTime = 0;
        bgmInterrogation.play().catch(e => console.warn("Interrogation BGM play error", e));
    }
}

function stopBGM() {
    if (bgmTitle) bgmTitle.pause();
    if (bgmInterrogation) bgmInterrogation.pause();
    currentBgm = null;
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

        // Dynamic BGM Track Switching
        if (screenId === "screen-menu" || screenId === "screen-briefing" || screenId === "screen-archive" || screenId === "screen-rules") {
            playBGM("title");
        } else if (screenId === "screen-interrogation") {
            playBGM("interrogation");
        } else if (screenId === "screen-result") {
            stopBGM();
        }
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
            alreadySolved: data.already_solved,
            completedData: data.completed_data,
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

    // Character Kit Procedural Portrait & Traits
    const portraitImg = document.getElementById("briefing-suspect-portrait");
    if (portraitImg) {
        portraitImg.src = caseObj.portrait_url || `/api/character/${caseObj.id || caseObj.date}.png`;
    }
    const traitsEl = document.getElementById("briefing-suspect-traits");
    if (traitsEl) {
        traitsEl.innerText = caseObj.suspect.traits_description || "Standard noir criminal suspect profile";
    }

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
    document.getElementById("room-suspect-mood").innerText = "[MOOD: CALM]";
    document.getElementById("room-suspect-mood").className = "mood-badge mood-calm";

    // Character Kit Portrait & Traits in Wire Monitor
    const roomPort = document.getElementById("room-suspect-portrait");
    if (roomPort) {
        roomPort.src = currentCase.portrait_url || `/api/character/${currentCase.id || currentCase.date}.png`;
    }
    const roomTraits = document.getElementById("room-sidebar-traits");
    if (roomTraits) {
        roomTraits.innerText = currentCase.suspect.traits_description || "";
    }

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
        const img = document.createElement("img");
        img.src = "/static/images/token.png";
        if (i < currentSession.remainingTokens) {
            img.className = "token-coin active" + (currentSession.remainingTokens <= 2 ? " critical" : "");
            img.title = `Token #${i + 1} (Available)`;
            img.alt = "[O]";
        } else {
            img.className = "token-coin spent";
            img.title = `Token #${i + 1} (Spent)`;
            img.alt = "[X]";
        }
        pipsContainer.appendChild(img);
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
                handleGameOver(false, "You ran out of Question Tokens without extracting a formal contradiction.", "", "", data.score_info, data.total_score, data.rank);
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
        const faceEl = document.getElementById("room-suspect-face");
        if (faceEl) faceEl.innerText = getFaceForEmotion(mood);

        // Append Suspect Reply (Clean noir dialogue without internal claim tag clutter)
        const sMsg = document.createElement("div");
        sMsg.className = "transcript-msg suspect-msg";
        sMsg.innerHTML = `
            <span class="msg-sender">[${escapeHtml(currentCase.suspect.name.toUpperCase())}]:</span>
            <span class="msg-text">"${escapeHtml(data.answer)}"</span>
        `;
        transcript.appendChild(sMsg);
        transcript.scrollTop = transcript.scrollHeight;

        // Check if out of tokens
        if (data.game_over && !data.won) {
            handleGameOver(false, "You exhausted your final question token without lodging an indictment.", "", "", data.score_info, data.total_score, data.rank);
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
            handleGameOver(true, data.explanation, data.breakdown_confession, data.share_grid, data.score_info, data.total_score, data.rank);
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
                handleGameOver(false, "Your accusation failed and exhausted all remaining interrogation tokens.", "", "", data.score_info, data.total_score, data.rank);
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
function handleGameOver(won, explanation, confession = "", shareGrid = "", scoreInfo = null, totalScore = 0, rank = "") {
    const banner = document.getElementById("result-status-banner");
    const heading = document.getElementById("result-main-heading");
    const explBox = document.getElementById("result-explanation-text");
    const confessionSec = document.getElementById("result-confession-section");
    const confessionQuote = document.getElementById("result-confession-quote");
    const gridPre = document.getElementById("result-share-grid-text");

    // Suspect Mugshot & Stamped Verdict
    const portraitImg = document.getElementById("result-suspect-portrait");
    if (portraitImg && currentCase) {
        portraitImg.src = currentCase.portrait_url || `/api/character/${currentCase.id || currentCase.date}.png`;
    }
    const suspectNameEl = document.getElementById("result-suspect-name");
    if (suspectNameEl && currentCase) {
        suspectNameEl.innerText = currentCase.suspect.name.toUpperCase();
    }
    const stampBadge = document.getElementById("result-verdict-stamp");

    if (won) {
        banner.className = "result-banner banner-win";
        heading.innerText = "★★★★★ CASE CLOSED: SUSPECT CONVICTED! ★★★★★";
        explBox.innerText = explanation || "Airtight contradiction established. Suspect broke down under interrogation.";
        
        if (stampBadge) {
            stampBadge.innerText = "[ CONVICTED ]";
            stampBadge.className = "verdict-stamp stamp-convicted";
        }

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

        if (stampBadge) {
            stampBadge.innerText = "[ WALKED FREE ]";
            stampBadge.className = "verdict-stamp stamp-dismissed";
        }
    }

    // Official Department Score Ledger Updates
    const earnedBadge = document.getElementById("result-score-earned-badge");
    const rowBase = document.getElementById("score-row-base");
    const rowTokens = document.getElementById("score-row-tokens");
    const rowQuick = document.getElementById("score-row-quick");
    const rowFlawless = document.getElementById("score-row-flawless");
    const rowStreak = document.getElementById("score-row-streak");
    const rowMultiplier = document.getElementById("score-row-multiplier");
    const careerScoreText = document.getElementById("result-career-score-text");
    const careerRankText = document.getElementById("result-career-rank-text");

    if (scoreInfo && won) {
        if (earnedBadge) earnedBadge.innerText = `+${(scoreInfo.total || 0).toLocaleString()} PTS`;
        if (rowBase) rowBase.innerText = `+${(scoreInfo.base || 1000).toLocaleString()} PTS`;
        const toks = scoreInfo.tokens_left ?? (currentSession ? currentSession.remainingTokens : 0);
        if (rowTokens) rowTokens.innerText = `+${(scoreInfo.tokens_bonus || 0).toLocaleString()} PTS (${toks} tokens saved)`;
        if (rowQuick) rowQuick.innerText = `+${(scoreInfo.quick_bonus || 0).toLocaleString()} PTS`;
        if (rowFlawless) rowFlawless.innerText = `+${(scoreInfo.flawless_bonus || 0).toLocaleString()} PTS`;
        if (rowStreak) rowStreak.innerText = `+${(scoreInfo.streak_bonus || 0).toLocaleString()} PTS`;
        if (rowMultiplier) rowMultiplier.innerText = `${scoreInfo.multiplier || 1.0}x (${(scoreInfo.difficulty || 'classic').toUpperCase()})`;
    } else {
        if (earnedBadge) earnedBadge.innerText = `0 PTS`;
        if (rowBase) rowBase.innerText = `0 PTS`;
        if (rowTokens) rowTokens.innerText = `0 PTS`;
        if (rowQuick) rowQuick.innerText = `0 PTS`;
        if (rowFlawless) rowFlawless.innerText = `0 PTS`;
        if (rowStreak) rowStreak.innerText = `0 PTS`;
        if (rowMultiplier) rowMultiplier.innerText = `1.0x (CLASSIC)`;
    }

    if (careerScoreText) careerScoreText.innerText = `${(totalScore || 0).toLocaleString()} PTS`;
    if (careerRankText) careerRankText.innerText = rank || "PATROL OFFICER";

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
    tbody.innerHTML = `<tr><td colspan="8" style="text-align:center; padding:20px; color:var(--color-slate);">RETRIEVING COLD CASE EVIDENCE REPOSITORY...</td></tr>`;

    try {
        const resp = await fetch("/api/archive");
        if (!resp.ok) return;
        const data = await resp.json();
        tbody.innerHTML = "";

        if (!data || data.length === 0) {
            tbody.innerHTML = `<tr><td colspan="8" style="text-align:center; padding:20px;">No archived cases found.</td></tr>`;
            return;
        }

        data.forEach(item => {
            const tr = document.createElement("tr");
            const isSolved = item.status === "SOLVED" || item.won;
            const statusTag = isSolved 
                ? `<span style="color:var(--color-green); font-weight:700;">[CONVICTED]</span>` 
                : (item.status === "FAILED" ? `<span style="color:var(--color-crimson);">[DISMISSED]</span>` : `<span style="color:var(--color-slate);">[COLD CASE]</span>`);
            const scoreStr = item.score ? `+${item.score.toLocaleString()} PTS` : `-`;
            const thumbUrl = item.portrait_url || `/api/character/${item.date}.png`;

            tr.innerHTML = `
                <td class="col-date">${escapeHtml(item.date)}</td>
                <td class="col-thumb">
                    <img src="${thumbUrl}" class="archive-portrait-thumb" alt="Mugshot" onerror="this.style.display='none'">
                </td>
                <td class="col-status">${statusTag}</td>
                <td class="col-score">${scoreStr}</td>
                <td class="col-title" style="color:var(--color-amber);">${escapeHtml(item.title)}</td>
                <td class="col-suspect" style="color:var(--color-cyan);">${escapeHtml(item.suspect_name)}</td>
                <td class="col-scene">${escapeHtml(item.setting)}</td>
                <td class="col-action">
                    <button class="archive-replay-btn" onclick="startCaseFlow(false, '${item.date}')">
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
            
            // Top Bar HUD
            const scoreEl = document.getElementById("hud-score-text");
            if (scoreEl) scoreEl.innerText = `${(data.total_score || 0).toLocaleString()} PTS`;

            const rankEl = document.getElementById("hud-rank-text");
            if (rankEl) rankEl.innerText = data.rank || "PATROL OFFICER";

            const recordEl = document.getElementById("hud-record-text");
            if (recordEl) recordEl.innerText = `${data.games_won || 0}/${data.games_played || 0}`;

            const streakEl = document.getElementById("streak-badge-text");
            if (streakEl) streakEl.innerText = data.current_streak || 0;

            // Archive Career Dossier
            const archScore = document.getElementById("archive-career-score");
            if (archScore) archScore.innerText = `${(data.total_score || 0).toLocaleString()} PTS`;

            const archRank = document.getElementById("archive-career-rank");
            if (archRank) archRank.innerText = `${data.rank_tier ? '[' + data.rank_tier + '] ' : ''}${data.rank || 'PATROL OFFICER'}`;

            const archRecord = document.getElementById("archive-career-record");
            if (archRecord) {
                const won = data.games_won || 0;
                const played = data.games_played || 0;
                const pct = played > 0 ? Math.round((won / played) * 100) : 0;
                archRecord.innerText = `${won} / ${played} (${pct}%)`;
            }

            const archStreak = document.getElementById("archive-career-streak");
            if (archStreak) archStreak.innerText = `${data.current_streak || 0} DAYS`;

            // Memory System: Check if Today's Challenge is Already Solved
            const todayBtn = document.getElementById("btn-menu-today");
            const todayTitle = document.getElementById("menu-today-title");
            const todayDesc = document.getElementById("menu-today-desc");
            const todayBadge = document.getElementById("menu-today-badge");

            if (data.today_solved && todayBtn) {
                todayBtn.classList.add("solved-today");
                const todayScore = data.today_data?.score || 0;
                if (todayTitle) todayTitle.innerText = "TODAY'S CASE: SOLVED ★";
                if (todayDesc) todayDesc.innerText = `Case closed! Earned +${todayScore.toLocaleString()} PTS. Review dossier or play practice cases.`;
                if (todayBadge) todayBadge.innerText = `[ SOLVED +${todayScore.toLocaleString()} PTS ]`;
            } else if (todayBtn) {
                todayBtn.classList.remove("solved-today");
                if (todayTitle) todayTitle.innerText = "START TODAY'S CASE";
                if (todayDesc) todayDesc.innerText = "Seeded daily micro-crime synchronized globally";
                if (todayBadge) todayBadge.innerText = "[ DAILY CASE ]";
            }
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
    // Unmute & start background music on first body interaction
    document.body.addEventListener("click", () => {
        unlockAudio();
        if (soundEnabled && !currentBgm) {
            const activeScreen = document.querySelector(".game-screen.active-screen");
            if (activeScreen && activeScreen.id === "screen-interrogation") {
                playBGM("interrogation");
            } else {
                playBGM("title");
            }
        }
    }, { once: true });

    // Header buttons
    document.getElementById("btn-engine-config").addEventListener("click", openEngineModal);
    document.getElementById("btn-close-engine-modal").addEventListener("click", closeEngineModal);
    document.getElementById("btn-save-engine-config").addEventListener("click", saveEngineConfig);

    document.getElementById("btn-audio-toggle").addEventListener("click", () => {
        soundEnabled = !soundEnabled;
        const btn = document.getElementById("audio-btn-text");
        btn.innerText = soundEnabled ? "[AUDIO: ON]" : "[AUDIO: MUTED]";
        btn.className = soundEnabled ? "hud-val-green" : "hud-label";

        if (!soundEnabled) {
            stopBGM();
        } else {
            unlockAudio();
            const activeScreen = document.querySelector(".game-screen.active-screen");
            if (activeScreen && activeScreen.id === "screen-interrogation") {
                playBGM("interrogation");
            } else {
                playBGM("title");
            }
        }
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
