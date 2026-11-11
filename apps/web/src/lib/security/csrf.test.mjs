import test from "node:test";
import assert from "node:assert/strict";
import { isSameOriginMutation } from "./csrf.ts";

const endpoint = "https://sky.example.com/api/backend/trips";

test("aceita pedido com Origin exactamente igual à origem do BFF", () => {
  const request = new Request(endpoint, {
    method: "POST",
    headers: { Origin: "https://sky.example.com" },
  });
  assert.equal(isSameOriginMutation(request), true);
});

test("rejeita pedido sem Origin", () => {
  const request = new Request(endpoint, { method: "POST" });
  assert.equal(isSameOriginMutation(request), false);
});

test("rejeita Origin de outro domínio", () => {
  const request = new Request(endpoint, {
    method: "POST",
    headers: { Origin: "https://attacker.example" },
  });
  assert.equal(isSameOriginMutation(request), false);
});

test("rejeita pedido marcado pelo browser como cross-site", () => {
  const request = new Request(endpoint, {
    method: "POST",
    headers: {
      Origin: "https://sky.example.com",
      "Sec-Fetch-Site": "cross-site",
    },
  });
  assert.equal(isSameOriginMutation(request), false);
});

test("rejeita pedido marcado como same-site mas não same-origin", () => {
  const request = new Request(endpoint, {
    method: "DELETE",
    headers: {
      Origin: "https://sky.example.com",
      "Sec-Fetch-Site": "same-site",
    },
  });
  assert.equal(isSameOriginMutation(request), false);
});

test("aceita pedido same-origin sem Sec-Fetch-Site", () => {
  const request = new Request(endpoint, {
    method: "PATCH",
    headers: { Origin: "https://sky.example.com" },
  });
  assert.equal(isSameOriginMutation(request), true);
});
