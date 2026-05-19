/* ── MedPredict — app.js ─────────────────────────────────────────
   Global JS utilities used across all pages.
   No frameworks — plain vanilla JS only.
────────────────────────────────────────────────────────────────── */

'use strict';

/* ── 1. PASSWORD VISIBILITY TOGGLE ──────────────────────────────── */
/**
 * Called from HTML: onclick="togglePassword('fieldId', btn)"
 * Toggles the input type between password and text.
 */
function togglePassword(fieldId, btn) {
  const input = document.getElementById(fieldId);
  if (!input) return;
  const isHidden = input.type === 'password';
  input.type = isHidden ? 'text' : 'password';

  // Swap icon SVG path to open/closed eye
  const svg = btn.querySelector('svg');
  if (svg) {
    svg.innerHTML = isHidden
      ? /* open eye (visible) */
        '<path d="M17.94 17.94A10.07 10.07 0 0112 20c-7 0-11-8-11-8a18.45 18.45 0 015.06-5.94"/>' +
        '<path d="M9.9 4.24A9.12 9.12 0 0112 4c7 0 11 8 11 8a18.5 18.5 0 01-2.16 3.19"/>' +
        '<line x1="1" y1="1" x2="23" y2="23"/>'
      : /* closed eye (hidden) */
        '<path d="M1 12s4-7 11-7 11 7 11 7-4 7-11 7S1 12 1 12z"/><circle cx="12" cy="12" r="3"/>';
  }
}

/* ── 2. FORM SUBMIT LOADING STATE ────────────────────────────────── */
/**
 * Attaches a loading spinner to any form submit button.
 * Usage: add data-loading="true" to the <form> element.
 */
document.addEventListener('DOMContentLoaded', () => {

  // Auto-attach loading state to all forms with data-loading attribute
  document.querySelectorAll('form[data-loading]').forEach(form => {
    form.addEventListener('submit', () => {
      const btn = form.querySelector('[type="submit"]');
      if (!btn) return;
      const spinner = btn.querySelector('.btn-spinner');
      const text    = btn.querySelector('.btn-text');
      if (spinner) spinner.classList.remove('hidden');
      if (text)    text.style.opacity = '0.5';
      btn.disabled = true;
    });
  });

  /* ── 3. AUTO-DISMISS FLASH MESSAGES ───────────────────────────── */
  const flashes = document.querySelectorAll('.flash');
  flashes.forEach(flash => {
    setTimeout(() => {
      flash.style.transition = 'opacity 0.4s';
      flash.style.opacity = '0';
      setTimeout(() => flash.remove(), 400);
    }, 4000);
  });

  /* ── 4. ACTIVE NAV LINK HIGHLIGHT ─────────────────────────────── */
  const currentPath = window.location.pathname;
  document.querySelectorAll('.nav-link').forEach(link => {
    if (link.getAttribute('href') === currentPath) {
      link.classList.add('active');
    }
  });

  /* ── 5. CONFIRM BEFORE LOGOUT ──────────────────────────────────── */
  const logoutLink = document.querySelector('a[href="/auth/logout"]');
  if (logoutLink) {
    logoutLink.addEventListener('click', e => {
      if (!confirm('Are you sure you want to logout?')) {
        e.preventDefault();
      }
    });
  }

  /* ── 6. INPUT FOCUS ANIMATION ──────────────────────────────────── */
  document.querySelectorAll('.field-input').forEach(input => {
    input.addEventListener('focus', () => {
      input.closest('.field-group')?.classList.add('field-focused');
    });
    input.addEventListener('blur', () => {
      input.closest('.field-group')?.classList.remove('field-focused');
    });
  });

  /* ── 7. SYMPTOM CARD KEYBOARD ACCESSIBILITY ────────────────────── */
  document.querySelectorAll('.symptom-card').forEach(card => {
    card.setAttribute('tabindex', '0');
    card.addEventListener('keydown', e => {
      if (e.key === ' ' || e.key === 'Enter') {
        e.preventDefault();
        const cb = card.querySelector('.sym-check');
        if (cb) {
          cb.checked = !cb.checked;
          cb.dispatchEvent(new Event('change'));
        }
      }
    });
  });

  /* ── 8. PLAN CARD HIGHLIGHT ────────────────────────────────────── */
  document.querySelectorAll('.plan-btn').forEach(btn => {
    btn.addEventListener('click', function (e) {
      e.preventDefault();
      // Remove selection from siblings
      document.querySelectorAll('.plan-card').forEach(c => c.classList.remove('plan-card--selected'));
      this.closest('.plan-card')?.classList.add('plan-card--selected');
      // Call the onclick handler defined in the template
      const onclickFn = this.getAttribute('onclick');
      if (onclickFn) {
        // Already handled by inline onclick in template
      }
    });
  });

});

/* ── 9. UTILITY: Format file size ────────────────────────────────── */
function formatBytes(bytes) {
  if (bytes < 1024)        return bytes + ' B';
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
  return (bytes / (1024 * 1024)).toFixed(2) + ' MB';
}

/* ── 10. UTILITY: Simple client-side form validator ─────────────── */
/**
 * Validates that all required radio groups in a form step have a selection.
 * @param {string[]} fieldNames - array of radio input name attributes to check
 * @returns {boolean}
 */
function validateRadioFields(fieldNames) {
  for (const name of fieldNames) {
    const checked = document.querySelector(`input[name="${name}"]:checked`);
    if (!checked) {
      // Highlight the unanswered group
      const group = document.querySelector(`input[name="${name}"]`)?.closest('.lifestyle-row, .fam-card, .field-group');
      if (group) {
        group.style.outline = '2px solid #e02424';
        group.style.borderRadius = '10px';
        setTimeout(() => { group.style.outline = ''; }, 2500);
      }
      return false;
    }
  }
  return true;
}


/* ── 11. CONFIDENCE BAR ANIMATION (dashboard) ──────────────── */
/* Triggered once from dashboard.html — NOT duplicated here.        */
function animateConfidenceBar() {
  const fill = document.querySelector('.confidence-fill');
  if (!fill) return;
  const targetWidth = fill.dataset.target || fill.style.width;
  fill.style.width = '0%';
  requestAnimationFrame(() => {
    setTimeout(() => {
      fill.style.transition = 'width 1.2s cubic-bezier(0.4, 0, 0.2, 1)';
      fill.style.width = targetWidth;
    }, 400);
  });
}
