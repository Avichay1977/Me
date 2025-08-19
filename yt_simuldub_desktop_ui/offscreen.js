// Offscreen - Desktop UI Demo
let ctx, source, stream, gain;
let currentVoice = null;

async function startDemo(streamId) {
  stream = await navigator.mediaDevices.getUserMedia({
    audio: {
      mandatory: {
        chromeMediaSource: 'tab',
        chromeMediaSourceId: streamId
      }
    }
  });
  ctx = new (window.AudioContext || window.webkitAudioContext)();
  source = ctx.createMediaStreamSource(stream);
  gain = ctx.createGain();
  gain.gain.value = 0.0; // don't re-play captured audio
  source.connect(gain).connect(ctx.destination);

  // Demo TTS line
  speakHebrew("דמו פועל במחשב: ניתן לכוון קול, ולהנמיך את הסרטון.");
}

function stopDemo() {
  try { stream?.getTracks().forEach(t => t.stop()); } catch {}
  try { ctx?.close(); } catch {}
  stream = null;
  ctx = null;
}

function speakHebrew(text) {
  if (!('speechSynthesis' in window)) return;
  const u = new SpeechSynthesisUtterance(text);
  u.lang = 'he-IL';
  if (currentVoice) u.voice = currentVoice;
  speechSynthesis.speak(u);
}

function pickVoice(name, lang) {
  const voices = speechSynthesis.getVoices();
  let chosen = null;
  if (name) chosen = voices.find(v => v.name === name);
  if (!chosen && lang) chosen = voices.find(v => (v.lang||'').toLowerCase().startsWith(lang.toLowerCase()));
  if (!chosen) chosen = voices.find(v => (v.lang||'').toLowerCase().startsWith('he'));
  currentVoice = chosen || null;
}

speechSynthesis.onvoiceschanged = () => {
  // keep currentVoice aligned if voices load late
};

chrome.runtime.onMessage.addListener((msg) => {
  if (msg?.type === "START_DEMO") startDemo(msg.streamId);
  if (msg?.type === "STOP_DEMO") stopDemo();
  if (msg?.type === "SET_VOICE") pickVoice(msg.name, msg.lang);
});
