import { fetchEventSource } from 'https://unpkg.com/@microsoft/fetch-event-source@2.0.1/lib/esm/index.js';

// DOM Elements
const chatBox = document.getElementById('chat-box');
const chatForm = document.getElementById("chat-form");
const chatInput = document.getElementById("chat-input");
const recordButton = document.getElementById('recordButton');
const loader = document.getElementById('loader');

// Speech & Recording variables
let mediaRecorder;
let audioChunks = [];
let isRecording = false;
let currentAudio = null;

// --- Function to display the USER's message bubble ---
function displayUserMessage(messageText) {
    document.getElementById("greeting-message")?.classList.add("fade-out");

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
    const indicator = chatBox.querySelector('.typing-indicator-container');
    if (indicator) {
        indicator.remove();
    }
}

// --- Function to create the main container for the BOT's response ---
function createBotResponseContainer() {
    const responseContainer = document.createElement('div');
    responseContainer.className = 'bot-response-container';

    const contentDiv = document.createElement('div');
    contentDiv.className = 'bot-response-content';

    const timestampDiv = document.createElement('div');
    timestampDiv.className = 'bot-response-timestamp';
    timestampDiv.textContent = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

    responseContainer.appendChild(contentDiv);
    responseContainer.appendChild(timestampDiv);
    chatBox.appendChild(responseContainer);

    return contentDiv; // Return the element where text will be streamed
}


// --- Main Chat Logic (Streaming) ---
function handleStream(prompt) {
    showTypingIndicator();

    // These variables are reset for each new message stream
    let fullReply = "";
    let replyTextElement = null;

    fetchEventSource("/stream_response", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question: prompt }),
        onopen: (res) => {
            if (!res.ok) {
                throw new Error("Stream connection failed");
            }
        },
        onmessage(ev) {
            // Create the bot's message bubble on the first message
            if (replyTextElement === null) {
                removeTypingIndicator();
                replyTextElement = createBotResponseContainer();
            }

            try {
                // The data from your backend is a JSON string, so we must parse it
                const data = JSON.parse(ev.data);
                const textChunk = data.text;

                // Check which event was sent from the backend
                if (ev.event === "token") {
                    // If it's a token, append it for the "typing" effect
                    fullReply += textChunk;
                    // Render the accumulated text as HTML on every token
                    replyTextElement.innerHTML = marked.parse(fullReply);

                } else if (ev.event === "final_response") {
                    // The final response event is now used for "finishing touches"
                    fullReply = textChunk; 
                    replyTextElement.innerHTML = marked.parse(fullReply); // Final render for consistency

                    // 1. Add copy buttons to all code blocks
                    replyTextElement.querySelectorAll('pre').forEach(pre => {
                        const codeBlock = pre.querySelector('code');
                        if (!codeBlock) return;
                        
                        // Avoid adding a duplicate button
                        if (pre.querySelector('.copy-code-btn')) return;

                        const copyButton = document.createElement('button');
                        copyButton.className = 'copy-code-btn';
                        copyButton.textContent = 'Copy';
                        copyButton.onclick = () => {
                            navigator.clipboard.writeText(codeBlock.innerText).then(() => {
                                copyButton.textContent = 'Copied!';
                                setTimeout(() => { copyButton.textContent = 'Copy'; }, 2000);
                            });
                        };
                        pre.appendChild(copyButton);
                    });

                    // 2. Apply syntax highlighting
                    hljs.highlightAll();

                    // 3. Trigger text-to-speech (replace code blocks with a placeholder message)
                    const textForSpeech = fullReply.replace(/```[\s\S]*?```/g, "Code block provided.");
                    speak(textForSpeech);
                }
            } catch (e) {
                console.error("Failed to parse stream data:", ev.data, e);
                replyTextElement.textContent = fullReply + " [Error parsing stream]";
            }

            chatBox.scrollTop = chatBox.scrollHeight;
        },
        onerror(err) {
            console.error("Stream error:", err);
            removeTypingIndicator();
            const errorElement = replyTextElement || createBotResponseContainer();
            errorElement.innerHTML = "⚠ An error occurred. Please check the console and try again.";
        },
    });
}


// --- Event Listeners and Voice Recording ---
chatForm.addEventListener("submit", (e) => {
    e.preventDefault();
    const message = chatInput.value.trim();
    if (!message) return;
    displayUserMessage(message);
    chatInput.value = "";
    handleStream(message);
});

async function sendAudioToBackend(audioBlob) {
    loader.style.display = 'block';
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
        loader.style.display = 'none';
    }
}

recordButton.addEventListener('click', async () => {
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
            recordButton.textContent = '🛑 Stop';
            isRecording = true;
        } catch (err) {
            console.error("Mic access error:", err);
            const errElement = createBotResponseContainer();
            errElement.textContent = "Microphone access denied.";
        }
    } else {
        mediaRecorder.stop();
        recordButton.textContent = '🎤 Speak';
        isRecording = false;
    }
});

function speak(text) {
    if (currentAudio && !currentAudio.paused) {
        currentAudio.pause();
    }
    fetch("/speak", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text })
    })
    .then(res => res.json())
    .then(data => {
        if (data.audio_url) {
            currentAudio = new Audio(data.audio_url);
            currentAudio.play();
        }
    })
    .catch(err => console.error("TTS Error:", err));
}