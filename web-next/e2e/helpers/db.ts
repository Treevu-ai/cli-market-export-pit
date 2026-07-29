import { spawnSync } from "node:child_process";
import { E2E_DB_PATH } from "../../playwright.config";

/**
 * Reads a column straight out of the disposable E2E SQLite DB via the
 * stdlib `sqlite3` module (no new dependency, same Python already running
 * the backend webServer). Used to fetch a signup's verification_token
 * without depending on real email delivery, since RESEND_API_KEY is
 * deliberately unset for the E2E backend (see playwright.config.ts).
 */
function queryUsersColumn(email: string, column: "verification_token" | "id"): string | null {
  const script = `
import sqlite3, sys
con = sqlite3.connect(sys.argv[1])
row = con.execute("SELECT ${column} FROM users WHERE email=?", (sys.argv[2],)).fetchone()
print(row[0] if row and row[0] is not None else "")
`;
  const result = spawnSync("python", ["-c", script, E2E_DB_PATH, email], { encoding: "utf-8" });
  if (result.status !== 0) {
    throw new Error(`E2E DB query failed: ${result.stderr}`);
  }
  const value = result.stdout.trim();
  return value.length > 0 ? value : null;
}

/**
 * Polls the DB for the verification token, since there's a small window
 * between the signup API call returning and this test process reading the
 * row back — the write is committed synchronously server-side, but we're
 * reading from a separate process/connection.
 */
export async function getVerificationToken(email: string, timeoutMs = 5000): Promise<string> {
  const deadline = Date.now() + timeoutMs;
  while (Date.now() < deadline) {
    const token = queryUsersColumn(email, "verification_token");
    if (token) return token;
    await new Promise((resolve) => setTimeout(resolve, 200));
  }
  throw new Error(`Verification token for ${email} never appeared in the E2E DB within ${timeoutMs}ms`);
}
