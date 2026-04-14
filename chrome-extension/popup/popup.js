document.addEventListener('DOMContentLoaded', async () => {
  const loginSection = document.getElementById('login-section');
  const mainSection = document.getElementById('main-section');
  const loginBtn = document.getElementById('login-btn');
  const logoutBtn = document.getElementById('logout-btn');
  const loginStatus = document.getElementById('login-status');
  const captureStatus = document.getElementById('capture-status');
  const displayUser = document.getElementById('display-user');
  const apiUrlInput = document.getElementById('api-url');

  // Engagement elements
  const engagementSection = document.getElementById('engagement-section');
  const engagementTitle = document.getElementById('engagement-title');
  const engagementList = document.getElementById('engagement-list');
  const engagementCount = document.getElementById('engagement-count');
  const engagementWarning = document.getElementById('engagement-warning');
  const selectAllCheckbox = document.getElementById('select-all');
  const captureSelectedBtn = document.getElementById('capture-selected-btn');
  const captureAllBtn = document.getElementById('capture-all-btn');
  const captureResult = document.getElementById('capture-result');

  let currentItems = [];
  let lookupResults = {};

  // Load saved state
  const { token, apiUrl, username, password } = await chrome.storage.local.get(['token', 'apiUrl', 'username', 'password']);

  if (apiUrl) apiUrlInput.value = apiUrl;
  if (username) document.getElementById('username').value = username;
  if (password) document.getElementById('password').value = password;

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
    checkEngagementPage();
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
      const result = await chrome.runtime.sendMessage({
        type: 'LOGIN',
        apiUrl,
        username,
        password,
      });

      if (!result || result.error) {
        throw new Error(result?.error || 'No response from service worker. Try reloading the extension.');
      }

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

  // --- Engagement capture logic ---

  async function checkEngagementPage() {
    try {
      const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
      if (!tab || !tab.url) return;

      const isProfile = tab.url.includes('linkedin.com/in/');
      const isEngagementPage =
        tab.url.includes('linkedin.com/notifications') ||
        tab.url.includes('linkedin.com/feed/update/') ||
        tab.url.includes('linkedin.com/messaging/');

      if (isProfile) {
        showStatus(captureStatus, 'LinkedIn profile detected. Click "Add to CRM" on the page.', 'info');
        return;
      }

      if (isEngagementPage) {
        captureStatus.style.display = 'none';
        engagementSection.style.display = 'block';
        await scanForEngagements();
        return;
      }

      showStatus(captureStatus, 'Navigate to LinkedIn to capture engagements', 'info');
    } catch {
      // Ignore tab access errors
    }
  }

  async function scanForEngagements() {
    engagementTitle.textContent = 'Scanning...';

    try {
      const response = await chrome.runtime.sendMessage({ type: 'SCAN_ENGAGEMENTS' });

      if (!response || !response.items || response.items.length === 0) {
        // Check for warning
        const { engagementWarning: warning } = await chrome.storage.local.get('engagementWarning');
        if (warning) {
          showStatus(engagementWarning, warning, 'warning');
          chrome.storage.local.remove('engagementWarning');
        }
        engagementTitle.textContent = 'No engagement items found';
        engagementList.innerHTML = '<p style="color:#888; font-size:12px; padding:8px;">Try scrolling the page to load more items, then reopen this popup.</p>';
        captureSelectedBtn.style.display = 'none';
        captureAllBtn.style.display = 'none';
        return;
      }

      currentItems = response.items;

      // Filter out already-captured items
      const { capturedInteractions = [] } = await chrome.storage.local.get('capturedInteractions');
      const weekAgo = Date.now() - 7 * 24 * 60 * 60 * 1000;
      const recentCaptures = capturedInteractions.filter(c => new Date(c.captured_at).getTime() > weekAgo);

      currentItems = currentItems.filter(item => {
        return !recentCaptures.some(c =>
          c.name === item.name &&
          c.action === item.action &&
          c.post_snippet === (item.postSnippet || '')
        );
      });

      if (currentItems.length === 0) {
        engagementTitle.textContent = 'All items already captured';
        engagementList.innerHTML = '';
        captureSelectedBtn.style.display = 'none';
        captureAllBtn.style.display = 'none';
        return;
      }

      // Batch lookup to annotate items
      await batchLookup(currentItems);
      renderEngagementList();
    } catch (err) {
      engagementTitle.textContent = 'Engagement Capture';
      showStatus(engagementWarning, 'Error scanning page: ' + err.message, 'error');
    }
  }

  async function batchLookup(items) {
    try {
      const result = await chrome.runtime.sendMessage({
        type: 'BATCH_LOOKUP',
        items: items.map(i => ({
          handle: i.profileUrl || '',
          display_name: i.name,
          profile_url: i.profileUrl || '',
        })),
      });

      if (result && !result.error && Array.isArray(result)) {
        result.forEach((r, idx) => {
          if (items[idx]) {
            lookupResults[items[idx].id] = r;
          }
        });
      }
    } catch {
      // Continue without lookup results
    }
  }

  function renderEngagementList() {
    const pageType = currentItems[0]?.pageType || 'notifications';
    const pageLabels = {
      notifications: 'Notifications',
      post_detail: 'Post Comments',
      messaging: 'Messages',
    };
    engagementTitle.textContent = `${pageLabels[pageType] || 'Engagement'} Capture`;
    engagementCount.textContent = `${currentItems.length} items`;

    engagementList.innerHTML = '';

    currentItems.forEach((item, idx) => {
      const div = document.createElement('div');
      div.className = 'engagement-item';

      const checkbox = document.createElement('input');
      checkbox.type = 'checkbox';
      checkbox.dataset.index = idx;
      checkbox.addEventListener('change', updateCaptureButton);

      const content = document.createElement('div');
      content.className = 'item-content';

      const nameSpan = document.createElement('span');
      nameSpan.className = 'item-name';
      nameSpan.textContent = item.name;

      // Add badge
      const lookup = lookupResults[item.id];
      if (lookup) {
        const badge = document.createElement('span');
        if (lookup.found) {
          badge.className = 'badge-exists';
          badge.textContent = 'IN VOSS';
          badge.title = `Matched: ${lookup.contact_name}`;
        } else {
          badge.className = 'badge-new';
          badge.textContent = 'NEW';
        }
        nameSpan.appendChild(badge);
      }

      const actionSpan = document.createElement('div');
      actionSpan.className = 'item-action';
      const actionLabels = {
        comment: 'commented',
        like: 'liked',
        share: 'shared',
        message: 'messaged',
        follow: 'followed',
        connection_request: 'connected',
        other: 'interacted',
      };
      let actionText = actionLabels[item.action] || item.action;
      if (item.postSnippet) actionText += ` on "${item.postSnippet}"`;
      actionSpan.textContent = actionText;

      content.appendChild(nameSpan);
      content.appendChild(actionSpan);

      if (item.textPreview && item.action !== 'like' && item.action !== 'follow') {
        const textSpan = document.createElement('div');
        textSpan.className = 'item-text';
        textSpan.textContent = item.textPreview.substring(0, 80);
        content.appendChild(textSpan);
      }

      div.appendChild(checkbox);
      div.appendChild(content);
      engagementList.appendChild(div);
    });

    captureSelectedBtn.style.display = '';
    captureAllBtn.style.display = '';
  }

  function getSelectedItems() {
    const checkboxes = engagementList.querySelectorAll('input[type="checkbox"]:checked');
    return Array.from(checkboxes).map(cb => currentItems[parseInt(cb.dataset.index)]);
  }

  function updateCaptureButton() {
    const selected = getSelectedItems();
    captureSelectedBtn.disabled = selected.length === 0;
    captureSelectedBtn.textContent = selected.length > 0
      ? `Capture Selected (${selected.length})`
      : 'Capture Selected';
  }

  selectAllCheckbox.addEventListener('change', () => {
    const checkboxes = engagementList.querySelectorAll('input[type="checkbox"]');
    checkboxes.forEach(cb => { cb.checked = selectAllCheckbox.checked; });
    updateCaptureButton();
  });

  captureSelectedBtn.addEventListener('click', async () => {
    const selected = getSelectedItems();
    if (selected.length === 0) return;
    await captureItems(selected);
  });

  captureAllBtn.addEventListener('click', async () => {
    await captureItems(currentItems);
  });

  async function captureItems(items) {
    captureSelectedBtn.disabled = true;
    captureAllBtn.disabled = true;
    showStatus(captureResult, `Capturing ${items.length} items...`, 'info');

    try {
      const result = await chrome.runtime.sendMessage({
        type: 'CAPTURE_ENGAGEMENTS',
        items,
      });

      if (result.error) {
        showStatus(captureResult, 'Error: ' + result.error, 'error');
      } else {
        const captured = result.captured || 0;
        const dupes = (result.results || []).filter(r => r.status === 'duplicate').length;
        const errors = (result.results || []).filter(r => r.status === 'error').length;

        let msg = `${captured} captured to VOSS ✓`;
        if (dupes > 0) msg += `, ${dupes} already captured`;
        if (errors > 0) msg += `, ${errors} errors`;
        showStatus(captureResult, msg, errors > 0 ? 'warning' : 'success');

        // Update badge
        chrome.runtime.sendMessage({ type: 'UPDATE_BADGE', count: 0 });

        // Re-scan to update the list
        setTimeout(() => scanForEngagements(), 1000);
      }
    } catch (err) {
      showStatus(captureResult, 'Error: ' + err.message, 'error');
    } finally {
      captureSelectedBtn.disabled = false;
      captureAllBtn.disabled = false;
    }
  }
});
