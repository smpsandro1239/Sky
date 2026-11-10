"use client";

import Link from "next/link";
import { FormEvent, useCallback, useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";

type Trip = {
  id: string;
  name: string;
  destination: string;
  start_date: string | null;
  end_date: string | null;
  notes: string | null;
};
type Flight = {
  id: string;
  provider: string | null;
  origin: string;
  destination: string;
  departure_at: string;
  arrival_at: string | null;
  price_amount: string | null;
  price_currency: string;
};
type Accommodation = {
  id: string;
  provider: string | null;
  name: string;
  location: string;
  check_in: string;
  check_out: string;
  price_amount: string | null;
  price_currency: string;
};
type FlightForm = {
  provider: string;
  origin: string;
  destination: string;
  departure_at: string;
  arrival_at: string;
  price_amount: string;
  price_currency: string;
};
type AccommodationForm = {
  provider: string;
  name: string;
  location: string;
  check_in: string;
  check_out: string;
  price_amount: string;
  price_currency: string;
};

const emptyFlight: FlightForm = {
  provider: "", origin: "", destination: "", departure_at: "", arrival_at: "",
  price_amount: "", price_currency: "EUR",
};
const emptyAccommodation: AccommodationForm = {
  provider: "", name: "", location: "", check_in: "", check_out: "",
  price_amount: "", price_currency: "EUR",
};

function dateTimeInput(value: string | null) {
  if (!value) return "";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "";
  const localDate = new Date(date.getTime() - date.getTimezoneOffset() * 60_000);
  return localDate.toISOString().slice(0, 16);
}

export default function TripDetailPage() {
  const params = useParams<{ tripId: string }>();
  const tripId = params.tripId;
  const router = useRouter();
  const [trip, setTrip] = useState<Trip | null>(null);
  const [flights, setFlights] = useState<Flight[]>([]);
  const [accommodations, setAccommodations] = useState<Accommodation[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [flightForm, setFlightForm] = useState<FlightForm>(emptyFlight);
  const [accommodationForm, setAccommodationForm] = useState<AccommodationForm>(emptyAccommodation);
  const [editingFlightId, setEditingFlightId] = useState<string | null>(null);
  const [editingAccommodationId, setEditingAccommodationId] = useState<string | null>(null);

  const loadTrip = useCallback(async () => {
    setError("");
    try {
      const [tripResponse, flightResponse, accommodationResponse] = await Promise.all([
        fetch(`/api/backend/trips/${tripId}`, { cache: "no-store" }),
        fetch(`/api/backend/trips/${tripId}/flights`, { cache: "no-store" }),
        fetch(`/api/backend/trips/${tripId}/accommodations`, { cache: "no-store" }),
      ]);
      if ([tripResponse, flightResponse, accommodationResponse].some((response) => response.status === 401)) {
        router.replace("/login");
        return;
      }
      if (!tripResponse.ok || !flightResponse.ok || !accommodationResponse.ok) {
        throw new Error("Não foi possível carregar os dados desta viagem.");
      }
      const [tripData, flightData, accommodationData] = await Promise.all([
        tripResponse.json(), flightResponse.json(), accommodationResponse.json(),
      ]);
      setTrip(tripData);
      setFlights(flightData);
      setAccommodations(accommodationData);
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Ocorreu um erro ao carregar a viagem.");
    } finally {
      setLoading(false);
    }
  }, [router, tripId]);

  useEffect(() => { void loadTrip(); }, [loadTrip]);

  function resetFlight() {
    setFlightForm(emptyFlight);
    setEditingFlightId(null);
  }
  function resetAccommodation() {
    setAccommodationForm(emptyAccommodation);
    setEditingAccommodationId(null);
  }

  async function saveFlight(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSaving(true);
    setError("");
    const payload = {
      provider: flightForm.provider.trim() || null,
      origin: flightForm.origin.trim().toUpperCase(),
      destination: flightForm.destination.trim().toUpperCase(),
      departure_at: new Date(flightForm.departure_at).toISOString(),
      arrival_at: flightForm.arrival_at ? new Date(flightForm.arrival_at).toISOString() : null,
      price_amount: flightForm.price_amount ? Number(flightForm.price_amount) : null,
      price_currency: flightForm.price_currency.trim().toUpperCase(),
    };
    try {
      const response = await fetch(
        editingFlightId
          ? `/api/backend/trips/${tripId}/flights/${editingFlightId}`
          : `/api/backend/trips/${tripId}/flights`,
        {
          method: editingFlightId ? "PATCH" : "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload),
        },
      );
      const data = await response.json().catch(() => ({}));
      if (!response.ok) {
        setError(typeof data.detail === "string" ? data.detail : "Não foi possível guardar o voo.");
        return;
      }
      setFlights((current) => editingFlightId
        ? current.map((flight) => flight.id === editingFlightId ? data : flight)
        : [...current, data].sort((a, b) => a.departure_at.localeCompare(b.departure_at)));
      resetFlight();
    } catch {
      setError("Não foi possível contactar a API. Verifica a ligação e tenta novamente.");
    } finally {
      setSaving(false);
    }
  }

  async function saveAccommodation(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSaving(true);
    setError("");
    const payload = {
      provider: accommodationForm.provider.trim() || null,
      name: accommodationForm.name.trim(),
      location: accommodationForm.location.trim(),
      check_in: accommodationForm.check_in,
      check_out: accommodationForm.check_out,
      price_amount: accommodationForm.price_amount ? Number(accommodationForm.price_amount) : null,
      price_currency: accommodationForm.price_currency.trim().toUpperCase(),
    };
    try {
      const response = await fetch(
        editingAccommodationId
          ? `/api/backend/trips/${tripId}/accommodations/${editingAccommodationId}`
          : `/api/backend/trips/${tripId}/accommodations`,
        {
          method: editingAccommodationId ? "PATCH" : "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload),
        },
      );
      const data = await response.json().catch(() => ({}));
      if (!response.ok) {
        setError(typeof data.detail === "string" ? data.detail : "Não foi possível guardar o alojamento.");
        return;
      }
      setAccommodations((current) => editingAccommodationId
        ? current.map((item) => item.id === editingAccommodationId ? data : item)
        : [...current, data].sort((a, b) => a.check_in.localeCompare(b.check_in)));
      resetAccommodation();
    } catch {
      setError("Não foi possível contactar a API. Verifica a ligação e tenta novamente.");
    } finally {
      setSaving(false);
    }
  }

  function editFlight(flight: Flight) {
    setEditingFlightId(flight.id);
    setFlightForm({
      provider: flight.provider ?? "",
      origin: flight.origin,
      destination: flight.destination,
      departure_at: dateTimeInput(flight.departure_at),
      arrival_at: dateTimeInput(flight.arrival_at),
      price_amount: flight.price_amount ?? "",
      price_currency: flight.price_currency,
    });
  }

  function editAccommodation(item: Accommodation) {
    setEditingAccommodationId(item.id);
    setAccommodationForm({
      provider: item.provider ?? "",
      name: item.name,
      location: item.location,
      check_in: item.check_in,
      check_out: item.check_out,
      price_amount: item.price_amount ?? "",
      price_currency: item.price_currency,
    });
  }

  async function deleteItem(kind: "flights" | "accommodations", id: string) {
    const label = kind === "flights" ? "voo" : "alojamento";
    if (!window.confirm(`Queres mesmo eliminar este ${label}?`)) return;
    setError("");
    try {
      const response = await fetch(`/api/backend/trips/${tripId}/${kind}/${id}`, { method: "DELETE" });
      if (!response.ok) {
        const data = await response.json().catch(() => ({}));
        setError(typeof data.detail === "string" ? data.detail : `Não foi possível eliminar o ${label}.`);
        return;
      }
      if (kind === "flights") {
        setFlights((current) => current.filter((item) => item.id !== id));
        if (editingFlightId === id) resetFlight();
      } else {
        setAccommodations((current) => current.filter((item) => item.id !== id));
        if (editingAccommodationId === id) resetAccommodation();
      }
    } catch {
      setError("Não foi possível contactar a API. Tenta novamente.");
    }
  }

  if (loading) return <main className="dashboard-shell"><p className="notice">A carregar a viagem...</p></main>;

  return (
    <main className="dashboard-shell">
      <header className="dashboard-header">
        <Link className="brand" href="/">SKY<span>.</span></Link>
        <Link className="text-button" href="/dashboard">As minhas viagens</Link>
      </header>
      <section className="dashboard-content">
        <Link className="back-link" href="/dashboard">← Voltar às viagens</Link>
        {error && <p className="form-error" role="alert">{error}</p>}
        {trip ? (
          <>
            <p className="eyebrow">PLANEAMENTO DA VIAGEM</p>
            <h1>{trip.name}</h1>
            <p className="intro dashboard-intro">{trip.destination}{trip.start_date ? ` · ${trip.start_date}` : ""}{trip.end_date ? ` — ${trip.end_date}` : ""}</p>
            {trip.notes && <p className="trip-notes">{trip.notes}</p>}

            <div className="section-heading"><div><p className="eyebrow">TRANSPORTE</p><h2>Voos</h2></div></div>
            <form className="trip-create-form" onSubmit={saveFlight}>
              <h3>{editingFlightId ? "Editar voo" : "Adicionar voo"}</h3>
              <div className="trip-form-grid">
                <label>Companhia / fornecedor<input maxLength={80} value={flightForm.provider} onChange={(e) => setFlightForm({ ...flightForm, provider: e.target.value })} placeholder="Opcional" /></label>
                <label>Origem (IATA)<input required minLength={3} maxLength={3} value={flightForm.origin} onChange={(e) => setFlightForm({ ...flightForm, origin: e.target.value.toUpperCase() })} placeholder="OPO" /></label>
                <label>Destino (IATA)<input required minLength={3} maxLength={3} value={flightForm.destination} onChange={(e) => setFlightForm({ ...flightForm, destination: e.target.value.toUpperCase() })} placeholder="LIS" /></label>
                <label>Partida<input required type="datetime-local" value={flightForm.departure_at} onChange={(e) => setFlightForm({ ...flightForm, departure_at: e.target.value })} /></label>
                <label>Chegada<input type="datetime-local" min={flightForm.departure_at || undefined} value={flightForm.arrival_at} onChange={(e) => setFlightForm({ ...flightForm, arrival_at: e.target.value })} /></label>
                <label>Preço<input type="number" min="0.01" step="0.01" value={flightForm.price_amount} onChange={(e) => setFlightForm({ ...flightForm, price_amount: e.target.value })} placeholder="Opcional" /></label>
                <label>Moeda<input required minLength={3} maxLength={3} value={flightForm.price_currency} onChange={(e) => setFlightForm({ ...flightForm, price_currency: e.target.value.toUpperCase() })} /></label>
              </div>
              <div className="trip-form-actions">
                <button className="primary-button trip-submit" type="submit" disabled={saving}>{saving ? "A guardar..." : editingFlightId ? "Guardar alterações" : "Adicionar voo"}</button>
                {editingFlightId && <button className="secondary-button" type="button" onClick={resetFlight}>Cancelar</button>}
              </div>
            </form>
            <div className="trip-list">
              {flights.length === 0 ? <div className="empty-state"><p>Ainda não existem voos associados a esta viagem.</p></div> : flights.map((flight) => (
                <article className="trip-card" key={flight.id}>
                  <div><h3>{flight.origin} → {flight.destination}</h3><p>{flight.provider || "Companhia por definir"} · {new Date(flight.departure_at).toLocaleString("pt-PT")}</p></div>
                  <div className="trip-card-actions"><span>{flight.price_amount ? `${flight.price_amount} ${flight.price_currency}` : "Preço por definir"}</span><div className="trip-action-buttons"><button className="edit-button" type="button" onClick={() => editFlight(flight)}>Editar</button><button className="delete-button" type="button" onClick={() => void deleteItem("flights", flight.id)}>Eliminar</button></div></div>
                </article>
              ))}
            </div>

            <div className="section-heading"><div><p className="eyebrow">ESTADIA</p><h2>Alojamentos</h2></div></div>
            <form className="trip-create-form" onSubmit={saveAccommodation}>
              <h3>{editingAccommodationId ? "Editar alojamento" : "Adicionar alojamento"}</h3>
              <div className="trip-form-grid">
                <label>Nome<input required minLength={2} maxLength={180} value={accommodationForm.name} onChange={(e) => setAccommodationForm({ ...accommodationForm, name: e.target.value })} placeholder="Nome do hotel ou alojamento" /></label>
                <label>Localização<input required minLength={2} maxLength={180} value={accommodationForm.location} onChange={(e) => setAccommodationForm({ ...accommodationForm, location: e.target.value })} placeholder="Cidade ou morada" /></label>
                <label>Fornecedor<input maxLength={80} value={accommodationForm.provider} onChange={(e) => setAccommodationForm({ ...accommodationForm, provider: e.target.value })} placeholder="Opcional" /></label>
                <label>Check-in<input required type="date" value={accommodationForm.check_in} onChange={(e) => setAccommodationForm({ ...accommodationForm, check_in: e.target.value })} /></label>
                <label>Check-out<input required type="date" min={accommodationForm.check_in || undefined} value={accommodationForm.check_out} onChange={(e) => setAccommodationForm({ ...accommodationForm, check_out: e.target.value })} /></label>
                <label>Preço total<input type="number" min="0.01" step="0.01" value={accommodationForm.price_amount} onChange={(e) => setAccommodationForm({ ...accommodationForm, price_amount: e.target.value })} placeholder="Opcional" /></label>
                <label>Moeda<input required minLength={3} maxLength={3} value={accommodationForm.price_currency} onChange={(e) => setAccommodationForm({ ...accommodationForm, price_currency: e.target.value.toUpperCase() })} /></label>
              </div>
              <div className="trip-form-actions">
                <button className="primary-button trip-submit" type="submit" disabled={saving}>{saving ? "A guardar..." : editingAccommodationId ? "Guardar alterações" : "Adicionar alojamento"}</button>
                {editingAccommodationId && <button className="secondary-button" type="button" onClick={resetAccommodation}>Cancelar</button>}
              </div>
            </form>
            <div className="trip-list">
              {accommodations.length === 0 ? <div className="empty-state"><p>Ainda não existem alojamentos associados a esta viagem.</p></div> : accommodations.map((item) => (
                <article className="trip-card" key={item.id}>
                  <div><h3>{item.name}</h3><p>{item.location} · {item.check_in} — {item.check_out}</p></div>
                  <div className="trip-card-actions"><span>{item.price_amount ? `${item.price_amount} ${item.price_currency}` : "Preço por definir"}</span><div className="trip-action-buttons"><button className="edit-button" type="button" onClick={() => editAccommodation(item)}>Editar</button><button className="delete-button" type="button" onClick={() => void deleteItem("accommodations", item.id)}>Eliminar</button></div></div>
                </article>
              ))}
            </div>
          </>
        ) : <div className="empty-state"><h2>Viagem não encontrada</h2><p>Não foi possível encontrar esta viagem ou não tens acesso a ela.</p><Link href="/dashboard">Voltar ao dashboard</Link></div>}
      </section>
    </main>
  );
}
