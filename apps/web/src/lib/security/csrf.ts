/**
 * Verifica que um pedido mutável para o BFF foi iniciado pela própria origem.
 * A comparação usa a origem pública do pedido recebida pelo Next.js; não confia
 * em cabeçalhos de encaminhamento fornecidos pelo browser.
 */
export function isSameOriginMutation(request: Request): boolean {
  const origin = request.headers.get("origin");
  if (!origin) {
    return false;
  }

  let requestOrigin: string;
  try {
    requestOrigin = new URL(request.url).origin;
  } catch {
    return false;
  }

  if (origin !== requestOrigin) {
    return false;
  }

  const fetchSite = request.headers.get("sec-fetch-site");
  if (fetchSite && fetchSite !== "same-origin") {
    return false;
  }

  return true;
}
