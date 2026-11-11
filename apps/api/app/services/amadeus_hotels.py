import asyncio
import time
from typing import Any

import httpx

from app.core.config import settings


class HotelProviderNotConfigured(Exception):
    pass


class HotelProviderError(Exception):
    pass


class AmadeusHotelProvider:
    """Pesquisa de hotéis e ofertas disponíveis; não efetua reservas."""

    def __init__(self) -> None:
        self._access_token: str | None = None
        self._token_expires_at = 0.0
        self._token_lock = asyncio.Lock()

    @property
    def _base_url(self) -> str:
        return settings.amadeus_base_url.rstrip("/")

    async def _get_access_token(self, client: httpx.AsyncClient) -> str:
        if not settings.amadeus_client_id or not settings.amadeus_client_secret:
            raise HotelProviderNotConfigured("O fornecedor Amadeus não está configurado.")
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
                    raise HotelProviderError("O fornecedor devolveu um token inválido.")
            except (httpx.HTTPError, ValueError, TypeError) as exc:
                raise HotelProviderError("Não foi possível autenticar no fornecedor de alojamentos.") from exc
            self._access_token = token
            self._token_expires_at = time.monotonic() + max(expires_in - 60, 0)
            return token

    async def search(self, criteria: dict[str, Any]) -> list[dict[str, Any]]:
        timeout = httpx.Timeout(25.0, connect=5.0)
        async with httpx.AsyncClient(timeout=timeout) as client:
            token = await self._get_access_token(client)
            headers = {"Authorization": f"Bearer {token}"}
            try:
                hotel_response = await client.get(
                    f"{self._base_url}/v1/reference-data/locations/hotels/by-city",
                    params={
                        "cityCode": criteria["city_code"],
                        "radius": criteria["radius"],
                        "radiusUnit": "KM",
                        "hotelSource": "ALL",
                    },
                    headers=headers,
                )
                hotel_response.raise_for_status()
                hotels_payload = hotel_response.json()
                hotels = hotels_payload.get("data", [])
                if not isinstance(hotels, list):
                    raise HotelProviderError("A lista de hotéis recebida tem um formato inesperado.")
                hotel_ids = [
                    str(item.get("hotelId"))
                    for item in hotels
                    if isinstance(item, dict) and item.get("hotelId")
                ][:criteria["max_hotels"]]
                if not hotel_ids:
                    return []

                offers_response = await client.get(
                    f"{self._base_url}/v3/shopping/hotel-offers",
                    params={
                        "hotelIds": ",".join(hotel_ids),
                        "adults": criteria["adults"],
                        "checkInDate": criteria["check_in"].isoformat(),
                        "checkOutDate": criteria["check_out"].isoformat(),
                        "roomQuantity": criteria["room_quantity"],
                        "currency": criteria["currency"],
                    },
                    headers=headers,
                )
                offers_response.raise_for_status()
                offers_payload = offers_response.json()
            except httpx.HTTPStatusError as exc:
                if exc.response.status_code == 429:
                    raise HotelProviderError("O fornecedor está a limitar temporariamente as pesquisas.") from exc
                raise HotelProviderError("O fornecedor não conseguiu concluir a pesquisa de alojamentos.") from exc
            except (httpx.HTTPError, ValueError) as exc:
                raise HotelProviderError("Não foi possível obter resultados do fornecedor de alojamentos.") from exc

        results = offers_payload.get("data", [])
        if not isinstance(results, list):
            raise HotelProviderError("O fornecedor devolveu resultados num formato inesperado.")
        return results


amadeus_hotel_provider = AmadeusHotelProvider()
