// Dark mode
function toggleDark() {
  document.body.classList.toggle('dark');
  const isDark = document.body.classList.contains('dark');
  localStorage.setItem('darkMode', isDark);
  document.getElementById('darkBtn').textContent = isDark ? '☀️' : '🌙';
}

// Apply saved dark mode on page load
(function() {
  if (localStorage.getItem('darkMode') === 'true') {
    document.body.classList.add('dark');
    const btn = document.getElementById('darkBtn');
    if (btn) btn.textContent = '☀️';
  }
})();