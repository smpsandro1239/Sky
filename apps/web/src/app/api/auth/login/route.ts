import { NextResponse } from "next/server";

const API_URL = process.env.API_INTERNAL_URL ?? "http://localhost:8000";

type LoginResponse = {
  access_token?: unknown;
  expires_in?: unknown;
  detail?: unknown;
};

export async function POST(request: Request) {
  let payload: { email?: string; password?: string };

  try {
    payload = await request.json();
  } catch {
    return NextResponse.json({ detail: "Pedido inválido." }, { status: 400 });
  }

  const loginResponse = await fetch(`${API_URL}/api/v1/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
    cache: "no-store",
  }).catch(() => null);

  if (!loginResponse) {
    return NextResponse.json(
      { detail: "Não foi possível contactar a API SKY." },
      { status: 502 },
    );
  }

  const loginData = (await loginResponse.json().catch(() => null)) as LoginResponse | null;
  if (!loginResponse.ok) {
    return NextResponse.json(
      {
        detail:
          typeof loginData?.detail === "string"
            ? loginData.detail
            : "Não foi possível iniciar sessão.",
      },
      { status: loginResponse.status },
    );
  }

  if (
    typeof loginData?.access_token !== "string" ||
    typeof loginData.expires_in !== "number" ||
    !Number.isFinite(loginData.expires_in) ||
    loginData.expires_in <= 0
  ) {
    return NextResponse.json(
      { detail: "A API SKY devolveu uma resposta de autenticação inválida." },
      { status: 502 },
    );
  }

  let profileResponse: Response;
  try {
    profileResponse = await fetch(`${API_URL}/api/v1/auth/me`, {
      headers: { Authorization: `Bearer ${loginData.access_token}` },
      cache: "no-store",
    });
  } catch {
    return NextResponse.json(
      { detail: "A sessão foi iniciada, mas não foi possível contactar o serviço de perfil." },
      { status: 502 },
    );
  }

  if (!profileResponse.ok) {
    return NextResponse.json(
      { detail: "A sessão foi iniciada, mas não foi possível carregar o perfil." },
      { status: 502 },
    );
  }

  const profile = await profileResponse.json().catch(() => null);
  if (profile === null || typeof profile !== "object" || Array.isArray(profile)) {
    return NextResponse.json(
      { detail: "O serviço de perfil devolveu uma resposta inválida." },
      { status: 502 },
    );
  }

  const response = NextResponse.json(profile);
  response.cookies.set("sky_access_token", loginData.access_token, {
    httpOnly: true,
    secure: process.env.NODE_ENV === "production",
    sameSite: "lax",
    path: "/",
    maxAge: loginData.expires_in,
  });
  return response;
}
