// Content script - YouTube ducking + set level
let video;

function findVideo() {
  video = document.querySelector('video');
  return !!video;
}

function setVol(x) {
  if (video || findVideo()) video.volume = Math.max(0, Math.min(1, x));
}

chrome.runtime.onMessage.addListener((msg) => {
  if (msg?.type === "DUCK_ON") setVol(0.25);
  if (msg?.type === "DUCK_OFF") setVol(1.0);
  if (msg?.type === "SET_DUCK") setVol(msg.value);
});
