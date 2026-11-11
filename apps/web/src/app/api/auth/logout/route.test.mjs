import assert from "node:assert/strict";
import { afterEach, describe, it } from "node:test";

import { POST } from "./route.ts";

const originalNodeEnv = process.env.NODE_ENV;

afterEach(() => {
  if (originalNodeEnv === undefined) {
    delete process.env.NODE_ENV;
  } else {
    process.env.NODE_ENV = originalNodeEnv;
  }
});

describe("POST /api/auth/logout", () => {
  it("rejects logout requests without an Origin header", async () => {
    const response = await POST(new Request("http://localhost/api/auth/logout", {
      method: "POST",
    }));

    assert.equal(response.status, 403);
    assert.equal(response.headers.get("set-cookie"), null);
    assert.equal(response.headers.get("cache-control"), "no-store");
  });

  it("rejects logout requests from a different origin", async () => {
    const response = await POST(new Request("http://localhost/api/auth/logout", {
      method: "POST",
      headers: { Origin: "https://attacker.example" },
    }));

    assert.equal(response.status, 403);
    assert.equal(response.headers.get("set-cookie"), null);
  });

  it("expires the session cookie and prevents response caching", async () => {
    process.env.NODE_ENV = "development";

    const response = await POST(new Request("http://localhost/api/auth/logout", { method: "POST", headers: { Origin: "http://localhost" } }));
    const cookie = response.headers.get("set-cookie") ?? "";

    assert.equal(response.status, 200);
    assert.equal(response.headers.get("cache-control"), "no-store");
    assert.match(cookie, /^sky_access_token=;/);
    assert.match(cookie, /HttpOnly/i);
    assert.match(cookie, /SameSite=Lax/i);
    assert.match(cookie, /Path=\//i);
    assert.match(cookie, /Max-Age=0/i);
    assert.match(cookie, /Expires=Thu, 01 Jan 1970 00:00:00 GMT/i);
    assert.doesNotMatch(cookie, /Secure/i);

    assert.deepEqual(await response.json(), { message: "Sessão terminada." });
  });

  it("keeps the Secure attribute when running in production", async () => {
    process.env.NODE_ENV = "production";

    const response = await POST();
    const cookie = response.headers.get("set-cookie") ?? "";

    assert.match(cookie, /Secure/i);
    assert.match(cookie, /Max-Age=0/i);
  });
});
