'use strict';
const form = document.querySelector('#chat-form');
const input = document.querySelector('#message');
const messages = document.querySelector('#messages');
const send = document.querySelector('#send');
const reset = document.querySelector('#new-chat');
const suggestions = document.querySelector('#suggestions');
const status = document.querySelector('#status');
const error = document.querySelector('#error');
const count = document.querySelector('#count');
const initialMessages = messages.innerHTML;
const idleStatus = status.textContent;
let busy = false;

function updateCount() {
  count.textContent = `${input.value.length} / 4000`;
  send.disabled = busy || !input.value.trim();
}
function addMessage(who, text) {
  const article = document.createElement('article');
  article.className = `message ${who}`;
  const label = document.createElement('span');
  label.className = 'sender';
  label.textContent = who === 'user' ? 'YOU' : 'LAYA';
  const body = document.createElement('p');
  body.textContent = text;
  article.append(label, body);
  messages.append(article);
  messages.scrollTop = messages.scrollHeight;
  return article;
}

form.addEventListener('submit', async (event) => {
  event.preventDefault();
  const text = input.value.trim();
  if (busy || !text || text.length > 4000) return;
  busy = true;
  error.hidden = true;
  suggestions.hidden = true;
  input.value = '';
  input.disabled = true;
  reset.disabled = true;
  updateCount();
  const outgoing = addMessage('user', text);
  status.textContent = 'Laya is working on your request. The first reply may take longer while the model loads…';
  messages.setAttribute('aria-busy', 'true');
  try {
    const response = await fetch(form.action, {
      method: 'POST',
      body: new URLSearchParams({ user_input: text }),
    });
    if (!response.ok) throw new Error('Request failed');
    const data = await response.json();
    if (typeof data.response !== 'string' || !data.response.trim()) throw new Error('Invalid reply');
    addMessage('assistant', data.response);
  } catch {
    outgoing.remove();
    input.value = text;
    error.textContent = 'We couldn’t get a reply. Your message is ready to send again.';
    error.hidden = false;
  } finally {
    busy = false;
    input.disabled = false;
    reset.disabled = false;
    messages.setAttribute('aria-busy', 'false');
    status.textContent = idleStatus;
    updateCount();
    input.focus();
  }
});
input.addEventListener('input', updateCount);
input.addEventListener('keydown', (event) => {
  if (event.key === 'Enter' && !event.shiftKey && !event.isComposing) {
    event.preventDefault();
    form.requestSubmit();
  }
});
suggestions.addEventListener('click', (event) => {
  const button = event.target.closest('button[data-message]');
  if (!button || busy) return;
  input.value = button.dataset.message;
  updateCount();
  input.focus();
});
reset.addEventListener('click', () => {
  if (busy) return;
  messages.innerHTML = initialMessages;
  suggestions.hidden = false;
  error.hidden = true;
  input.value = '';
  updateCount();
  input.focus();
});
updateCount();
