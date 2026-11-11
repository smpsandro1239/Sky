import { cookies } from "next/headers";
import { NextResponse } from "next/server";

const API_URL = process.env.API_INTERNAL_URL ?? "http://localhost:8000";
const UUID_PATTERN = "[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[1-8][0-9a-fA-F]{3}-[89aAbB][0-9a-fA-F]{3}-[0-9a-fA-F]{12}";

async function proxyRequest(
  request: Request,
  context: { params: Promise<{ path: string[] }> },
  method: "GET" | "POST" | "PATCH" | "DELETE",
) {
  const { path } = await context.params;
  const resource = path.join("/");
  const isCollection = resource === "trips";
  const isProfile = resource === "auth/me";
  const isTripItem = new RegExp("^trips/" + UUID_PATTERN + "$").test(resource);
  const isTripAccess = new RegExp("^trips/" + UUID_PATTERN + "/access$").test(resource);
  const isTripBalances = new RegExp("^trips/" + UUID_PATTERN + "/balances$").test(resource);
  const isTripSettlements = new RegExp("^trips/" + UUID_PATTERN + "/settlements$").test(resource);
  const isTripActivity = new RegExp("^trips/" + UUID_PATTERN + "/activity$").test(resource);
  const isFlightCollection = new RegExp("^trips/" + UUID_PATTERN + "/flights$").test(resource);
  const isFlightItem = new RegExp("^trips/" + UUID_PATTERN + "/flights/" + UUID_PATTERN + "$").test(resource);
  const isAccommodationCollection = new RegExp("^trips/" + UUID_PATTERN + "/accommodations$").test(resource);
  const isAccommodationItem = new RegExp("^trips/" + UUID_PATTERN + "/accommodations/" + UUID_PATTERN + "$").test(resource);
  const isExpenseCollection = new RegExp("^trips/" + UUID_PATTERN + "/expenses$").test(resource);
  const isExpenseItem = new RegExp("^trips/" + UUID_PATTERN + "/expenses/" + UUID_PATTERN + "$").test(resource);
  const isExpenseSharesCollection = new RegExp("^trips/" + UUID_PATTERN + "/expenses/" + UUID_PATTERN + "/shares$").test(resource);
  const isParticipantCollection = new RegExp("^trips/" + UUID_PATTERN + "/participants$").test(resource);
  const isParticipantItem = new RegExp("^trips/" + UUID_PATTERN + "/participants/" + UUID_PATTERN + "$").test(resource);
  const isInvitationCollection = new RegExp("^trips/" + UUID_PATTERN + "/invitations$").test(resource);
  const isInvitationItem = new RegExp("^trips/" + UUID_PATTERN + "/invitations/" + UUID_PATTERN + "$").test(resource);
  const isInvitationAccept = resource === "invitations/accept";
  const isFlightSearch = resource === "flights/search";
  const isHotelSearch = resource === "hotels/search";

  const allowed =
    (method === "GET" && (isFlightSearch || isHotelSearch || isProfile || isCollection || isTripItem || isTripAccess || isTripBalances || isTripSettlements || isTripActivity || isFlightCollection || isAccommodationCollection || isExpenseCollection || isExpenseSharesCollection || isParticipantCollection || isInvitationCollection)) ||
    (method === "POST" && (isCollection || isFlightCollection || isAccommodationCollection || isExpenseCollection || isTripSettlements || isParticipantCollection || isInvitationCollection || isInvitationAccept)) ||
    (method === "PATCH" && (isTripItem || isParticipantItem || isFlightItem || isAccommodationItem || isExpenseItem || isExpenseSharesCollection)) ||
    (method === "DELETE" && (isTripItem || isFlightItem || isAccommodationItem || isExpenseItem || isParticipantItem || isInvitationItem));

  if (!allowed) {
    return NextResponse.json({ detail: "Recurso ou operação não permitido." }, { status: 404 });
  }

  const cookieStore = await cookies();
  const token = cookieStore.get("sky_access_token")?.value;

  if (!token) {
    return NextResponse.json({ detail: "Sessão não autenticada." }, { status: 401 });
  }

  const headers: Record<string, string> = { Authorization: "Bearer " + token };
  let body: string | undefined;
  if (method === "POST" || method === "PATCH") {
    headers["Content-Type"] = "application/json";
    body = await request.text();
  }

  const query = new URL(request.url).search;
  const apiResponse = await fetch(API_URL + "/api/v1/" + resource + query, {
    method,
    headers,
    body,
    cache: "no-store",
  }).catch(() => null);

  if (!apiResponse) {
    return NextResponse.json(
      { detail: "Não foi possível contactar a API SKY." },
      { status: 502 },
    );
  }

  if (apiResponse.status === 204) {
    return new NextResponse(null, { status: 204 });
  }

  const data = await apiResponse.json().catch(() => ({}));
  return NextResponse.json(data, { status: apiResponse.status });
}

type RouteContext = { params: Promise<{ path: string[] }> };

export async function GET(request: Request, context: RouteContext) {
  return proxyRequest(request, context, "GET");
}

export async function POST(request: Request, context: RouteContext) {
  return proxyRequest(request, context, "POST");
}

export async function PATCH(request: Request, context: RouteContext) {
  return proxyRequest(request, context, "PATCH");
}

export async function DELETE(request: Request, context: RouteContext) {
  return proxyRequest(request, context, "DELETE");
}
