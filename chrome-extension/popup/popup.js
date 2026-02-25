document.addEventListener('DOMContentLoaded', async () => {
  const loginSection = document.getElementById('login-section');
  const mainSection = document.getElementById('main-section');
  const loginBtn = document.getElementById('login-btn');
  const logoutBtn = document.getElementById('logout-btn');
  const loginStatus = document.getElementById('login-status');
  const captureStatus = document.getElementById('capture-status');
  const displayUser = document.getElementById('display-user');
  const apiUrlInput = document.getElementById('api-url');

  // Load saved state
  const { token, apiUrl, username } = await chrome.storage.local.get(['token', 'apiUrl', 'username']);

  if (apiUrl) apiUrlInput.value = apiUrl;

  if (token) {
    showMainSection(username || 'User');
  } else {
    showLoginSection();
  }

  function showLoginSection() {
    loginSection.style.display = 'block';
    mainSection.style.display = 'none';
  }

  function showMainSection(user) {
    loginSection.style.display = 'none';
    mainSection.style.display = 'block';
    displayUser.textContent = user;
  }

  function showStatus(el, msg, type) {
    el.textContent = msg;
    el.className = 'status ' + type;
    el.style.display = 'block';
  }

  loginBtn.addEventListener('click', async () => {
    const apiUrl = apiUrlInput.value.replace(/\/$/, '');
    const username = document.getElementById('username').value;
    const password = document.getElementById('password').value;

    if (!apiUrl || !username || !password) {
      showStatus(loginStatus, 'All fields required', 'error');
      return;
    }

    loginBtn.disabled = true;
    loginBtn.textContent = 'Logging in...';

    try {
      const resp = await fetch(`${apiUrl}/api/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password }),
      });

      if (!resp.ok) {
        const data = await resp.json();
        throw new Error(data.detail || 'Login failed');
      }

      const data = await resp.json();
      await chrome.storage.local.set({
        token: data.access_token,
        apiUrl,
        username,
      });

      showMainSection(username);
    } catch (err) {
      showStatus(loginStatus, err.message, 'error');
    } finally {
      loginBtn.disabled = false;
      loginBtn.textContent = 'Login';
    }
  });

  logoutBtn.addEventListener('click', async () => {
    await chrome.storage.local.remove(['token', 'username']);
    showLoginSection();
  });

  // Check current tab for LinkedIn profile
  try {
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    if (tab && tab.url && tab.url.includes('linkedin.com/in/')) {
      showStatus(captureStatus, 'LinkedIn profile detected. Click "Add to CRM" on the page.', 'info');
    }
  } catch {
    // Ignore tab access errors
  }
});
