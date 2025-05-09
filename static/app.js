// static/app.js

const chatEl = document.getElementById('chat');
const formEl = document.getElementById('inputForm');
const inputEl = document.getElementById('messageInput');

function appendMessage(text, cssClass) {
  const msg = document.createElement('div');
  msg.className = `message ${cssClass}`;
  msg.textContent = text;
  chatEl.appendChild(msg);
  chatEl.scrollTop = chatEl.scrollHeight;
}

formEl.addEventListener('submit', async (e) => {
  e.preventDefault();
  const message = inputEl.value.trim();
  if (!message) return;
  appendMessage(`You: ${message}`, 'user');
  inputEl.value = '';

  // 1) Open the SSE connection via GET
  const evtSource = new EventSource(`/api/query?message=${encodeURIComponent(message)}`);

  // 2) Handle incoming chunks
  let fullResponse = '';
  evtSource.onmessage = (event) => {
    const chunk = event.data;
    fullResponse += chunk;

    // Update or create the bot message element
    let lastBot = document.querySelector('#chat .bot:last-child');
    if (!lastBot) {
      appendMessage(`Agent: ${fullResponse}`, 'bot');
    } else {
      lastBot.textContent = `Agent: ${fullResponse}`;
    }
  };
  evtSource.onerror = () => {
    evtSource.close();
  };

  // (If you still need to POST—for non-SSE routes—do it after opening the SSE
  //  so you don’t race the GET request. But for pure SSE GET endpoints, you
  //  don’t need the fetch() at all.)
});
