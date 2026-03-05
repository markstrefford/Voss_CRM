/**
 * LinkedIn Engagement Content Script
 * Injects an on-page capture panel on notifications/feed/messaging pages.
 *
 * LinkedIn DOM structure (as of March 2026):
 * - Notification cards: .nt-card elements or <a> with class nt-card__headline
 * - Name: <strong> inside <span class="nt-card__text--3-line">
 * - Action text: plain text after </strong> in the same span (e.g. "liked your comment.")
 * - Post link: href on the <a class="nt-card__headline">
 * - Timestamp: sibling/nearby element with short relative time text
 */
(() => {
  if (window.__vossEngagementLoaded) return;
  window.__vossEngagementLoaded = true;

  function safeSendMessage(msg) {
    try {
      if (!chrome.runtime?.id) return; // Extension context invalidated
      chrome.runtime.sendMessage(msg, () => {
        if (chrome.runtime.lastError) { /* ignore */ }
      });
    } catch (e) { /* ignore */ }
  }

  function detectPageType() {
    const url = window.location.href;
    if (url.includes('/notifications')) return 'notifications';
    if (url.includes('/feed/update/')) return 'post_detail';
    if (url.includes('/messaging/')) return 'messaging';
    return null;
  }

  function parseActionType(text) {
    const lower = text.toLowerCase();
    if (lower.includes('replied')) return 'comment';
    if (lower.includes('commented')) return 'comment';
    if (lower.includes('reacted')) return 'like';
    if (lower.includes('liked')) return 'like';
    if (lower.includes('shared') || lower.includes('reposted')) return 'share';
    if (lower.includes('message') || lower.includes('sent you')) return 'message';
    if (lower.includes('accepted') || lower.includes('connection')) return 'connection_request';
    if (lower.includes('follow')) return 'follow';
    if (lower.includes('mentioned')) return 'comment';
    return 'other';
  }

  // --- Notifications parsing ---

  function parseNotificationsPage() {
    const items = [];

    // Primary: find nt-card containers or nt-card__headline links
    let cards = document.querySelectorAll('.nt-card');
    if (cards.length === 0) {
      // Cards might be the <a> elements themselves
      cards = document.querySelectorAll('a[class*="nt-card"]');
    }
    if (cards.length === 0) {
      // Broader fallback
      cards = document.querySelectorAll('[class*="notification"]');
    }

    cards.forEach((card, index) => {
      try {
        // Find the text span — "nt-card__text--3-line" or similar
        const textSpan = card.querySelector('[class*="nt-card__text"]') ||
                         card.querySelector('span[class*="text--3-line"]');

        // If card IS the headline link, look inside it directly
        const container = textSpan ? textSpan : card;
        const fullText = container.textContent.trim().replace(/\s+/g, ' ');

        // Extract name from <strong>
        let name = '';
        const strongEl = container.querySelector('strong');
        if (strongEl) {
          name = strongEl.textContent.trim();
        }

        if (!name) {
          // Fallback: first capitalized words
          const m = fullText.match(/^([A-Z][a-zà-ö]+ [A-Z][a-zà-ö]+(?:[- ][A-Z][a-zà-ö]+)?)/);
          if (m) name = m[1];
        }

        if (!name) return;

        // Clean "and X others" from name
        name = name.replace(/\s+and\s+\d+\s+others?.*$/i, '').trim();

        // Get the action text (everything after the name in the text)
        const actionText = fullText.replace(name, '').trim();
        const action = parseActionType(actionText);
        if (action === 'other') return;

        // Post URL from the <a> href
        let postUrl = '';
        const link = card.tagName === 'A' ? card : card.querySelector('a[href*="/feed/"]') || card.querySelector('a[href*="/posts/"]');
        if (link) postUrl = link.href.split('?')[0];

        // Profile URL — may not be directly available in notification cards,
        // but we can construct from name for matching purposes
        let profileUrl = '';
        const profileLink = card.querySelector('a[href*="/in/"]');
        if (profileLink) profileUrl = profileLink.href.split('?')[0];

        // Timestamp
        let timestamp = '';
        // Look in the card and its parent for short time text
        const searchArea = card.parentElement || card;
        const allSpans = searchArea.querySelectorAll('span, time, p');
        for (const el of allSpans) {
          const t = el.textContent.trim();
          if (/^\d+[smhd]$/.test(t) || /^\d+ (min|hour|day|week)s?\s*(ago)?$/i.test(t)) {
            timestamp = t;
            break;
          }
        }

        // Post snippet — the content preview text if present
        let postSnippet = '';
        // LinkedIn shows a preview block below the action text
        const previewBlock = card.querySelector('[class*="snippet"]') ||
                             card.querySelector('[class*="preview"]') ||
                             card.querySelector('blockquote');
        if (previewBlock) {
          postSnippet = previewBlock.textContent.trim().substring(0, 100);
        }

        items.push({
          id: `notif-${index}-${name.replace(/\s+/g, '-').toLowerCase()}-${action}`,
          name,
          action,
          postSnippet,
          textPreview: actionText.substring(0, 120),
          profileUrl,
          postUrl,
          timestamp,
          pageType: 'notifications',
        });
      } catch (e) { /* skip */ }
    });

    // Deduplicate
    const seen = new Set();
    return items.filter(item => {
      const key = `${item.name}|${item.action}|${item.postSnippet}`;
      if (seen.has(key)) return false;
      seen.add(key);
      return true;
    });
  }

  function parsePostDetailPage() {
    const items = [];
    let comments = [];
    const selectors = ['.comments-comment-item', 'article[data-id]', '[class*="comments-comment"]'];
    for (const sel of selectors) {
      comments = document.querySelectorAll(sel);
      if (comments.length > 0) break;
    }

    Array.from(comments).forEach((comment, index) => {
      try {
        let name = '', profileUrl = '';
        const link = comment.querySelector('a[href*="/in/"]');
        if (link) { profileUrl = link.href.split('?')[0]; name = link.textContent.trim(); }
        if (!name || name.length > 50) return;
        const bodyText = comment.textContent.trim().replace(name, '').trim().substring(0, 200);
        items.push({
          id: `comment-${index}-${name.replace(/\s+/g, '-').toLowerCase()}`,
          name, action: 'comment', postSnippet: document.title || '',
          textPreview: bodyText, profileUrl, postUrl: window.location.href,
          timestamp: '', pageType: 'post_detail',
        });
      } catch (e) { /* skip */ }
    });
    return items;
  }

  function parseMessagingPage() {
    const items = [];
    const selectors = ['.msg-conversation-listitem', '[class*="msg-conversation"]'];
    let threads = [];
    for (const sel of selectors) {
      threads = document.querySelectorAll(sel);
      if (threads.length > 0) break;
    }
    Array.from(threads).forEach((thread, index) => {
      try {
        let name = '';
        const nameEl = thread.querySelector('[class*="participant-names"], [class*="entity-name"]');
        if (nameEl) name = nameEl.textContent.trim();
        if (!name) { const link = thread.querySelector('a'); if (link) name = link.textContent.trim(); }
        if (!name || name.length > 60) return;
        let preview = '';
        const previewEl = thread.querySelector('[class*="snippet"], [class*="message-body"]');
        if (previewEl) preview = previewEl.textContent.trim();
        items.push({
          id: `msg-${index}-${name.replace(/\s+/g, '-').toLowerCase()}`,
          name, action: 'message', postSnippet: '', textPreview: preview.substring(0, 200),
          profileUrl: '', postUrl: '', timestamp: '', pageType: 'messaging',
        });
      } catch (e) { /* skip */ }
    });
    return items;
  }

  function scanPage() {
    const pageType = detectPageType();
    if (!pageType) return [];
    switch (pageType) {
      case 'notifications': return parseNotificationsPage();
      case 'post_detail': return parsePostDetailPage();
      case 'messaging': return parseMessagingPage();
    }
    return [];
  }

  // --- On-page UI ---

  let panelEl = null;
  let currentItems = [];
  let capturedSet = new Set();

  const ACTION_LABELS = {
    comment: 'commented', like: 'liked', share: 'shared', message: 'messaged',
    follow: 'followed', connection_request: 'connected',
  };

  function escapeHtml(str) {
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
  }

  function createPanel() {
    if (panelEl) return;

    panelEl = document.createElement('div');
    panelEl.id = 'voss-engagement-panel';
    panelEl.innerHTML = `
      <div class="voss-panel-header">
        <span class="voss-panel-title">Voss</span>
        <span class="voss-panel-count" id="voss-count"></span>
        <button class="voss-panel-toggle" id="voss-toggle">−</button>
      </div>
      <div id="voss-panel-body"></div>
      <div class="voss-panel-actions" id="voss-panel-actions">
        <button class="voss-btn voss-btn-secondary" id="voss-capture-selected" disabled>Capture Selected</button>
        <button class="voss-btn voss-btn-primary" id="voss-capture-all">Capture All</button>
      </div>
      <div id="voss-panel-status" class="voss-panel-status"></div>
    `;
    document.body.appendChild(panelEl);

    document.getElementById('voss-toggle').addEventListener('click', () => {
      const btn = document.getElementById('voss-toggle');
      const body = document.getElementById('voss-panel-body');
      const actions = document.getElementById('voss-panel-actions');
      const collapsed = body.style.display === 'none';
      body.style.display = collapsed ? '' : 'none';
      actions.style.display = collapsed ? '' : 'none';
      btn.textContent = collapsed ? '−' : '+';
    });

    document.getElementById('voss-capture-selected').addEventListener('click', () => {
      const checked = panelEl.querySelectorAll('.voss-item-check:checked');
      const items = Array.from(checked).map(cb => currentItems[parseInt(cb.dataset.index)]).filter(Boolean);
      if (items.length > 0) captureItems(items);
    });

    document.getElementById('voss-capture-all').addEventListener('click', () => {
      const uncaptured = currentItems.filter(i => !capturedSet.has(i.id));
      if (uncaptured.length > 0) captureItems(uncaptured);
    });
  }

  function renderItems(items) {
    const body = document.getElementById('voss-panel-body');
    const countEl = document.getElementById('voss-count');
    if (!body) return;

    currentItems = items;
    const uncaptured = items.filter(i => !capturedSet.has(i.id));
    countEl.textContent = uncaptured.length > 0 ? `(${uncaptured.length})` : '(0)';
    body.innerHTML = '';

    if (items.length === 0) {
      body.innerHTML = '<div class="voss-empty">No engagement items found. Try scrolling to load more.</div>';
      document.getElementById('voss-panel-actions').style.display = 'none';
      return;
    }

    document.getElementById('voss-panel-actions').style.display = '';

    items.forEach((item, idx) => {
      const isCaptured = capturedSet.has(item.id);
      const row = document.createElement('label');
      row.className = `voss-item${isCaptured ? ' voss-item-captured' : ''}`;

      const actionLabel = ACTION_LABELS[item.action] || item.action;

      row.innerHTML = `
        <input type="checkbox" class="voss-item-check" data-index="${idx}" ${isCaptured ? 'disabled' : ''}>
        <div class="voss-item-content">
          <div class="voss-item-name">${escapeHtml(item.name)}${isCaptured ? ' <span class="voss-badge-done">✓</span>' : ''}${item.timestamp ? ' <span class="voss-item-time">' + escapeHtml(item.timestamp) + '</span>' : ''}</div>
          <div class="voss-item-action">${escapeHtml(actionLabel)}${item.textPreview ? ' · ' + escapeHtml(item.textPreview.substring(0, 50)) : ''}</div>
        </div>
      `;

      row.querySelector('.voss-item-check').addEventListener('change', updateSelectedButton);
      body.appendChild(row);
    });

    updateSelectedButton();
  }

  function updateSelectedButton() {
    const btn = document.getElementById('voss-capture-selected');
    if (!btn) return;
    const count = panelEl.querySelectorAll('.voss-item-check:checked').length;
    btn.disabled = count === 0;
    btn.textContent = count > 0 ? `Capture Selected (${count})` : 'Capture Selected';
  }

  function showStatus(msg, type) {
    const el = document.getElementById('voss-panel-status');
    if (!el) return;
    el.textContent = msg;
    el.className = `voss-panel-status voss-status-${type}`;
    el.style.display = 'block';
    if (type === 'success') setTimeout(() => { el.style.display = 'none'; }, 4000);
  }

  // --- Capture ---

  async function captureItems(items) {
    const btns = panelEl.querySelectorAll('.voss-btn');
    btns.forEach(b => b.disabled = true);
    showStatus(`Capturing ${items.length} items...`, 'info');

    try {
      const result = await chrome.runtime.sendMessage({
        type: 'CAPTURE_ENGAGEMENTS',
        items,
      });

      if (result && result.error) {
        showStatus('Error: ' + result.error, 'error');
      } else {
        const captured = result?.captured || 0;
        items.forEach(i => capturedSet.add(i.id));
        showStatus(`${captured} captured to Voss ✓`, 'success');
        renderItems(currentItems);
      }
    } catch (err) {
      showStatus('Error: ' + err.message, 'error');
    } finally {
      btns.forEach(b => b.disabled = false);
      updateSelectedButton();
    }
  }

  // --- Lifecycle ---

  function doScan() {
    const items = scanPage();
    createPanel();
    renderItems(items);
    safeSendMessage({ type: 'UPDATE_BADGE', count: items.filter(i => !capturedSet.has(i.id)).length });
  }

  // Listen for scan requests from popup
  chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
    if (message.type === 'SCAN_ENGAGEMENTS') {
      sendResponse({ items: scanPage(), pageType: detectPageType() });
      return true;
    }
  });

  // Initial scan with delay for LinkedIn's lazy loading
  setTimeout(doScan, 2500);

  // Re-scan on DOM changes
  let scanTimeout = null;
  const observer = new MutationObserver(() => {
    if (scanTimeout) clearTimeout(scanTimeout);
    scanTimeout = setTimeout(doScan, 2000);
  });
  if (document.body) {
    observer.observe(document.body, { childList: true, subtree: true });
  }
})();
