<template>
  <router-view />
</template>

<style>
:root {
  --primary: #1e3a5f;
  --primary-light: #2a5080;
  --primary-dark: #152c4a;
  --accent: #e8913a;
  --accent-hover: #d47e2a;
  --success: #27ae60;
  --danger: #e74c3c;
  --warning: #f39c12;
  --text: #1a2332;
  --text-secondary: #64748b;
  --bg: #f0f2f5;
  --surface: #ffffff;
  --surface-raised: #ffffff;
  --border: #e2e8f0;
  --shadow-sm: 0 1px 2px rgba(0, 0, 0, 0.05);
  --shadow: 0 1px 3px rgba(0, 0, 0, 0.08), 0 1px 2px rgba(0, 0, 0, 0.04);
  --shadow-md: 0 4px 6px rgba(0, 0, 0, 0.06), 0 2px 4px rgba(0, 0, 0, 0.04);
  --shadow-lg: 0 10px 15px rgba(0, 0, 0, 0.08), 0 4px 6px rgba(0, 0, 0, 0.04);
  --radius: 10px;
  --radius-sm: 6px;
  --radius-lg: 14px;
  --sidebar-width: 260px;
  --sidebar-collapsed: 68px;
  --topbar-height: 56px;
}

@media (prefers-color-scheme: dark) {
  :root:not([data-theme="light"]) {
    --primary: #2a5080;
    --primary-light: #3a6a9f;
    --primary-dark: #1a3660;
    --accent: #e8913a;
    --accent-hover: #f0a050;
    --success: #2ecc71;
    --danger: #e74c3c;
    --warning: #f39c12;
    --text: #e8ecf1;
    --text-secondary: #8b95a5;
    --bg: #0f1117;
    --surface: #1a1d2e;
    --surface-raised: #212438;
    --border: #2a2d42;
    --shadow-sm: 0 1px 2px rgba(0, 0, 0, 0.2);
    --shadow: 0 1px 3px rgba(0, 0, 0, 0.3), 0 1px 2px rgba(0, 0, 0, 0.2);
    --shadow-md: 0 4px 6px rgba(0, 0, 0, 0.25), 0 2px 4px rgba(0, 0, 0, 0.15);
    --shadow-lg: 0 10px 15px rgba(0, 0, 0, 0.3), 0 4px 6px rgba(0, 0, 0, 0.15);
  }
}

:root[data-theme="dark"] {
  --primary: #2a5080;
  --primary-light: #3a6a9f;
  --primary-dark: #1a3660;
  --accent: #e8913a;
  --accent-hover: #f0a050;
  --success: #2ecc71;
  --danger: #e74c3c;
  --warning: #f39c12;
  --text: #e8ecf1;
  --text-secondary: #8b95a5;
  --bg: #0f1117;
  --surface: #1a1d2e;
  --surface-raised: #212438;
  --border: #2a2d42;
  --shadow-sm: 0 1px 2px rgba(0, 0, 0, 0.2);
  --shadow: 0 1px 3px rgba(0, 0, 0, 0.3), 0 1px 2px rgba(0, 0, 0, 0.2);
  --shadow-md: 0 4px 6px rgba(0, 0, 0, 0.25), 0 2px 4px rgba(0, 0, 0, 0.15);
  --shadow-lg: 0 10px 15px rgba(0, 0, 0, 0.3), 0 4px 6px rgba(0, 0, 0, 0.15);
}

*,
*::before,
*::after {
  box-sizing: border-box;
  margin: 0;
  padding: 0;
}

html, body {
  height: 100%;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  background: var(--bg);
  color: var(--text);
  line-height: 1.5;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

#app {
  height: 100%;
}

a {
  color: var(--accent);
  text-decoration: none;
}

button {
  cursor: pointer;
  font-family: inherit;
  transition: all 0.15s ease;
}

input, select, textarea {
  font-family: inherit;
  font-size: inherit;
  transition: border-color 0.15s ease;
}

input:focus, select:focus, textarea:focus {
  border-color: var(--accent);
}

::placeholder {
  color: var(--text-secondary);
  opacity: 0.6;
}

:focus-visible {
  outline: 2px solid var(--accent);
  outline-offset: 2px;
}

:focus:not(:focus-visible) {
  outline: none;
}

.sr-only {
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  margin: -1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  white-space: nowrap;
  border: 0;
}

@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
  }
}
</style>
