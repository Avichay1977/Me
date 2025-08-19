const $ = (s)=>document.querySelector(s);
const $state = $("#state");
const $toggle = $("#toggle");
const $duck = $("#duck");
const $voice = $("#voice");

async function refreshState() {
  return new Promise((resolve) => {
    chrome.runtime.sendMessage({ type: "GET_STATE" }, (resp)=>{
      const on = !!resp?.on;
      $state.textContent = on ? "פועל" : "כבוי";
      $state.className = on ? "ok" : "off";
      $toggle.textContent = on ? "Stop" : "Start";
      resolve(on);
    });
  });
}

$toggle.addEventListener("click", ()=> chrome.runtime.sendMessage({ type: "TOGGLE" }));
$duck.addEventListener("input", ()=> chrome.runtime.sendMessage({ type: "SET_DUCK", value: Number($duck.value) }));
$voice.addEventListener("change", ()=> {
  const opt = $voice.selectedOptions[0];
  chrome.runtime.sendMessage({ type: "SET_VOICE", name: opt?.dataset?.name || "", lang: opt?.dataset?.lang || "" });
});

function populateVoices() {
  if (!("speechSynthesis" in window)) return;
  const voices = speechSynthesis.getVoices();
  $voice.innerHTML = "";
  const heVoices = voices.filter(v => (v.lang||"").toLowerCase().startsWith("he"));
  const list = heVoices.length ? heVoices : voices;
  for (const v of list) {
    const o = document.createElement("option");
    o.textContent = v.name + (v.lang ? ` (${v.lang})` : "");
    o.value = v.name;
    o.dataset.name = v.name;
    o.dataset.lang = v.lang || "";
    $voice.appendChild(o);
  }
}

speechSynthesis.onvoiceschanged = populateVoices;

chrome.runtime.onMessage.addListener((msg)=>{
  if (msg?.type === "STATE_CHANGED") refreshState();
});

populateVoices();
refreshState();
