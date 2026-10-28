(() => {
  'use strict';
  const $ = (selector, root = document) => root.querySelector(selector);
  const $$ = (selector, root = document) => [...root.querySelectorAll(selector)];
  const STORAGE_KEY = 'mindease-demo-state-v2';
  const defaultState = {
    page: 'dashboard', scenario: 'normal', monitoring: true, episodes: [], sessions: 0, checkins: 0,
    contacts: [], contactPrefs: { ask: true, share: false }, apiBase: 'http://localhost:8000'
  };
  let state = loadState();
  let readings = [];
  let toastTimer, breathTimer, phaseTimer, breathRemaining = 60, breathing = false, exercise = 'breathing', tick = 0, chatBusy = false;
  const localReflections = [
    'You do not need to solve everything at once. Notice what is around you, relax your shoulders if that feels comfortable, and choose one small next step.',
    'A body signal can change for many reasons. If it helps, pause and check your surroundings before deciding what you need.',
    'You are allowed to take a break. Try naming one thing you can see, one sound you can hear, and one thing that would make the next few minutes easier.',
    'Support is personal. If a breathing exercise does not feel right today, it is okay to stop and try a different kind of grounding.'
  ];
  function loadState() { try { return { ...defaultState, ...JSON.parse(localStorage.getItem(STORAGE_KEY) || '{}') }; } catch { return { ...defaultState }; } }
  function persist() { try { localStorage.setItem(STORAGE_KEY, JSON.stringify(state)); } catch { /* storage may be unavailable */ } }
  function escapeHTML(value) { return String(value ?? '').replace(/[&<>"']/g, c => ({ '&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;' }[c])); }
  function toast(message) { const el = $('#toast'); el.textContent = message; el.classList.add('show'); clearTimeout(toastTimer); toastTimer = setTimeout(() => el.classList.remove('show'), 2800); }
  function timeLabel(date = new Date()) { return date.toLocaleString([], { month: 'short', day: 'numeric', hour: 'numeric', minute: '2-digit' }); }
  function addEvent(type, title, description, tag = 'Demo') { state.episodes.unshift({ id: `${Date.now()}-${Math.random().toString(16).slice(2,7)}`, type, title, description, tag, timestamp: new Date().toISOString(), time: timeLabel() }); state.episodes = state.episodes.slice(0, 100); persist(); renderHistory(); }
  function go(page) { state.page = page; $$('.page').forEach(p => p.classList.toggle('active-page', p.id === `page-${page}`)); $$('.nav-item[data-page]').forEach(b => b.classList.toggle('active', b.dataset.page === page)); const active = $(`.nav-item[data-page="${page}"]`); $('#crumbTitle').textContent = active ? active.textContent.trim().replace('BETA','').trim() : page; $('#sidebar').classList.remove('open'); window.scrollTo({ top: 0, behavior: 'smooth' }); if (page === 'history') renderHistory(); if (page === 'contacts') renderContacts(); if (page === 'settings') testBackend(false); persist(); }
  $$('.nav-item[data-page]').forEach(b => b.addEventListener('click', () => go(b.dataset.page)));
  $$('[data-goto]').forEach(b => b.addEventListener('click', () => { go(b.dataset.goto); if (b.dataset.exercise) setExercise(b.dataset.exercise); }));
  $('#menuToggle').addEventListener('click', () => $('#sidebar').classList.toggle('open'));
  $('#todayLabel').textContent = new Date().toLocaleDateString(undefined, { weekday: 'short', month: 'short', day: 'numeric' });
  $('#noticeClose').addEventListener('click', () => $('#simulationNotice').remove());

  function sampleReading(scenario = state.scenario) {
    tick++;
    const wave = Math.sin(tick / 3.1) * 2.2 + Math.sin(tick / 7) * 1.5;
    const elevated = scenario === 'elevated';
    const active = scenario === 'activity';
    return { time: new Date(), hr: Math.round((elevated ? 108 : active ? 112 : 72) + wave + (Math.random() * 2 - 1)), hrv: Math.round((elevated ? 27 : active ? 43 : 48) + Math.sin(tick / 4) * 2 + Math.random() * 2), eda: +(elevated ? 4.1 : active ? 2.7 : 2.1) + Math.sin(tick / 5) * .15 + Math.random() * .12, movement: elevated ? 'Low' : active ? 'Active' : 'Low', quality: 95 };
  }
  function seedReadings() { readings = []; for (let i = 0; i < 40; i++) { tick = i; readings.push(sampleReading('normal')); } tick = 40; }
  function drawChart() {
    const canvas = $('#heartChart'); if (!canvas) return;
    const rect = canvas.getBoundingClientRect(); if (!rect.width || !rect.height) return;
    const dpr = window.devicePixelRatio || 1; canvas.width = Math.round(rect.width * dpr); canvas.height = Math.round(rect.height * dpr);
    const ctx = canvas.getContext('2d'); ctx.scale(dpr, dpr);
    const w = rect.width, h = rect.height, pad = { left: 4, right: 5, top: 12, bottom: 8 }, plotH = h - pad.top - pad.bottom, plotW = w - pad.left - pad.right;
    ctx.clearRect(0, 0, w, h);
    [50,70,90,110,130].forEach(v => { const y = pad.top + (130 - v) / 80 * plotH; ctx.beginPath(); ctx.setLineDash([3,5]); ctx.strokeStyle = '#edf0f6'; ctx.lineWidth = 1; ctx.moveTo(pad.left,y); ctx.lineTo(w-pad.right,y); ctx.stroke(); });
    const count = Number($('#chartRange').value || 20); const data = readings.slice(-count); if (data.length < 2) return;
    const x = i => pad.left + (i/(data.length-1))*plotW; const y = v => pad.top + (130 - Math.max(45,Math.min(135,v)))/80*plotH;
    ctx.beginPath(); data.forEach((r,i) => i ? ctx.lineTo(x(i),y(r.hr)) : ctx.moveTo(x(i),y(r.hr))); ctx.lineTo(x(data.length-1),h-pad.bottom); ctx.lineTo(x(0),h-pad.bottom); ctx.closePath(); const grad = ctx.createLinearGradient(0,pad.top,0,h); grad.addColorStop(0,'rgba(125,119,230,.22)'); grad.addColorStop(1,'rgba(125,119,230,0)'); ctx.fillStyle=grad; ctx.fill();
    ctx.beginPath(); data.forEach((r,i) => i ? ctx.lineTo(x(i),y(r.hr)) : ctx.moveTo(x(i),y(r.hr))); ctx.strokeStyle='#807be5'; ctx.lineWidth=2.5; ctx.lineJoin='round'; ctx.lineCap='round'; ctx.stroke();
    const last=data[data.length-1]; ctx.beginPath(); ctx.arc(x(data.length-1),y(last.hr),4,0,Math.PI*2); ctx.fillStyle='#807be5'; ctx.fill(); ctx.strokeStyle='#fff'; ctx.lineWidth=2; ctx.stroke();
  }
  function updateMetrics(r = readings[readings.length-1]) {
    if (!r) return;
    $('#heartRate').textContent = Math.round(r.hr); $('#hrvValue').textContent = Math.round(r.hrv); $('#edaValue').textContent = Number(r.eda).toFixed(1); $('#movementValue').textContent = r.movement;
    const elevated = state.scenario === 'elevated'; const active = state.scenario === 'activity';
    $('#heartTrend').textContent = elevated ? '↑ Above demo baseline' : active ? '↑ Activity context' : '↘ Within baseline'; $('#heartTrend').className = `trend ${elevated ? 'warning' : active ? 'neutral' : 'calm'}`;
    $('#hrvTrend').textContent = elevated ? 'Below demo baseline' : active ? 'Activity can affect HRV' : 'Stable sample'; $('#hrvTrend').className = `trend ${elevated ? 'warning' : 'calm'}`;
    $('#edaTrend').textContent = elevated ? 'Elevated sample' : 'Low variation'; $('#edaTrend').className = `trend ${elevated ? 'warning' : 'calm'}`;
    $('#movementTrend').textContent = active ? 'Movement detected' : 'Low movement'; $('#movementUnit').textContent = active ? 'context' : 'activity';
    const panel = $('.state-panel'); panel.classList.toggle('elevated', elevated);
    $('#stateBadge').className = `state-badge ${elevated ? 'elevated' : 'normal'}`; $('#stateBadge').innerHTML = `<i></i> ${elevated ? 'ELEVATED PATTERN' : active ? 'ACTIVITY CONTEXT' : 'WITHIN BASELINE'}`;
    $('#stateTitle').textContent = elevated ? 'Let’s pause for a moment.' : active ? 'Movement may explain the change.' : 'Your sample looks steady.';
    $('#stateDescription').textContent = elevated ? 'Several synthetic signals differ from the example baseline while movement is low. This is not a diagnosis and can have many causes.' : active ? 'Heart rate can rise during movement. The demo uses activity context to avoid interpreting this pattern as anxiety.' : 'The simulated signals are close to the example baseline. Take a pause whenever it feels useful.';
    $('#lastUpdated').textContent = `Updated ${new Date().toLocaleTimeString([], {hour:'2-digit',minute:'2-digit',second:'2-digit'})}`;
    drawChart();
  }
  function setScenario(name, log = true) {
    state.scenario = name; const names = { normal:'Normal activity', elevated:'Elevated physiological pattern', activity:'Movement / exercise context' };
    if (name === 'elevated') { for (let i=0;i<8;i++) readings.push(sampleReading(name)); }
    else { readings.push(sampleReading(name)); }
    readings = readings.slice(-100); updateMetrics(readings[readings.length-1]);
    if (log) { addEvent('episode', names[name], name === 'elevated' ? 'Synthetic heart rate and EDA increased while movement stayed low. The app offered a support prompt; this does not confirm anxiety.' : name === 'activity' ? 'Synthetic heart rate increased alongside movement context, demonstrating why activity must be considered.' : 'The simulator returned to stable example values.', name === 'elevated' ? 'Support offered' : 'Scenario'); toast(`${names[name]} scenario loaded. Synthetic data only.`); }
    persist();
  }
  $('#simulateBtn').addEventListener('click', () => { setScenario('elevated'); go('support'); });
  $('#resetDemo').addEventListener('click', () => { state.scenario = 'normal'; seedReadings(); updateMetrics(); addEvent('episode','Demo reset','The simulator was returned to its normal example pattern.','Reset'); toast('Demo readings reset.'); });
  $('#chartRange').addEventListener('change', drawChart);
  $('#monitoringToggle').addEventListener('change', e => { state.monitoring = e.target.checked; persist(); toast(e.target.checked ? 'Simulated monitoring enabled.' : 'Simulated monitoring paused.'); });
  window.addEventListener('resize', () => requestAnimationFrame(drawChart));
  setInterval(() => { if (!state.monitoring) return; readings.push(sampleReading()); readings = readings.slice(-100); updateMetrics(); }, 3500);

  function setExercise(which) {
    exercise = which; stopBreathing(); $$('.exercise-tabs button').forEach(b => b.classList.toggle('selected', b.dataset.exerciseTab === which));
    if (which === 'grounding') { $('#exerciseTitle').textContent = '5–4–3–2–1 grounding'; $('#exerciseSubtitle').textContent = 'Gently reconnect with the present'; $('#breathPrompt').textContent = 'Notice'; $('#breathCount').textContent = '5 things you see · 4 you feel · 3 you hear · 2 you smell · 1 you taste'; $('#breathStart').textContent = 'Start grounding'; }
    else { $('#exerciseTitle').textContent = 'Paced breathing'; $('#exerciseSubtitle').textContent = 'Breathe in for 4 seconds, out for 6'; $('#breathPrompt').textContent = 'Ready?'; $('#breathCount').textContent = 'A minute just for you'; $('#breathStart').textContent = 'Start exercise'; }
  }
  $$('[data-exercise-tab]').forEach(b => b.addEventListener('click', () => setExercise(b.dataset.exerciseTab)));
  $('#breathStart').addEventListener('click', startExercise); $('#breathStop').addEventListener('click', stopBreathing);
  function startExercise() {
    if (breathing) return;
    breathing = true; breathRemaining = 60; $('#breathStart').textContent = 'In progress…'; $('#breathCount').textContent = 'Follow along at your own pace';
    if (exercise === 'grounding') { $('#breathPrompt').textContent = '5 things'; $('#breathCount').textContent = 'Name 5 things you see, 4 you feel, 3 you hear, 2 you smell, 1 you taste.'; addEvent('checkin','Grounding exercise started','5–4–3–2–1 grounding instructions were shown.','Support'); state.sessions++; persist(); renderHistory(); return; }
    let inhale = true; function phase() { if (!breathing) return; $('#breathPrompt').textContent = inhale ? 'Breathe in' : 'Breathe out'; $('#breathingStage').classList.toggle('breathing-in', inhale); $('#breathingStage').classList.toggle('breathing-out', !inhale); phaseTimer = setTimeout(() => { inhale = !inhale; phase(); }, inhale ? 4000 : 6000); } phase();
    breathTimer = setInterval(() => { breathRemaining--; $('#breathCount').textContent = `${breathRemaining} seconds remaining · no rush`; if (breathRemaining <= 0) { stopBreathing(); state.sessions++; addEvent('checkin','Breathing session completed','A one-minute paced breathing session was completed in the demo.','Completed'); persist(); toast('Session complete. Notice how you feel.'); } },1000);
    addEvent('checkin','Breathing session started','Paced breathing was started in the demo.','Support'); state.sessions++; persist();
  }
  function stopBreathing() { const wasBreathing = breathing; breathing = false; clearInterval(breathTimer); clearTimeout(phaseTimer); $('#breathingStage').classList.remove('breathing-in','breathing-out'); $('#breathPrompt').textContent = exercise === 'grounding' ? 'Notice' : 'Ready?'; $('#breathStart').textContent = exercise === 'grounding' ? 'Start grounding' : 'Start exercise'; if (wasBreathing) $('#breathCount').textContent = 'Paused — restart whenever you like'; }
  $$('#moodOptions button').forEach(b => b.addEventListener('click', () => { $$('#moodOptions button').forEach(x => x.classList.remove('selected')); b.classList.add('selected'); }));
  $('#saveCheckin').addEventListener('click', () => { const mood = $('#moodOptions .selected')?.dataset.mood; const note = $('#checkinNote').value.trim(); if (!mood && !note) { toast('Choose a feeling or add a short note first.'); return; } state.checkins++; addEvent('checkin',`Check-in saved${mood ? ` · ${mood}` : ''}`,note || 'No note added. User feedback saved locally.','Saved'); $('#checkinNote').value = ''; $$('#moodOptions button').forEach(x => x.classList.remove('selected')); persist(); toast('Check-in saved in this browser.'); });
  $('#needHelpBtn').addEventListener('click', triggerEmergencyDispatch);
  $('#imOkayBtn').addEventListener('click', () => { stopBreathing(); addEvent('checkin','Check-in closed','The user selected “I’m okay”.','Resolved'); toast('Check-in closed. You can return any time.'); go('dashboard'); });

  function renderHistory() {
    const target = $('#timeline'); if (!target) return; const filter = $('#historyFilter').value;
    const items = state.episodes.filter(e => filter === 'all' || (filter === 'episode' && e.type === 'episode') || (filter === 'checkin' && e.type === 'checkin') || (filter === 'help' && e.type === 'help'));
    $('#episodeCount').textContent = state.episodes.length; $('#sessionCount').textContent = state.sessions; $('#checkinCount').textContent = state.checkins;
    if (!items.length) { target.innerHTML = '<div class="empty-state">No activity yet. Try a demo scenario or save a check-in.</div>'; return; }
    target.innerHTML = items.map(e => `<div class="timeline-item ${e.type === 'help' ? 'help' : ''}"><div class="timeline-marker">${e.type === 'help' ? '♡' : e.type === 'episode' ? '⌁' : '◷'}</div><div><h4>${escapeHTML(e.title)}</h4><p>${escapeHTML(e.description)}</p><span class="timeline-tag">${escapeHTML(e.tag)}</span></div><time>${escapeHTML(e.time || timeLabel(new Date(e.timestamp)))}</time></div>`).join('');
  }
  $('#historyFilter').addEventListener('change', renderHistory);
  $('#exportHistory').addEventListener('click', () => { const blob = new Blob([JSON.stringify({ exported_at:new Date().toISOString(), source:'MindEase AI browser demo', episodes:state.episodes },null,2)],{type:'application/json'}); const url=URL.createObjectURL(blob); const a=document.createElement('a'); a.href=url; a.download='mindease-demo-history.json'; a.click(); URL.revokeObjectURL(url); toast('Activity export prepared.'); });
  $('#clearHistory').addEventListener('click', () => { if (!confirm('Clear all locally saved demo activity? This cannot be undone.')) return; state.episodes=[]; state.sessions=0; state.checkins=0; persist(); renderHistory(); toast('Local demo history cleared.'); });

  function renderContacts() { const el=$('#contactsList'); if (!state.contacts.length) { el.innerHTML='<div class="empty-state">No demo contacts yet. Add a contact placeholder to test the interface.</div>'; return; } el.innerHTML=state.contacts.map((c,i)=>`<div class="contact-row"><div class="contact-avatar">${escapeHTML(c.initials || initials(c.name))}</div><div class="contact-info"><strong>${escapeHTML(c.name)}</strong><span>${escapeHTML(c.relation || 'Trusted contact · Demo only')}</span></div><span class="contact-state">DEMO</span><button class="remove-contact icon-button" data-index="${i}" aria-label="Remove ${escapeHTML(c.name)}">×</button></div>`).join(''); $$('.remove-contact').forEach(b=>b.addEventListener('click',()=>{state.contacts.splice(Number(b.dataset.index),1);persist();renderContacts();toast('Demo contact removed.');})); }
  function initials(name) { return String(name).trim().split(/\s+/).slice(0,2).map(x=>x[0]?.toUpperCase()||'').join(''); }
  $('#addContact').addEventListener('click',()=>{const name=prompt('Enter a demo contact name:');if(!name?.trim())return;state.contacts.push({name:name.trim(),relation:'Added for demo · No messages sent',initials:initials(name)});persist();renderContacts();toast('Demo contact added locally.');});
  $('#saveContactPrefs').addEventListener('click',()=>{state.contactPrefs={ask:$('#askBeforeNotify').checked,share:$('#shareSummary').checked};persist();$('#contactPrefsStatus').textContent='Preferences saved in this browser.';toast('Preferences saved locally.');});

  function addChatMessage(role, text) { const row=document.createElement('div'); row.className=`chat-message ${role}`; const avatar=document.createElement('span'); avatar.className='chat-avatar'; avatar.textContent=role==='assistant'?'✦':'You'; const p=document.createElement('p'); p.textContent=text; row.append(avatar,p); $('#chatMessages').append(row); $('#chatMessages').scrollTop=$('#chatMessages').scrollHeight; }
  async function askBackend(message) { const base=($('#apiBase').value || state.apiBase || 'http://localhost:8000').trim().replace(/\/$/,''); const response=await fetch(`${base}/api/v1/chat`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({message})}); if(!response.ok) throw new Error('AI endpoint unavailable'); const data=await response.json(); if(!data.reply) throw new Error('No reply returned'); return data.reply; }
  $('#chatForm').addEventListener('submit', async e=>{e.preventDefault();if(chatBusy)return;const input=$('#chatInput');const message=input.value.trim();if(!message)return;input.value='';addChatMessage('user',message);chatBusy=true;$('#chatSend').disabled=true;$('#chatSend').textContent='Thinking…';let reply;try{reply=await askBackend(message);$('#aiStatus').textContent='BACKEND CONNECTED';$('#assistantMode').textContent='Reply received from the backend chat endpoint';}catch{reply=localReflections[Math.floor(Math.random()*localReflections.length)];$('#aiStatus').textContent='LOCAL FALLBACK';$('#assistantMode').textContent='Backend AI is unavailable; using a local supportive response';}addChatMessage('assistant',reply);chatBusy=false;$('#chatSend').disabled=false;$('#chatSend').innerHTML='Send <span>↑</span>'; });

  async function testBackend(showToast=true) { const base=($('#apiBase').value || state.apiBase || 'http://localhost:8000').trim().replace(/\/$/,''); const status=$('#backendStatus'); const detail=$('#backendDetail'); const footer=$('#apiFooter'); status.textContent='Checking'; status.classList.remove('online'); try { const res=await fetch(`${base}/health`,{signal:AbortSignal.timeout(2500)}); if(!res.ok)throw new Error('API returned an error'); const data=await res.json(); status.textContent='Connected'; status.classList.add('online'); detail.textContent=`${data.app || 'Backend'} · database ${data.database || 'status unknown'}`; footer.textContent='Backend connected'; if(showToast)toast('Backend connection successful.'); return true; } catch { status.textContent='Offline'; status.classList.remove('online'); detail.textContent='Local simulation works without the backend.'; footer.textContent='Backend offline · demo mode'; if(showToast)toast('Backend unavailable. The local demo still works.'); return false; } }
  $('#saveApiBase').addEventListener('click',()=>{state.apiBase=$('#apiBase').value.trim().replace(/\/$/,'')||'http://localhost:8000';$('#apiBase').value=state.apiBase;persist();testBackend(true);});
  $('#privacyReset').addEventListener('click',()=>{if(!confirm('Reset demo settings and contacts? Saved episode history will remain.'))return;state.monitoring=true;state.contactPrefs={ask:true,share:false};state.contacts=[];$('#monitoringToggle').checked=true;$('#askBeforeNotify').checked=true;$('#shareSummary').checked=false;persist();renderContacts();toast('Demo preferences reset.');});
  async function triggerEmergencyDispatch() {
    const btn = $('#needHelpBtn');
    if (btn) { btn.disabled = true; btn.textContent = 'Dispatching alerts…'; }
    const base = ($('#apiBase').value || state.apiBase || 'http://localhost:8000').trim().replace(/\/$/, '');
    const customContacts = (state.contacts || []).map(c => ({
      name: c.name,
      relationship: c.relation || 'Trusted Contact',
      phone: c.phone || '+1-555-0100',
      email: c.email || 'contact@mindease.ai',
      is_primary: true
    }));
    const payload = {
      severity: state.scenario === 'elevated' ? 9.2 : 8.0,
      notes: 'User triggered urgent assistance via support panel.',
      custom_contacts: customContacts.length ? customContacts : undefined,
      channels: ['sms', 'in_app'],
      simulate_only: true
    };
    try {
      const res = await fetch(`${base}/api/v1/emergency/dispatch`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      if (!res.ok) throw new Error('Emergency service unavailable');
      const data = await res.json();
      const contactsText = (data.contacts_alerted || []).map(c => `• <strong>${escapeHTML(c.name)}</strong>: ${escapeHTML(c.status)}`).join('<br>');
      const hotlinesText = (data.hotlines || []).slice(0, 4).map(h => `• <strong>${escapeHTML(h.name)}</strong>: <a href="tel:${escapeHTML(h.number.replace(/[^0-9]/g, ''))}" style="color:#4f46e5;font-weight:600;">${escapeHTML(h.number)}</a> (${escapeHTML(h.available)})`).join('<br>');
      const modalHtml = `
        <div style="text-align: left; margin: 10px 0; font-size: 0.92rem; line-height: 1.5;">
          <div style="background: #fef2f2; border: 1px solid #fecaca; border-radius: 8px; padding: 10px 12px; margin-bottom: 12px; color: #991b1b;">
            <strong>🚨 Dispatch ID: ${escapeHTML(data.dispatch_id)}</strong> (${escapeHTML(data.status)})<br>
            ${data.alerts_created} simulated emergency alert(s) recorded in audit logs.
          </div>
          <div style="margin-bottom: 10px;">
            <strong style="color: #374151;">Notified Contacts:</strong><br>
            ${contactsText || 'Primary Caregiver (+1-555-0199)'}
          </div>
          <div style="margin-bottom: 12px;">
            <strong style="color: #374151;">24/7 Crisis Helplines (Free & Confidential):</strong><br>
            ${hotlinesText}
          </div>
          <div style="background: #f0fdf4; border: 1px solid #bbf7d0; border-radius: 8px; padding: 10px 12px; color: #166534; font-size: 0.86rem;">
            <strong>Immediate Coping Guide:</strong> Place both feet firmly on the floor. Take a slow 4-second breath in, and gently exhale for 6 seconds. You are safe in this moment.
          </div>
        </div>
      `;
      addEvent('help', `Emergency Alert · ${data.dispatch_id}`, `Dispatched ${data.alerts_created} simulated alerts to emergency contacts.`, 'Emergency SOS');
      $('#helpFeedback').textContent = `Alert logged (${data.dispatch_id}). Simulated SOS dispatched to contacts.`;
      openModal('Emergency Support Initiated', modalHtml, true);
    } catch (err) {
      addEvent('help', 'Help request recorded (Local mode)', 'User pressed “I need help”. Displayed 24/7 crisis hotlines.', 'Offline SOS');
      $('#helpFeedback').textContent = 'Help request recorded locally.';
      const fallbackHtml = `
        <div style="text-align: left; margin: 10px 0; font-size: 0.92rem; line-height: 1.6;">
          <p style="margin-bottom: 10px;">If you are in immediate danger, please dial your local emergency services directly:</p>
          <p>
            • <strong>US / Canada:</strong> Call or text <a href="tel:988" style="color:#4f46e5;font-weight:600;">988</a> (Crisis Lifeline) or <a href="tel:911" style="color:#4f46e5;font-weight:600;">911</a><br>
            • <strong>Crisis Text Line:</strong> Text HOME to <a href="sms:741741" style="color:#4f46e5;font-weight:600;">741741</a><br>
            • <strong>UK:</strong> Call <a href="tel:111" style="color:#4f46e5;font-weight:600;">111</a> (NHS) or <a href="tel:999" style="color:#4f46e5;font-weight:600;">999</a><br>
            • <strong>EU / India:</strong> Call <a href="tel:112" style="color:#4f46e5;font-weight:600;">112</a> (Emergency Services)
          </p>
        </div>
      `;
      openModal('Emergency Assistance', fallbackHtml, true);
    } finally {
      if (btn) { btn.disabled = false; btn.innerHTML = '♡ &nbsp; I need help'; }
    }
  }

  function openModal(title,text,isHtml=false){$('#modalTitle').textContent=title; if(isHtml){$('#modalText').innerHTML=text;}else{$('#modalText').textContent=text;} $('#modalBackdrop').classList.add('open');$('#modalOkay').focus();}
  function closeModal(){$('#modalBackdrop').classList.remove('open');}
  $('#helpBtn').addEventListener('click',()=>openModal('About MindEase AI','MindEase AI is a browser-based wellness-support prototype. Sensor values are synthetic. The system does not diagnose anxiety, connect to a real wearable, or send emergency notifications. Use the support tools only if they feel comfortable. If you need urgent help, contact a trusted person or local emergency services directly.'));
  $('#profileMenu').addEventListener('click',()=>openModal('Demo profile','This prototype stores demo preferences and activity in your current browser using local storage. Avoid entering identifying or highly sensitive information.'));
  $('#modalClose').addEventListener('click',closeModal);$('#modalOkay').addEventListener('click',closeModal);$('#modalBackdrop').addEventListener('click',e=>{if(e.target.id==='modalBackdrop')closeModal();});document.addEventListener('keydown',e=>{if(e.key==='Escape')closeModal();});

  // Restore persisted preferences, initialize chart, and check backend availability.
  $('#apiBase').value=state.apiBase; $('#monitoringToggle').checked=state.monitoring; $('#askBeforeNotify').checked=state.contactPrefs.ask; $('#shareSummary').checked=state.contactPrefs.share;
  seedReadings(); for(let i=0;i<readings.length;i++){const r=readings[i];r.hr+=Math.sin(i/4)*1.1;} updateMetrics(); renderHistory(); renderContacts(); testBackend(false);
})();
