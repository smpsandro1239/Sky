"use client";

import { FormEvent, useState } from "react";
import PriceHistoryPanel from "./price-history-panel";

type FlightSegment = {
  carrier: string;
  flight_number: string;
  origin: string;
  destination: string;
  departure_at: string;
  arrival_at: string;
};

type FlightOffer = {
  id: string;
  price_tracking_key: string;
  provider: "amadeus";
  price_total: string;
  currency: string;
  number_of_stops: number;
  duration_minutes: number | null;
  recommendation_score: number | null;
  recommendation_reasons: string[];
  itineraries: FlightSegment[][];
};

type SavedFlight = {
  id: string;
  provider: string | null;
  origin: string;
  destination: string;
  departure_at: string;
  arrival_at: string | null;
  price_amount: string | null;
  price_currency: string;
};

type FlightSearchResponse = {
  provider: "amadeus";
  results_count: number;
  search_key: string;
  offers: FlightOffer[];
};

function formatDateTime(value: string) {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleString("pt-PT", {
    dateStyle: "medium",
    timeStyle: "short",
  });
}

function formatPrice(amount: string, currency: string) {
  const value = Number(amount);
  if (!Number.isFinite(value)) return amount + " " + currency;
  return new Intl.NumberFormat("pt-PT", {
    style: "currency",
    currency,
  }).format(value);
}

export default function FlightSearchPanel({
  tripId,
  canEdit,
  onFlightsSaved,
}: {
  tripId: string;
  canEdit: boolean;
  onFlightsSaved: (flights: SavedFlight[]) => void;
}) {
  const [origin, setOrigin] = useState("OPO");
  const [destination, setDestination] = useState("");
  const [departureDate, setDepartureDate] = useState("");
  const [returnDate, setReturnDate] = useState("");
  const [adults, setAdults] = useState("1");
  const [currency, setCurrency] = useState("EUR");
  const [nonStop, setNonStop] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [results, setResults] = useState<FlightSearchResponse | null>(null);
  const [savingOfferId, setSavingOfferId] = useState<string | null>(null);
  const [saveMessage, setSaveMessage] = useState("");

  async function saveOffer(offer: FlightOffer) {
    if (!canEdit || savingOfferId) return;
    const segments = offer.itineraries.flat();
    if (segments.length === 0) {
      setSaveMessage("Esta oferta não contém segmentos de voo para guardar.");
      return;
    }

    setSavingOfferId(offer.id);
    setSaveMessage("");
    const saved: SavedFlight[] = [];

    try {
      for (const [index, segment] of segments.entries()) {
        const response = await fetch("/api/backend/trips/" + tripId + "/flights", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            provider: "Amadeus · " + segment.carrier + " " + segment.flight_number,
            origin: segment.origin,
            destination: segment.destination,
            departure_at: segment.departure_at,
            arrival_at: segment.arrival_at,
            price_amount: index === 0 ? Number(offer.price_total) : null,
            price_currency: offer.currency,
          }),
        });
        const data = await response.json().catch(() => ({}));
        if (!response.ok) {
          throw new Error(typeof data.detail === "string" ? data.detail : "Não foi possível guardar todos os segmentos da oferta.");
        }
        saved.push(data as SavedFlight);
      }

      onFlightsSaved(saved);
      setSaveMessage(
        saved.length === 1
          ? "Voo guardado na viagem."
          : saved.length + " segmentos guardados na viagem. O preço total foi registado apenas no primeiro segmento para evitar duplicação.",
      );
    } catch (cause) {
      if (saved.length > 0) onFlightsSaved(saved);
      setSaveMessage(
        (cause instanceof Error ? cause.message : "Ocorreu um erro ao guardar a oferta.") +
        (saved.length > 0 ? " Foram guardados " + saved.length + " segmento(s); os restantes não foram guardados." : ""),
      );
    } finally {
      setSavingOfferId(null);
    }
  }

  async function search(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setLoading(true);
    setError("");
    setResults(null);

    const query = new URLSearchParams({
      origin: origin.trim().toUpperCase(),
      destination: destination.trim().toUpperCase(),
      departure_date: departureDate,
      adults,
      currency: currency.trim().toUpperCase(),
      non_stop: String(nonStop),
      max_results: "20",
    });
    if (returnDate) query.set("return_date", returnDate);

    try {
      const response = await fetch("/api/backend/flights/search?" + query.toString(), {
        cache: "no-store",
      });
      const data = await response.json().catch(() => ({})) as FlightSearchResponse & { detail?: unknown };
      if (!response.ok) {
        const detail = typeof data.detail === "string"
          ? data.detail
          : response.status === 503
            ? "A pesquisa Amadeus ainda não está configurada no servidor."
            : "Não foi possível pesquisar voos. Confirma os dados e tenta novamente.";
        throw new Error(detail);
      }
      setResults(data);
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Ocorreu um erro ao pesquisar voos.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <section className="activity-panel" aria-labelledby="flight-search-title">
      <div className="activity-heading">
        <div>
          <p className="eyebrow">PESQUISA EXTERNA · AMADEUS</p>
          <h2 id="flight-search-title">Encontrar voos</h2>
          <p className="budget-description">
            Compara ofertas disponíveis. Esta pesquisa não reserva nem emite bilhetes.
          </p>
        </div>
      </div>

      <form className="trip-create-form" onSubmit={search}>
        <div className="trip-form-grid">
          <label>
            Origem (IATA)
            <input required minLength={3} maxLength={3} pattern="[A-Za-z]{3}" value={origin}
              onChange={(event) => setOrigin(event.target.value.toUpperCase())} placeholder="OPO" />
          </label>
          <label>
            Destino (IATA)
            <input required minLength={3} maxLength={3} pattern="[A-Za-z]{3}" value={destination}
              onChange={(event) => setDestination(event.target.value.toUpperCase())} placeholder="LHR" />
          </label>
          <label>
            Ida
            <input required type="date" min={new Date().toISOString().slice(0, 10)} value={departureDate}
              onChange={(event) => setDepartureDate(event.target.value)} />
          </label>
          <label>
            Regresso (opcional)
            <input type="date" min={departureDate || new Date().toISOString().slice(0, 10)} value={returnDate}
              onChange={(event) => setReturnDate(event.target.value)} />
          </label>
          <label>
            Adultos
            <select value={adults} onChange={(event) => setAdults(event.target.value)}>
              {Array.from({ length: 9 }, (_, index) => index + 1).map((count) => (
                <option key={count} value={count}>{count}</option>
              ))}
            </select>
          </label>
          <label>
            Moeda
            <select value={currency} onChange={(event) => setCurrency(event.target.value)}>
              <option value="EUR">EUR</option>
              <option value="USD">USD</option>
              <option value="GBP">GBP</option>
            </select>
          </label>
          <label className="checkbox-label">
            <input type="checkbox" checked={nonStop} onChange={(event) => setNonStop(event.target.checked)} />
            Apenas voos diretos
          </label>
        </div>
        <div className="trip-form-actions">
          <button className="primary-button trip-submit" type="submit" disabled={loading}>
            {loading ? "A pesquisar..." : "Pesquisar voos"}
          </button>
        </div>
      </form>

      {error && <p className="notice" role="alert">{error}</p>}
      {results && (
        <div className="trip-list" aria-live="polite">
          <p className="budget-description">
            {results.results_count === 0
              ? "Não foram encontradas ofertas para estes critérios."
              : results.results_count + " ofertas encontradas · ordenadas pela recomendação SKY"}
          </p>
          {results.offers.map((offer) => (
            <article className="trip-card" key={offer.id}>
              <div>
                <h3>{formatPrice(offer.price_total, offer.currency)}</h3>
                {offer.recommendation_score !== null && <p className="budget-description"><strong>Recomendação SKY · {offer.recommendation_score.toLocaleString("pt-PT", { maximumFractionDigits: 1 })}/100</strong>{offer.recommendation_reasons.length > 0 ? " · " + offer.recommendation_reasons.join(" · ") : ""}</p>}
                <p>{offer.number_of_stops === 0 ? "Direto" : offer.number_of_stops + " escala(s)"} · {offer.duration_minutes !== null ? Math.floor(offer.duration_minutes / 60) + " h " + (offer.duration_minutes % 60) + " min" : "Duração indisponível"} · Amadeus</p>
                {canEdit && (
                  <button className="secondary-button" type="button" disabled={savingOfferId !== null} onClick={() => void saveOffer(offer)}>
                    {savingOfferId === offer.id ? "A guardar..." : "Guardar na viagem"}
                  </button>
                )}
                {offer.itineraries.map((itinerary, itineraryIndex) => (
                  <div key={itineraryIndex}>
                    <strong>{itineraryIndex === 0 ? "Ida" : "Regresso"}</strong>
                    {itinerary.map((segment, segmentIndex) => (
                      <p key={segmentIndex}>
                        {segment.origin} → {segment.destination} · {segment.carrier} {segment.flight_number}
                        <br />
                        {formatDateTime(segment.departure_at)} — {formatDateTime(segment.arrival_at)}
                      </p>
                    ))}
                  </div>
                ))}
              </div>
            </article>
          ))}
          {results.offers.length > 0 && (
            <PriceHistoryPanel
              key={results.search_key}
              searchType="flight"
              searchKey={results.search_key}
              items={results.offers.map((offer) => ({
                key: offer.price_tracking_key,
                label: offer.itineraries[0]?.map((segment) => segment.origin + "–" + segment.destination).join(" / ") || offer.id,
              }))}
            />
          )}
          {saveMessage && <p className="notice" role="status">{saveMessage}</p>}
        </div>
      )}
      {saveMessage && !results && <p className="notice" role="status">{saveMessage}</p>}
      <p className="budget-description">
        Os preços e a disponibilidade são indicativos e podem mudar no fornecedor.
      </p>
    </section>
  );
}
