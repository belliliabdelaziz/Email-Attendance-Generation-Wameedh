/* ==========================================
   WAMEEDH SC BOOTCAMP — ATTENDANCE SYSTEM
   app.js
   ========================================== */

// ─── State ────────────────────────────────────────────────────────────────────
let participants = [];   // [{email, first, last, group, r1, r2, r3, r4}]
let qrDataURLs   = {};   // name → dataURL

// ─── DOM refs ─────────────────────────────────────────────────────────────────
const tableBody      = document.getElementById('tableBody');
const tableEmpty     = document.getElementById('tableEmpty');
const statTotal      = document.getElementById('statTotal');
const statGroup1     = document.getElementById('statGroup1');
const statGroup2     = document.getElementById('statGroup2');
const statGroup3     = document.getElementById('statGroup3');
const statGroup4     = document.getElementById('statGroup4');
const searchInput    = document.getElementById('searchInput');
const filterGroup    = document.getElementById('filterGroup');
const sendLog        = document.getElementById('sendLog');
const qrPreviewArea  = document.getElementById('qrPreviewArea');
const configPreview  = document.getElementById('configPreview');

// ─── Navigation ───────────────────────────────────────────────────────────────
document.querySelectorAll('.nav-item').forEach(item => {
  item.addEventListener('click', e => {
    e.preventDefault();
    const page = item.dataset.page;
    document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
    document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
    item.classList.add('active');
    document.getElementById('page-' + page).classList.add('active');

    if (page === 'qr') refreshConfigPreview();
  });
});

// ─── Toast ────────────────────────────────────────────────────────────────────
function toast(msg, type = 'info') {
  const el = document.getElementById('toast');
  el.textContent = msg;
  el.className = `toast show ${type}`;
  clearTimeout(el._timer);
  el._timer = setTimeout(() => el.classList.remove('show'), 3400);
}

// ─── Helpers ──────────────────────────────────────────────────────────────────
function makeRow() {
  return { email: '', first: '', last: '', group: 1, r1: 0, r2: 0, r3: 0, r4: 0 };
}

function fullName(p) { return `${p.first} ${p.last}`.trim(); }

function updateStats() {
  statTotal.textContent  = participants.length;
  statGroup1.textContent = participants.filter(p => +p.group === 1).length;
  statGroup2.textContent = participants.filter(p => +p.group === 2).length;
  statGroup3.textContent = participants.filter(p => +p.group === 3).length;
  statGroup4.textContent = participants.filter(p => +p.group === 4).length;
}

// ─── Render Table ─────────────────────────────────────────────────────────────
function renderTable() {
  const search  = searchInput.value.toLowerCase();
  const gFilter = filterGroup.value;

  const filtered = participants.filter((p, i) => {
    const matchSearch = !search ||
      fullName(p).toLowerCase().includes(search) ||
      p.email.toLowerCase().includes(search);
    const matchGroup = !gFilter || String(p.group) === gFilter;
    return matchSearch && matchGroup;
  });

  tableBody.innerHTML = '';
  updateStats();

  if (participants.length === 0) {
    tableEmpty.classList.add('show');
    return;
  }
  tableEmpty.classList.remove('show');

  filtered.forEach((p, displayIdx) => {
    const realIdx = participants.indexOf(p);
    const g = +p.group;
    const gClass = ['', 'g1', 'g2', 'g3', 'g4'][g] || 'g1';

    const tr = document.createElement('tr');
    tr.innerHTML = `
      <td class="row-num">${realIdx + 1}</td>
      <td><input type="email" value="${esc(p.email)}" data-field="email" data-idx="${realIdx}" placeholder="email@example.com" /></td>
      <td><input type="text"  value="${esc(p.first)}" data-field="first" data-idx="${realIdx}" placeholder="First" /></td>
      <td><input type="text"  value="${esc(p.last)}"  data-field="last"  data-idx="${realIdx}" placeholder="Last" /></td>
      <td>
        <select data-field="group" data-idx="${realIdx}" class="filter-select" style="padding:5px 8px;font-size:12px;border-radius:7px;">
          <option ${g===1?'selected':''}>1</option>
          <option ${g===2?'selected':''}>2</option>
          <option ${g===3?'selected':''}>3</option>
          <option ${g===4?'selected':''}>4</option>
        </select>
      </td>
      <td style="text-align:center"><input type="checkbox" ${+p.r1?'checked':''} data-field="r1" data-idx="${realIdx}" /></td>
      <td style="text-align:center"><input type="checkbox" ${+p.r2?'checked':''} data-field="r2" data-idx="${realIdx}" /></td>
      <td style="text-align:center"><input type="checkbox" ${+p.r3?'checked':''} data-field="r3" data-idx="${realIdx}" /></td>
      <td style="text-align:center"><input type="checkbox" ${+p.r4?'checked':''} data-field="r4" data-idx="${realIdx}" /></td>
      <td>
        <button class="delete-btn" data-idx="${realIdx}" title="Delete">
          <svg viewBox="0 0 24 24"><polyline points="3 6 5 6 21 6"/><path d="M19 6l-1 14H6L5 6"/><path d="M10 11v6"/><path d="M14 11v6"/><path d="M9 6V4h6v2"/></svg>
        </button>
      </td>
    `;
    tableBody.appendChild(tr);
  });

  // Events
  tableBody.querySelectorAll('input[data-field], select[data-field]').forEach(el => {
    el.addEventListener('change', () => {
      const idx   = +el.dataset.idx;
      const field = el.dataset.field;
      participants[idx][field] = el.type === 'checkbox' ? (el.checked ? 1 : 0) : el.value;
      if (['email','first','last','group'].includes(field)) updateStats();
      if (field === 'group') renderTable();
    });
    el.addEventListener('input', () => {
      const idx   = +el.dataset.idx;
      const field = el.dataset.field;
      if (el.type !== 'checkbox') participants[idx][field] = el.value;
    });
  });

  tableBody.querySelectorAll('.delete-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      participants.splice(+btn.dataset.idx, 1);
      renderTable();
      toast('Row deleted', 'info');
    });
  });
}

function esc(s) { return String(s).replace(/"/g, '&quot;'); }

// ─── Add Row ──────────────────────────────────────────────────────────────────
document.getElementById('addRowBtn').addEventListener('click', () => {
  participants.push(makeRow());
  searchInput.value = '';
  filterGroup.value = '';
  renderTable();
  // Scroll to bottom of table
  const wrap = document.querySelector('.table-wrap');
  wrap.scrollTop = wrap.scrollHeight;
});

// ─── Search / Filter ──────────────────────────────────────────────────────────
searchInput.addEventListener('input', renderTable);
filterGroup.addEventListener('change', renderTable);

// ─── CSV Import ───────────────────────────────────────────────────────────────
document.getElementById('csvUpload').addEventListener('change', function () {
  const file = this.files[0];
  if (!file) return;
  const reader = new FileReader();
  reader.onload = e => {
    const lines = e.target.result.split('\n').map(l => l.trim()).filter(Boolean);
    const parsed = [];
    for (const line of lines) {
      const cols = line.split(',').map(c => c.trim());
      if (cols.length < 3) continue;
      parsed.push({
        email: cols[0] || '',
        first: cols[1] || '',
        last:  cols[2] || '',
        group: cols[3] || 1,
        r1:    cols[4] || 0,
        r2:    cols[5] || 0,
        r3:    cols[6] || 0,
        r4:    cols[7] || 0,
      });
    }
    participants = parsed;
    renderTable();
    toast(`Imported ${parsed.length} participants`, 'success');
  };
  reader.readAsText(file);
  this.value = '';
});

// ─── CSV Export ───────────────────────────────────────────────────────────────
document.getElementById('exportCsvBtn').addEventListener('click', () => {
  if (!participants.length) { toast('Nothing to export', 'error'); return; }
  const rows = participants.map(p =>
    [p.email, p.first, p.last, p.group, p.r1, p.r2, p.r3, p.r4].join(',')
  );
  downloadText(rows.join('\n'), 'participants.csv', 'text/csv');
  toast('CSV exported!', 'success');
});

// ─── QR Generation (browser-side via QR API) ──────────────────────────────────
document.getElementById('generateQrBtn').addEventListener('click', async () => {
  if (!participants.length) { toast('No participants to generate QR for', 'error'); return; }

  qrPreviewArea.innerHTML = '<div class="qr-placeholder"><svg viewBox="0 0 24 24"><rect x="3" y="3" width="7" height="7"/><rect x="14" y="3" width="7" height="7"/><rect x="3" y="14" width="7" height="7"/></svg><span>Generating…</span></div>';
  qrDataURLs = {};

  // Use QR Server API to generate QR codes
  await new Promise(r => setTimeout(r, 100));

  qrPreviewArea.innerHTML = '';
  let count = 0;

  for (const p of participants) {
    const name = fullName(p);
    if (!name.trim()) continue;

    const url = `https://api.qrserver.com/v1/create-qr-code/?size=200x200&data=${encodeURIComponent(name)}`;

    const item = document.createElement('div');
    item.className = 'qr-item';

    const img = document.createElement('img');
    img.src = url;
    img.alt = name;
    img.crossOrigin = 'anonymous';

    const label = document.createElement('span');
    label.textContent = name;

    item.appendChild(img);
    item.appendChild(label);
    qrPreviewArea.appendChild(item);

    // On click: download this QR
    item.addEventListener('click', () => {
      const a = document.createElement('a');
      a.href = url;
      a.download = name.replace(/ /g, '_') + '.png';
      a.target = '_blank';
      a.click();
    });

    // Store for ZIP download
    img.onload = () => {
      const canvas = document.createElement('canvas');
      canvas.width = img.naturalWidth;
      canvas.height = img.naturalHeight;
      canvas.getContext('2d').drawImage(img, 0, 0);
      qrDataURLs[name] = canvas.toDataURL('image/png');
    };

    count++;
  }

  toast(`Generated ${count} QR codes`, 'success');
  document.getElementById('downloadAllBtn').style.display = 'flex';
});

// ─── Download All QRs as ZIP ──────────────────────────────────────────────────
document.getElementById('downloadAllBtn').addEventListener('click', async () => {
  if (!Object.keys(qrDataURLs).length) { toast('Generate QR codes first', 'error'); return; }

  // Use JSZip if available via CDN, otherwise download individually
  if (typeof JSZip === 'undefined') {
    // fallback: download each one individually (just first 5 to avoid spam)
    const entries = Object.entries(qrDataURLs);
    for (const [name, dataURL] of entries) {
      const a = document.createElement('a');
      a.href = dataURL;
      a.download = name.replace(/ /g, '_') + '.png';
      a.click();
      await new Promise(r => setTimeout(r, 200));
    }
    toast('QR codes downloaded individually', 'success');
    return;
  }

  const zip = new JSZip();
  for (const [name, dataURL] of Object.entries(qrDataURLs)) {
    const base64 = dataURL.split(',')[1];
    zip.file(name.replace(/ /g, '_') + '.png', base64, { base64: true });
  }
  const blob = await zip.generateAsync({ type: 'blob' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = 'qr_codes.zip';
  a.click();
  URL.revokeObjectURL(url);
  toast('ZIP downloaded!', 'success');
});

// ─── Email Config ─────────────────────────────────────────────────────────────
function getEmailConfig() {
  return {
    smtp_host:    document.getElementById('smtpHost').value.trim(),
    smtp_port:    +document.getElementById('smtpPort').value,
    smtp_use_ssl: document.getElementById('smtpSSL').checked,
    smtp_user:    document.getElementById('smtpSender').value.trim(),
    smtp_pass:    document.getElementById('smtpPass').value,
    sender:       document.getElementById('smtpSender').value.trim(),
    subject:      document.getElementById('emailSubject').value.trim(),
    headline:     document.getElementById('emailHeadline').value.trim(),
    greeting:     document.getElementById('emailGreeting').value.trim(),
  };
}

function logLine(msg, type = 'info') {
  sendLog.style.display = 'flex';
  const div = document.createElement('div');
  div.textContent = msg;
  div.className = `log-${type}`;
  sendLog.appendChild(div);
  sendLog.scrollTop = sendLog.scrollHeight;
}

const API = 'http://localhost:5050';

async function apiCall(endpoint, body) {
  const r = await fetch(API + endpoint, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body)
  });
  return r.json();
}

document.getElementById('testEmailBtn').addEventListener('click', async () => {
  const cfg = getEmailConfig();
  if (!cfg.smtp_user || !cfg.smtp_pass) {
    toast('Fill in sender email and password first', 'error');
    return;
  }
  sendLog.innerHTML = '';
  logLine(`ℹ Connecting to ${cfg.smtp_host}:${cfg.smtp_port}…`, 'info');
  document.getElementById('testEmailBtn').disabled = true;
  try {
    const res = await apiCall('/test', { email: cfg });
    if (res.ok) {
      logLine('✓ SMTP connection successful!', 'ok');
      toast('SMTP connection OK', 'success');
    } else {
      logLine('✗ ' + res.error, 'err');
      toast('Connection failed', 'error');
    }
  } catch (e) {
    logLine('✗ Could not reach local server.', 'err');
    logLine('ℹ Make sure server.py is running:  python server.py', 'info');
    toast('Local server not running — see log', 'error');
  } finally {
    document.getElementById('testEmailBtn').disabled = false;
  }
});

document.getElementById('sendAllBtn').addEventListener('click', async () => {
  if (!participants.length) { toast('No participants loaded', 'error'); return; }
  const cfg = getEmailConfig();
  if (!cfg.smtp_user || !cfg.smtp_pass) {
    toast('Fill in sender email and password first', 'error');
    return;
  }
  sendLog.innerHTML = '';
  document.getElementById('sendAllBtn').disabled = true;
  const toSend = participants.filter(p => p.email && p.email.includes('@'));
  logLine(`ℹ Sending to ${toSend.length} recipients…`, 'info');
  try {
    const res = await apiCall('/send', {
      email: cfg,
      participants: toSend.map(p => ({
        email: p.email.trim(),
        name: `${p.first} ${p.last}`.trim()
      })),
      qr_dir: document.getElementById('outputDir').value.trim() || 'qr_out'
    });
    if (res.results) {
      res.results.forEach(r => {
        if (r.ok) logLine(`✓ ${r.name} <${r.email}>`, 'ok');
        else      logLine(`✗ ${r.name}: ${r.error}`, 'err');
      });
      const ok  = res.results.filter(r => r.ok).length;
      const err = res.results.filter(r => !r.ok).length;
      logLine(`─ Done: ${ok} sent, ${err} failed`, 'info');
      toast(`${ok} emails sent, ${err} failed`, ok > 0 ? 'success' : 'error');
    } else {
      logLine('✗ ' + (res.error || 'Unknown error'), 'err');
      toast('Send failed', 'error');
    }
  } catch (e) {
    logLine('✗ Could not reach local server.', 'err');
    logLine('ℹ Run:  python server.py', 'info');
    toast('Local server not running — see log', 'error');
  } finally {
    document.getElementById('sendAllBtn').disabled = false;
  }
});

// ─── Config JSON ──────────────────────────────────────────────────────────────
function buildConfig() {
  const email = getEmailConfig();
  return {
    csvfile:    'participants.csv',
    session:    document.getElementById('globalSession').value,
    output_dir: document.getElementById('outputDir').value.trim() || 'qr_out',
    email: {
      smtp_host:        email.smtp_host,
      smtp_port:        email.smtp_port,
      smtp_use_ssl:     email.smtp_use_ssl,
      smtp_user:        email.smtp_user,
      smtp_pass:        email.smtp_pass,
      sender:           email.sender,
      subject:          email.subject,
      headline:         email.headline,
      greeting:         email.greeting,
      logo_path:        'logoBootcamp.png',
      brand_name:       'Wameedh SC Bootcamp',
      brand_primary:    '#0B4F6C',
      brand_accent:     '#F5B700',
      brand_background: '#F6F7FB',
      brand_text:       '#1F2933',
    }
  };
}

function refreshConfigPreview() {
  configPreview.textContent = JSON.stringify(buildConfig(), null, 2);
}

document.getElementById('refreshConfigBtn').addEventListener('click', refreshConfigPreview);

document.getElementById('downloadConfigBtn').addEventListener('click', () => {
  const cfg = buildConfig();
  downloadText(JSON.stringify(cfg, null, 2), 'config.json', 'application/json');
  toast('config.json downloaded!', 'success');
});

document.getElementById('downloadParticipantsBtn').addEventListener('click', () => {
  if (!participants.length) { toast('No participants to export', 'error'); return; }
  const rows = participants.map(p =>
    [p.email, p.first, p.last, p.group, p.r1, p.r2, p.r3, p.r4].join(',')
  );
  downloadText(rows.join('\n'), 'participants.csv', 'text/csv');
  toast('participants.csv downloaded!', 'success');
});

// ─── Util ─────────────────────────────────────────────────────────────────────
function downloadText(content, filename, mime) {
  const blob = new Blob([content], { type: mime });
  const url  = URL.createObjectURL(blob);
  const a    = document.createElement('a');
  a.href     = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}

// ─── Init ─────────────────────────────────────────────────────────────────────
renderTable();

// ─────────────────────────────────────────────────────────────────────────────
// SCANNER
// ─────────────────────────────────────────────────────────────────────────────

const ROOMS = ['C105', 'C117', 'C204', 'C206'];
const ROOM_SCHEDULE = [
  [1,2,3,4], [2,1,4,3], [3,4,1,2], [4,3,2,1]
];

let camStream       = null;
let scanInterval    = null;
let lastScanned     = '';
let lastScannedTime = 0;
let scanCounts      = { ok: 0, absent: 0, wrong: 0 };

const camVideo         = document.getElementById('camVideo');
const camCanvas        = document.getElementById('camCanvas');
const camStatus        = document.getElementById('camStatus');
const scanResultOverlay= document.getElementById('scanResultOverlay');
const scanResultIcon   = document.getElementById('scanResultIcon');
const scanResultName   = document.getElementById('scanResultName');
const scanResultMsg    = document.getElementById('scanResultMsg');
const scanLogList      = document.getElementById('scanLogList');
const startCamBtn      = document.getElementById('startCamBtn');
const stopCamBtn       = document.getElementById('stopCamBtn');
const cameraSelect     = document.getElementById('cameraSelect');
const scanCheckedIn    = document.getElementById('scanCheckedIn');
const scanAbsent       = document.getElementById('scanAbsent');
const scanWrong        = document.getElementById('scanWrong');

// Enumerate cameras on page load
async function populateCameras() {
  try {
    const devices = await navigator.mediaDevices.enumerateDevices();
    const cams = devices.filter(d => d.kind === 'videoinput');
    cameraSelect.innerHTML = '';
    cams.forEach((cam, i) => {
      const opt = document.createElement('option');
      opt.value = cam.deviceId;
      opt.textContent = cam.label || `Camera ${i + 1}`;
      cameraSelect.appendChild(opt);
    });
    if (!cams.length) {
      const opt = document.createElement('option');
      opt.textContent = 'No cameras found';
      cameraSelect.appendChild(opt);
    }
  } catch (e) {
    console.warn('Could not enumerate cameras:', e);
  }
}

// Call after permission is granted (labels only available after getUserMedia)
startCamBtn.addEventListener('click', async () => {
  try {
    const constraints = {
      video: {
        deviceId: cameraSelect.value ? { exact: cameraSelect.value } : undefined,
        width: { ideal: 1280 },
        height: { ideal: 720 },
        facingMode: 'environment'
      }
    };
    camStream = await navigator.mediaDevices.getUserMedia(constraints);
    camVideo.srcObject = camStream;
    await camVideo.play();

    camStatus.classList.add('hidden');
    startCamBtn.disabled = true;
    stopCamBtn.disabled  = false;
    document.querySelector('.cam-viewport').classList.add('scanning');

    // Re-enumerate cameras now we have permission (labels become available)
    await populateCameras();

    // Start QR decode loop
    scanInterval = setInterval(decodeFrame, 200);

    toast('Camera started — ready to scan', 'success');
  } catch (e) {
    toast('Could not access camera: ' + e.message, 'error');
    camStatus.querySelector('span').textContent = 'Camera access denied. Check browser permissions.';
  }
});

stopCamBtn.addEventListener('click', stopCamera);

function stopCamera() {
  clearInterval(scanInterval);
  scanInterval = null;
  if (camStream) {
    camStream.getTracks().forEach(t => t.stop());
    camStream = null;
  }
  camVideo.srcObject = null;
  camStatus.classList.remove('hidden');
  camStatus.querySelector('span').textContent = 'Click Start Camera to begin scanning';
  startCamBtn.disabled = false;
  stopCamBtn.disabled  = true;
  document.querySelector('.cam-viewport').classList.remove('scanning');
}

// Stop camera when leaving scanner page
document.querySelectorAll('.nav-item').forEach(item => {
  item.addEventListener('click', () => {
    if (item.dataset.page !== 'scanner' && camStream) stopCamera();
  });
});

function decodeFrame() {
  if (!camVideo.videoWidth) return;

  const ctx = camCanvas.getContext('2d');
  camCanvas.width  = camVideo.videoWidth;
  camCanvas.height = camVideo.videoHeight;
  ctx.drawImage(camVideo, 0, 0);

  const imageData = ctx.getImageData(0, 0, camCanvas.width, camCanvas.height);

  // jsQR is loaded from CDN
  if (typeof jsQR === 'undefined') {
    console.warn('jsQR not loaded yet');
    return;
  }

  const code = jsQR(imageData.data, imageData.width, imageData.height, {
    inversionAttempts: 'dontInvert'
  });

  if (!code) return;

  const name = code.data.trim();
  const now  = Date.now();

  // Debounce: same QR within 5 seconds = ignore
  if (name === lastScanned && (now - lastScannedTime) < 5000) return;

  lastScanned     = name;
  lastScannedTime = now;

  handleScan(name);
}

function removeSpaces(s) { return s.replace(/\s+/g, '').toLowerCase(); }

function getCorrectGroupForRoom(roomIdx) {
  const session = +document.getElementById('globalSession').value - 1;
  return ROOM_SCHEDULE[session][roomIdx - 1];
}

function handleScan(name) {
  if (!participants.length) {
    showResultFlash('⚠', name, 'No participants loaded. Go to Participants page first.', 'err');
    return;
  }

  const roomIdx = +document.getElementById('scanRoom').value;
  const correctGroup = getCorrectGroupForRoom(roomIdx);
  const roomName = ROOMS[roomIdx - 1];

  // Find participant by full name (case + space insensitive)
  const idx = participants.findIndex(p => {
    const full = `${p.first} ${p.last}`;
    return removeSpaces(full) === removeSpaces(name);
  });

  if (idx === -1) {
    // Not in list
    scanCounts.absent++;
    updateScanStats();
    addLogEntry(name, 'err', 'Not in participant list');
    showResultFlash('✗', name, 'Not in participant list', 'err');
    return;
  }

  const p = participants[idx];
  const pGroup = +p.group;

  if (pGroup !== correctGroup) {
    // Wrong room
    // Find which room they should be in
    const session = +document.getElementById('globalSession').value - 1;
    const correctRoomIdx = ROOM_SCHEDULE[session].indexOf(pGroup);
    const correctRoom = ROOMS[correctRoomIdx] || '?';
    scanCounts.wrong++;
    updateScanStats();
    addLogEntry(name, 'wrong', `Wrong room — go to ${correctRoom}`);
    showResultFlash('⚠', name, `Wrong room! Go to ${correctRoom}`, 'err');
    return;
  }

  // Mark attendance: r1/r2/r3/r4 based on room
  const roomKey = `r${roomIdx}`;
  if (participants[idx][roomKey] == 1) {
    // Already checked in
    addLogEntry(name, 'ok', 'Already checked in ✓');
    showResultFlash('✓', name, 'Already checked in', 'ok');
    return;
  }

  participants[idx][roomKey] = 1;
  scanCounts.ok++;
  updateScanStats();
  addLogEntry(name, 'ok', `Checked in — ${roomName}`);
  showResultFlash('✓', name, `Welcome! Checked in to ${roomName}`, 'ok');
}

function updateScanStats() {
  scanCheckedIn.textContent = scanCounts.ok;
  scanAbsent.textContent    = scanCounts.absent;
  scanWrong.textContent     = scanCounts.wrong;
}

function showResultFlash(icon, name, msg, type) {
  scanResultOverlay.className = 'scan-result-overlay show ' + (type === 'ok' ? 'ok-bg' : 'err-bg');
  scanResultIcon.textContent = icon;
  scanResultName.textContent = name;
  scanResultMsg.textContent  = msg;

  clearTimeout(scanResultOverlay._timer);
  scanResultOverlay._timer = setTimeout(() => {
    scanResultOverlay.className = 'scan-result-overlay hidden';
  }, 3000);
}

function addLogEntry(name, type, status) {
  const empty = scanLogList.querySelector('.scan-log-empty');
  if (empty) empty.remove();

  const now = new Date();
  const time = now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });

  const item = document.createElement('div');
  item.className = 'scan-log-item';
  item.innerHTML = `
    <div class="log-dot ${type}"></div>
    <div class="log-item-info">
      <div class="log-item-name">${name}</div>
      <div class="log-item-status">${status}</div>
    </div>
    <div class="log-item-time">${time}</div>
  `;

  scanLogList.insertBefore(item, scanLogList.firstChild);
}

document.getElementById('clearLogBtn').addEventListener('click', () => {
  scanLogList.innerHTML = '<div class="scan-log-empty">No scans yet</div>';
  scanCounts = { ok: 0, absent: 0, wrong: 0 };
  updateScanStats();
});

document.getElementById('exportAttendanceBtn').addEventListener('click', () => {
  if (!participants.length) { toast('No participants to export', 'error'); return; }
  const rows = participants.map(p =>
    [p.email, p.first, p.last, p.group, p.r1, p.r2, p.r3, p.r4].join(',')
  );
  const roomName = ROOMS[+document.getElementById('scanRoom').value - 1];
  downloadText(rows.join('\n'), `attendance_${roomName}.csv`, 'text/csv');
  toast(`Attendance for ${roomName} exported!`, 'success');
});

// Init cameras list (no labels until permission)
populateCameras();

// ─── Load config.json into Email Settings ────────────────────────────────────
document.getElementById('configJsonUpload').addEventListener('change', function () {
  const file = this.files[0];
  if (!file) return;
  const reader = new FileReader();
  reader.onload = e => {
    try {
      const cfg = JSON.parse(e.target.result);
      const em  = cfg.email || {};

      // Top-level fields
      if (cfg.session) document.getElementById('globalSession').value = cfg.session;
      if (cfg.room)    document.getElementById('scanRoom').value = cfg.room;

      // Email fields
      if (em.smtp_host !== undefined) document.getElementById('smtpHost').value    = em.smtp_host;
      if (em.smtp_port !== undefined) document.getElementById('smtpPort').value    = em.smtp_port;
      if (em.smtp_use_ssl !== undefined) document.getElementById('smtpSSL').checked = !!em.smtp_use_ssl;
      if (em.sender    !== undefined) document.getElementById('smtpSender').value  = em.sender;
      if (em.smtp_pass !== undefined) document.getElementById('smtpPass').value    = em.smtp_pass;
      if (em.subject   !== undefined) document.getElementById('emailSubject').value = em.subject;
      if (em.headline  !== undefined) document.getElementById('emailHeadline').value = em.headline;
      if (em.greeting  !== undefined) document.getElementById('emailGreeting').value = em.greeting;

      // Output dir if present
      if (cfg.output_dir) document.getElementById('outputDir').value = cfg.output_dir;

      refreshConfigPreview();
      toast('config.json loaded ✓', 'success');
    } catch (err) {
      toast('Invalid JSON file: ' + err.message, 'error');
    }
  };
  reader.readAsText(file);
  this.value = '';
});
