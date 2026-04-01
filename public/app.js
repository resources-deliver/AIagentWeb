const messagesEl = document.getElementById("messages");
const formEl = document.getElementById("chatForm");
const inputEl = document.getElementById("promptInput");
const sendBtn = document.getElementById("sendBtn");
const modelSelect = document.getElementById("modelSelect");
const languageSelect = document.getElementById("languageSelect");
const languageHint = document.getElementById("languageHint");
const networkStatus = document.getElementById("networkStatus");
const ttsToggle = document.getElementById("ttsToggle");
const listenBtn = document.getElementById("listenBtn");
const clearChatBtn = document.getElementById("clearChatBtn");
const avatarStage = document.getElementById("avatarStage");
const avatarStatus = document.getElementById("avatarStatus");
const voiceHint = document.getElementById("voiceHint");
const MAX_STORED_MESSAGES = 24;
const MAX_CONTEXT_MESSAGES = 12;
const WELCOME_MESSAGE = "你好，我已经连上本地 Ollama。";
const state = { 
    messages: [], 
    ttsEnabled: true, 
    recognition: null, 
    recognitionActive: false, 
    currentAudio: null, 
    currentAudioUrl: null, 
    currentVoiceLabel: "Microsoft Edge-TTS",
    isSpeaking: false 
};
const languageMeta = {
    "zh-CN": { label: "普通话", lang: "zh-CN" },
    "zh-HK": { label: "粤语", lang: "zh-HK" },
    "zh-TW": { label: "台湾国语", lang: "zh-TW" },
    "en-US": { label: "美式英语", lang: "en-US" },
    "en-GB": { label: "英式英语", lang: "en-GB" },
    "en-AU": { label: "澳式英语", lang: "en-AU" },
    "ja-JP": { label: "日语", lang: "ja-JP" },
    "ko-KR": { label: "韩语", lang: "ko-KR" },
    "fr-FR": { label: "法语", lang: "fr-FR" },
    "de-DE": { label: "德语", lang: "de-DE" },
    "es-ES": { label: "西班牙语", lang: "es-ES" },
    "pt-BR": { label: "葡萄牙语", lang: "pt-BR" },
    "it-IT": { label: "意大利语", lang: "it-IT" },
    "ru-RU": { label: "俄语", lang: "ru-RU" }
};
function setAvatar(mode, text) { 
    avatarStage.classList.remove("is-speaking", "is-thinking"); 
    if (mode === "speaking") {
        avatarStage.classList.add("is-speaking");
        state.isSpeaking = true;
    } else {
        state.isSpeaking = false;
    }
    if (mode === "thinking") {
        avatarStage.classList.add("is-thinking");
    }
    avatarStatus.textContent = text; 
}

function createMessageNode(role, content) { 
    const article = document.createElement("article"); 
    article.className = "message " + role; 
    article.innerHTML = "<div class=bubble></div>"; 
    article.querySelector(".bubble").textContent = content; 
    return article; 
}

function renderMessages() { 
    messagesEl.innerHTML = ""; 
    if (state.messages.length === 0) { 
        messagesEl.appendChild(createMessageNode("assistant", WELCOME_MESSAGE)); 
    } else { 
        for (const m of state.messages) { 
            messagesEl.appendChild(createMessageNode(m.role, m.content)); 
        } 
    } 
    messagesEl.scrollTop = messagesEl.scrollHeight; 
}

function pruneMessages() { 
    if (state.messages.length > MAX_STORED_MESSAGES) {
        state.messages = state.messages.slice(-MAX_STORED_MESSAGES); 
    }
}

function refreshLanguageHint() { 
    const meta = languageMeta[languageSelect.value]; 
    languageHint.textContent = "当前语言：" + meta.label; 
}

function refreshVoiceHint() { 
    voiceHint.textContent = "当前语音：" + state.currentVoiceLabel; 
}

function sanitizeSpeechText(text) { 
    return String(text || "")
        .replace(/```[\s\S]*?```/g, " ")
        .replace(/`[^`]*`/g, " ")
        .replace(/https?:\/\/\S+/g, " ")
        .replace(/[\u{1F600}-\u{1F64F}\u{1F300}-\u{1F5FF}\u{1F680}-\u{1F6FF}\u{1F1E0}-\u{1F1FF}\u{2600}-\u{26FF}\u{2700}-\u{27BF}]/gu, " ")
        .replace(/[~^*_#=<>|\\/\[\]{}]/g, " ")
        .replace(/\s{2,}/g, " ")
        .trim(); 
}

async function readJsonSafely(res) { 
    const raw = await res.text(); 
    if (!raw) return {}; 
    try { 
        return JSON.parse(raw); 
    } catch { 
        return { message: raw }; 
    } 
}

function stopAudioPlayback() { 
    if (state.currentAudio) { 
        state.currentAudio.pause(); 
        state.currentAudio = null; 
    } 
    if (state.currentAudioUrl) { 
        URL.revokeObjectURL(state.currentAudioUrl); 
        state.currentAudioUrl = null; 
    } 
    state.isSpeaking = false;
}

function addMessage(role, content) { 
    state.messages.push({ role, content }); 
    pruneMessages(); 
    renderMessages(); 
}

function buildContextMessages() { 
    return state.messages.slice(-MAX_CONTEXT_MESSAGES); 
}

function resetConversation() { 
    stopAudioPlayback(); 
    state.messages = []; 
    renderMessages(); 
    setAvatar("idle", "待机中"); 
    networkStatus.textContent = "已连接本地 Ollama"; 
}

async function refreshTtsStatus() { 
    try { 
        const res = await fetch("/api/tts-status?language=" + encodeURIComponent(languageSelect.value)); 
        const data = await readJsonSafely(res); 
        if (!res.ok || !data.ready) { 
            state.currentVoiceLabel = data.voice ? "Edge-TTS · " + data.voice : "Edge-TTS 未就绪"; 
            refreshVoiceHint(); 
            networkStatus.textContent = data.message || "Edge-TTS 未就绪"; 
            return; 
        } 
        state.currentVoiceLabel = "Edge-TTS · " + data.voice; 
        refreshVoiceHint(); 
    } catch { 
        state.currentVoiceLabel = "Edge-TTS 状态未知"; 
        refreshVoiceHint(); 
    } 
}

async function speak(text) { 
    const cleanText = sanitizeSpeechText(text); 
    if (!state.ttsEnabled || !cleanText) { 
        setAvatar("idle", "待机中"); 
        return; 
    } 
    
    stopAudioPlayback(); 
    const meta = languageMeta[languageSelect.value]; 
    setAvatar("thinking", "正在合成语音"); 
    networkStatus.textContent = "语音合成中"; 
    
    try { 
        const res = await fetch("/api/tts", { 
            method: "POST", 
            headers: { "Content-Type": "application/json" }, 
            body: JSON.stringify({ 
                text: cleanText, 
                language: languageSelect.value 
            }) 
        }); 
        
        if (!res.ok) { 
            const err = await readJsonSafely(res); 
            throw new Error(err.message || "TTS 请求失败"); 
        } 
        
        const blob = await res.blob(); 
        const audioUrl = URL.createObjectURL(blob); 
        const audio = new Audio(audioUrl); 
        
        state.currentAudio = audio; 
        state.currentAudioUrl = audioUrl; 
        
        // 语音开始播放
        audio.onplay = () => { 
            setAvatar("speaking", meta.label + "播报中"); 
            networkStatus.textContent = "Edge-TTS 播放中"; 
        }; 
        
        // 语音播放结束
        audio.onended = () => { 
            stopAudioPlayback(); 
            setAvatar("idle", "待机中"); 
            networkStatus.textContent = "已连接本地 Ollama"; 
        }; 
        
        // 播放错误
        audio.onerror = () => { 
            stopAudioPlayback(); 
            setAvatar("idle", "语音播放失败"); 
            networkStatus.textContent = "语音播放失败"; 
        }; 
        
        await audio.play(); 
    } catch (error) { 
        setAvatar("idle", "语音不可用"); 
        networkStatus.textContent = "Edge-TTS 异常"; 
        addMessage("assistant", "语音播报失败：" + error.message); 
    } 
}

async function sendMessage(content) { 
    const trimmed = content.trim(); 
    if (!trimmed) return; 
    
    addMessage("user", trimmed); 
    inputEl.value = ""; 
    sendBtn.disabled = true; 
    networkStatus.textContent = "数字人思考中"; 
    setAvatar("thinking", "正在组织回答"); 
    
    try { 
        const res = await fetch("/api/chat", { 
            method: "POST", 
            headers: { "Content-Type": "application/json" }, 
            body: JSON.stringify({ 
                model: modelSelect.value, 
                language: languageSelect.value, 
                messages: buildContextMessages() 
            }) 
        }); 
        
        const data = await readJsonSafely(res); 
        if (!res.ok) throw new Error(data.message || "请求失败"); 
        
        const assistantMessage = data.message || "我这边暂时没组织出回答。"; 
        addMessage("assistant", assistantMessage); 
        networkStatus.textContent = "已连接本地 Ollama"; 
        
        // 自动播放语音回答
        await speak(assistantMessage); 
    } catch (error) { 
        addMessage("assistant", "连接失败：" + error.message); 
        networkStatus.textContent = "连接异常"; 
        setAvatar("idle", "连接异常"); 
    } finally { 
        sendBtn.disabled = false; 
    } 
}

function setupRecognition() { 
    const Recognition = window.SpeechRecognition || window.webkitSpeechRecognition; 
    if (!Recognition) { 
        listenBtn.disabled = true; 
        listenBtn.textContent = "当前浏览器不支持语音输入"; 
        return; 
    } 
    
    const recognition = new Recognition(); 
    recognition.continuous = false; 
    recognition.interimResults = true; 
    recognition.maxAlternatives = 1; 
    
    recognition.onstart = () => { 
        state.recognitionActive = true; 
        listenBtn.textContent = "正在听..."; 
        setAvatar("thinking", "正在听你说话"); 
    }; 
    
    recognition.onresult = (event) => { 
        const transcript = Array.from(event.results)
            .map(result => result[0].transcript)
            .join("");
        inputEl.value = transcript;
        
        // 如果是最终结果，自动发送
        if (event.results[0].isFinal) {
            setTimeout(() => {
                formEl.dispatchEvent(new Event('submit'));
            }, 300);
        }
    }; 
    
    recognition.onend = () => { 
        state.recognitionActive = false; 
        listenBtn.textContent = "语音输入"; 
        setAvatar("idle", "待机中"); 
    }; 
    
    recognition.onerror = () => { 
        state.recognitionActive = false; 
        listenBtn.textContent = "语音输入"; 
        setAvatar("idle", "语音输入失败"); 
    }; 
    
    state.recognition = recognition; 
}

// 事件监听
formEl.addEventListener("submit", (e) => { 
    e.preventDefault(); 
    sendMessage(inputEl.value); 
});

languageSelect.addEventListener("change", () => { 
    refreshLanguageHint(); 
    refreshTtsStatus(); 
    if (state.recognition) {
        state.recognition.lang = languageMeta[languageSelect.value].lang; 
    }
});

ttsToggle.addEventListener("click", () => { 
    state.ttsEnabled = !state.ttsEnabled; 
    ttsToggle.classList.toggle("active", state.ttsEnabled); 
    ttsToggle.textContent = state.ttsEnabled ? "语音已开" : "语音已关"; 
    if (!state.ttsEnabled) { 
        stopAudioPlayback(); 
        setAvatar("idle", "待机中"); 
        networkStatus.textContent = "已连接本地 Ollama"; 
    } 
});

listenBtn.addEventListener("click", () => { 
    if (!state.recognition || state.recognitionActive) return; 
    state.recognition.lang = languageMeta[languageSelect.value].lang; 
    try { 
        state.recognition.start(); 
    } catch { 
        state.recognitionActive = false; 
        setAvatar("idle", "语音输入失败"); 
    } 
});

clearChatBtn.addEventListener("click", resetConversation);

// 初始化
refreshLanguageHint(); 
refreshVoiceHint(); 
ttsToggle.classList.toggle("active", state.ttsEnabled); 
ttsToggle.textContent = state.ttsEnabled ? "语音已开" : "语音已关"; 
setupRecognition(); 
refreshTtsStatus(); 
renderMessages();



