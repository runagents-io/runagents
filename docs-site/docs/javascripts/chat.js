/* RunAgents docs AI chat widget */
(function () {
  const API = 'https://a8f29e2732a6b47729122b4599f31625-1772937351.us-east-1.elb.amazonaws.com/docs/chat';
  let history = [];
  let open = false;

  function init() {
    // FAB button
    const fab = document.createElement('button');
    fab.id = 'ra-chat-fab';
    fab.title = 'Ask RunAgents AI';
    fab.innerHTML = '💬';
    document.body.appendChild(fab);

    // Panel
    const panel = document.createElement('div');
    panel.id = 'ra-chat-panel';
    panel.innerHTML = `
      <div id="ra-chat-header">
        <span>🤖</span> Ask RunAgents AI
        <button id="ra-chat-close" title="Close">✕</button>
      </div>
      <div id="ra-chat-messages">
        <div class="ra-msg assistant">Hi! Ask me anything about RunAgents — deploying agents, tools, approvals, the CLI, or getting started.</div>
      </div>
      <form id="ra-chat-form" autocomplete="off">
        <input id="ra-chat-input" type="text" placeholder="Ask a question…" maxlength="500" />
        <button id="ra-chat-send" type="submit">Send</button>
      </form>
    `;
    document.body.appendChild(panel);

    fab.addEventListener('click', toggle);
    document.getElementById('ra-chat-close').addEventListener('click', toggle);
    document.getElementById('ra-chat-form').addEventListener('submit', send);
    document.getElementById('ra-chat-input').addEventListener('keydown', function (e) {
      if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); send(e); }
    });
  }

  function toggle() {
    open = !open;
    const panel = document.getElementById('ra-chat-panel');
    if (open) {
      panel.classList.add('open');
      document.getElementById('ra-chat-input').focus();
    } else {
      panel.classList.remove('open');
    }
  }

  function addMsg(role, text) {
    const msgs = document.getElementById('ra-chat-messages');
    const div = document.createElement('div');
    div.className = 'ra-msg ' + role;
    div.textContent = text;
    msgs.appendChild(div);
    msgs.scrollTop = msgs.scrollHeight;
    return div;
  }

  async function send(e) {
    e.preventDefault();
    const input = document.getElementById('ra-chat-input');
    const btn = document.getElementById('ra-chat-send');
    const text = input.value.trim();
    if (!text) return;

    input.value = '';
    btn.disabled = true;
    addMsg('user', text);
    const thinking = addMsg('assistant thinking', '…');

    try {
      const res = await fetch(API, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: text, history: history.slice(-10) }),
      });
      const data = await res.json();
      const reply = data.reply || 'Sorry, I could not get a response.';
      thinking.className = 'ra-msg assistant';
      thinking.textContent = reply;
      history.push({ role: 'user', content: text }, { role: 'assistant', content: reply });
    } catch {
      thinking.className = 'ra-msg assistant';
      thinking.textContent = 'Sorry, something went wrong. Try again or email try@runagents.io.';
    } finally {
      btn.disabled = false;
      input.focus();
    }
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
