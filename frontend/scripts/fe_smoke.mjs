#!/usr/bin/env node
/**
 * Same-origin rewrite smoke (NX-FE).
 * Django'ya doğrudan istek bu kapıyı geçirmez.
 *
 * Usage: npm run smoke
 * Env: FE_ORIGIN (default http://localhost:3000)
 *      SMOKE_USER / SMOKE_PASS (default demo_alici / DemoPortal1!)
 */
import { env } from "node:process";

const origin = (env.FE_ORIGIN || "http://localhost:3000").replace(/\/$/, "");
const user = env.SMOKE_USER || "demo_alici";
const pass = env.SMOKE_PASS || "DemoPortal1!";

function fail(msg) {
  console.error(`FAIL: ${msg}`);
  process.exit(1);
}

function ok(msg) {
  console.log(`OK: ${msg}`);
}

function cookieJar() {
  /** @type {Map<string, string>} */
  const map = new Map();
  return {
    store(res) {
      const raw = res.headers.getSetCookie?.() || [];
      for (const line of raw) {
        const nv = line.split(";", 1)[0];
        const i = nv.indexOf("=");
        if (i > 0) map.set(nv.slice(0, i), nv.slice(i + 1));
      }
      // Node < setCookie fallback
      const single = res.headers.get("set-cookie");
      if (single && raw.length === 0) {
        const nv = single.split(";", 1)[0];
        const i = nv.indexOf("=");
        if (i > 0) map.set(nv.slice(0, i), nv.slice(i + 1));
      }
    },
    header() {
      return [...map.entries()].map(([k, v]) => `${k}=${v}`).join("; ");
    },
    get(name) {
      return map.get(name) || null;
    },
  };
}

async function main() {
  const jar = cookieJar();

  // 1) CSRF — no redirect loop
  const csrfUrl = `${origin}/api/v1/auth/csrf/`;
  const csrfRes = await fetch(csrfUrl, {
    redirect: "manual",
    headers: { Accept: "application/json" },
  });
  if (csrfRes.status >= 300 && csrfRes.status < 400) {
    fail(
      `CSRF redirect ${csrfRes.status} → ${csrfRes.headers.get("location")} (rewrite/trailing-slash döngüsü?)`,
    );
  }
  if (!csrfRes.ok) fail(`CSRF HTTP ${csrfRes.status}`);
  jar.store(csrfRes);
  const csrfJson = await csrfRes.json();
  const csrf =
    jar.get("csrftoken") || csrfJson.csrf_token || fail("csrf_token yok");
  ok(`CSRF 200 (${csrfUrl})`);

  // 2) Login via rewrite
  const loginRes = await fetch(`${origin}/api/v1/auth/login/`, {
    method: "POST",
    redirect: "manual",
    headers: {
      Accept: "application/json",
      "Content-Type": "application/json",
      "X-CSRFToken": csrf,
      Cookie: jar.header(),
    },
    body: JSON.stringify({ username: user, password: pass }),
  });
  if (loginRes.status >= 300 && loginRes.status < 400) {
    fail(`Login redirect ${loginRes.status} (proxy slash bug?)`);
  }
  jar.store(loginRes);
  if (!loginRes.ok) {
    const t = await loginRes.text();
    fail(`Login HTTP ${loginRes.status}: ${t.slice(0, 200)}`);
  }
  const meLogin = await loginRes.json();
  if (!meLogin.username) fail("Login body username yok");
  ok(`Login 200 as ${meLogin.username} (${meLogin.rol || "?"})`);

  // 3) /me/
  const meRes = await fetch(`${origin}/api/v1/me/`, {
    redirect: "manual",
    headers: {
      Accept: "application/json",
      Cookie: jar.header(),
    },
  });
  if (meRes.status >= 300 && meRes.status < 400) {
    fail(` /me/ redirect ${meRes.status}`);
  }
  if (!meRes.ok) fail(`/me/ HTTP ${meRes.status}`);
  const me = await meRes.json();
  if (!me.capabilities) fail("/me/ capabilities yok");
  ok(`/me/ 200 · capabilities=${Object.keys(me.capabilities).length}`);

  // 4) health through rewrite
  const healthRes = await fetch(`${origin}/api/v1/health/`, {
    redirect: "manual",
  });
  if (!healthRes.ok) fail(`health HTTP ${healthRes.status}`);
  ok("health 200");

  console.log("\nfe_smoke PASSED (same-origin rewrite)");
}

main().catch((e) => fail(e?.message || String(e)));
