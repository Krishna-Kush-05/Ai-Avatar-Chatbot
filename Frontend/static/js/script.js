// ============================================================
// script.js – Chat logic, streaming, TTS, voice recording
// ============================================================

// --- Immediately prevent form default to stop page reloads ---
document.addEventListener('DOMContentLoaded', () => {
    const form = document.getElementById('chat-form');
    if (form) {
        form.addEventListener('submit', (e) => {
            e.preventDefault();
            const input = document.getElementById('chat-input');
            const message = input ? input.value.trim() : '';
            if (!message) return;
            displayUserMessage(message);
            input.value = '';
            handleStream(message);
        });
    }

    // Record button
    const recordBtn = document.getElementById('recordButton');
    if (recordBtn) {
        recordBtn.addEventListener('click', handleRecord);
    }

    // Global Stop Audio & Avatar button
    const globalStopBtn = document.getElementById('global-stop-audio-btn');
    if (globalStopBtn) {
        globalStopBtn.addEventListener('click', () => {
            if (currentAudio && !currentAudio.paused) {
                currentAudio.pause();
                currentAudio.currentTime = 0;
            }
            window.isTalking = false;
            // Clear the TTS audio queue
            if (window.audioQueue) window.audioQueue.length = 0;
            window.isPlayingQueue = false;
        });
    }
});

// DOM Elements (grabbed after DOMContentLoaded via functions)
function getChatBox() { return document.getElementById('chat-box'); }
function getLoader() { return document.getElementById('loader'); }

// Speech & Recording variables
let mediaRecorder;
let audioChunks = [];
let isRecording = false;
let currentAudio = null;

// Configure marked for better rendering
if (window.marked) {
    marked.setOptions({
        breaks: true,
        gfm: true,
        headerIds: false,
        mangle: false
    });
}

// --- Sanitize and render markdown safely ---
function renderMarkdown(text) {
    if (!window.marked) return text;
    const rawHtml = marked.parse(text);
    // Use DOMPurify if available, otherwise use raw (marked has basic sanitize)
    if (window.DOMPurify) {
        return DOMPurify.sanitize(rawHtml, {
            ADD_TAGS: ['pre', 'code'],
            ADD_ATTR: ['class']
        });
    }
    return rawHtml;
}

// --- Function to display the USER's message bubble ---
function displayUserMessage(messageText) {
    const chatBox = getChatBox();
    if (!chatBox) return;

    const greeting = document.getElementById("greeting-message");
    if (greeting) {
        greeting.classList.add("fade-out");
        setTimeout(() => greeting.remove(), 300); // Fully remove from DOM after fade
    }

    const messageContainer = document.createElement('div');
    messageContainer.className = 'user-message-container';

    const messageContent = document.createElement('div');
    messageContent.className = 'user-message-content';
    messageContent.textContent = messageText;

    messageContainer.appendChild(messageContent);
    chatBox.appendChild(messageContainer);
    chatBox.scrollTop = chatBox.scrollHeight;
}

// --- Functions to manage the BOT's typing animation ---
function showTypingIndicator() {
    const chatBox = getChatBox();
    if (!chatBox) return;

    const indicatorContainer = document.createElement('div');
    indicatorContainer.className = 'typing-indicator-container';
    indicatorContainer.innerHTML = `
        <div class="typing-indicator">
            <span></span><span></span><span></span>
        </div>`;
    chatBox.appendChild(indicatorContainer);
    chatBox.scrollTop = chatBox.scrollHeight;
}

function removeTypingIndicator() {
    const chatBox = getChatBox();
    if (!chatBox) return;
    const indicator = chatBox.querySelector('.typing-indicator-container');
    if (indicator) indicator.remove();
}

// --- Avatar Thinking Animation ---
function startAvatarThinking() {
    const avatarCard = document.getElementById('avatar-card');
    if (avatarCard) avatarCard.classList.add('thinking');
}

function stopAvatarThinking() {
    const avatarCard = document.getElementById('avatar-card');
    if (avatarCard) avatarCard.classList.remove('thinking');
}

// --- Add copy buttons and syntax highlighting to code blocks ---
function polishCodeBlocks(container) {
    container.querySelectorAll('pre').forEach(pre => {
        const codeBlock = pre.querySelector('code');
        if (!codeBlock) return;
        if (pre.querySelector('.copy-code-btn')) return;

        const copyButton = document.createElement('button');
        copyButton.className = 'copy-code-btn';
        copyButton.textContent = 'Copy';
        copyButton.setAttribute('aria-label', 'Copy code to clipboard');
        copyButton.onclick = () => {
            navigator.clipboard.writeText(codeBlock.innerText).then(() => {
                copyButton.textContent = 'Copied!';
                setTimeout(() => { copyButton.textContent = 'Copy'; }, 2000);
            });
        };
        pre.appendChild(copyButton);
    });

    // Apply syntax highlighting
    if (window.hljs) hljs.highlightAll();
}

// --- Function to create the main container for the BOT's response ---
function createBotResponseContainer() {
    const chatBox = getChatBox();
    if (!chatBox) return document.createElement('div');

    const responseContainer = document.createElement('div');
    responseContainer.className = 'bot-response-container';

    const contentWrapper = document.createElement('div');
    contentWrapper.className = 'bot-response-wrapper';

    const contentDiv = document.createElement('div');
    contentDiv.className = 'bot-response-content';

    const timestampDiv = document.createElement('div');
    timestampDiv.className = 'bot-response-timestamp';
    timestampDiv.textContent = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

    contentWrapper.appendChild(contentDiv);
    contentWrapper.appendChild(timestampDiv);
    responseContainer.appendChild(contentWrapper);
    chatBox.appendChild(responseContainer);

    return contentDiv;
}

// --- Global Abort Controller for Stopping Streams ---
let currentAborter = null;

// --- Main Chat Logic (Streaming via fetch + SSE) ---
function handleStream(prompt) {
    showTypingIndicator();
    startAvatarThinking();

    // Reset abort controller for new stream
    if (currentAborter) currentAborter.abort();
    currentAborter = new AbortController();

    // UI Button swapping
    const sendBtn = document.getElementById('sendButton');
    const stopBtn = document.getElementById('stopButton');
    if (sendBtn && stopBtn) {
        sendBtn.style.display = 'none';
        stopBtn.style.display = 'grid';

        // Ensure old listeners aren't piling up
        stopBtn.onclick = () => {
            if (currentAborter) {
                currentAborter.abort();
                currentAborter = null;
            }
        };
    }

    let fullReply = "";
    let spokenLength = 0;
    let replyTextElement = null;

    // Use standard fetch with ReadableStream instead of fetchEventSource
    fetch("/stream_response", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question: prompt }),
        signal: currentAborter.signal
    })
        .then(response => {
            if (!response.ok) throw new Error("Server error: " + response.status);

            const reader = response.body.getReader();
            const decoder = new TextDecoder();
            let buffer = "";

            function processStream() {
                return reader.read().then(({ done, value }) => {
                    if (done) {
                        // Stream complete
                        if (replyTextElement) {
                            polishCodeBlocks(replyTextElement);
                            // Render Math formatting
                            if (window.MathJax) {
                                MathJax.typesetPromise([replyTextElement]).catch(err => console.error(err));
                            }
                            // Speak any remaining text that wasn't chunked by a sentence terminator
                            const remainder = fullReply.substring(spokenLength)
                                .replace(/```[\s\S]*?```/g, "Code block provided.")
                                .replace(/`[^`]+`/g, "")
                                .replace(/[#*_~>\-|]/g, "")
                                .trim();
                            if (remainder) speak(remainder);
                        }
                        // Reset Buttons
                        if (sendBtn && stopBtn) {
                            stopBtn.style.display = 'none';
                            sendBtn.style.display = 'grid';
                        }
                        currentAborter = null;
                        return;
                    }

                    buffer += decoder.decode(value, { stream: true });

                    // Process complete SSE events in the buffer
                    const lines = buffer.split("\n");
                    buffer = lines.pop(); // Keep incomplete line in buffer

                    let currentEventType = "";
                    for (const line of lines) {
                        // Track the event type from "event: token" / "event: final_response" lines
                        if (line.startsWith("event: ")) {
                            currentEventType = line.slice(7).trim();
                            continue;
                        }

                        if (line.startsWith("data: ")) {
                            const dataStr = line.slice(6).trim();
                            if (!dataStr) continue;

                            try {
                                const data = JSON.parse(dataStr);
                                const textChunk = data.text || "";

                                // ── FIX: double-response bug ─────────────────────────
                                // The backend emits every character as event:token,
                                // then repeats the FULL text as event:final_response.
                                // We must SKIP final_response if we already have tokens,
                                // and only use it as a fallback if the stream had no tokens.
                                if (currentEventType === "final_response") {
                                    if (fullReply.length === 0) {
                                        // No tokens received yet — use final_response as the full reply
                                        if (replyTextElement === null) {
                                            removeTypingIndicator();
                                            stopAvatarThinking();
                                            replyTextElement = createBotResponseContainer();
                                        }
                                        fullReply = textChunk;
                                        replyTextElement.innerHTML = renderMarkdown(fullReply);
                                    }
                                    // If we already have tokens, do NOT append final_response
                                    // (it would duplicate the entire response)
                                    continue;
                                }

                                // For "token" events (or untyped): accumulate normally
                                if (replyTextElement === null) {
                                    removeTypingIndicator();
                                    stopAvatarThinking();
                                    replyTextElement = createBotResponseContainer();
                                }

                                fullReply += textChunk;
                                replyTextElement.innerHTML = renderMarkdown(fullReply);

                                // --- Chunkwise Audio Streaming ---
                                // Detect sentence ends and queue them dynamically
                                let newText = fullReply.substring(spokenLength);
                                let match = newText.match(/(?:[.!\?\n])\s+/g);
                                if (match) {
                                    // Find the last match so we chunk as much complete thought as possible
                                    let lastMatch = match[match.length - 1];
                                    let splitIndex = newText.lastIndexOf(lastMatch) + lastMatch.length;
                                    let sentence = newText.substring(0, splitIndex);
                                    spokenLength += splitIndex;

                                    let speechChunk = sentence
                                        .replace(/```[\s\S]*?(```|$)/g, " ")
                                        .replace(/`[^`]+`/g, "")
                                        .replace(/[#*_~>\-|]/g, "")
                                        .trim();
                                    if (speechChunk) speak(speechChunk);
                                }
                            } catch (e) {
                                // Not valid JSON — skip
                            }
                        }
                    }

                    const chatBox = getChatBox();
                    if (chatBox) chatBox.scrollTop = chatBox.scrollHeight;

                    return processStream();
                });
            }

            return processStream();
        })
        .catch(err => {
            // Reset Buttons
            if (sendBtn && stopBtn) {
                stopBtn.style.display = 'none';
                sendBtn.style.display = 'grid';
            }

            if (err.name === 'AbortError') {
                console.log("Stream stopped by user.");
                if (replyTextElement) {
                    polishCodeBlocks(replyTextElement); // Formatting whatever was received
                    // Append stopped tag
                    const stoppedTag = document.createElement('span');
                    stoppedTag.style.cssText = "font-size: 0.75rem; color: #ef4444; font-weight: 600; margin-left: 0.5rem; display: inline-block;";
                    stoppedTag.textContent = "[ Stopped Generating ]";
                    replyTextElement.appendChild(stoppedTag);
                }
                removeTypingIndicator();
                stopAvatarThinking();
                return;
            }

            console.error("Stream error:", err);
            removeTypingIndicator();
            stopAvatarThinking();
            const errorElement = createBotResponseContainer();
            errorElement.innerHTML = `
            <div class="chat-error" style="color: #dc2626; background: #fef2f2; padding: 1rem; border-radius: 8px; border: 1px solid #fca5a5; margin-top: 0.5rem;">
                <strong style="display: flex; align-items: center; gap: 0.5rem; margin-bottom: 0.5rem;">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width: 18px; height: 18px;">
                        <circle cx="12" cy="12" r="10"></circle>
                        <line x1="12" y1="8" x2="12" y2="12"></line>
                        <line x1="12" y1="16" x2="12.01" y2="16"></line>
                    </svg>
                    Oops! Connection Error
                </strong>
                <p style="margin: 0; font-size: 0.9rem; color: #991b1b;">I'm having trouble connecting to my brain right now. Please wait a moment and try asking again.</p>
            </div>`;
        });
}

// --- Voice Recording ---
async function sendAudioToBackend(audioBlob) {
    const loader = getLoader();
    if (loader) loader.style.display = 'block';
    const formData = new FormData();
    formData.append('audio', audioBlob, 'recording.wav');
    try {
        const response = await fetch('/transcribe', { method: 'POST', body: formData });
        const data = await response.json();
        const transcribedText = data.transcribedText || "Transcription failed";
        displayUserMessage(transcribedText);
        handleStream(transcribedText);
    } catch (error) {
        console.error('Error during transcription:', error);
        const errElement = createBotResponseContainer();
        errElement.textContent = "Error: Could not transcribe audio.";
    } finally {
        if (loader) loader.style.display = 'none';
    }
}

async function handleRecord() {
    const recordButton = document.getElementById('recordButton');
    if (!recordButton) return;

    if (!isRecording) {
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            mediaRecorder = new MediaRecorder(stream);
            audioChunks = [];
            mediaRecorder.ondataavailable = event => audioChunks.push(event.data);
            mediaRecorder.onstop = () => {
                const audioBlob = new Blob(audioChunks, { type: 'audio/wav' });
                sendAudioToBackend(audioBlob);
                stream.getTracks().forEach(track => track.stop());
            };
            mediaRecorder.start();
            recordButton.classList.add('recording');
            recordButton.setAttribute('aria-label', 'Stop recording');
            isRecording = true;
        } catch (err) {
            console.error("Mic access error:", err);
            const errElement = createBotResponseContainer();
            errElement.textContent = "Microphone access denied.";
        }
    } else {
        mediaRecorder.stop();
        recordButton.classList.remove('recording');
        recordButton.setAttribute('aria-label', 'Start voice recording');
        isRecording = false;
    }
}

// --- Text-to-Speech with Avatar Integration ---
// window.isTalking is the shared flag read by avatar.js to drive lip-sync.
window.isTalking = false;
window.audioQueue = [];
window.isPlayingQueue = false;

function playNextInQueue() {
    if (window.audioQueue.length === 0) {
        window.isPlayingQueue = false;
        window.isTalking = false;
        return;
    }
    window.isPlayingQueue = true;
    window.isTalking = true;

    let audData = window.audioQueue.shift();
    currentAudio = new Audio(audData);

    currentAudio.onplay = () => { window.isTalking = true; };
    currentAudio.onended = () => { window.isTalking = false; playNextInQueue(); };
    currentAudio.onpause = () => { window.isTalking = false; };
    currentAudio.onerror = () => { window.isTalking = false; playNextInQueue(); };

    if (window.avatarSpeak) {
        window.avatarSpeak(currentAudio);
    }
    currentAudio.play().catch(err => {
        console.error("Audio play error:", err);
        playNextInQueue();
    });
}

function speak(text) {
    if (!text.trim()) return;

    fetch("/speak", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text })
    })
        .then(res => res.json())
        .then(data => {
            if (data.audio_url) {
                window.audioQueue.push(data.audio_url);
                if (!window.isPlayingQueue) {
                    playNextInQueue();
                }
            }
        })
        .catch(err => {
            console.error("TTS Error:", err);
        });
}
