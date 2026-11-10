"use client";

import Link from "next/link";
import { FormEvent, useEffect, useState } from "react";
import { useRouter } from "next/navigation";

type User = { id: string; email: string; display_name: string | null };
type Trip = {
  id: string;
  name: string;
  destination: string;
  start_date: string | null;
  end_date: string | null;
  notes: string | null;
};

export default function DashboardPage() {
  const router = useRouter();
  const [user, setUser] = useState<User | null>(null);
  const [trips, setTrips] = useState<Trip[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [tripName, setTripName] = useState("");
  const [destination, setDestination] = useState("");
  const [startDate, setStartDate] = useState("");
  const [endDate, setEndDate] = useState("");
  const [notes, setNotes] = useState("");
  const [editingTripId, setEditingTripId] = useState<string | null>(null);

  useEffect(() => {
    let active = true;

    async function loadDashboard() {
      try {
        const [profileResponse, tripsResponse] = await Promise.all([
          fetch("/api/backend/auth/me", { cache: "no-store" }),
          fetch("/api/backend/trips", { cache: "no-store" }),
        ]);

        if (profileResponse.status === 401 || tripsResponse.status === 401) {
          router.replace("/login");
          return;
        }
        if (!profileResponse.ok || !tripsResponse.ok) {
          throw new Error("Não foi possível carregar os dados da conta.");
        }

        const [profile, tripList] = await Promise.all([
          profileResponse.json(),
          tripsResponse.json(),
        ]);
        if (active) {
          setUser(profile);
          setTrips(tripList);
        }
      } catch (cause) {
        if (active) setError(cause instanceof Error ? cause.message : "Ocorreu um erro.");
      } finally {
        if (active) setLoading(false);
      }
    }

    void loadDashboard();
    return () => { active = false; };
  }, [router]);

  async function handleSaveTrip(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    setSaving(true);

    try {
      const response = await fetch(
        editingTripId ? `/api/backend/trips/${editingTripId}` : "/api/backend/trips",
        {
          method: editingTripId ? "PATCH" : "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            name: tripName,
            destination,
            start_date: startDate || null,
            end_date: endDate || null,
            notes: notes || null,
          }),
        },
      );
      const data = await response.json().catch(() => ({}));
      if (!response.ok) {
        setError(data.detail ?? (editingTripId ? "Não foi possível atualizar a viagem." : "Não foi possível criar a viagem."));
        return;
      }

      setTrips((current) => editingTripId
        ? current.map((trip) => trip.id === editingTripId ? data : trip)
        : [data, ...current]);
      setEditingTripId(null);
      setTripName("");
      setDestination("");
      setStartDate("");
      setEndDate("");
      setNotes("");
    } catch {
      setError("Não foi possível contactar o serviço. Tenta novamente.");
    } finally {
      setSaving(false);
    }
  }

  function editTrip(trip: Trip) {
    setEditingTripId(trip.id);
    setTripName(trip.name);
    setDestination(trip.destination);
    setStartDate(trip.start_date ?? "");
    setEndDate(trip.end_date ?? "");
    setNotes(trip.notes ?? "");
    setError("");
    window.scrollTo({ top: 0, behavior: "smooth" });
  }

  function cancelEdit() {
    setEditingTripId(null);
    setTripName("");
    setDestination("");
    setStartDate("");
    setEndDate("");
    setNotes("");
    setError("");
  }

  async function deleteTrip(tripId: string) {
    if (!window.confirm("Tens a certeza de que pretendes eliminar esta viagem?")) return;
    setError("");

    try {
      const response = await fetch(`/api/backend/trips/${tripId}`, { method: "DELETE" });
      if (!response.ok) {
        const data = await response.json().catch(() => ({}));
        setError(data.detail ?? "Não foi possível eliminar a viagem.");
        return;
      }
      setTrips((current) => current.filter((trip) => trip.id !== tripId));
      if (editingTripId === tripId) cancelEdit();
    } catch {
      setError("Não foi possível contactar o serviço. Tenta novamente.");
    }
  }

  async function logout() {
    await fetch("/api/auth/logout", { method: "POST" });
    router.replace("/");
    router.refresh();
  }

  return (
    <main className="dashboard-shell">
      <header className="dashboard-header">
        <Link className="brand" href="/">SKY<span>.</span></Link>
        <button className="text-button" onClick={logout}>Terminar sessão</button>
      </header>
      <section className="dashboard-content">
        <p className="eyebrow">A TUA ÁREA PESSOAL</p>
        <h1>{user?.display_name ? `Olá, ${user.display_name}.` : "As tuas viagens."}</h1>
        <p className="intro dashboard-intro">Organiza os teus planos e acompanha tudo num só lugar.</p>

        <div className="dashboard-stats">
          <article className="stat-card"><span>Viagens guardadas</span><strong>{loading ? "—" : trips.length}</strong></article>
          <article className="stat-card"><span>Conta</span><strong>{loading ? "—" : "Ativa"}</strong></article>
        </div>

        <div className="section-heading"><div><p className="eyebrow">PLANEAMENTO</p><h2>As minhas viagens</h2></div></div>
        {error && <p className="form-error" role="alert">{error}</p>}
        <form className="trip-create-form" onSubmit={handleSaveTrip}>
          <h3>{editingTripId ? "Editar viagem" : "Criar uma viagem"}</h3>
          <div className="trip-form-grid">
            <label>Nome da viagem<input required minLength={2} maxLength={160} value={tripName} onChange={(event) => setTripName(event.target.value)} placeholder="Ex.: Férias de verão" /></label>
            <label>Destino<input required minLength={2} maxLength={160} value={destination} onChange={(event) => setDestination(event.target.value)} placeholder="Ex.: Madeira" /></label>
            <label>Data de partida<input type="date" value={startDate} onChange={(event) => setStartDate(event.target.value)} /></label>
            <label>Data de regresso<input type="date" min={startDate || undefined} value={endDate} onChange={(event) => setEndDate(event.target.value)} /></label>
          </div>
          <label className="notes-field">Notas (opcional)<textarea rows={3} maxLength={10000} value={notes} onChange={(event) => setNotes(event.target.value)} placeholder="O que queres organizar nesta viagem?" /></label>
          <div className="trip-form-actions">
            <button className="primary-button trip-submit" type="submit" disabled={saving || loading}>{saving ? "A guardar..." : editingTripId ? "Guardar alterações" : "Guardar viagem"}</button>
            {editingTripId && <button className="secondary-button" type="button" onClick={cancelEdit} disabled={saving}>Cancelar</button>}
          </div>
        </form>

        {loading && <p className="notice">A carregar a tua área pessoal...</p>}
        {!loading && !error && trips.length === 0 && (
          <div className="empty-state">
            <h3>Ainda não tens viagens.</h3>
            <p>Cria a tua primeira viagem no formulário acima.</p>
          </div>
        )}
        {!loading && trips.length > 0 && (
          <div className="trip-list">
            {trips.map((trip) => (
              <article className="trip-card" key={trip.id}>
                <div><h3>{trip.name}</h3><p>{trip.destination}</p></div>
                <div className="trip-card-actions">
                  <span>{trip.start_date ?? "Data por definir"}{trip.end_date ? ` — ${trip.end_date}` : ""}</span>
                  <div className="trip-action-buttons">
                    <button className="edit-button" type="button" onClick={() => editTrip(trip)}>Editar</button>
                    <button className="delete-button" type="button" onClick={() => deleteTrip(trip.id)}>Eliminar</button>
                  </div>
                </div>
              </article>
            ))}
          </div>
        )}
      </section>
    </main>
  );
}
