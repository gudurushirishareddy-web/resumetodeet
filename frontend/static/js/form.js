/* DEET Registration Form JS */
const API = '';
const token = localStorage.getItem('deet_token');
const user = JSON.parse(localStorage.getItem('deet_user') || '{}');

if (!token) window.location.href = '/';

// State
let resumeId = localStorage.getItem('deet_resume_id');
let extractedData = null;
let currentRegId = null;
const tagSets = { prog: [], web: [], tools: [], concepts: [], langs: [], hobbies: [] };

// Tag category map
const tagCategories = {
  prog: 'programming_languages',
  web: 'web_technologies',
  tools: 'tools_platforms',
  concepts: 'core_concepts'
};

function authHeaders() {
  return { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json' };
}

// ─── Init ─────────────────────────────────────────────────────────────────────

window.addEventListener('DOMContentLoaded', async () => {
  initUser();

  const cached = localStorage.getItem('deet_extracted');
  if (cached) {
    try {
      extractedData = JSON.parse(cached);
      populateForm(extractedData);
      localStorage.removeItem('deet_extracted');
    } catch(e) { console.error('Cached data parse error', e); }
  } else if (resumeId) {
    await loadResumeData(resumeId);
  }

  updateEmptyStates();
});

function initUser() {
  const name = user.full_name || 'User';
  document.getElementById('sidebarName').textContent = name;
  const initials = name.split(' ').map(w=>w[0]).join('').substring(0,2).toUpperCase();
  document.getElementById('userAvatar').textContent = initials;
}

async function loadResumeData(id) {
  try {
    const res = await fetch(`${API}/api/resume/${id}`, { headers: authHeaders() });
    if (!res.ok) return;
    const data = await res.json();
    extractedData = data.extracted_data;
    if (extractedData) populateForm(extractedData);
  } catch(e) {
    console.error('Load resume error:', e);
  }
}

// ─── Populate Form ─────────────────────────────────────────────────────────────

function populateForm(data) {
  if (!data) return;

  // Personal info
  setVal('f_name', data.name);
  setVal('f_email', data.email);
  setVal('f_phone', data.phone);
  setVal('f_address', data.address);
  setVal('f_linkedin', data.linkedin);
  setVal('f_github', data.github);
  setVal('f_objective', data.career_objective);

  // Confidence indicators
  const conf = data.confidence || {};
  setConfidence('ci_name', conf.name);
  setConfidence('ci_email', conf.email);
  setConfidence('ci_phone', conf.phone);

  // Skills
  const skills = data.skills || {};
  const cat = skills.categorized || {};
  (cat.programming_languages || []).forEach(s => addTagValue('prog', s));
  (cat.web_technologies || []).forEach(s => addTagValue('web', s));
  (cat.tools_platforms || []).forEach(s => addTagValue('tools', s));
  (cat.core_concepts || []).forEach(s => addTagValue('concepts', s));

  // Education
  (data.education || []).forEach(edu => addEducationEntry(edu));

  // Projects
  (data.projects || []).forEach(proj => addProjectEntry(proj));

  // Certifications
  (data.certifications || []).forEach(cert => addCertEntry(cert));

  // Languages & Hobbies
  (data.languages || []).forEach(l => addTagValue('langs', l));
  (data.hobbies || []).forEach(h => addTagValue('hobbies', h));

  // Participations
  if (data.participations && data.participations.length) {
    const parts = data.participations.map(p => `${p.event}${p.organizer ? ' – ' + p.organizer : ''}`).join('\n');
    setVal('f_participations', parts);
  }

  // Quality score
  showQualityScore(data.quality_score || 0);

  // Update banner
  const method = data.parse_method || 'automatic';
  document.getElementById('infoBannerMsg').textContent =
    `✅ Resume parsed via ${method}. Review and edit the auto-filled fields below, then submit.`;

  // Run gap analysis
  const allSkills = skills.all || [];
  if (allSkills.length > 0) {
    runGapAnalysis(allSkills);
  }

  updateEmptyStates();
}

function setVal(id, val) {
  const el = document.getElementById(id);
  if (el && val) el.value = val;
}

function setConfidence(id, level) {
  const el = document.getElementById(id);
  if (!el || !level) return;
  el.textContent = level.toUpperCase();
  el.className = `conf-indicator conf-${level}`;
}

function showQualityScore(score) {
  const card = document.getElementById('qualityCard');
  card.style.display = 'flex';
  document.getElementById('qualityBar').style.width = `${score}%`;
  document.getElementById('qualityScore').textContent = `${score}/100`;
  const tips = score >= 80
    ? '🌟 Excellent resume! All key sections detected.'
    : score >= 60
    ? '👍 Good resume. Consider adding more project details.'
    : score >= 40
    ? '⚠️ Average resume. Add skills, projects, and certifications.'
    : '❗ Needs improvement. Ensure all sections are clearly labeled.';
  document.getElementById('qualityTip').textContent = tips;
}

// ─── Tag Input ─────────────────────────────────────────────────────────────────

function addTag(event, category) {
  if (event.key === 'Enter' || event.key === ',') {
    event.preventDefault();
    const input = event.target;
    const val = input.value.trim().replace(/,$/, '');
    if (val) {
      addTagValue(category, val);
      input.value = '';
    }
  }
}

function addTagValue(category, val) {
  if (!val || tagSets[category].includes(val)) return;
  tagSets[category].push(val);
  renderTags(category);
}

function removeTag(category, val) {
  tagSets[category] = tagSets[category].filter(t => t !== val);
  renderTags(category);
}

function renderTags(category) {
  const container = document.getElementById(`tags_${category}`);
  if (!container) return;
  container.innerHTML = tagSets[category].map(t => `
    <span class="tag">
      ${escHtml(t)}
      <button type="button" class="tag-x" onclick="removeTag('${category}','${escHtml(t)}')">×</button>
    </span>
  `).join('');
}

// ─── Entry Cards ───────────────────────────────────────────────────────────────

let eduCount = 0;
function addEducationEntry(data = {}) {
  eduCount++;
  const id = `edu_${eduCount}`;
  const container = document.getElementById('educationEntries');

  const div = document.createElement('div');
  div.className = 'entry-card';
  div.id = id;
  div.innerHTML = `
    <div class="entry-card-header">
      <span class="entry-card-title">Education Entry #${eduCount}</span>
      <button type="button" class="entry-remove" onclick="removeEntry('${id}')">✕</button>
    </div>
    <div class="entry-body">
      <div class="field-group full">
        <label>Degree / Course</label>
        <input type="text" name="edu_degree_${eduCount}" value="${escHtml(data.degree||'')}" placeholder="e.g. B.Tech Computer Science" />
      </div>
      <div class="field-group">
        <label>Institution</label>
        <input type="text" name="edu_inst_${eduCount}" value="${escHtml(data.institution||'')}" placeholder="University / College name" />
      </div>
      <div class="field-group">
        <label>Year</label>
        <input type="text" name="edu_year_${eduCount}" value="${escHtml(data.year||'')}" placeholder="e.g. 2020 – 2024" />
      </div>
      <div class="field-group">
        <label>CGPA / Percentage</label>
        <input type="text" name="edu_score_${eduCount}" value="${escHtml(data.score||'')}" placeholder="e.g. 8.5 / 85%" />
      </div>
    </div>`;
  container.appendChild(div);
  updateEmptyStates();
}

let projCount = 0;
function addProjectEntry(data = {}) {
  projCount++;
  const id = `proj_${projCount}`;
  const container = document.getElementById('projectEntries');
  const div = document.createElement('div');
  div.className = 'entry-card';
  div.id = id;
  div.innerHTML = `
    <div class="entry-card-header">
      <span class="entry-card-title">Project #${projCount}</span>
      <button type="button" class="entry-remove" onclick="removeEntry('${id}')">✕</button>
    </div>
    <div class="entry-body">
      <div class="field-group full">
        <label>Project Title</label>
        <input type="text" name="proj_title_${projCount}" value="${escHtml(data.title||'')}" placeholder="Project name" />
      </div>
      <div class="field-group full">
        <label>Description</label>
        <textarea name="proj_desc_${projCount}" rows="2" placeholder="Short 1-2 line description...">${escHtml(data.description||'')}</textarea>
      </div>
      <div class="field-group full">
        <label>Technologies Used</label>
        <input type="text" name="proj_tech_${projCount}" value="${escHtml((data.technologies||[]).join(', '))}" placeholder="e.g. React, Python, MySQL" />
      </div>
    </div>`;
  container.appendChild(div);
  updateEmptyStates();
}

let certCount = 0;
function addCertEntry(data = {}) {
  certCount++;
  const id = `cert_${certCount}`;
  const container = document.getElementById('certEntries');
  const div = document.createElement('div');
  div.className = 'entry-card';
  div.id = id;
  div.innerHTML = `
    <div class="entry-card-header">
      <span class="entry-card-title">Certification #${certCount}</span>
      <button type="button" class="entry-remove" onclick="removeEntry('${id}')">✕</button>
    </div>
    <div class="entry-body">
      <div class="field-group">
        <label>Certification Name</label>
        <input type="text" name="cert_name_${certCount}" value="${escHtml(data.name||'')}" placeholder="e.g. AWS Certified" />
      </div>
      <div class="field-group">
        <label>Platform / Organization</label>
        <input type="text" name="cert_platform_${certCount}" value="${escHtml(data.platform||'')}" placeholder="e.g. Coursera, Udemy" />
      </div>
    </div>`;
  container.appendChild(div);
  updateEmptyStates();
}

function removeEntry(id) {
  const el = document.getElementById(id);
  if (el) el.remove();
  updateEmptyStates();
}

function updateEmptyStates() {
  const eduEmpty = document.getElementById('eduEmpty');
  const projEmpty = document.getElementById('projEmpty');
  const certEmpty = document.getElementById('certEmpty');
  if (eduEmpty) eduEmpty.style.display = document.getElementById('educationEntries').children.length ? 'none' : 'block';
  if (projEmpty) projEmpty.style.display = document.getElementById('projectEntries').children.length ? 'none' : 'block';
  if (certEmpty) certEmpty.style.display = document.getElementById('certEntries').children.length ? 'none' : 'block';
}

// ─── Collect Form Data ──────────────────────────────────────────────────────────

function collectFormData() {
  const form = document.getElementById('deetForm');
  const data = {
    full_name: form.querySelector('#f_name').value.trim(),
    email: form.querySelector('#f_email').value.trim(),
    phone: form.querySelector('#f_phone').value.trim(),
    address: form.querySelector('#f_address').value.trim(),
    linkedin: form.querySelector('#f_linkedin').value.trim(),
    github: form.querySelector('#f_github').value.trim(),
    career_objective: form.querySelector('#f_objective').value.trim(),
    participations: form.querySelector('#f_participations').value.trim(),
    skills: {
      programming_languages: [...tagSets.prog],
      web_technologies: [...tagSets.web],
      tools_platforms: [...tagSets.tools],
      core_concepts: [...tagSets.concepts]
    },
    languages: [...tagSets.langs],
    hobbies: [...tagSets.hobbies],
    education: [],
    projects: [],
    certifications: []
  };

  // Education
  for (let i = 1; i <= eduCount; i++) {
    const degree = form.querySelector(`[name="edu_degree_${i}"]`);
    if (degree && degree.value.trim()) {
      data.education.push({
        degree: degree.value.trim(),
        institution: (form.querySelector(`[name="edu_inst_${i}"]`) || {}).value?.trim() || '',
        year: (form.querySelector(`[name="edu_year_${i}"]`) || {}).value?.trim() || '',
        score: (form.querySelector(`[name="edu_score_${i}"]`) || {}).value?.trim() || ''
      });
    }
  }

  // Projects
  for (let i = 1; i <= projCount; i++) {
    const title = form.querySelector(`[name="proj_title_${i}"]`);
    if (title && title.value.trim()) {
      data.projects.push({
        title: title.value.trim(),
        description: (form.querySelector(`[name="proj_desc_${i}"]`) || {}).value?.trim() || '',
        technologies: ((form.querySelector(`[name="proj_tech_${i}"]`) || {}).value || '')
          .split(',').map(t => t.trim()).filter(Boolean)
      });
    }
  }

  // Certifications
  for (let i = 1; i <= certCount; i++) {
    const name = form.querySelector(`[name="cert_name_${i}"]`);
    if (name && name.value.trim()) {
      data.certifications.push({
        name: name.value.trim(),
        platform: (form.querySelector(`[name="cert_platform_${i}"]`) || {}).value?.trim() || ''
      });
    }
  }

  return data;
}

// ─── Save / Submit ──────────────────────────────────────────────────────────────

async function saveDraft() {
  const data = collectFormData();
  try {
    const res = await fetch(`${API}/api/deet/save`, {
      method: 'POST',
      headers: authHeaders(),
      body: JSON.stringify({ resume_id: resumeId, form_data: data })
    });
    const result = await res.json();
    if (!res.ok) throw new Error(result.error);
    currentRegId = result.registration_id;
    showToast('Draft saved!', 'success');
  } catch(err) {
    showToast(`Save failed: ${err.message}`, 'error');
  }
}

async function submitForm() {
  const data = collectFormData();

  // Validate required fields
  if (!data.full_name) { showToast('Full name is required', 'error'); return; }
  if (!data.email) { showToast('Email is required', 'error'); return; }
  if (!data.phone) { showToast('Phone number is required', 'error'); return; }

  try {
    const res = await fetch(`${API}/api/deet/submit`, {
      method: 'POST',
      headers: authHeaders(),
      body: JSON.stringify({
        registration_id: currentRegId,
        resume_id: resumeId,
        form_data: data
      })
    });
    const result = await res.json();
    if (!res.ok) throw new Error(result.error);

    document.getElementById('confirmationNum').textContent = result.confirmation_number;
    document.getElementById('successModal').classList.remove('hidden');
    localStorage.removeItem('deet_resume_id');

  } catch(err) {
    showToast(`Submission failed: ${err.message}`, 'error');
  }
}

// ─── Gap Analysis ───────────────────────────────────────────────────────────────

async function runGapAnalysis(skills) {
  if (!skills) {
    skills = [
      ...tagSets.prog, ...tagSets.web, ...tagSets.tools, ...tagSets.concepts
    ];
  }
  if (!skills.length) return;

  try {
    const res = await fetch(`${API}/api/resume/gap-analysis`, {
      method: 'POST',
      headers: authHeaders(),
      body: JSON.stringify({ skills })
    });
    const data = await res.json();
    if (!res.ok) return;

    renderGapAnalysis(data);
    document.getElementById('analysisCard').style.display = 'block';
  } catch(e) { console.error('Gap analysis error:', e); }
}

function renderGapAnalysis(data) {
  const container = document.getElementById('analysisResults');
  const suggestions = data.job_suggestions || {};

  const top5 = Object.entries(suggestions).slice(0, 6);
  container.innerHTML = `<div class="job-match-grid">` +
    top5.map(([role, info]) => `
      <div class="jm-card">
        <div class="jm-role">${role.replace(/\b\w/g, c => c.toUpperCase())}</div>
        <div class="jm-pct">${info.match_percentage}%</div>
        <div class="jm-bar-wrap"><div class="jm-bar" style="width:${info.match_percentage}%"></div></div>
        ${info.missing_skills.length ?
          `<div class="jm-missing">Missing: <span>${info.missing_skills.slice(0,3).join(', ')}</span></div>` :
          `<div class="jm-missing" style="color:var(--c-success)">✓ All required skills present</div>`
        }
      </div>
    `).join('') + `</div>`;
}

// ─── Utilities ──────────────────────────────────────────────────────────────────

function escHtml(s) {
  return String(s)
    .replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;')
    .replace(/"/g,'&quot;').replace(/'/g,'&#039;');
}

function showToast(msg, type = 'info') {
  const existing = document.getElementById('toast');
  if (existing) existing.remove();

  const toast = document.createElement('div');
  toast.id = 'toast';
  const colors = { success: 'var(--c-success)', error: 'var(--c-error)', info: 'var(--c-accent)' };
  toast.style.cssText = `
    position:fixed; bottom:24px; right:24px; z-index:1000;
    padding:12px 20px; border-radius:8px;
    background:var(--bg-card); border:1px solid ${colors[type]};
    color:var(--c-text); font-size:13px; font-weight:500;
    box-shadow:var(--shadow-lg); animation: slideUp 0.3s ease;
    max-width:300px;
  `;
  toast.textContent = msg;
  document.body.appendChild(toast);
  setTimeout(() => toast.remove(), 3000);
}

function toggleSidebar() {
  document.getElementById('sidebar').classList.toggle('open');
}

function logout() {
  localStorage.clear();
  window.location.href = '/';
}
