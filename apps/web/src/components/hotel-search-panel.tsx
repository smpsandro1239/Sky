"use client";

import { FormEvent, useEffect, useState } from "react";

type HotelOffer = {
  id: string;
  provider: "amadeus";
  hotel_name: string;
  hotel_id: string;
  location: string;
  check_in: string;
  check_out: string;
  price_total: string;
  currency: string;
  room_description: string | null;
  board_type: string | null;
  payment_type: string | null;
  cancellation_deadline: string | null;
  cancellation_description: string | null;
  nights: number | null;
  price_per_night: string | null;
  recommendation_score: number | null;
  recommendation_reasons: string[];
};

type SavedAccommodation = {
  id: string;
  provider: string | null;
  name: string;
  location: string;
  check_in: string;
  check_out: string;
  price_amount: string | null;
  price_currency: string;
};

type Props = {
  tripId: string;
  canEdit: boolean;
  onAccommodationSaved: (accommodation: SavedAccommodation) => void;
};

type SearchResponse = { results_count: number; search_key: string; offers: HotelOffer[] };

type HotelFavorite = {
  id: string;
  provider: string;
  hotel_id: string;
  hotel_name: string;
  location: string;
  created_at: string;
};

async function fetchHotelFavorites(): Promise<HotelFavorite[]> {
  const response = await fetch("/api/backend/hotels/favorites", { cache: "no-store" });
  const payload = await response.json().catch(() => null);
  if (!response.ok) {
    const detail = payload && typeof payload.detail === "string" ? payload.detail : "Não foi possível carregar os hotéis favoritos.";
    throw new Error(detail);
  }
  if (!Array.isArray(payload) || !payload.every((item) =>
    item && typeof item.id === "string" && typeof item.hotel_id === "string"
    && typeof item.hotel_name === "string" && typeof item.location === "string"
  )) {
    throw new Error("A resposta dos favoritos tem um formato inválido.");
  }
  return payload as HotelFavorite[];
}

function formatPrice(amount: string, currency: string) {
  const value = Number(amount);
  if (!Number.isFinite(value)) return amount + " " + currency;
  return new Intl.NumberFormat("pt-PT", { style: "currency", currency }).format(value);
}

export default function HotelSearchPanel({ tripId, canEdit, onAccommodationSaved }: Props) {
  const [cityCode, setCityCode] = useState("");
  const [checkIn, setCheckIn] = useState("");
  const [checkOut, setCheckOut] = useState("");
  const [adults, setAdults] = useState("2");
  const [roomQuantity, setRoomQuantity] = useState("1");
  const [radius, setRadius] = useState("20");
  const [currency, setCurrency] = useState("EUR");
  const [loading, setLoading] = useState(false);
  const [savingId, setSavingId] = useState<string | null>(null);
  const [results, setResults] = useState<SearchResponse | null>(null);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const [savedOfferIds, setSavedOfferIds] = useState<string[]>([]);
  const [comparisonIds, setComparisonIds] = useState<string[]>([]);
  const [minimumPrice, setMinimumPrice] = useState("");
  const [maximumPrice, setMaximumPrice] = useState("");
  const [favorites, setFavorites] = useState<HotelFavorite[]>([]);
  const [favoritesLoading, setFavoritesLoading] = useState(true);
  const [favoritesError, setFavoritesError] = useState("");
  const [favoriteActionId, setFavoriteActionId] = useState<string | null>(null);

  async function loadFavorites() {
    setFavoritesLoading(true);
    setFavoritesError("");
    try {
      setFavorites(await fetchHotelFavorites());
    } catch (cause) {
      setFavoritesError(cause instanceof Error ? cause.message : "Ocorreu um erro ao carregar os favoritos.");
    } finally {
      setFavoritesLoading(false);
    }
  }

  useEffect(() => {
    let active = true;
    fetchHotelFavorites()
      .then((items) => {
        if (active) {
          setFavorites(items);
          setFavoritesError("");
        }
      })
      .catch((cause: unknown) => {
        if (active) setFavoritesError(cause instanceof Error ? cause.message : "Ocorreu um erro ao carregar os favoritos.");
      })
      .finally(() => {
        if (active) setFavoritesLoading(false);
      });
    return () => { active = false; };
  }, []);

  async function search(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setLoading(true);
    setError("");
    setMessage("");
    setResults(null);
    setComparisonIds([]);
    setMinimumPrice("");
    setMaximumPrice("");
    const params = new URLSearchParams({
      city_code: cityCode.trim().toUpperCase(),
      check_in: checkIn,
      check_out: checkOut,
      adults,
      room_quantity: roomQuantity,
      radius,
      currency,
    });
    try {
      const response = await fetch("/api/backend/hotels/search?" + params.toString(), { cache: "no-store" });
      const payload = await response.json().catch(() => ({}));
      if (!response.ok) throw new Error(typeof payload.detail === "string" ? payload.detail : "Não foi possível pesquisar alojamentos.");
      setResults(payload as SearchResponse);
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Ocorreu um erro na pesquisa.");
    } finally {
      setLoading(false);
    }
  }

  async function toggleFavorite(offer: HotelOffer) {
    const existing = favorites.find((favorite) => favorite.hotel_id === offer.hotel_id);
    setFavoriteActionId(offer.hotel_id);
    setError("");
    setMessage("");
    try {
      const response = existing
        ? await fetch("/api/backend/hotels/favorites/" + existing.id, { method: "DELETE" })
        : await fetch("/api/backend/hotels/favorites", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              provider: offer.provider,
              hotel_id: offer.hotel_id,
              hotel_name: offer.hotel_name,
              location: offer.location || cityCode.toUpperCase(),
            }),
          });
      const payload = existing ? null : await response.json().catch(() => ({}));
      if (!response.ok) {
        const detail = payload && typeof payload.detail === "string" ? payload.detail : "Não foi possível atualizar os favoritos.";
        throw new Error(detail);
      }
      if (existing) {
        setFavorites((current) => current.filter((favorite) => favorite.id !== existing.id));
        setMessage(offer.hotel_name + " foi retirado dos favoritos.");
      } else {
        setFavorites((current) => current.some((favorite) => favorite.hotel_id === offer.hotel_id) ? current : [...current, payload as HotelFavorite]);
        setMessage(offer.hotel_name + " foi adicionado aos favoritos.");
      }
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Ocorreu um erro ao atualizar os favoritos.");
    } finally {
      setFavoriteActionId(null);
    }
  }


  async function removeFavorite(favorite: HotelFavorite) {
    setFavoriteActionId(favorite.hotel_id);
    setError("");
    setMessage("");
    try {
      const response = await fetch("/api/backend/hotels/favorites/" + favorite.id, { method: "DELETE" });
      if (!response.ok) throw new Error("Não foi possível remover este favorito.");
      setFavorites((current) => current.filter((item) => item.id !== favorite.id));
      setMessage(favorite.hotel_name + " foi retirado dos favoritos.");
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Ocorreu um erro ao remover o favorito.");
    } finally {
      setFavoriteActionId(null);
    }
  }

  function toggleComparison(offerId: string) {
    setComparisonIds((current) => {
      if (current.includes(offerId)) return current.filter((id) => id !== offerId);
      if (current.length >= 3) return current;
      return [...current, offerId];
    });
  }

  const resultsCurrency = results?.offers[0]?.currency ?? currency;
  const parsedMinimumPrice = minimumPrice === "" ? null : Number(minimumPrice);
  const parsedMaximumPrice = maximumPrice === "" ? null : Number(maximumPrice);
  const minimumPriceInvalid = parsedMinimumPrice !== null && (!Number.isFinite(parsedMinimumPrice) || parsedMinimumPrice < 0);
  const maximumPriceInvalid = parsedMaximumPrice !== null && (!Number.isFinite(parsedMaximumPrice) || parsedMaximumPrice < 0);
  const priceRangeInvalid = minimumPriceInvalid || maximumPriceInvalid
    || (parsedMinimumPrice !== null && parsedMaximumPrice !== null && parsedMinimumPrice > parsedMaximumPrice);
  const filteredOffers = (results?.offers ?? []).filter((offer) => {
    const price = Number(offer.price_total);
    if (!Number.isFinite(price) || priceRangeInvalid) return false;
    if (parsedMinimumPrice !== null && price < parsedMinimumPrice) return false;
    if (parsedMaximumPrice !== null && price > parsedMaximumPrice) return false;
    return true;
  });
  const comparisonOffers = (results?.offers ?? []).filter((offer) => comparisonIds.includes(offer.id));
  const comparisonNights = comparisonOffers.length > 0
    ? Math.max(1, Math.round((new Date(comparisonOffers[0].check_out + "T00:00:00Z").getTime() - new Date(comparisonOffers[0].check_in + "T00:00:00Z").getTime()) / 86_400_000))
    : 0;

  async function saveOffer(offer: HotelOffer) {
    setSavingId(offer.id);
    setError("");
    setMessage("");
    try {
      const response = await fetch("/api/backend/trips/" + tripId + "/accommodations", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          provider: "Amadeus",
          name: offer.hotel_name,
          location: offer.location || cityCode.toUpperCase(),
          check_in: offer.check_in,
          check_out: offer.check_out,
          price_amount: Number(offer.price_total),
          price_currency: offer.currency,
        }),
      });
      const payload = await response.json().catch(() => ({}));
      if (!response.ok) throw new Error(typeof payload.detail === "string" ? payload.detail : "Não foi possível guardar o alojamento.");
      onAccommodationSaved(payload as SavedAccommodation);
      setSavedOfferIds((current) => current.includes(offer.id) ? current : [...current, offer.id]);
      setMessage(offer.hotel_name + " foi guardado na viagem.");
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Ocorreu um erro ao guardar o alojamento.");
    } finally {
      setSavingId(null);
    }
  }

  return (
    <section className="trip-create-form" aria-labelledby="hotel-search-title">
      <h3 id="hotel-search-title">Pesquisar alojamentos com Amadeus</h3>
      <p className="budget-description">Pesquisa por código IATA da cidade (por exemplo, LIS, OPO ou PAR). Os preços e a disponibilidade são fornecidos pelo Amadeus e podem mudar.</p>
      <form onSubmit={search}>
        <div className="trip-form-grid">
          <label>Código da cidade<input required minLength={3} maxLength={3} value={cityCode} onChange={(event) => setCityCode(event.target.value.toUpperCase())} placeholder="LIS" /></label>
          <label>Check-in<input required type="date" value={checkIn} onChange={(event) => setCheckIn(event.target.value)} /></label>
          <label>Check-out<input required type="date" min={checkIn || undefined} value={checkOut} onChange={(event) => setCheckOut(event.target.value)} /></label>
          <label>Adultos<select value={adults} onChange={(event) => setAdults(event.target.value)}>{Array.from({ length: 9 }, (_, index) => index + 1).map((count) => <option key={count} value={count}>{count}</option>)}</select></label>
          <label>Quartos<select value={roomQuantity} onChange={(event) => setRoomQuantity(event.target.value)}>{Array.from({ length: 8 }, (_, index) => index + 1).map((count) => <option key={count} value={count}>{count}</option>)}</select></label>
          <label>Raio de pesquisa<select value={radius} onChange={(event) => setRadius(event.target.value)}><option value="5">5 km</option><option value="10">10 km</option><option value="20">20 km</option><option value="30">30 km</option><option value="50">50 km</option></select></label>
          <label>Moeda<select value={currency} onChange={(event) => setCurrency(event.target.value)}><option value="EUR">EUR</option><option value="USD">USD</option><option value="GBP">GBP</option></select></label>
        </div>
        <div className="trip-form-actions">
          <button className="primary-button trip-submit" type="submit" disabled={loading}>{loading ? "A pesquisar..." : "Pesquisar alojamentos"}</button>
        </div>
      </form>
      <section className="trip-list" aria-labelledby="hotel-favorites-title">
        <div className="activity-heading">
          <h4 id="hotel-favorites-title">Os meus hotéis favoritos ({favorites.length})</h4>
          <button className="secondary-button" type="button" onClick={() => { setFavoritesLoading(true); void loadFavorites(); }} disabled={favoritesLoading}>
            {favoritesLoading ? "A carregar..." : "Atualizar favoritos"}
          </button>
        </div>
        {favoritesError && <p className="notice" role="alert">{favoritesError}</p>}
        {favoritesLoading && favorites.length === 0 && <p className="budget-description" role="status">A carregar hotéis favoritos...</p>}
        {!favoritesLoading && !favoritesError && favorites.length === 0 && (
          <p className="budget-description">Ainda não guardaste hotéis. Podes adicioná-los a partir dos resultados da pesquisa.</p>
        )}
        {favorites.map((favorite) => (
          <article className="trip-card" key={favorite.id}>
            <div>
              <h4>{favorite.hotel_name}</h4>
              <p>{favorite.location}</p>
            </div>
            <div className="trip-card-actions">
              <button className="secondary-button" type="button" disabled={favoriteActionId !== null} onClick={() => void removeFavorite(favorite)}>
                {favoriteActionId === favorite.hotel_id ? "A remover..." : "Retirar dos favoritos"}
              </button>
            </div>
          </article>
        ))}
      </section>
      {error && <p className="notice" role="alert">{error}</p>}
      {message && <p className="notice" role="status">{message}</p>}
      {results && (
        <div className="trip-list" aria-live="polite">
          <p className="budget-description">{results.results_count === 0 ? "Não foram encontradas ofertas disponíveis para estes critérios." : results.results_count + " ofertas recebidas do fornecedor, ordenadas pela recomendação SKY."} Pesquisa para {adults} adulto(s), {roomQuantity} quarto(s), num raio de {radius} km.</p>
          {results.results_count > 0 && (
            <div className="trip-form-grid" aria-label="Filtrar ofertas por preço">
              <label>Preço mínimo ({resultsCurrency})<input type="number" min="0" step="0.01" inputMode="decimal" value={minimumPrice} onChange={(event) => setMinimumPrice(event.target.value)} placeholder="Sem mínimo" /></label>
              <label>Preço máximo ({resultsCurrency})<input type="number" min="0" step="0.01" inputMode="decimal" value={maximumPrice} onChange={(event) => setMaximumPrice(event.target.value)} placeholder="Sem máximo" /></label>
              <p className="budget-description">{priceRangeInvalid
                ? minimumPriceInvalid || maximumPriceInvalid
                  ? "Os preços têm de ser números válidos iguais ou superiores a zero."
                  : "O preço mínimo não pode ser superior ao preço máximo."
                : `A mostrar ${filteredOffers.length} de ${results.results_count} ofertas.`}</p>
              <div className="trip-form-actions"><button className="secondary-button" type="button" onClick={() => { setMinimumPrice(""); setMaximumPrice(""); }}>Limpar filtros</button></div>
            </div>
          )}
          {results.results_count > 0 && filteredOffers.length === 0 && !priceRangeInvalid && (
            <p className="notice" role="status">Não existem ofertas dentro deste intervalo de preços. Altera os valores ou limpa os filtros.</p>
          )}
          {filteredOffers.map((offer) => (
            <article className="trip-card" key={offer.id}>
              <div>
                <h3>{offer.hotel_name}</h3>
                <p>{offer.location} · {offer.check_in} — {offer.check_out}</p>
                {offer.room_description && <p>{offer.room_description}</p>}
                {offer.board_type && <p>Regime: {offer.board_type}</p>}
                {offer.payment_type && <p>Pagamento: {offer.payment_type}</p>}
                {offer.cancellation_description && <p>Cancelamento: {offer.cancellation_description}</p>}
                {offer.cancellation_deadline && <p>Prazo de cancelamento indicado: {offer.cancellation_deadline}</p>}
                <strong>{formatPrice(offer.price_total, offer.currency)}</strong>
                {offer.price_per_night !== null && offer.nights !== null && <p className="budget-description">{formatPrice(offer.price_per_night, offer.currency)} por noite · {offer.nights} noite(s)</p>}
                {offer.recommendation_score !== null && <p className="budget-description"><strong>Recomendação SKY · {offer.recommendation_score.toLocaleString("pt-PT", { maximumFractionDigits: 1 })}/100</strong>{offer.recommendation_reasons.length > 0 ? " · " + offer.recommendation_reasons.join(" · ") : ""}</p>}
              </div>
              <div className="trip-card-actions">
                <button
                  className="secondary-button"
                  type="button"
                  aria-pressed={favorites.some((favorite) => favorite.hotel_id === offer.hotel_id)}
                  disabled={favoriteActionId !== null}
                  onClick={() => void toggleFavorite(offer)}
                >
                  {favoriteActionId === offer.hotel_id ? "A atualizar..." : favorites.some((favorite) => favorite.hotel_id === offer.hotel_id) ? "Retirar dos favoritos" : "Adicionar aos favoritos"}
                </button>
                <button
                  className="secondary-button"
                  type="button"
                  aria-pressed={comparisonIds.includes(offer.id)}
                  disabled={!comparisonIds.includes(offer.id) && comparisonIds.length >= 3}
                  onClick={() => toggleComparison(offer.id)}
                >
                  {comparisonIds.includes(offer.id) ? "Remover da comparação" : "Comparar"}
                </button>
                {canEdit && <button className="secondary-button" type="button" disabled={savingId !== null || savedOfferIds.includes(offer.id)} onClick={() => void saveOffer(offer)}>{savedOfferIds.includes(offer.id) ? "Já guardado" : savingId === offer.id ? "A guardar..." : "Guardar na viagem"}</button>}
              </div>
            </article>
          ))}
          {comparisonOffers.length > 0 && (
            <section className="trip-card" aria-labelledby="hotel-comparison-title">
              <div>
                <h3 id="hotel-comparison-title">Comparação de alojamentos ({comparisonOffers.length}/3)</h3>
                <p className="budget-description">Comparação para {comparisonNights} noite(s). Os valores são os totais devolvidos pelo fornecedor para os critérios pesquisados.</p>
              </div>
              <div className="trip-form-grid">
                {comparisonOffers.map((offer) => (
                  <article key={offer.id}>
                    <h4>{offer.hotel_name}</h4>
                    <p><strong>Preço total:</strong> {formatPrice(offer.price_total, offer.currency)}</p>
                    <p><strong>Média por noite:</strong> {formatPrice((Number(offer.price_total) / comparisonNights).toFixed(2), offer.currency)}</p>
                    <p><strong>Quarto:</strong> {offer.room_description || "Não indicado pelo fornecedor"}</p>
                    <p><strong>Regime:</strong> {offer.board_type || "Não indicado pelo fornecedor"}</p>
                    <p><strong>Pagamento:</strong> {offer.payment_type || "Não indicado pelo fornecedor"}</p>
                    <p><strong>Cancelamento:</strong> {offer.cancellation_description || "Condições não indicadas pelo fornecedor"}</p>
                    {offer.cancellation_deadline && <p><strong>Prazo indicado:</strong> {offer.cancellation_deadline}</p>}
                    <p><strong>Localização:</strong> {offer.location || "Não indicada"}</p>
                    <button className="secondary-button" type="button" onClick={() => toggleComparison(offer.id)}>Retirar</button>
                  </article>
                ))}
              </div>
            </section>
          )}
        </div>
      )}
    </section>
  );
}
