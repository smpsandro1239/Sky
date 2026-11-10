import { cookies } from "next/headers";
import { NextResponse } from "next/server";

const API_URL = process.env.API_INTERNAL_URL ?? "http://localhost:8000";

export async function GET(
  _request: Request,
  context: { params: Promise<{ path: string[] }> },
) {
  const { path } = await context.params;
  const resource = path.join("/");

  if (resource !== "auth/me" && resource !== "trips") {
    return NextResponse.json({ detail: "Recurso não permitido." }, { status: 404 });
  }

  const cookieStore = await cookies();
  const token = cookieStore.get("sky_access_token")?.value;

  if (!token) {
    return NextResponse.json({ detail: "Sessão não autenticada." }, { status: 401 });
  }

  const apiResponse = await fetch(`${API_URL}/api/v1/${resource}`, {
    headers: { Authorization: `Bearer ${token}` },
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
