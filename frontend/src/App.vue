<template>
  <router-view />
</template>

<style>
:root {
  --primary: #1e3a5f;
  --primary-light: #2a5080;
  --accent: #e8913a;
  --success: #27ae60;
  --danger: #e74c3c;
  --warning: #f39c12;
  --text: #2c3e50;
  --text-secondary: #7f8c8d;
  --bg: #f5f6fa;
  --surface: #ffffff;
  --border: #e1e4e8;
  --shadow: rgba(0, 0, 0, 0.08);
}

@media (prefers-color-scheme: dark) {
  :root {
    --primary: #2a5080;
    --primary-light: #3a6a9f;
    --accent: #e8913a;
    --success: #2ecc71;
    --danger: #e74c3c;
    --warning: #f39c12;
    --text: #ecf0f1;
    --text-secondary: #95a5a6;
    --bg: #1a1b2e;
    --surface: #232440;
    --border: #3d3e5c;
    --shadow: rgba(0, 0, 0, 0.3);
  }
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
}

input, select, textarea {
  font-family: inherit;
  font-size: inherit;
}
</style>
