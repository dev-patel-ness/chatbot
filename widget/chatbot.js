/**
 * Embeddable Chatbot Widget (architecture.md §17).
 *
 * Usage:
 *   <script src="widget/chatbot.js"></script>
 *   <script>
 *     Chatbot.init({ websiteId: "ness", websiteName: "Ness", apiBaseUrl: "http://127.0.0.1:8080" });
 *   </script>
 */
(function () {
  "use strict";

  const Chatbot = {
    init(options) {
      const config = Object.assign(
        { websiteId: "ness", websiteName: "Ness", apiBaseUrl: "http://127.0.0.1:8080" },
        options || {}
      );
      let conversationId = null;

      injectStyles();
      const root = document.createElement("div");
      root.id = "chatbot-widget-root";
      root.innerHTML = `
        <button id="chatbot-toggle" aria-label="Open chat">💬</button>
        <div id="chatbot-panel" class="chatbot-hidden">
          <div id="chatbot-header">Chat with ${config.websiteName}</div>
          <div id="chatbot-messages"></div>
          <form id="chatbot-form">
            <input id="chatbot-input" type="text" placeholder="Ask a question..." autocomplete="off" />
            <button type="submit">Send</button>
          </form>
        </div>
      `;
      document.body.appendChild(root);

      const panel = root.querySelector("#chatbot-panel");
      const toggle = root.querySelector("#chatbot-toggle");
      const messages = root.querySelector("#chatbot-messages");
      const form = root.querySelector("#chatbot-form");
      const input = root.querySelector("#chatbot-input");

      toggle.addEventListener("click", () => panel.classList.toggle("chatbot-hidden"));

      form.addEventListener("submit", async (event) => {
        event.preventDefault();
        const message = input.value.trim();
        if (!message) return;

        appendMessage("user", message);
        input.value = "";
        const typingEl = appendMessage("assistant", "…");

        try {
          const response = await fetch(`${config.apiBaseUrl}/api/chat`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              website_id: config.websiteId,
              website_name: config.websiteName,
              message,
              conversation_id: conversationId,
            }),
          });
          const data = await response.json();
          conversationId = data.conversation_id;
          typingEl.textContent = data.response;
        } catch (err) {
          typingEl.textContent = "Sorry, something went wrong. Please try again.";
        }
      });

      function appendMessage(role, text) {
        const el = document.createElement("div");
        el.className = `chatbot-message chatbot-${role}`;
        el.textContent = text;
        messages.appendChild(el);
        messages.scrollTop = messages.scrollHeight;
        return el;
      }
    },
  };

  function injectStyles() {
    const style = document.createElement("style");
    style.textContent = `
      #chatbot-widget-root { position: fixed; bottom: 20px; right: 20px; z-index: 9999; font-family: system-ui, sans-serif; }
      #chatbot-toggle { width: 56px; height: 56px; border-radius: 50%; border: none; background: #2563eb; color: white; font-size: 24px; cursor: pointer; box-shadow: 0 2px 8px rgba(0,0,0,0.3); }
      #chatbot-panel { position: absolute; bottom: 70px; right: 0; width: 320px; height: 420px; background: white; border-radius: 12px; box-shadow: 0 4px 16px rgba(0,0,0,0.2); display: flex; flex-direction: column; overflow: hidden; }
      #chatbot-panel.chatbot-hidden { display: none; }
      #chatbot-header { background: #2563eb; color: white; padding: 12px; font-weight: 600; }
      #chatbot-messages { flex: 1; padding: 10px; overflow-y: auto; display: flex; flex-direction: column; gap: 8px; }
      .chatbot-message { padding: 8px 12px; border-radius: 10px; max-width: 85%; white-space: pre-wrap; font-size: 14px; }
      .chatbot-user { align-self: flex-end; background: #2563eb; color: white; }
      .chatbot-assistant { align-self: flex-start; background: #f1f5f9; color: #111; }
      #chatbot-form { display: flex; border-top: 1px solid #e2e8f0; }
      #chatbot-input { flex: 1; border: none; padding: 10px; font-size: 14px; }
      #chatbot-form button { border: none; background: #2563eb; color: white; padding: 0 14px; cursor: pointer; }
    `;
    document.head.appendChild(style);
  }

  window.Chatbot = Chatbot;
})();
