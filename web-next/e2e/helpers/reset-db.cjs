// Wipes the disposable E2E SQLite DB/raw-response dir before each Playwright
// run. A standalone script (not an inline `node -e "..."`) so it doesn't hit
// cross-platform shell-quoting issues in playwright.config.ts's webServer
// command on Windows.
const fs = require("fs");
const path = require("path");

const tmpDir = path.join(__dirname, "..", ".tmp");
const rawDir = path.join(tmpDir, "raw");

fs.rmSync(tmpDir, { recursive: true, force: true });
fs.mkdirSync(rawDir, { recursive: true });
