import { NextResponse } from "next/server";

const API_URL = process.env.API_INTERNAL_URL ?? "https://sky-api-cmm2.onrender.com";

export async function POST(request: Request) {
  let payload: { email?: string; password?: string; display_name?: string };

  try {
    payload = await request.json();
  } catch {
    return NextResponse.json({ detail: "Pedido inválido." }, { status: 400 });
  }

  const apiResponse = await fetch(`${API_URL}/api/v1/auth/register`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
    cache: "no-store",
  }).catch(() => null);

  if (!apiResponse) {
    return NextResponse.json(
      { detail: "Não foi possível contactar a API SKY." },
      { status: 502 },
    );
  }

  const data = await apiResponse.json().catch(() => ({}));
  return NextResponse.json(data, { status: apiResponse.status });
}
