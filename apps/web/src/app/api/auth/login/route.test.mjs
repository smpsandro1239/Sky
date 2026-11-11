import assert from "node:assert/strict";
import { afterEach, describe, it, mock } from "node:test";

import { POST } from "./route.ts";

const originalNodeEnv = process.env.NODE_ENV;

afterEach(() => {
  mock.restoreAll();
  if (originalNodeEnv === undefined) {
    delete process.env.NODE_ENV;
  } else {
    process.env.NODE_ENV = originalNodeEnv;
  }
});

function jsonResponse(body, status = 200) {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

function request(body = { email: "user@example.com", password: "correct-password" }) {
  return new Request("http://localhost/api/auth/login", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
}

describe("POST /api/auth/login", () => {
  it("returns 400 for malformed JSON without contacting the API", async () => {
    mock.method(globalThis, "fetch", async () => {
      assert.fail("fetch não devia ser chamado");
    });

    const response = await POST(
      new Request("http://localhost/api/auth/login", {
        method: "POST",
        body: "{",
      }),
    );

    assert.equal(response.status, 400);
  });

  it("returns 502 when the login API cannot be reached", async () => {
    mock.method(globalThis, "fetch", async () => {
      throw new Error("network unavailable");
    });

    const response = await POST(request());

    assert.equal(response.status, 502);
  });

  it("rejects a successful login response with an empty token", async () => {
    mock.method(globalThis, "fetch", async () => jsonResponse({ access_token: " ", expires_in: 3600 }));

    const response = await POST(request());

    assert.equal(response.status, 502);
    assert.equal(response.headers.get("set-cookie"), null);
  });

  it("rejects a successful login response with an invalid expiry", async () => {
    mock.method(globalThis, "fetch", async () => jsonResponse({ access_token: "valid-token", expires_in: "3600" }));

    const response = await POST(request());

    assert.equal(response.status, 502);
    assert.equal(response.headers.get("set-cookie"), null);
  });

  it("returns 502 when the profile API cannot be reached", async () => {
    let calls = 0;
    mock.method(globalThis, "fetch", async () => {
      calls += 1;
      if (calls === 1) {
        return jsonResponse({ access_token: "valid-token", expires_in: 3600 });
      }
      throw new Error("profile service unavailable");
    });

    const response = await POST(request());

    assert.equal(calls, 2);
    assert.equal(response.status, 502);
    assert.equal(response.headers.get("set-cookie"), null);
  });

  it("does not create a session cookie when the profile endpoint rejects the token", async () => {
    let calls = 0;
    mock.method(globalThis, "fetch", async () => {
      calls += 1;
      if (calls === 1) {
        return jsonResponse({ access_token: "valid-token", expires_in: 3600 });
      }
      return jsonResponse({ detail: "Unauthorized" }, 401);
    });

    const response = await POST(request());

    assert.equal(response.status, 502);
    assert.equal(response.headers.get("set-cookie"), null);
  });

  it("does not create a session cookie when the profile response is not JSON", async () => {
    let calls = 0;
    mock.method(globalThis, "fetch", async () => {
      calls += 1;
      if (calls === 1) {
        return jsonResponse({ access_token: "valid-token", expires_in: 3600 });
      }
      return new Response("not-json", {
        status: 200,
        headers: { "Content-Type": "text/plain" },
      });
    });

    const response = await POST(request());

    assert.equal(response.status, 502);
    assert.equal(response.headers.get("set-cookie"), null);
  });

  it("sets an HttpOnly session cookie only after the profile loads", async () => {
    let calls = 0;
    mock.method(globalThis, "fetch", async () => {
      calls += 1;
      if (calls === 1) {
        return jsonResponse({ access_token: "valid-token", expires_in: 3600 });
      }
      return jsonResponse({
        id: "user-id",
        email: "user@example.com",
        display_name: "Utilizador",
        is_active: true,
        is_verified: false,
      });
    });

    const response = await POST(request());
    const cookie = response.headers.get("set-cookie");

    assert.equal(response.status, 200);
    assert.equal(calls, 2);
    assert.match(cookie ?? "", /sky_access_token=valid-token/);
    assert.match(cookie ?? "", /HttpOnly/i);
    assert.match(cookie ?? "", /SameSite=Lax/i);
    assert.match(cookie ?? "", /Path=\//i);
    assert.match(cookie ?? "", /Max-Age=3600/i);
  });
});
