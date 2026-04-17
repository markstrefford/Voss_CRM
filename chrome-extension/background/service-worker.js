// Service worker for CRM Chrome Extension
// Handles message passing between content scripts and popup

chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.type === 'GET_AUTH') {
    chrome.storage.local.get(['token', 'apiUrl'], (result) => {
      sendResponse(result);
    });
    return true; // Keep the message channel open for async response
  }

  if (message.type === 'LOGIN') {
    handleLogin(message)
      .then(sendResponse)
      .catch((err) => sendResponse({ error: err.message }));
    return true;
  }

  if (message.type === 'API_REQUEST') {
    handleApiRequest(message)
      .then(sendResponse)
      .catch((err) => sendResponse({ error: err.message }));
    return true;
  }

  if (message.type === 'UPDATE_BADGE') {
    const count = message.count || 0;
    chrome.action.setBadgeText({ text: count > 0 ? String(count) : '' });
    chrome.action.setBadgeBackgroundColor({ color: '#0073b1' });
    sendResponse({ ok: true });
    return true;
  }

  if (message.type === 'SCAN_ENGAGEMENTS') {
    // Forward to the active tab's content script
    chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
      if (tabs[0]) {
        chrome.tabs.sendMessage(tabs[0].id, { type: 'SCAN_ENGAGEMENTS' }, (response) => {
          sendResponse(response || { items: [] });
        });
      } else {
        sendResponse({ items: [] });
      }
    });
    return true;
  }

  if (message.type === 'CAPTURE_ENGAGEMENTS') {
    handleCaptureEngagements(message.items)
      .then(sendResponse)
      .catch((err) => sendResponse({ error: err.message }));
    return true;
  }

  if (message.type === 'BATCH_LOOKUP') {
    handleBatchLookup(message.items)
      .then(sendResponse)
      .catch((err) => sendResponse({ error: err.message }));
    return true;
  }

  if (message.type === 'ENGAGEMENT_ITEMS') {
    // Store latest engagement items for popup access
    chrome.storage.local.set({ engagementItems: message.items });
    sendResponse({ ok: true });
    return true;
  }

  if (message.type === 'ENGAGEMENT_WARNING') {
    chrome.storage.local.set({ engagementWarning: message.message });
    sendResponse({ ok: true });
    return true;
  }
});

async function handleLogin({ apiUrl, username, password }) {
  const resp = await fetch(`${apiUrl}/api/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username, password }),
  });

  const data = await resp.json();
  if (!resp.ok) {
    throw new Error(data.detail || 'Login failed');
  }

  await chrome.storage.local.set({
    token: data.access_token,
    apiUrl,
    username,
    password,
  });

  return { success: true, access_token: data.access_token };
}

let refreshInFlight = null;

async function refreshToken(apiUrl, currentToken) {
  if (refreshInFlight) return refreshInFlight;
  refreshInFlight = (async () => {
    try {
      const resp = await fetch(`${apiUrl}/api/auth/refresh`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${currentToken}` },
      });
      if (!resp.ok) return null;
      const data = await resp.json();
      if (!data.access_token) return null;
      await chrome.storage.local.set({ token: data.access_token });
      return data.access_token;
    } catch {
      return null;
    } finally {
      // Clear after a tick so concurrent callers share the same promise
      setTimeout(() => { refreshInFlight = null; }, 0);
    }
  })();
  return refreshInFlight;
}

async function authFetch(path, init = {}) {
  const { token, apiUrl } = await chrome.storage.local.get(['token', 'apiUrl']);
  if (!token || !apiUrl) {
    throw new Error('Not logged in');
  }

  const buildOptions = (t) => ({
    ...init,
    headers: {
      'Content-Type': 'application/json',
      ...(init.headers || {}),
      'Authorization': `Bearer ${t}`,
    },
  });

  let resp = await fetch(`${apiUrl}${path}`, buildOptions(token));

  if (resp.status === 401) {
    const newToken = await refreshToken(apiUrl, token);
    if (!newToken) {
      throw new Error('Session expired — please log in again');
    }
    resp = await fetch(`${apiUrl}${path}`, buildOptions(newToken));
  }

  return resp;
}

async function handleApiRequest({ method, path, body }) {
  const resp = await authFetch(path, {
    method: method || 'GET',
    body: body ? JSON.stringify(body) : undefined,
  });
  const data = await resp.json();

  if (!resp.ok) {
    let msg = `HTTP ${resp.status}`;
    if (Array.isArray(data.detail)) {
      msg = data.detail.map(e => e.msg || e.message || JSON.stringify(e)).join('; ');
    } else if (typeof data.detail === 'string') {
      msg = data.detail;
    }
    throw new Error(msg);
  }

  return data;
}

async function handleCaptureEngagements(items) {
  const results = [];
  const captured = await getRecentlyCaptured();

  for (const item of items) {
    if (isAlreadyCaptured(captured, item)) {
      results.push({ item, status: 'duplicate' });
      continue;
    }

    const event = {
      platform: 'linkedin',
      person: {
        handle: item.profileUrl || '',
        display_name: item.name,
        profile_url: item.profileUrl || '',
      },
      action: item.action,
      content_ref: {
        post_url: '',
        post_title: item.postSnippet || '',
      },
      text: item.textPreview || '',
      timestamp: new Date().toISOString(),
    };

    try {
      const resp = await authFetch('/api/social/capture', {
        method: 'POST',
        body: JSON.stringify(event),
      });

      if (!resp.ok) {
        const err = await resp.json().catch(() => ({}));
        results.push({ item, status: 'error', error: err.detail || `HTTP ${resp.status}` });
        continue;
      }

      const data = await resp.json();
      results.push({ item, status: 'captured', data });

      await recordCapture(item);
    } catch (err) {
      results.push({ item, status: 'error', error: err.message });
    }
  }

  return { results, captured: results.filter(r => r.status === 'captured').length };
}

async function handleBatchLookup(items) {
  const resp = await authFetch('/api/social/batch-lookup', {
    method: 'POST',
    body: JSON.stringify({
      items: items.map(i => ({
        handle: i.profileUrl || '',
        display_name: i.name,
        profile_url: i.profileUrl || '',
      })),
    }),
  });

  if (!resp.ok) {
    throw new Error(`Batch lookup failed: HTTP ${resp.status}`);
  }

  return await resp.json();
}

// --- Deduplication via chrome.storage.local ---

async function getRecentlyCaptured() {
  const { capturedInteractions = [] } = await chrome.storage.local.get('capturedInteractions');
  const weekAgo = Date.now() - 7 * 24 * 60 * 60 * 1000;
  // Prune old entries
  const recent = capturedInteractions.filter(c => new Date(c.captured_at).getTime() > weekAgo);
  if (recent.length !== capturedInteractions.length) {
    await chrome.storage.local.set({ capturedInteractions: recent });
  }
  return recent;
}

function isAlreadyCaptured(captured, item) {
  return captured.some(c =>
    c.name === item.name &&
    c.action === item.action &&
    c.post_snippet === (item.postSnippet || '')
  );
}

async function recordCapture(item) {
  const { capturedInteractions = [] } = await chrome.storage.local.get('capturedInteractions');
  capturedInteractions.push({
    name: item.name,
    action: item.action,
    post_snippet: item.postSnippet || '',
    captured_at: new Date().toISOString(),
  });
  await chrome.storage.local.set({ capturedInteractions });
}
