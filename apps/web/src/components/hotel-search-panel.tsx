"use client";

import { FormEvent, useState } from "react";

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

type SearchResponse = { results_count: number; offers: HotelOffer[] };

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
  const [currency, setCurrency] = useState("EUR");
  const [loading, setLoading] = useState(false);
  const [savingId, setSavingId] = useState<string | null>(null);
  const [results, setResults] = useState<SearchResponse | null>(null);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");

  async function search(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setLoading(true);
    setError("");
    setMessage("");
    setResults(null);
    const params = new URLSearchParams({
      city_code: cityCode.trim().toUpperCase(),
      check_in: checkIn,
      check_out: checkOut,
      adults,
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
          <label>Moeda<select value={currency} onChange={(event) => setCurrency(event.target.value)}><option value="EUR">EUR</option><option value="USD">USD</option><option value="GBP">GBP</option></select></label>
        </div>
        <div className="trip-form-actions">
          <button className="primary-button trip-submit" type="submit" disabled={loading}>{loading ? "A pesquisar..." : "Pesquisar alojamentos"}</button>
        </div>
      </form>
      {error && <p className="notice" role="alert">{error}</p>}
      {message && <p className="notice" role="status">{message}</p>}
      {results && (
        <div className="trip-list" aria-live="polite">
          <p className="budget-description">{results.results_count === 0 ? "Não foram encontradas ofertas disponíveis para estes critérios." : results.results_count + " ofertas disponíveis, ordenadas por preço."}</p>
          {results.offers.map((offer) => (
            <article className="trip-card" key={offer.id}>
              <div>
                <h3>{offer.hotel_name}</h3>
                <p>{offer.location} · {offer.check_in} — {offer.check_out}</p>
                {offer.room_description && <p>{offer.room_description}</p>}
                {offer.board_type && <p>Regime: {offer.board_type}</p>}
                <strong>{formatPrice(offer.price_total, offer.currency)}</strong>
              </div>
              {canEdit && <div className="trip-card-actions"><button className="secondary-button" type="button" disabled={savingId !== null} onClick={() => void saveOffer(offer)}>{savingId === offer.id ? "A guardar..." : "Guardar na viagem"}</button></div>}
            </article>
          ))}
        </div>
      )}
    </section>
  );
}
