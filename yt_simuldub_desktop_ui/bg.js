// Background service worker (MV3) - Desktop UI Demo
let isOnByTab = new Map();

chrome.runtime.onMessage.addListener(async (msg, sender, sendResponse) => {
  if (msg?.type === "GET_STATE") {
    const [tab] = await chrome.tabs.query({active:true, currentWindow:true});
    const on = isOnByTab.get(tab?.id) || false;
    sendResponse({ on });
    return true;
  }

  if (msg?.type === "TOGGLE") {
    const [tab] = await chrome.tabs.query({active:true, currentWindow:true});
    if (!tab || !tab.id) return;

    const currentlyOn = isOnByTab.get(tab.id) || false;
    if (!currentlyOn) {
      // Ensure content.js is present
      try {
        await chrome.scripting.executeScript({ target: { tabId: tab.id }, files: ["content.js"] });
      } catch {}
      // Create offscreen if needed
      if (!(await chrome.offscreen.hasDocument?.())) {
        await chrome.offscreen.createDocument({
          url: "offscreen.html",
          reasons: ["AUDIO_PLAYBACK", "AUDIO_CAPTURE"],
          justification: "SimulDub Desktop UI Demo"
        });
      }
      // Get stream id
      const streamId = await new Promise((resolve, reject) => {
        chrome.tabCapture.getMediaStreamId({ consumerTabId: tab.id }, id => {
          if (id) resolve(id);
          else reject(chrome.runtime.lastError);
        });
      });
      // Start
      await chrome.tabs.sendMessage(tab.id, { type: "DUCK_ON" });
      await chrome.runtime.sendMessage({ type: "START_DEMO", streamId, tabId: tab.id });
      isOnByTab.set(tab.id, true);
      await chrome.action.setBadgeText({ text: "ON", tabId: tab.id });
    } else {
      // Stop
      await chrome.runtime.sendMessage({ type: "STOP_DEMO" });
      try { await chrome.tabs.sendMessage(tab.id, { type: "DUCK_OFF" }); } catch {}
      isOnByTab.set(tab.id, false);
      await chrome.action.setBadgeText({ text: "", tabId: tab.id });
    }
    // Update popup
    chrome.runtime.sendMessage({ type: "STATE_CHANGED" });
  }

  if (msg?.type === "SET_DUCK") {
    const [tab] = await chrome.tabs.query({active:true, currentWindow:true});
    if (tab?.id) {
      await chrome.tabs.sendMessage(tab.id, { type: "SET_DUCK", value: msg.value });
    }
  }

  if (msg?.type === "SET_VOICE") {
    // Forward to offscreen
    await chrome.runtime.sendMessage({ type: "SET_VOICE", name: msg.name, lang: msg.lang });
  }
});
