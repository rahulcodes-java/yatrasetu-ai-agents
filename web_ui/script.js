// script.js – YatraSetu Web UI v6 (Agent selector in settings)
"use strict";

const API_BASE = "http://localhost:8000";

// Per-agent session tracking
const agentSessions = {};
let userId = "default_user";

// Whether the user has sent their first message (hides empty state permanently)
let firstMessageSent = false;

// ---------- Rate-limit cooldown ----------------------------------------
const COOLDOWN_SECONDS = 15;
let cooldownTimer = null;

function startCooldown() {
  const btn   = document.getElementById("sendButton");
  const input = document.getElementById("messageInput");
  const btnText = document.getElementById("sendBtnText");
  let remaining = COOLDOWN_SECONDS;

  btn.disabled   = true;
  input.disabled = true;
  if (btnText) btnText.textContent = `${remaining}s`;

  cooldownTimer = setInterval(() => {
    remaining -= 1;
    if (remaining <= 0) {
      clearInterval(cooldownTimer);
      cooldownTimer = null;
      btn.disabled   = false;
      input.disabled = false;
      resetSendButton();
      input.focus();
    } else {
      if (btnText) btnText.textContent = `${remaining}s`;
    }
  }, 1000);
}

function resetSendButton() {
  const btnText = document.getElementById("sendBtnText");
  if (btnText) btnText.textContent = "Plan";
}

function setSendingState(isSending) {
  const btn     = document.getElementById("sendButton");
  const btnText = document.getElementById("sendBtnText");
  const icon    = btn.querySelector(".ti");

  if (isSending) {
    btn.disabled = true;
    if (btnText) btnText.textContent = "Planning…";
    if (icon) { icon.classList.remove("ti-send"); icon.classList.add("ti-loader-2"); }
  } else {
    btn.disabled = false;
    if (btnText) btnText.textContent = "Plan";
    if (icon) { icon.classList.remove("ti-loader-2"); icon.classList.add("ti-send"); }
  }
}
// -----------------------------------------------------------------------

/** Get or create a session ID for the given agent */
function getSessionId(agentName) {
  if (!agentSessions[agentName]) {
    agentSessions[agentName] = "session_" + Math.random().toString(36).substring(2, 9);
  }
  return agentSessions[agentName];
}

/** Friendly display name for an agent */
function agentDisplayName(agentName) {
  if (agentName === "planner_agent") return "Planner AI";
  return agentName
    .replace(/_agent$/i, "")
    .replace(/_/g, " ")
    .replace(/\b\w/g, c => c.toUpperCase())
    + " Agent";
}

/** Render Markdown to safe HTML using marked.js */
function renderMarkdown(text) {
  if (typeof marked !== "undefined") {
    try {
      return marked.parse(text);
    } catch (e) {
      console.warn("marked.parse failed, falling back to text", e);
    }
  }
  return text.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
}

/** Show or hide the empty-state placeholder */
function syncEmptyState() {
  const empty = document.getElementById("emptyState");
  if (!empty) return;
  if (firstMessageSent) {
    empty.style.display = "none";
  } else {
    const chat = document.getElementById("chatWindow");
    const hasMessages = chat.querySelectorAll(".message-wrapper").length > 0;
    empty.style.display = hasMessages ? "none" : "flex";
  }
}

/** Announce new messages to screen readers */
function announceToScreenReader(text) {
  const announcer = document.getElementById("sr-announcer");
  if (announcer) {
    announcer.textContent = "";
    // Small delay to ensure screen reader picks up change
    setTimeout(() => { announcer.textContent = text; }, 50);
  }
}

/** Append a message bubble to the chat window */
function appendMessage(role, content, agentName) {
  const chat = document.getElementById("chatWindow");

  const wrapper = document.createElement("div");
  wrapper.className = `message-wrapper ${role}`;

  // Avatar
  const avatar = document.createElement("div");
  avatar.className = "avatar";
  avatar.setAttribute("aria-hidden", "true");

  if (role === "user") {
    avatar.innerHTML = '<i class="ti ti-user"></i>';
  } else if (role === "assistant") {
    avatar.innerHTML = '<i class="ti ti-robot"></i>';
  } else {
    avatar.innerHTML = '<i class="ti ti-alert-triangle"></i>';
  }

  // Bubble column (label + bubble)
  const column = document.createElement("div");
  column.className = "bubble-column";

  // Agent label above assistant messages
  if (role === "assistant" && agentName) {
    const label = document.createElement("div");
    label.className = "agent-label";
    label.textContent = agentDisplayName(agentName);
    column.appendChild(label);
  }

  const bubble = document.createElement("div");
  bubble.className = `message ${role}`;

  if (role === "assistant") {
    const headerHtml = (agentName === "planner_agent")
      ? `<div class="planner-header-card">
           <i class="ti ti-map-route" aria-hidden="true"></i>
           <strong>Your Complete Travel Plan</strong>
         </div>`
      : "";
    bubble.innerHTML = headerHtml + renderMarkdown(content);
    bubble.querySelectorAll("a").forEach(a => {
      a.target = "_blank";
      a.rel = "noopener noreferrer";
    });
  } else {
    bubble.textContent = content;
  }

  column.appendChild(bubble);

  if (role === "user") {
    wrapper.appendChild(column);
    wrapper.appendChild(avatar);
  } else {
    wrapper.appendChild(avatar);
    wrapper.appendChild(column);
  }

  chat.appendChild(wrapper);
  chat.scrollTop = chat.scrollHeight;
  syncEmptyState();
  return bubble;
}

/** Replace the loading bubble content with real content or error */
function replaceLoadingBubble(realContent, agentName, isError) {
  const wrappers = document.querySelectorAll(".message-wrapper.assistant");
  const lastWrapper = wrappers[wrappers.length - 1];
  if (!lastWrapper) return;

  const bubble = lastWrapper.querySelector(".message.assistant");
  if (!bubble) return;

  const isLoading = bubble.getAttribute("data-loading") === "true";
  if (!isLoading) return;

  bubble.removeAttribute("data-loading");
  bubble.classList.remove("loading");

  if (isError) {
    bubble.className = "message assistant error";
    bubble.innerHTML = `<i class="ti ti-alert-triangle" aria-hidden="true" style="margin-right:6px;vertical-align:middle;"></i>${escapeHtml(realContent)}`;
    announceToScreenReader("Error: " + realContent);
  } else {
    bubble.className = "message assistant";
    const headerHtml = (agentName === "planner_agent")
      ? `<div class="planner-header-card">
           <i class="ti ti-map-route" aria-hidden="true"></i>
           <strong>Your Complete Travel Plan</strong>
         </div>`
      : "";
    bubble.innerHTML = headerHtml + renderMarkdown(realContent);
    bubble.querySelectorAll("a").forEach(a => {
      a.target = "_blank";
      a.rel = "noopener noreferrer";
    });
    announceToScreenReader("Response received");
  }

  // Also update the agent label if not yet set
  const col = lastWrapper.querySelector(".bubble-column");
  if (col && agentName && !col.querySelector(".agent-label")) {
    const label = document.createElement("div");
    label.className = "agent-label";
    label.textContent = agentDisplayName(agentName);
    col.insertBefore(label, col.firstChild);
  }

  // Scroll to bottom after content revealed
  const chat = document.getElementById("chatWindow");
  if (chat) chat.scrollTop = chat.scrollHeight;
}

/** Append a loading (thinking) bubble */
function appendLoadingBubble() {
  const chat = document.getElementById("chatWindow");

  const wrapper = document.createElement("div");
  wrapper.className = "message-wrapper assistant";

  const avatar = document.createElement("div");
  avatar.className = "avatar";
  avatar.setAttribute("aria-hidden", "true");
  avatar.innerHTML = '<i class="ti ti-robot"></i>';

  const column = document.createElement("div");
  column.className = "bubble-column";

  const bubble = document.createElement("div");
  bubble.className = "message assistant loading";
  bubble.setAttribute("data-loading", "true");
  bubble.setAttribute("aria-label", "Loading response");
  bubble.innerHTML = '<span class="dot"></span><span class="dot"></span><span class="dot"></span>';

  column.appendChild(bubble);
  wrapper.appendChild(avatar);
  wrapper.appendChild(column);
  chat.appendChild(wrapper);
  chat.scrollTop = chat.scrollHeight;
  syncEmptyState();
}

/** Escape HTML for safe display in error messages */
function escapeHtml(str) {
  return str
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

/** Format API/network errors into user-friendly messages */
function friendlyError(err) {
  const msg = err.message || "";
  if (msg.includes("Failed to fetch") || msg.includes("NetworkError")) {
    return "Can't reach the server. Please check your connection.";
  }
  if (msg.includes("timeout") || msg.includes("AbortError")) {
    return "Request took too long. Try a shorter question.";
  }
  if (msg.includes("HTTP 5")) {
    return "Something went wrong on the server. Please try again.";
  }
  if (msg.includes("HTTP 4")) {
    return "Invalid request. Please rephrase your question.";
  }
  return "Something went wrong. Please try again.";
}

/** Send user input to the agent */
async function sendMessage() {
  if (cooldownTimer !== null) return;

  const inputEl = document.getElementById("messageInput");
  const text = inputEl.value.trim();
  if (!text) {
    inputEl.focus();
    return;
  }

  // Mark first message sent — empty state gone for good
  if (!firstMessageSent) {
    firstMessageSent = true;
    const empty = document.getElementById("emptyState");
    if (empty) {
      empty.style.opacity = "0";
      empty.style.transition = "opacity 200ms ease";
      setTimeout(() => { if (empty) empty.style.display = "none"; }, 200);
    }
  }

  const agent = getActiveAgent();
  const sessionId = getSessionId(agent);

  appendMessage("user", text, null);
  inputEl.value = "";
  inputEl.focus();

  setSendingState(true);
  appendLoadingBubble();

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

    // Extract assistant message from ADK response
    let assistantMsg = "";
    if (Array.isArray(result)) {
      const modelEvents = result.filter(e => e.content && e.content.role === "model");
      if (modelEvents.length > 0) {
        const lastEvent = modelEvents[modelEvents.length - 1];
        const textParts = lastEvent.content.parts
          .filter(p => p.text && !p.thought)
          .map(p => p.text);
        assistantMsg = textParts.join("\n");
      }
      if (!assistantMsg) {
        for (let i = result.length - 1; i >= 0; i--) {
          const e = result[i];
          if (e.content && e.content.role === "model" && e.content.parts) {
            const txt = e.content.parts.filter(p => p.text && !p.thought).map(p => p.text).join("\n");
            if (txt) { assistantMsg = txt; break; }
          }
        }
      }
    }

    if (!assistantMsg) {
      assistantMsg = "No response received from the agent. Please try again.";
    }

    replaceLoadingBubble(assistantMsg, agent, false);

  } catch (err) {
    console.error("[YatraSetu]", err);
    replaceLoadingBubble(friendlyError(err), agent, true);
  } finally {
    setSendingState(false);
    startCooldown();
  }
}

// ============================================================
// DARK MODE
// ============================================================
function applyTheme(dark) {
  document.body.classList.toggle("dark-theme", dark);

  const themeIcon      = document.getElementById("themeIcon");
  const headerToggle   = document.getElementById("darkModeToggle");
  const settingsToggle = document.getElementById("settingsDarkToggle");

  if (themeIcon) {
    themeIcon.classList.toggle("ti-moon", !dark);
    themeIcon.classList.toggle("ti-sun",  dark);
  }
  if (headerToggle)   headerToggle.setAttribute("aria-label", dark ? "Switch to light mode" : "Switch to dark mode");
  if (settingsToggle) settingsToggle.setAttribute("aria-checked", String(dark));
}

function toggleTheme() {
  const isDark = document.body.classList.contains("dark-theme");
  const newDark = !isDark;
  applyTheme(newDark);
  try { localStorage.setItem("yatrasetu-theme", newDark ? "dark" : "light"); } catch (_) {}
}

function loadTheme() {
  let saved = null;
  try { saved = localStorage.getItem("yatrasetu-theme"); } catch (_) {}
  if (saved === "dark") {
    applyTheme(true);
  } else if (saved === "light") {
    applyTheme(false);
  } else {
    // Use system preference as fallback
    const prefersDark = window.matchMedia && window.matchMedia("(prefers-color-scheme: dark)").matches;
    applyTheme(prefersDark);
  }
}

// ============================================================
// SETTINGS POPOVER
// ============================================================
function openPopover() {
  const pop = document.getElementById("settingsPopover");
  if (!pop) return;
  pop.classList.add("open");
  pop.setAttribute("aria-hidden", "false");
}

function closePopover() {
  const pop = document.getElementById("settingsPopover");
  if (!pop) return;
  pop.classList.remove("open");
  pop.setAttribute("aria-hidden", "true");
}

function togglePopover() {
  const pop = document.getElementById("settingsPopover");
  if (!pop) return;
  pop.classList.contains("open") ? closePopover() : openPopover();
}

// ============================================================
// CLEAR CHAT
// ============================================================
function clearChat() {
  const chat = document.getElementById("chatWindow");
  if (!chat) return;
  chat.querySelectorAll(".message-wrapper").forEach(el => el.remove());
  firstMessageSent = false;

  const empty = document.getElementById("emptyState");
  if (empty) {
    empty.style.display = "flex";
    empty.style.opacity = "1";
  }
  closePopover();
}

// ============================================================
// AGENT SELECTION
// ============================================================

/** Return the currently selected agent name for the /run call */
function getActiveAgent() {
  const plannerRadio = document.getElementById("agentPlanner");
  if (plannerRadio && plannerRadio.checked) return "planner_agent";
  const select = document.getElementById("specificAgentSelect");
  return select ? select.value : "planner_agent";
}

/** Persist agent choice to localStorage */
function saveAgentChoice() {
  try {
    const mode = document.getElementById("agentPlanner")?.checked ? "planner" : "specific";
    const specific = document.getElementById("specificAgentSelect")?.value || "heritage_agent";
    localStorage.setItem("yatrasetu-agent", JSON.stringify({ mode, specific }));
  } catch (_) {}
}

/** Restore agent choice from localStorage */
function loadAgentChoice() {
  try {
    const raw = localStorage.getItem("yatrasetu-agent");
    if (!raw) return;
    const data = JSON.parse(raw);
    const plannerRadio = document.getElementById("agentPlanner");
    const specificRadio = document.getElementById("agentSpecific");
    const specificRow = document.getElementById("specificAgentRow");
    const select = document.getElementById("specificAgentSelect");

    if (data.mode === "specific" && specificRadio) {
      specificRadio.checked = true;
      if (plannerRadio) plannerRadio.checked = false;
      if (specificRow) specificRow.hidden = false;
      if (select && data.specific) select.value = data.specific;
    } else {
      if (plannerRadio) plannerRadio.checked = true;
      if (specificRadio) specificRadio.checked = false;
      if (specificRow) specificRow.hidden = true;
    }
  } catch (_) {}
}

/** Handle agent radio/dropdown changes: show/hide dropdown, save, clear chat */
function onAgentChoiceChanged() {
  const specificRadio = document.getElementById("agentSpecific");
  const specificRow = document.getElementById("specificAgentRow");
  const isSpecific = specificRadio && specificRadio.checked;

  if (specificRow) specificRow.hidden = !isSpecific;
  saveAgentChoice();
  clearChatSilent();
}

/** Clear chat without closing the popover (used on agent switch) */
function clearChatSilent() {
  const chat = document.getElementById("chatWindow");
  if (!chat) return;
  chat.querySelectorAll(".message-wrapper").forEach(el => el.remove());
  firstMessageSent = false;

  const empty = document.getElementById("emptyState");
  if (empty) {
    empty.style.display = "flex";
    empty.style.opacity = "1";
  }
}

// ============================================================
// INIT
// ============================================================
function init() {
  // Load theme immediately
  loadTheme();

  // Create screen reader announcer
  const announcer = document.createElement("div");
  announcer.id = "sr-announcer";
  announcer.setAttribute("role", "status");
  announcer.setAttribute("aria-live", "polite");
  announcer.setAttribute("aria-atomic", "true");
  announcer.className = "sr-only";
  document.body.appendChild(announcer);

  // Send button
  const sendBtn = document.getElementById("sendButton");
  if (sendBtn) sendBtn.addEventListener("click", sendMessage);

  // Enter key to send
  const inputEl = document.getElementById("messageInput");
  if (inputEl) {
    inputEl.addEventListener("keydown", ev => {
      if (ev.key === "Enter" && !ev.shiftKey) {
        ev.preventDefault();
        sendMessage();
      }
    });
  }

  // Dark mode toggle (header)
  const darkBtn = document.getElementById("darkModeToggle");
  if (darkBtn) darkBtn.addEventListener("click", toggleTheme);

  // Settings toggle
  const settingsBtn = document.getElementById("settingsToggle");
  if (settingsBtn) settingsBtn.addEventListener("click", (e) => {
    e.stopPropagation();
    togglePopover();
  });

  // Settings dark mode toggle (inside popover)
  const settingsDark = document.getElementById("settingsDarkToggle");
  if (settingsDark) settingsDark.addEventListener("click", toggleTheme);

  // Clear chat button
  const clearBtn = document.getElementById("clearChatBtn");
  if (clearBtn) clearBtn.addEventListener("click", clearChat);

  // Close popover when clicking outside
  document.addEventListener("click", (e) => {
    const pop = document.getElementById("settingsPopover");
    const btn = document.getElementById("settingsToggle");
    if (pop && pop.classList.contains("open")) {
      if (!pop.contains(e.target) && e.target !== btn) {
        closePopover();
      }
    }
  });

  // Close popover on Escape
  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape") closePopover();
  });

  // Example chips in empty state
  document.querySelectorAll(".example-chip").forEach(chip => {
    chip.addEventListener("click", () => {
      const query = chip.getAttribute("data-query");
      if (!query) return;
      const el = document.getElementById("messageInput");
      if (el) {
        el.value = query;
        el.focus();
        sendMessage();
      }
    });
  });

  // Agent selection radios
  const agentPlannerRadio = document.getElementById("agentPlanner");
  const agentSpecificRadio = document.getElementById("agentSpecific");
  const specificSelect = document.getElementById("specificAgentSelect");

  if (agentPlannerRadio) agentPlannerRadio.addEventListener("change", onAgentChoiceChanged);
  if (agentSpecificRadio) agentSpecificRadio.addEventListener("change", onAgentChoiceChanged);
  if (specificSelect) specificSelect.addEventListener("change", () => {
    saveAgentChoice();
    clearChatSilent();
  });

  // Restore agent choice from localStorage
  loadAgentChoice();

  // Initial empty state sync
  syncEmptyState();
}

window.addEventListener("DOMContentLoaded", init);
