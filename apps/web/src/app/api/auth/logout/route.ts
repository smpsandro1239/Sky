import { isSameOriginMutation } from "../../../../lib/security/csrf.ts";

const API_URL = process.env.API_INTERNAL_URL ?? "https://sky-api-cmm2.onrender.com";

function readAccessToken(request: Request): string | null {
  const cookie = request.headers.get("cookie") ?? "";
  const match = cookie.match(/(?:^|;\s*)sky_access_token=([^;]+)/);
  if (!match) return null;

  try {
    return decodeURIComponent(match[1]);
  } catch {
    return null;
  }
}

export async function POST(request: Request) {
  if (!isSameOriginMutation(request)) {
    return Response.json(
      { detail: "Pedido rejeitado: origem não autorizada." },
      { status: 403, headers: { "Cache-Control": "no-store" } },
    );
  }

  const token = readAccessToken(request);
  let serverRevoked = token === null;

  if (token) {
    try {
      const revokeResponse = await fetch(`${API_URL}/api/v1/auth/logout`, {
        method: "POST",
        headers: { Authorization: `Bearer ${token}` },
        cache: "no-store",
      });
      serverRevoked = revokeResponse.ok || revokeResponse.status === 401;
    } catch {
      serverRevoked = false;
    }
  }

  const response = Response.json(
    {
      message: serverRevoked
        ? "Sessão terminada."
        : "Cookie eliminado; a revogação no servidor não foi confirmada.",
      server_revoked: serverRevoked,
    },
    { headers: { "Cache-Control": "no-store" } },
  );

  const cookieAttributes = [
    "sky_access_token=",
    "HttpOnly",
    "SameSite=Lax",
    "Path=/",
    "Max-Age=0",
    "Expires=Thu, 01 Jan 1970 00:00:00 GMT",
  ];

  if (process.env.NODE_ENV === "production") {
    cookieAttributes.push("Secure");
  }

  response.headers.append("Set-Cookie", cookieAttributes.join("; "));
  return response;
}
