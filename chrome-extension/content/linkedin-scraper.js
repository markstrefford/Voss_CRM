(() => {
  // Avoid injecting multiple times
  if (document.getElementById('crm-capture-btn')) return;

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

  async function addToCRM() {
    const btn = document.getElementById('crm-capture-btn');
    const originalText = btn.textContent;
    btn.textContent = 'Saving...';
    btn.disabled = true;

    try {
      const { token, apiUrl } = await chrome.storage.local.get(['token', 'apiUrl']);
      if (!token || !apiUrl) {
        btn.textContent = 'Not logged in';
        btn.style.background = '#c62828';
        setTimeout(() => { btn.textContent = originalText; btn.style.background = ''; btn.disabled = false; }, 2000);
        return;
      }

      const profileData = scrapeProfile();

      const resp = await fetch(`${apiUrl}/api/contacts/from-linkedin`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify(profileData),
      });

      if (!resp.ok) {
        const data = await resp.json().catch(() => ({}));
        throw new Error(data.detail || `HTTP ${resp.status}`);
      }

      btn.textContent = 'Added to Voss!';
      btn.style.background = '#2e7d32';
      setTimeout(() => { btn.textContent = originalText; btn.style.background = ''; btn.disabled = false; }, 3000);
    } catch (err) {
      btn.textContent = 'Error: ' + err.message;
      btn.style.background = '#c62828';
      setTimeout(() => { btn.textContent = originalText; btn.style.background = ''; btn.disabled = false; }, 3000);
    }
  }

  // Create floating button
  async function injectButton() {
    await waitForElement(['h1.text-heading-xlarge', 'h1.inline.t-24', 'h1']);

    const btn = document.createElement('button');
    btn.id = 'crm-capture-btn';
    btn.textContent = 'Add to Voss';
    btn.addEventListener('click', addToCRM);
    document.body.appendChild(btn);
  }

  injectButton();
})();
