const documentElement = document.documentElement;

documentElement.dataset.bennoReady = "true";

const chatPanel = document.querySelector("[data-chat-panel]");
const copyButton = document.querySelector("[data-copy-button]");
const copySource = document.querySelector("[data-copy-source]");
const mainNav = document.querySelector("[data-main-nav]");
const navToggle = document.querySelector("[data-nav-toggle]");
const reportForm = document.querySelector("[data-report-form]");
const voiceCancelButton = document.querySelector("[data-voice-cancel]");
const voiceControls = document.querySelector("[data-voice-controls]");
const voiceStartButton = document.querySelector("[data-voice-start]");
const voiceStatus = document.querySelector("[data-voice-status]");
const voiceStopButton = document.querySelector("[data-voice-stop]");

const voiceState = {
  active: false,
  analyser: null,
  audioContext: null,
  chunks: [],
  levelTimer: null,
  maxTimer: null,
  mediaRecorder: null,
  silenceStartedAt: null,
  startedAt: null,
  stream: null,
};

const maxRecordingMs = 24000;
const maxPlaybackWaitMs = 45000;
const minimumRecordingMs = 1200;
const silenceCloseMs = 1400;
const silenceThreshold = 0.018;

function voiceStopStorageKey() {
  if (!voiceControls?.dataset.voiceChatId) {
    return null;
  }

  return `benno.voice.autostart.stopped.${voiceControls.dataset.voiceChatId}`;
}

function voiceAutostartIsStopped() {
  const storageKey = voiceStopStorageKey();
  return Boolean(storageKey && sessionStorage.getItem(storageKey));
}

function setVoiceAutostartStopped(isStopped) {
  const storageKey = voiceStopStorageKey();
  if (!storageKey) {
    return;
  }

  if (isStopped) {
    sessionStorage.setItem(storageKey, "true");
  } else {
    sessionStorage.removeItem(storageKey);
  }
}

function scrollChatToBottom() {
  if (!chatPanel) {
    return;
  }

  chatPanel.scrollTop = chatPanel.scrollHeight;
}

function addChatMessage(sender, text, extraClass = "", options = {}) {
  if (!chatPanel) {
    return;
  }

  const article = document.createElement("article");
  article.className = `chat-message chat-message--${sender} ${extraClass}`.trim();
  if (options.messageId) {
    article.dataset.messageId = options.messageId;
  }
  if (sender === "assistant" && (options.messageId || options.speechUrl)) {
    article.dataset.assistantMessage = "";
  }
  if (options.speechUrl) {
    article.dataset.speechUrl = options.speechUrl;
  }

  const label = document.createElement("span");
  label.textContent = sender === "assistant" ? "BENNO" : "Du";

  const paragraph = document.createElement("p");
  paragraph.textContent = text;

  article.append(label, paragraph);
  chatPanel.append(article);
  scrollChatToBottom();
}

function removeTypingMessages() {
  document
    .querySelectorAll(".chat-message--typing")
    .forEach((message) => message.remove());
}

function latestAssistantMessage() {
  const messages = document.querySelectorAll("[data-assistant-message]");
  return messages[messages.length - 1] || null;
}

function setVoiceStatus(message) {
  if (voiceStatus) {
    voiceStatus.textContent = message;
  }
}

function setVoiceControlsRecording(isRecording) {
  if (voiceStartButton) {
    voiceStartButton.hidden = isRecording || voiceState.active;
  }
  if (voiceStopButton) {
    voiceStopButton.hidden = !isRecording;
  }
  if (voiceCancelButton) {
    voiceCancelButton.hidden = !voiceState.active;
  }
}

function toggleNavigation() {
  if (!mainNav || !navToggle) {
    return;
  }

  const isOpen = mainNav.classList.toggle("is-open");
  navToggle.setAttribute("aria-expanded", isOpen.toString());
}

async function copySetupLink() {
  if (!copySource || !copyButton) {
    return;
  }

  copySource.select();
  copySource.setSelectionRange(0, copySource.value.length);

  try {
    await navigator.clipboard.writeText(copySource.value);
  } catch (_error) {
    document.execCommand("copy");
  }

  copyButton.textContent = "Kopiert";
}

async function startVoiceMode(options = {}) {
  if (!voiceControls) {
    return;
  }

  if (options.auto && voiceAutostartIsStopped()) {
    return;
  }
  if (!options.auto) {
    setVoiceAutostartStopped(false);
  }

  voiceState.active = true;
  setVoiceControlsRecording(false);
  setVoiceStatus("BENNO bereitet die Sprachausgabe vor.");

  try {
    await playLatestAssistantSpeech();
    if (voiceState.active) {
      await startVoiceRecording();
    }
  } catch (error) {
    stopVoiceMode();
    if (options.auto) {
      setVoiceAutostartStopped(true);
      setVoiceStatus(
        "Automatischer Sprachstart wurde blockiert. Bitte starte den Sprachmodus einmal manuell.",
      );
    } else {
      setVoiceStatus(error.message || "Sprachmodus konnte nicht gestartet werden.");
    }
  }
}

function stopVoiceMode() {
  voiceState.active = false;
  stopActiveRecording();
  stopMicrophoneStream();
  setVoiceControlsRecording(false);
  if (voiceStartButton) {
    voiceStartButton.hidden = false;
  }
}

async function ensureMicrophoneStream() {
  if (voiceState.stream) {
    return voiceState.stream;
  }

  if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
    throw new Error("Dein Browser erlaubt hier keine Mikrofonaufnahme.");
  }

  voiceState.stream = await navigator.mediaDevices.getUserMedia({ audio: true });
  return voiceState.stream;
}

async function playLatestAssistantSpeech() {
  const message = latestAssistantMessage();
  if (!message || !message.dataset.speechUrl) {
    return;
  }

  setVoiceStatus("BENNO bereitet die Sprachausgabe vor.");
  const response = await fetch(message.dataset.speechUrl, { method: "POST" });
  if (!response.ok) {
    throw new Error("Sprachausgabe ist nicht verfügbar.");
  }

  const audioBlob = await response.blob();
  setVoiceStatus("BENNO spricht.");
  await playAudioBlob(audioBlob);
}

async function playAudioBlob(audioBlob) {
  const audioUrl = URL.createObjectURL(audioBlob);
  const audio = new Audio(audioUrl);

  try {
    await audio.play();
    await new Promise((resolve) => {
      const finish = () => {
        window.clearTimeout(playbackTimer);
        resolve();
      };
      const playbackTimer = window.setTimeout(finish, maxPlaybackWaitMs);

      audio.addEventListener("error", finish, { once: true });
      audio.addEventListener("ended", finish, { once: true });
    });
  } finally {
    URL.revokeObjectURL(audioUrl);
  }
}

async function playBase64Audio(audioBase64, mimetype) {
  if (!audioBase64) {
    return;
  }

  const byteCharacters = atob(audioBase64);
  const byteNumbers = Array.from(byteCharacters, (character) =>
    character.charCodeAt(0),
  );
  const audioBlob = new Blob([new Uint8Array(byteNumbers)], {
    type: mimetype || "audio/wav",
  });
  await playAudioBlob(audioBlob);
}

async function startVoiceRecording() {
  const stream = await ensureMicrophoneStream();
  voiceState.chunks = [];
  voiceState.mediaRecorder = new MediaRecorder(stream);
  voiceState.startedAt = Date.now();
  voiceState.silenceStartedAt = null;

  voiceState.mediaRecorder.addEventListener("dataavailable", (event) => {
    if (event.data.size > 0) {
      voiceState.chunks.push(event.data);
    }
  });
  voiceState.mediaRecorder.addEventListener("stop", submitVoiceRecording, {
    once: true,
  });

  prepareAudioAnalyser(stream);
  voiceState.mediaRecorder.start();
  voiceState.levelTimer = window.setInterval(checkVoiceLevel, 160);
  voiceState.maxTimer = window.setTimeout(stopActiveRecording, maxRecordingMs);
  setVoiceControlsRecording(true);
  setVoiceStatus("Ich höre zu. Sprich deine Antwort.");
}

function prepareAudioAnalyser(stream) {
  if (!voiceState.audioContext) {
    voiceState.audioContext = new AudioContext();
  }

  const source = voiceState.audioContext.createMediaStreamSource(stream);
  voiceState.analyser = voiceState.audioContext.createAnalyser();
  voiceState.analyser.fftSize = 1024;
  source.connect(voiceState.analyser);
}

function checkVoiceLevel() {
  if (!voiceState.analyser || !voiceState.startedAt) {
    return;
  }

  const sampleBuffer = new Uint8Array(voiceState.analyser.fftSize);
  voiceState.analyser.getByteTimeDomainData(sampleBuffer);
  const recordingAge = Date.now() - voiceState.startedAt;
  if (recordingAge < minimumRecordingMs) {
    return;
  }

  updateSilenceState(rmsVolume(sampleBuffer));
}

function updateSilenceState(volume) {
  if (volume < silenceThreshold) {
    voiceState.silenceStartedAt ||= Date.now();
  } else {
    voiceState.silenceStartedAt = null;
  }

  if (
    voiceState.silenceStartedAt &&
    Date.now() - voiceState.silenceStartedAt > silenceCloseMs
  ) {
    stopActiveRecording();
  }
}

function rmsVolume(sampleBuffer) {
  const sum = sampleBuffer.reduce((total, value) => {
    const normalized = (value - 128) / 128;
    return total + normalized * normalized;
  }, 0);
  return Math.sqrt(sum / sampleBuffer.length);
}

function stopActiveRecording() {
  if (
    voiceState.mediaRecorder &&
    voiceState.mediaRecorder.state !== "inactive"
  ) {
    voiceState.mediaRecorder.stop();
  }
  clearVoiceTimers();
  setVoiceControlsRecording(false);
}

function clearVoiceTimers() {
  window.clearInterval(voiceState.levelTimer);
  window.clearTimeout(voiceState.maxTimer);
  voiceState.levelTimer = null;
  voiceState.maxTimer = null;
}

function stopMicrophoneStream() {
  if (voiceState.stream) {
    voiceState.stream.getTracks().forEach((track) => track.stop());
  }
  voiceState.stream = null;
}

async function submitVoiceRecording() {
  clearVoiceTimers();
  if (!voiceState.active || voiceState.chunks.length === 0) {
    return;
  }

  setVoiceStatus("BENNO transkribiert und analysiert.");
  addChatMessage("assistant", "BENNO transkribiert", "chat-message--typing");

  const audioBlob = new Blob(voiceState.chunks, {
    type: voiceState.mediaRecorder?.mimeType || "audio/webm",
  });
  const formData = new FormData();
  formData.append("audio", audioBlob, "recording.webm");

  try {
    const response = await fetch(voiceControls.dataset.voiceTurnUrl, {
      method: "POST",
      body: formData,
    });
    const payload = await response.json();
    removeTypingMessages();
    if (!response.ok) {
      throw new Error(payload.error || "Sprachverarbeitung fehlgeschlagen.");
    }

    addChatMessage("user", payload.transcript);
    addChatMessage("assistant", payload.assistant_reply, "", {
      messageId: payload.assistant_message_id,
      speechUrl: payload.assistant_speech_url,
    });
    if (payload.tts_error || !payload.audio) {
      stopVoiceMode();
      setVoiceStatus(
        payload.tts_error ||
          "Sprachausgabe ist nicht verfügbar. Bitte nutze die Texteingabe.",
      );
      return;
    }
    setVoiceStatus("BENNO antwortet.");
    await playBase64Audio(payload.audio, payload.audio_mime_type);
    await continueVoiceMode(payload);
  } catch (error) {
    removeTypingMessages();
    stopVoiceMode();
    setVoiceStatus(error.message || "Sprachverarbeitung fehlgeschlagen.");
  }
}

async function continueVoiceMode(payload) {
  if (payload.ready_for_review || payload.chat_status !== "in_progress") {
    window.location.reload();
    return;
  }
  if (voiceState.active) {
    await startVoiceRecording();
  }
}

function submitReportMessage(event) {
  event.preventDefault();

  const formData = new FormData(reportForm);
  const messageText = formData.get("message") || "";
  if (!messageText.toString().trim()) {
    return;
  }

  const textarea = reportForm.querySelector("textarea");
  const button = reportForm.querySelector("button[type='submit']");
  addChatMessage("user", messageText.toString(), "chat-message--pending");
  addChatMessage("assistant", "BENNO analysiert", "chat-message--typing");
  reportForm.classList.add("is-submitting");
  reportForm.setAttribute("aria-busy", "true");

  if (textarea) {
    textarea.readOnly = true;
  }
  if (button) {
    button.disabled = true;
    button.setAttribute("aria-label", "BENNO analysiert");
  }

  window.setTimeout(() => {
    reportForm.submit();
  }, 450);
}

scrollChatToBottom();

if (navToggle) {
  navToggle.addEventListener("click", toggleNavigation);
}

if (reportForm) {
  reportForm.addEventListener("submit", submitReportMessage);
}

if (voiceStartButton) {
  voiceStartButton.addEventListener("click", startVoiceMode);
}

if (voiceStopButton) {
  voiceStopButton.addEventListener("click", stopActiveRecording);
}

if (voiceCancelButton) {
  voiceCancelButton.addEventListener("click", () => {
    setVoiceAutostartStopped(true);
    stopVoiceMode();
    setVoiceStatus("Sprachmodus beendet.");
  });
}

if (copyButton) {
  copyButton.addEventListener("click", copySetupLink);
}

if (voiceControls?.dataset.voiceAutoStart === "true") {
  window.setTimeout(() => startVoiceMode({ auto: true }), 0);
}
