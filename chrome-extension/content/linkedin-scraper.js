(() => {
  // Avoid injecting multiple times
  if (window.__vossScraperLoaded) return;
  window.__vossScraperLoaded = true;

  // Wait for the page to load
  function waitForElement(selectors, timeout = 5000) {
    return new Promise((resolve) => {
      for (const selector of selectors) {
        const el = document.querySelector(selector);
        if (el) return resolve(el);
      }

      const observer = new MutationObserver(() => {
        for (const selector of selectors) {
          const el = document.querySelector(selector);
          if (el) {
            observer.disconnect();
            resolve(el);
            return;
          }
        }
      });

      observer.observe(document.body, { childList: true, subtree: true });
      setTimeout(() => { observer.disconnect(); resolve(null); }, timeout);
    });
  }

  function scrapeProfile() {
    // Name — multiple possible selectors for LinkedIn's changing DOM
    const nameSelectors = [
      'h1.text-heading-xlarge',
      'h1.inline.t-24',
      '.pv-top-card--list li:first-child',
      'h1',
    ];
    let fullName = '';
    for (const sel of nameSelectors) {
      const el = document.querySelector(sel);
      if (el && el.textContent.trim()) {
        fullName = el.textContent.trim();
        break;
      }
    }

    const nameParts = fullName.split(' ');
    const firstName = nameParts[0] || '';
    const lastName = nameParts.slice(1).join(' ') || '';

    // Role/headline
    const roleSelectors = [
      '.text-body-medium.break-words',
      'h2.mt1.t-18',
      '.pv-top-card--list.pv-top-card--list-bullet li:first-child',
    ];
    let role = '';
    for (const sel of roleSelectors) {
      const el = document.querySelector(sel);
      if (el && el.textContent.trim()) {
        role = el.textContent.trim();
        break;
      }
    }

    // Company — try experience section first, then top card
    const companySelectors = [
      '.pv-text-details__right-panel .inline-show-more-text',
      'div.inline-show-more-text span[aria-hidden="true"]',
    ];
    let companyName = '';
    for (const sel of companySelectors) {
      const el = document.querySelector(sel);
      if (el && el.textContent.trim()) {
        companyName = el.textContent.trim();
        break;
      }
    }

    // LinkedIn URL — clean it
    let linkedinUrl = window.location.href.split('?')[0];
    if (linkedinUrl.endsWith('/')) linkedinUrl = linkedinUrl.slice(0, -1);

    return {
      first_name: firstName,
      last_name: lastName,
      role,
      company_name: companyName,
      linkedin_url: linkedinUrl,
      email: '',
      phone: '',
    };
  }

  function showContextPanel() {
    // If panel already open, focus it
    const existing = document.getElementById('crm-context-panel');
    if (existing) {
      existing.querySelector('textarea').focus();
      return;
    }

    const profile = scrapeProfile();

    const panel = document.createElement('div');
    panel.id = 'crm-context-panel';
    Object.assign(panel.style, {
      position: 'fixed',
      bottom: '80px',
      right: '20px',
      zIndex: '10001',
      background: '#fff',
      border: '1px solid #ddd',
      borderRadius: '10px',
      boxShadow: '0 4px 20px rgba(0,0,0,0.15)',
      padding: '14px',
      width: '300px',
      fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
      fontSize: '13px',
    });

    const preview = document.createElement('div');
    preview.style.cssText = 'margin-bottom:10px;color:#555;line-height:1.4;';
    const name = `${profile.first_name} ${profile.last_name}`.trim();
    let previewText = `<strong>${name}</strong>`;
    if (profile.role) previewText += `<br>${profile.role}`;
    if (profile.company_name) previewText += `<br>${profile.company_name}`;
    preview.innerHTML = previewText;
    panel.appendChild(preview);

    const textarea = document.createElement('textarea');
    textarea.placeholder = 'Add context (e.g. where you met, why relevant...)';
    Object.assign(textarea.style, {
      width: '100%',
      height: '60px',
      border: '1px solid #ddd',
      borderRadius: '6px',
      padding: '8px',
      fontSize: '13px',
      fontFamily: 'inherit',
      resize: 'vertical',
      boxSizing: 'border-box',
    });
    panel.appendChild(textarea);

    const btnRow = document.createElement('div');
    btnRow.style.cssText = 'display:flex;gap:8px;margin-top:10px;';

    const cancelBtn = document.createElement('button');
    cancelBtn.textContent = 'Cancel';
    Object.assign(cancelBtn.style, {
      flex: '1',
      padding: '7px 0',
      border: '1px solid #ddd',
      borderRadius: '6px',
      background: '#fff',
      cursor: 'pointer',
      fontSize: '13px',
    });
    cancelBtn.addEventListener('click', () => panel.remove());

    const saveBtn = document.createElement('button');
    saveBtn.textContent = 'Save to Voss';
    Object.assign(saveBtn.style, {
      flex: '1',
      padding: '7px 0',
      border: 'none',
      borderRadius: '6px',
      background: '#0a66c2',
      color: '#fff',
      cursor: 'pointer',
      fontWeight: '600',
      fontSize: '13px',
    });
    saveBtn.addEventListener('click', () => submitToCRM(profile, textarea.value, saveBtn, panel));

    btnRow.appendChild(cancelBtn);
    btnRow.appendChild(saveBtn);
    panel.appendChild(btnRow);

    document.body.appendChild(panel);
    textarea.focus();
  }

  async function submitToCRM(profileData, notes, saveBtn, panel) {
    saveBtn.textContent = 'Saving...';
    saveBtn.disabled = true;

    try {
      if (!chrome.runtime?.sendMessage) {
        throw new Error('Extension reloaded — please refresh the page');
      }

      const auth = await chrome.runtime.sendMessage({ type: 'GET_AUTH' });
      if (!auth || !auth.token || !auth.apiUrl) {
        saveBtn.textContent = 'Not logged in';
        saveBtn.style.background = '#c62828';
        setTimeout(() => { saveBtn.textContent = 'Save to Voss'; saveBtn.style.background = '#0a66c2'; saveBtn.disabled = false; }, 2000);
        return;
      }

      profileData.notes = notes;

      const result = await chrome.runtime.sendMessage({
        type: 'API_REQUEST',
        method: 'POST',
        path: '/api/contacts/from-linkedin',
        body: profileData,
      });

      if (result.error) {
        throw new Error(result.error);
      }

      const btn = document.getElementById('crm-capture-btn');
      btn.textContent = 'Added to Voss!';
      btn.style.background = '#2e7d32';
      panel.remove();
      setTimeout(() => { btn.textContent = 'Add to Voss'; btn.style.background = ''; btn.disabled = false; }, 3000);
    } catch (err) {
      saveBtn.textContent = 'Error';
      saveBtn.style.background = '#c62828';
      setTimeout(() => { saveBtn.textContent = 'Save to Voss'; saveBtn.style.background = '#0a66c2'; saveBtn.disabled = false; }, 3000);
    }
  }

  function isProfilePage() {
    return /linkedin\.com\/in\/[^/]+/.test(window.location.href);
  }

  function removeButton() {
    const btn = document.getElementById('crm-capture-btn');
    if (btn) btn.remove();
    const panel = document.getElementById('crm-context-panel');
    if (panel) panel.remove();
  }

  // Create floating button
  async function injectButton() {
    if (!isProfilePage()) return;

    await waitForElement(['h1.text-heading-xlarge', 'h1.inline.t-24', 'h1']);

    // Re-check after waiting — user may have navigated away
    if (!isProfilePage()) return;

    const btn = document.createElement('button');
    btn.id = 'crm-capture-btn';
    btn.textContent = 'Add to Voss';
    btn.addEventListener('click', showContextPanel);
    document.body.appendChild(btn);
  }

  // Watch for SPA navigation — show/hide button based on URL
  let lastUrl = window.location.href;
  new MutationObserver(() => {
    if (window.location.href !== lastUrl) {
      lastUrl = window.location.href;
      removeButton();
      if (isProfilePage()) {
        injectButton();
      }
    }
  }).observe(document.body, { childList: true, subtree: true });

  injectButton();
})();
