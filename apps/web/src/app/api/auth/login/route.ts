import { isSameOriginMutation } from "../../../../lib/security/csrf";

const API_URL = process.env.API_INTERNAL_URL ?? "http://localhost:8000";

type LoginResponse = {
  access_token?: unknown;
  expires_in?: unknown;
  detail?: unknown;
};

function jsonResponse(body: unknown, status = 200) {
  return Response.json(body, {
    status,
    headers: { "Cache-Control": "no-store" },
  });
}

export async function POST(request: Request) {
  if (!isSameOriginMutation(request)) {
    return jsonResponse({ detail: "Pedido rejeitado: origem não autorizada." }, 403);
  }

  let payload: { email?: string; password?: string };

  try {
    payload = await request.json();
  } catch {
    return jsonResponse({ detail: "Pedido inválido." }, 400);
  }

  const loginResponse = await fetch(`${API_URL}/api/v1/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
    cache: "no-store",
  }).catch(() => null);

  if (!loginResponse) {
    return jsonResponse(
      { detail: "Não foi possível contactar a API SKY." },
      502,
    );
  }

  const loginData = (await loginResponse.json().catch(() => null)) as LoginResponse | null;
  if (!loginResponse.ok) {
    return jsonResponse(
      {
        detail:
          typeof loginData?.detail === "string"
            ? loginData.detail
            : "Não foi possível iniciar sessão.",
      },
      loginResponse.status,
    );
  }

  if (
    typeof loginData?.access_token !== "string" ||
    loginData.access_token.trim().length === 0 ||
    typeof loginData.expires_in !== "number" ||
    !Number.isSafeInteger(loginData.expires_in) ||
    loginData.expires_in <= 0
  ) {
    return jsonResponse(
      { detail: "A API SKY devolveu uma resposta de autenticação inválida." },
      502,
    );
  }

  let profileResponse: Response;
  try {
    profileResponse = await fetch(`${API_URL}/api/v1/auth/me`, {
      headers: { Authorization: `Bearer ${loginData.access_token}` },
      cache: "no-store",
    });
  } catch {
    return jsonResponse(
      { detail: "A sessão foi iniciada, mas não foi possível contactar o serviço de perfil." },
      502,
    );
  }

  if (!profileResponse.ok) {
    return jsonResponse(
      { detail: "A sessão foi iniciada, mas não foi possível carregar o perfil." },
      502,
    );
  }

  const profile = await profileResponse.json().catch(() => null);
  if (profile === null || typeof profile !== "object" || Array.isArray(profile)) {
    return jsonResponse(
      { detail: "O serviço de perfil devolveu uma resposta inválida." },
      502,
    );
  }

  const response = jsonResponse(profile);
  const cookieAttributes = [
    `sky_access_token=${encodeURIComponent(loginData.access_token)}`,
    "HttpOnly",
    "SameSite=Lax",
    "Path=/",
    `Max-Age=${loginData.expires_in}`,
  ];

  if (process.env.NODE_ENV === "production") {
    cookieAttributes.push("Secure");
  }

  response.headers.append("Set-Cookie", cookieAttributes.join("; "));
  return response;
}
