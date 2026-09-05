const $ = (selector) => document.querySelector(selector);
let registrations = [];

async function api(path, options = {}) {
  const response = await fetch(path, { headers: { 'Content-Type': 'application/json' }, ...options });
  if (!response.ok) throw new Error(`Request failed: ${response.status}`);
  return response.json();
}
async function refresh() { registrations = await api('/api/registrations'); }
function toast(message) { const element = $('#toast'); element.textContent = message; element.classList.add('show'); setTimeout(() => element.classList.remove('show'), 3200); }
function renderQueue() {
  const waiting = registrations.filter(item => item.status === 'Waiting').length;
  $('#total-count').textContent = registrations.length.toString().padStart(2, '0');
  $('#waiting-count').textContent = waiting.toString().padStart(2, '0');
  $('#done-count').textContent = (registrations.length - waiting).toString().padStart(2, '0');
  $('#queue-rows').innerHTML = registrations.length ? registrations.map((item, index) => `<div class="queue-row"><span>${item.queue}</span><span>${item.name}</span><span><small>${item.type}</small></span><span>${item.service}</span><span>${item.time}</span><span>${item.status === 'Waiting' ? `<button class="done-button" data-index="${index}">Mark done</button>` : '<span class="status-pill">DONE</span>'}</span></div>`).join('') : '<div class="queue-row"><span>No registrations yet.</span></div>';
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
function renderQr() {
  const url = `${window.location.origin}/#register`;
  $('#office-url').textContent = url;
  $('#qr-image').src = `https://api.qrserver.com/v1/create-qr-code/?size=180x180&data=${encodeURIComponent(url)}`;
}
async function renderAll() { await refresh(); renderQueue(); renderStaffData(); renderQr(); }
function showStaffPanel(name) { document.querySelectorAll('.staff-panel').forEach(panel => panel.classList.toggle('active', panel.id === `${name}-panel`)); document.querySelectorAll('.staff-tab').forEach(tab => tab.classList.toggle('active', tab.dataset.staffTab === name)); renderStaffData(); }

document.querySelectorAll('[data-staff-tab]').forEach(tab => tab.addEventListener('click', () => showStaffPanel(tab.dataset.staffTab)));
$('#queue-rows').addEventListener('click', async event => { if (!event.target.matches('.done-button')) return; const item = registrations[Number(event.target.dataset.index)]; try { await api(`/api/registrations/${item.id}`, { method: 'PATCH', body: JSON.stringify({ status: 'Done' }) }); await renderAll(); toast('Registration marked as completed.'); } catch { toast('Could not update the shared queue.'); } });
document.querySelectorAll('#student-rows, #customer-rows').forEach(table => table.addEventListener('click', async event => { if (!event.target.matches('.done-button')) return; const item = registrations[Number(event.target.dataset.index)]; try { await api(`/api/registrations/${item.id}`, { method: 'PATCH', body: JSON.stringify({ status: 'Done' }) }); await renderAll(); toast('Registration marked as completed.'); } catch { toast('Could not update the shared queue.'); } }));
$('#clear-demo').addEventListener('click', async () => { try { await api('/api/registrations/done', { method: 'DELETE' }); await renderAll(); toast('Completed registrations cleared.'); } catch { toast('Could not clear completed registrations.'); } });
setInterval(async () => { try { await renderAll(); } catch { toast('The shared office server is unavailable.'); } }, 10000);
renderAll().catch(() => toast('Start server.py to connect the staff portal to the customer form.'));
