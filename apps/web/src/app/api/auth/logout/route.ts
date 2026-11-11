export async function POST() {
  const response = Response.json(
    { message: "Sessão terminada." },
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
