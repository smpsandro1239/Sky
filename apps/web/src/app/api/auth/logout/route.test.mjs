import assert from "node:assert/strict";
import { afterEach, describe, it } from "node:test";

import { POST } from "./route.ts";

const originalNodeEnv = process.env.NODE_ENV;
const originalFetch = globalThis.fetch;

afterEach(() => {
  if (originalNodeEnv === undefined) {
    delete process.env.NODE_ENV;
  } else {
    process.env.NODE_ENV = originalNodeEnv;
  }
  globalThis.fetch = originalFetch;
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

  it("expires the local cookie when no access token is present", async () => {
    process.env.NODE_ENV = "development";

    const response = await POST(new Request("http://localhost/api/auth/logout", {
      method: "POST",
      headers: { Origin: "http://localhost" },
    }));
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
    assert.deepEqual(await response.json(), {
      message: "Sessão terminada.",
      server_revoked: true,
    });
  });

  it("revokes the API session before expiring the local cookie", async () => {
    let calledUrl = "";
    let calledAuthorization = "";
    globalThis.fetch = async (url, init) => {
      calledUrl = String(url);
      calledAuthorization = new Headers(init?.headers).get("authorization") ?? "";
      return new Response(null, { status: 204 });
    };

    const response = await POST(new Request("http://localhost/api/auth/logout", {
      method: "POST",
      headers: {
        Origin: "http://localhost",
        Cookie: "sky_access_token=opaque-token",
      },
    }));

    assert.equal(calledUrl, "http://localhost:8000/api/v1/auth/logout");
    assert.equal(calledAuthorization, "Bearer opaque-token");
    assert.equal(response.status, 200);
    assert.deepEqual(await response.json(), {
      message: "Sessão terminada.",
      server_revoked: true,
    });
    assert.match(response.headers.get("set-cookie") ?? "", /Max-Age=0/i);
  });

  it("reports when server-side revocation could not be confirmed", async () => {
    globalThis.fetch = async () => {
      throw new Error("API unavailable");
    };

    const response = await POST(new Request("http://localhost/api/auth/logout", {
      method: "POST",
      headers: {
        Origin: "http://localhost",
        Cookie: "sky_access_token=opaque-token",
      },
    }));

    assert.equal(response.status, 200);
    assert.deepEqual(await response.json(), {
      message: "Cookie eliminado; a revogação no servidor não foi confirmada.",
      server_revoked: false,
    });
    assert.match(response.headers.get("set-cookie") ?? "", /Max-Age=0/i);
  });

  it("keeps the Secure attribute when running in production", async () => {
    process.env.NODE_ENV = "production";

    const response = await POST(new Request("http://localhost/api/auth/logout", {
      method: "POST",
      headers: { Origin: "http://localhost" },
    }));
    const cookie = response.headers.get("set-cookie") ?? "";

    assert.match(cookie, /Secure/i);
    assert.match(cookie, /Max-Age=0/i);
  });
});
