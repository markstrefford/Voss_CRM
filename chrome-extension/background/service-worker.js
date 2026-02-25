// Service worker for CRM Chrome Extension
// Handles message passing between content scripts and popup

chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.type === 'GET_AUTH') {
    chrome.storage.local.get(['token', 'apiUrl'], (result) => {
      sendResponse(result);
    });
    return true; // Keep the message channel open for async response
  }

  if (message.type === 'API_REQUEST') {
    handleApiRequest(message)
      .then(sendResponse)
      .catch((err) => sendResponse({ error: err.message }));
    return true;
  }
});

async function handleApiRequest({ method, path, body }) {
  const { token, apiUrl } = await chrome.storage.local.get(['token', 'apiUrl']);
  if (!token || !apiUrl) {
    throw new Error('Not logged in');
  }

  const options = {
    method: method || 'GET',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`,
    },
  };

  if (body) {
    options.body = JSON.stringify(body);
  }

  const resp = await fetch(`${apiUrl}${path}`, options);
  const data = await resp.json();

  if (!resp.ok) {
    throw new Error(data.detail || `HTTP ${resp.status}`);
  }

  return data;
}
