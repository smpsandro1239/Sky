import asyncio
import time
from typing import Any

import httpx

from app.core.config import settings


class FlightProviderNotConfigured(Exception):
    pass


class FlightProviderError(Exception):
    pass


class AmadeusFlightProvider:
    """Adaptador de pesquisa Amadeus; não cria reservas nem emite bilhetes."""

    def __init__(self) -> None:
        self._access_token: str | None = None
        self._token_expires_at = 0.0
        self._token_lock = asyncio.Lock()

    @property
    def _base_url(self) -> str:
        return settings.amadeus_base_url.rstrip("/")

    async def _get_access_token(self, client: httpx.AsyncClient) -> str:
        if not settings.amadeus_client_id or not settings.amadeus_client_secret:
            raise FlightProviderNotConfigured("O fornecedor Amadeus não está configurado.")

        if self._access_token and time.monotonic() < self._token_expires_at:
            return self._access_token

        async with self._token_lock:
            if self._access_token and time.monotonic() < self._token_expires_at:
                return self._access_token

            try:
                response = await client.post(
                    f"{self._base_url}/v1/security/oauth2/token",
                    data={
                        "grant_type": "client_credentials",
                        "client_id": settings.amadeus_client_id,
                        "client_secret": settings.amadeus_client_secret,
                    },
                    headers={"Content-Type": "application/x-www-form-urlencoded"},
                )
                response.raise_for_status()
                payload = response.json()
                token = payload.get("access_token")
                expires_in = int(payload.get("expires_in", 0))
                if not token or expires_in <= 0:
                    raise FlightProviderError("O fornecedor devolveu um token inválido.")
            except (httpx.HTTPError, ValueError, TypeError) as exc:
                raise FlightProviderError("Não foi possível autenticar no fornecedor de voos.") from exc

            self._access_token = token
            self._token_expires_at = time.monotonic() + max(expires_in - 60, 0)
            return token

    async def search(self, criteria: dict[str, Any]) -> list[dict[str, Any]]:
        timeout = httpx.Timeout(20.0, connect=5.0)
        async with httpx.AsyncClient(timeout=timeout) as client:
            token = await self._get_access_token(client)
            params = {
                "originLocationCode": criteria["origin"],
                "destinationLocationCode": criteria["destination"],
                "departureDate": criteria["departure_date"].isoformat(),
                "adults": criteria["adults"],
                "currencyCode": criteria["currency"],
                "nonStop": str(criteria["non_stop"]).lower(),
                "max": criteria["max_results"],
            }
            if criteria.get("return_date"):
                params["returnDate"] = criteria["return_date"].isoformat()

            try:
                response = await client.get(
                    f"{self._base_url}/v2/shopping/flight-offers",
                    params=params,
                    headers={"Authorization": f"Bearer {token}"},
                )
                response.raise_for_status()
                payload = response.json()
            except httpx.HTTPStatusError as exc:
                status_code = exc.response.status_code
                if status_code == 429:
                    raise FlightProviderError("O fornecedor está a limitar temporariamente as pesquisas.") from exc
                raise FlightProviderError("O fornecedor não conseguiu concluir a pesquisa de voos.") from exc
            except (httpx.HTTPError, ValueError) as exc:
                raise FlightProviderError("Não foi possível obter resultados do fornecedor de voos.") from exc

        offers = payload.get("data", [])
        if not isinstance(offers, list):
            raise FlightProviderError("O fornecedor devolveu resultados num formato inesperado.")
        return offers


amadeus_flight_provider = AmadeusFlightProvider()
