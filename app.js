const localKey = 'pixcellens-registrations';
const lastQueueKey = 'pixcellens-last-queue';
const $ = (selector) => document.querySelector(selector);
const usingServer = window.location.protocol === 'http:' || window.location.protocol === 'https:';
const apiBase = window.PIXCELLENS_API_BASE || '';
let registrations = usingServer ? [] : JSON.parse(localStorage.getItem(localKey) || '[]');
let selectedType = 'customer';

async function api(path, options = {}) {
  const response = await fetch(`${apiBase}${path}`, { headers: { 'Content-Type': 'application/json' }, ...options });
  if (!response.ok) throw new Error(`Request failed: ${response.status}`);
  return response.json();
}
async function refresh() {
  if (usingServer) registrations = await api('/api/registrations');
  else registrations = JSON.parse(localStorage.getItem(localKey) || '[]');
}
async function loadSchools() {
  if (!usingServer) return;
  const schools = await api('/api/schools');
  $('#school').innerHTML = '<option value="">Select school</option>' + schools.map(school => `<option>${school}</option>`).join('');
}
function saveLocal() { localStorage.setItem(localKey, JSON.stringify(registrations)); }
function showView(name) {
  document.querySelectorAll('.view').forEach(view => view.classList.remove('active'));
  $(`#${name}-view`).classList.add('active');
  document.querySelectorAll('nav a').forEach(link => link.classList.toggle('active', link.dataset.view === name));
  if (name === 'status') renderStatus();
  if (name === 'staff') { renderQueue(); renderQr(); }
}
function toast(message) { const element = $('#toast'); element.textContent = message; element.classList.add('show'); setTimeout(() => element.classList.remove('show'), 3200); }
function renderStatus() {
  const preferredQueue = localStorage.getItem(lastQueueKey);
  const latest = registrations.find(item => item.queue === preferredQueue) || registrations.at(-1);
  const content = $('#status-content');
  if (!latest) { content.className = 'status-empty'; content.innerHTML = '<div class="empty-mark">P</div><h2>No active registration</h2><p>Register for a service to see your place in the queue here.</p><a class="secondary-button" href="#register" data-view="register">Start registration</a>'; return; }
  const waiting = registrations.filter(item => item.status === 'Waiting').indexOf(latest) + 1;
  content.className = 'status-card';
  content.innerHTML = `<p class="eyebrow">Active registration / ${latest.type}</p><div class="queue-number">${latest.queue}</div><h2>${latest.name}</h2><p>${latest.service} · ${latest.status === 'Done' ? 'Completed' : `You are number ${waiting} in line`}</p><div class="status-pill ${latest.status === 'Waiting' ? 'waiting' : ''}">${latest.status}</div>`;
}
function renderQueue() {
  const rows = $('#queue-rows');
  const waiting = registrations.filter(item => item.status === 'Waiting').length;
  $('#total-count').textContent = registrations.length.toString().padStart(2, '0');
  $('#waiting-count').textContent = waiting.toString().padStart(2, '0');
  $('#done-count').textContent = (registrations.length - waiting).toString().padStart(2, '0');
  rows.innerHTML = registrations.length ? registrations.map((item, index) => `<div class="queue-row"><span>${item.queue}</span><span>${item.name}</span><span><small>${item.type}</small></span><span>${item.service}</span><span>${item.time}</span><span>${item.status === 'Waiting' ? `<button class="done-button" data-index="${index}">Mark done</button>` : '<span class="status-pill">DONE</span>'}</span></div>`).join('') : '<div class="queue-row"><span>No registrations yet.</span></div>';
}
function renderStaffData() {
  const students = registrations.filter(item => item.type === 'Student');
  const customers = registrations.filter(item => item.type === 'Customer');
  const completed = registrations.filter(item => item.status === 'Done');
  const fillRows = (selector, records, columns) => { $(selector).innerHTML = records.length ? records.map(item => `<div class="queue-row">${columns(item)}<span>${item.status === 'Waiting' ? `<button class="done-button" data-index="${registrations.indexOf(item)}">Mark done</button>` : '<span class="status-pill">DONE</span>'}</span></div>`).join('') : '<div class="queue-row"><span>No registrations yet.</span></div>'; };
  fillRows('#student-rows', students, item => `<span>${item.queue}</span><span>${item.name}</span><span>${item.school || 'Not provided'}</span><span>${item.service}</span><span>${item.time}</span>`);
  fillRows('#customer-rows', customers, item => `<span>${item.queue}</span><span>${item.name}</span><span>${item.contact}</span><span>${item.service}</span><span>${item.time}</span>`);
  $('#completed-rows').innerHTML = completed.length ? completed.map(item => `<div class="queue-row"><span>${item.queue}</span><span>${item.name}</span><span>${item.type}</span><span>${item.service}</span><span>${item.time}</span><span><span class="status-pill">DONE</span></span></div>`).join('') : '<div class="queue-row"><span>No completed sessions yet.</span></div>';
  $('#student-total').textContent = students.length.toString().padStart(2, '0'); $('#student-waiting').textContent = students.filter(item => item.status === 'Waiting').length.toString().padStart(2, '0'); $('#student-done').textContent = students.filter(item => item.status === 'Done').length.toString().padStart(2, '0'); $('#school-count').textContent = new Set(students.map(item => item.school).filter(Boolean)).size.toString().padStart(2, '0');
  $('#customer-total').textContent = customers.length.toString().padStart(2, '0'); $('#customer-waiting').textContent = customers.filter(item => item.status === 'Waiting').length.toString().padStart(2, '0'); $('#customer-done').textContent = customers.filter(item => item.status === 'Done').length.toString().padStart(2, '0'); $('#service-count').textContent = new Set(registrations.map(item => item.service)).size.toString().padStart(2, '0'); $('#report-done').textContent = completed.length.toString().padStart(2, '0');
  const serviceCounts = registrations.reduce((counts, item) => ({ ...counts, [item.service]: (counts[item.service] || 0) + 1 }), {}); const topService = Object.entries(serviceCounts).sort((a, b) => b[1] - a[1])[0]; $('#top-service').textContent = topService ? `${topService[0]} (${topService[1]})` : 'No bookings yet';
}
function showStaffPanel(name) { document.querySelectorAll('.staff-panel').forEach(panel => panel.classList.toggle('active', panel.id === `${name}-panel`)); document.querySelectorAll('.staff-tab').forEach(tab => tab.classList.toggle('active', tab.dataset.staffTab === name)); renderStaffData(); }
function renderQr() {
  const url = usingServer ? `${window.location.origin}/#register` : 'Run server.py to create the office QR link';
  $('#office-url').textContent = url;
  $('#qr-image').src = usingServer ? `https://api.qrserver.com/v1/create-qr-code/?size=180x180&data=${encodeURIComponent(url)}` : '';
}
document.querySelectorAll('[data-view]').forEach(link => link.addEventListener('click', async event => { event.preventDefault(); const view = link.dataset.view; history.pushState({}, '', `#${view}`); await refresh(); showView(view); }));
document.querySelectorAll('[data-type]').forEach(button => button.addEventListener('click', () => { selectedType = button.dataset.type; document.querySelectorAll('[data-type]').forEach(item => item.classList.toggle('selected', item === button)); document.querySelectorAll('.student-only').forEach(field => field.classList.toggle('hidden', selectedType !== 'student')); $('#school').required = selectedType === 'student'; }));
document.querySelectorAll('[data-staff-tab]').forEach(tab => tab.addEventListener('click', () => showStaffPanel(tab.dataset.staffTab)));
$('#registration-form').addEventListener('submit', async event => {
  event.preventDefault();
  const entry = { name: $('#name').value, contact: $('#contact').value, email: $('#email').value, type: selectedType === 'student' ? 'Student' : 'Customer', school: $('#school').value, service: $('#service').value };
  try {
    const created = usingServer ? await api('/api/registrations', { method: 'POST', body: JSON.stringify(entry) }) : { ...entry, queue: String(101 + registrations.length).padStart(3, '0'), time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }), status: 'Waiting' };
    if (!usingServer) { registrations.push(created); saveLocal(); }
    localStorage.setItem(lastQueueKey, created.queue);
    await refresh(); event.target.reset(); selectedType = 'customer'; document.querySelectorAll('[data-type]').forEach(item => item.classList.toggle('selected', item.dataset.type === 'customer')); document.querySelectorAll('.student-only').forEach(field => field.classList.add('hidden'));
    toast(`Registration confirmed. Your queue number is ${created.queue}.`); setTimeout(() => { history.pushState({}, '', '#status'); showView('status'); }, 350);
  } catch { toast('The office server is unavailable. Please ask the staff at the counter.'); }
});
$('#queue-rows').addEventListener('click', async event => { if (!event.target.matches('.done-button')) return; const item = registrations[Number(event.target.dataset.index)]; try { if (usingServer) await api(`/api/registrations/${item.id}`, { method: 'PATCH', body: JSON.stringify({ status: 'Done' }) }); else { item.status = 'Done'; saveLocal(); } await refresh(); renderQueue(); toast('Registration marked as completed.'); } catch { toast('Could not update the shared queue.'); } });
$('#clear-demo').addEventListener('click', async () => { try { if (usingServer) await api('/api/registrations/done', { method: 'DELETE' }); else { registrations = registrations.filter(item => item.status !== 'Done'); saveLocal(); } await refresh(); renderQueue(); } catch { toast('Could not clear completed registrations.'); } });
window.addEventListener('popstate', async () => { await refresh(); showView(location.hash.slice(1) || 'register'); });
(async () => { try { await refresh(); await loadSchools(); } catch { toast('Offline preview mode. Start server.py for shared office registrations.'); } showView(location.hash.slice(1) || 'register'); })();