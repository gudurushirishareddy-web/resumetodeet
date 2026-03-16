/* Auth page JS */
const API = '';

function showPanel(type) {
  const login = document.getElementById('loginCard');
  const signup = document.getElementById('signupCard');
  if (type === 'login') {
    login.classList.remove('hidden');
    signup.classList.add('hidden');
  } else {
    signup.classList.remove('hidden');
    login.classList.add('hidden');
  }
  document.getElementById('authPanel').scrollIntoView({ behavior: 'smooth', block: 'center' });
}

function togglePw(id, btn) {
  const input = document.getElementById(id);
  if (input.type === 'password') {
    input.type = 'text';
    btn.textContent = '🙈';
  } else {
    input.type = 'password';
    btn.textContent = '👁';
  }
}

function showError(id, msg) {
  const el = document.getElementById(id);
  el.textContent = msg;
  el.classList.add('show');
}
function clearError(id) {
  const el = document.getElementById(id);
  el.textContent = '';
  el.classList.remove('show');
}

function setLoading(btnId, loading) {
  const btn = document.getElementById(btnId);
  const label = btn.querySelector('.btn-label');
  const loader = btn.querySelector('.btn-loader');
  btn.disabled = loading;
  if (loading) {
    label.classList.add('hidden');
    loader.classList.remove('hidden');
  } else {
    label.classList.remove('hidden');
    loader.classList.add('hidden');
  }
}

// Password strength indicator
const pwInput = document.getElementById('signupPassword');
if (pwInput) {
  pwInput.addEventListener('input', () => {
    const pw = pwInput.value;
    const bar = document.getElementById('pwStrength');
    let strength = 0;
    if (pw.length >= 8) strength++;
    if (/[A-Z]/.test(pw)) strength++;
    if (/\d/.test(pw)) strength++;
    if (/[!@#$%^&*(),.?":{}|<>]/.test(pw)) strength++;
    const colors = ['', '#f87171', '#fbbf24', '#34d399', '#6366f1'];
    const widths = ['0%', '25%', '50%', '75%', '100%'];
    bar.style.background = colors[strength] || '#f87171';
    bar.style.width = widths[strength];
    bar.style.height = '4px';
    bar.style.borderRadius = '2px';
    bar.style.transition = 'all 0.3s';
  });
}

async function handleLogin(e) {
  e.preventDefault();
  clearError('loginError');
  const email = document.getElementById('loginEmail').value.trim();
  const password = document.getElementById('loginPassword').value;

  if (!email || !password) {
    showError('loginError', 'Please fill in all fields');
    return;
  }
  setLoading('loginBtn', true);
  try {
    const res = await fetch(`${API}/api/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password })
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || 'Login failed');
    localStorage.setItem('deet_token', data.access_token);
    localStorage.setItem('deet_user', JSON.stringify(data.user));
    window.location.href = '/dashboard';
  } catch (err) {
    showError('loginError', err.message);
  } finally {
    setLoading('loginBtn', false);
  }
}

async function handleSignup(e) {
  e.preventDefault();
  clearError('signupError');
  const full_name = document.getElementById('signupName').value.trim();
  const email = document.getElementById('signupEmail').value.trim();
  const password = document.getElementById('signupPassword').value;
  const confirm_password = document.getElementById('signupConfirm').value;

  if (!full_name || !email || !password || !confirm_password) {
    showError('signupError', 'Please fill in all fields');
    return;
  }
  setLoading('signupBtn', true);
  try {
    const res = await fetch(`${API}/api/auth/signup`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ full_name, email, password, confirm_password })
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || 'Signup failed');
    localStorage.setItem('deet_token', data.access_token);
    localStorage.setItem('deet_user', JSON.stringify(data.user));
    window.location.href = '/dashboard';
  } catch (err) {
    showError('signupError', err.message);
  } finally {
    setLoading('signupBtn', false);
  }
}

// Redirect if already logged in
if (localStorage.getItem('deet_token')) {
  window.location.href = '/dashboard';
}
