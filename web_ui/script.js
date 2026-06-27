// script.js – Frontend logic for YatraSetu Web UI
const API_BASE = "http://localhost:8000";
let sessionId = "session_" + Math.random().toString(36).substring(2, 9);
let userId = "default_user";

/** Populate the agent dropdown */
async function loadAgents() {
  try {
    const resp = await fetch(`${API_BASE}/list-apps`);
    const data = await resp.json();
    // Expected shape: { apps: [{ app_name: "heritage_agent" }, ...] } or simple array
    const apps = Array.isArray(data) ? data : (data.apps || []);
    const select = document.getElementById("agentDropdown");
    apps.forEach(app => {
      const name = app.app_name || app; // support both formats
      const opt = document.createElement("option");
      opt.value = name;
      opt.textContent = name;
      select.appendChild(opt);
    });
    if (select.options.length > 0) select.selectedIndex = 0;
  } catch (e) {
    console.error("Failed to load agents", e);
    alert("Could not fetch agent list from the API server.");
  }
}

/** Append a message bubble to the chat window */
function appendMessage(role, content) {
  const chat = document.getElementById("chatWindow");
  const bubble = document.createElement("div");
  bubble.className = `message ${role}`;
  bubble.textContent = content;
  chat.appendChild(bubble);
  chat.scrollTop = chat.scrollHeight;
}

/** Send user input to the selected agent */
async function sendMessage() {
  const inputEl = document.getElementById("messageInput");
  const text = inputEl.value.trim();
  if (!text) return;
  const agent = document.getElementById("agentDropdown").value;
  appendMessage("user", text);
  inputEl.value = "";
  // Show a temporary loading indicator
  const loadingId = Date.now();
  appendMessage("assistant", "…");
  try {
    const payload = {
      appName: agent,
      userId: userId,
      sessionId: sessionId,
      newMessage: {
        role: "user",
        parts: [{ text: text }]
      }
    };
    const resp = await fetch(`${API_BASE}/run`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });
    if (!resp.ok) {
      const errText = await resp.text();
      throw new Error(`HTTP ${resp.status}: ${errText || resp.statusText}`);
    }
    const result = await resp.json();
    
    // Extract assistant reply from the array of events
    let assistantMsg = "";
    if (Array.isArray(result)) {
      // Find the last event with model content
      const modelEvents = result.filter(e => e.content && e.content.role === "model");
      if (modelEvents.length > 0) {
        const lastEvent = modelEvents[modelEvents.length - 1];
        const textParts = lastEvent.content.parts
          .filter(p => p.text && !p.thought)
          .map(p => p.text);
        assistantMsg = textParts.join("\n");
      }
      if (!assistantMsg) {
        // Fallback: search backwards for any model content parts
        for (let i = result.length - 1; i >= 0; i--) {
          const e = result[i];
          if (e.content && e.content.role === "model" && e.content.parts) {
            const txt = e.content.parts.filter(p => p.text && !p.thought).map(p => p.text).join("\n");
            if (txt) {
              assistantMsg = txt;
              break;
            }
          }
        }
      }
    }
    if (!assistantMsg) {
      assistantMsg = "No response content received from agent.";
    }
    // Replace the temporary loading bubble
    const bubbles = document.querySelectorAll(".message.assistant");
    const lastBubble = bubbles[bubbles.length - 1];
    if (lastBubble && lastBubble.textContent === "…") {
      lastBubble.textContent = assistantMsg;
    } else {
      appendMessage("assistant", assistantMsg);
    }
  } catch (e) {
    console.error(e);
    // Replace temporary loading bubble with error message
    const bubbles = document.querySelectorAll(".message.assistant");
    const lastBubble = bubbles[bubbles.length - 1];
    if (lastBubble && lastBubble.textContent === "…") {
      lastBubble.textContent = `Error: ${e.message}`;
    } else {
      appendMessage("assistant", `Error: ${e.message}`);
    }
  }
}

/** Initialise event listeners */
function init() {
  document.getElementById("sendButton").addEventListener("click", sendMessage);
  document.getElementById("messageInput").addEventListener("keypress", ev => {
    if (ev.key === "Enter" && !ev.shiftKey) {
      ev.preventDefault();
      sendMessage();
    }
  });
  loadAgents();
}

window.addEventListener("DOMContentLoaded", init);
