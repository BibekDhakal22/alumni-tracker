// =============================================================================
// MAIN.JS — Shared JavaScript for Alumni Tracker System
// =============================================================================

// ─── Dark Mode ───────────────────────────────────────────────────────────────

function toggleDark() {
  document.body.classList.toggle('dark');
  const isDark = document.body.classList.contains('dark');
  localStorage.setItem('darkMode', isDark);
  const btn = document.getElementById('darkBtn');
  if (btn) btn.textContent = isDark ? '☀️' : '🌙';
}

// Apply saved dark mode on page load
(function() {
  if (localStorage.getItem('darkMode') === 'true') {
    document.body.classList.add('dark');
    const btn = document.getElementById('darkBtn');
    if (btn) btn.textContent = '☀️';
  }
})();


// ─── Page Loading Animation ───────────────────────────────────────────────────

// Create loader element
const loader = document.createElement('div');
loader.id = 'page-loader';
loader.innerHTML = `
  <div class="loader-bar"></div>
  <div class="loader-spinner">
    <div class="spinner-ring"></div>
  </div>
`;
loader.style.cssText = `
  position: fixed; top: 0; left: 0; width: 100%; height: 100%;
  background: rgba(255,255,255,0.85); backdrop-filter: blur(4px);
  z-index: 9999; display: none; flex-direction: column;
  align-items: center; justify-content: center;
  transition: opacity 0.2s;
`;

const loaderStyle = document.createElement('style');
loaderStyle.textContent = `
  .loader-bar {
    position: fixed; top: 0; left: 0; height: 3px; width: 0%;
    background: linear-gradient(90deg, #6366f1, #8b5cf6, #06b6d4);
    border-radius: 0 2px 2px 0;
    animation: loadBar 0.8s ease forwards;
    z-index: 10000;
  }
  @keyframes loadBar {
    0%   { width: 0%; }
    50%  { width: 70%; }
    100% { width: 90%; }
  }
  .loader-spinner {
    display: flex; align-items: center; justify-content: center;
    margin-top: 20px;
  }
  .spinner-ring {
    width: 40px; height: 40px; border-radius: 50%;
    border: 3px solid #e2e8f0;
    border-top-color: #6366f1;
    animation: spin 0.7s linear infinite;
  }
  @keyframes spin { to { transform: rotate(360deg); } }
  body.dark #page-loader {
    background: rgba(15,23,42,0.85);
  }
  body.dark .loader-bar {
    background: linear-gradient(90deg, #6366f1, #8b5cf6);
  }
  body.dark .spinner-ring {
    border-color: #1e293b;
    border-top-color: #6366f1;
  }
  /* Page entrance animation */
  .page-enter {
    animation: pageEnter 0.3s ease forwards;
  }
  @keyframes pageEnter {
    from { opacity: 0; transform: translateY(8px); }
    to   { opacity: 1; transform: translateY(0); }
  }
`;

document.head.appendChild(loaderStyle);
document.body.appendChild(loader);

// Show loader on navigation
function showLoader() {
  loader.style.display = 'flex';
  loader.style.opacity = '1';
}

function hideLoader() {
  loader.style.opacity = '0';
  setTimeout(() => { loader.style.display = 'none'; }, 200);
}

// Intercept all link clicks
document.addEventListener('click', function(e) {
  const link = e.target.closest('a');
  if (!link) return;
  const href = link.getAttribute('href');
  if (!href || href.startsWith('#') || href.startsWith('javascript') ||
      href.startsWith('mailto') || link.target === '_blank' ||
      e.ctrlKey || e.metaKey || e.shiftKey) return;
  if (href.startsWith('http') && !href.includes('127.0.0.1') &&
      !href.includes('localhost')) return;
  showLoader();
});

// Intercept form submissions
document.addEventListener('submit', function(e) {
  const form = e.target;
  if (form.method && form.method.toLowerCase() === 'get') return;
  showLoader();
});

// Hide loader when page loads
window.addEventListener('load', hideLoader);
window.addEventListener('pageshow', hideLoader);

// Add entrance animation to main content
document.addEventListener('DOMContentLoaded', function() {
  const container = document.querySelector('.container, .container-md, .container-sm, .chat-layout, .id-wrap, .login-wrap');
  if (container) container.classList.add('page-enter');
});


// ─── Flash message auto-dismiss ──────────────────────────────────────────────

document.addEventListener('DOMContentLoaded', function() {
  const alerts = document.querySelectorAll('.alert-success, .alert');
  alerts.forEach(alert => {
    setTimeout(() => {
      alert.style.transition = 'opacity 0.5s, transform 0.5s';
      alert.style.opacity = '0';
      alert.style.transform = 'translateY(-8px)';
      setTimeout(() => alert.remove(), 500);
    }, 3000);
  });
});


// ─── Confirm dialogs ─────────────────────────────────────────────────────────

function confirmDelete(message) {
  return confirm(message || 'Are you sure you want to delete this?');
}


// ─── Nav Dropdown ─────────────────────────────────────────────────────────────
function toggleDropdown() {
  const menu = document.getElementById('dropMenu');
  if (menu) menu.classList.toggle('show');
}

// Close dropdown when clicking outside
document.addEventListener('click', function(e) {
  const dropdown = document.getElementById('moreDropdown');
  const menu     = document.getElementById('dropMenu');
  if (dropdown && menu && !dropdown.contains(e.target)) {
    menu.classList.remove('show');
  }
});

// ─── Notification Bell Counter ────────────────────────────────────────────────
async function updateNotifCount() {
  try {
    const res  = await fetch('/notifications/unread-count');
    const data = await res.json();
    const badge = document.getElementById('notifCount');
    if (badge) {
      if (data.count > 0) {
        badge.textContent = data.count > 9 ? '9+' : data.count;
        badge.style.display = 'flex';
      } else {
        badge.style.display = 'none';
      }
    }
  } catch(e) {}
}

// Update count every 30 seconds
updateNotifCount();
setInterval(updateNotifCount, 30000);