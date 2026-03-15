/* Dashboard JS */
const API = '';
const token = localStorage.getItem('deet_token');
const user = JSON.parse(localStorage.getItem('deet_user') || '{}');

// Auth guard
if (!token) window.location.href = '/';

// Populate user info
function initUser() {
  const name = user.full_name || 'User';
  document.getElementById('headerName').textContent = name;
  document.getElementById('sidebarName').textContent = name;
  const initials = name.split(' ').map(w => w[0]).join('').substring(0, 2).toUpperCase();
  document.getElementById('userAvatar').textContent = initials;
}

function authHeaders() {
  return { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json' };
}

// Load dashboard data
async function loadDashboard() {
  try {
    const [resumeRes, regRes] = await Promise.all([
      fetch(`${API}/api/resume/list`, { headers: authHeaders() }),
      fetch(`${API}/api/deet/list`, { headers: authHeaders() })
    ]);

    if (resumeRes.status === 401 || regRes.status === 401) {
      logout(); return;
    }

    const resumeData = await resumeRes.json();
    const regData = await regRes.json();

    const resumes = resumeData.resumes || [];
    const regs = regData.registrations || [];

    // Stats
    document.getElementById('statResumes').textContent = resumes.length;
    document.getElementById('statSubmitted').textContent = regs.filter(r => r.status === 'submitted').length;
    document.getElementById('statDrafts').textContent = regs.filter(r => r.status === 'draft').length;

    if (resumes.length > 0) {
      const latest = resumes[0];
      const score = latest.quality_score || 0;
      document.getElementById('statScore').textContent = `${score}/100`;
    }

    renderResumesTable(resumes);
    renderRegsTable(regs);

  } catch (err) {
    console.error('Dashboard load error:', err);
  }
}

function renderResumesTable(resumes) {
  const tbody = document.getElementById('resumesBody');
  if (!resumes.length) {
    tbody.innerHTML = '<tr><td colspan="5" class="empty-row">No resumes uploaded yet</td></tr>';
    return;
  }
  tbody.innerHTML = resumes.map(r => {
    const score = r.quality_score || 0;
    const scoreClass = score >= 70 ? 'score-high' : score >= 40 ? 'score-med' : 'score-low';
    const date = new Date(r.uploaded_at).toLocaleDateString();
    return `<tr>
      <td>${escHtml(r.filename)}</td>
      <td><span style="text-transform:uppercase;font-size:11px;color:var(--c-muted)">${r.file_type}</span></td>
      <td><span class="score-badge ${scoreClass}">${score}/100</span></td>
      <td>${date}</td>
      <td>
        <button class="action-btn primary-action" onclick="useResume(${r.id})">Fill Form →</button>
      </td>
    </tr>`;
  }).join('');
}

function renderRegsTable(regs) {
  const tbody = document.getElementById('regsBody');
  if (!regs.length) {
    tbody.innerHTML = '<tr><td colspan="4" class="empty-row">No registrations yet</td></tr>';
    return;
  }
  tbody.innerHTML = regs.map(r => {
    const statusClass = r.status === 'submitted' ? 'status-submitted' : 'status-draft';
    const created = new Date(r.created_at).toLocaleDateString();
    const submitted = r.submitted_at ? new Date(r.submitted_at).toLocaleDateString() : '—';
    return `<tr>
      <td><span style="font-family:var(--font-display);font-weight:700">DEET-${String(r.id).padStart(6,'0')}</span></td>
      <td><span class="status-pill ${statusClass}">${r.status}</span></td>
      <td>${created}</td>
      <td>${submitted}</td>
    </tr>`;
  }).join('');
}

function escHtml(s) {
  return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
}

function useResume(resumeId) {
  localStorage.setItem('deet_resume_id', resumeId);
  window.location.href = '/register-form';
}

// Upload modal
function openUploadModal() {
  document.getElementById('uploadModal').classList.remove('hidden');
}
function closeUploadModal() {
  document.getElementById('uploadModal').classList.add('hidden');
  resetUploadUI();
}
function closeModalOutside(e) {
  if (e.target === document.getElementById('uploadModal')) closeUploadModal();
}
function resetUploadUI() {
  document.getElementById('dropzone').classList.remove('hidden');
  document.getElementById('uploadProgress').classList.add('hidden');
  document.getElementById('progressBar').style.width = '0%';
  ['step1','step2','step3','step4'].forEach((s,i) => {
    document.getElementById(s).className = `progress-step${i===0?' active':''}`;
  });
}

function handleDragOver(e) {
  e.preventDefault();
  document.getElementById('dropzone').classList.add('dragover');
}
function handleDragLeave(e) {
  document.getElementById('dropzone').classList.remove('dragover');
}
function handleDrop(e) {
  e.preventDefault();
  document.getElementById('dropzone').classList.remove('dragover');
  const file = e.dataTransfer.files[0];
  if (file) uploadFile(file);
}
function handleFileSelect(e) {
  const file = e.target.files[0];
  if (file) uploadFile(file);
}

async function uploadFile(file) {
  const allowed = ['application/pdf', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                   'image/jpeg', 'image/jpg', 'image/png'];
  const allowedExt = /\.(pdf|docx|jpg|jpeg|png)$/i;
  if (!allowedExt.test(file.name)) {
    alert('Invalid file type. Please upload PDF, DOCX, JPG, or PNG.');
    return;
  }
  if (file.size > 16 * 1024 * 1024) {
    alert('File too large. Maximum size is 16MB.');
    return;
  }

  // Show progress
  document.getElementById('dropzone').classList.add('hidden');
  document.getElementById('uploadProgress').classList.remove('hidden');

  const steps = ['step1','step2','step3','step4'];
  const msgs = ['Uploading file...', 'Parsing document...', 'Extracting information...', 'Complete!'];

  function setStep(n) {
    steps.forEach((s, i) => {
      const el = document.getElementById(s);
      if (i < n) el.className = 'progress-step done';
      else if (i === n) el.className = 'progress-step active';
      else el.className = 'progress-step';
    });
    document.getElementById('progressMsg').textContent = msgs[n] || '';
    document.getElementById('progressBar').style.width = `${(n+1) * 25}%`;
  }

  setStep(0);

  try {
    const formData = new FormData();
    formData.append('resume', file);

    setTimeout(() => setStep(1), 600);
    setTimeout(() => setStep(2), 1200);

    const res = await fetch(`${API}/api/resume/upload`, {
      method: 'POST',
      headers: { 'Authorization': `Bearer ${token}` },
      body: formData
    });

    const data = await res.json();
    if (!res.ok) throw new Error(data.error || 'Upload failed');

    setStep(3);
    document.getElementById('progressMsg').textContent = '✅ Resume processed successfully!';

    // Store extracted data
    localStorage.setItem('deet_resume_id', data.resume_id);
    localStorage.setItem('deet_extracted', JSON.stringify(data.extracted));

    setTimeout(() => {
      closeUploadModal();
      window.location.href = '/register-form';
    }, 1200);

  } catch (err) {
    document.getElementById('progressMsg').textContent = `❌ ${err.message}`;
    document.getElementById('progressBar').style.background = 'var(--c-error)';
    setTimeout(resetUploadUI, 3000);
  }
}

function toggleSidebar() {
  document.getElementById('sidebar').classList.toggle('open');
}

function showSection(section) {
  document.getElementById('registrationsSection').scrollIntoView({ behavior: 'smooth' });
}

function logout() {
  localStorage.removeItem('deet_token');
  localStorage.removeItem('deet_user');
  localStorage.removeItem('deet_resume_id');
  localStorage.removeItem('deet_extracted');
  window.location.href = '/';
}

// Init
initUser();
loadDashboard();
