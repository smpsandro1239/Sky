"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
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
  const [error, setError] = useState("");

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
        {loading && <p className="notice">A carregar a tua área pessoal...</p>}
        {error && <p className="form-error" role="alert">{error}</p>}
        {!loading && !error && trips.length === 0 && (
          <div className="empty-state">
            <h3>Ainda não tens viagens.</h3>
            <p>O próximo passo será criar a tua primeira viagem diretamente nesta área.</p>
            <span className="coming-soon">Criação de viagens — próxima entrega</span>
          </div>
        )}
        {!loading && trips.length > 0 && (
          <div className="trip-list">
            {trips.map((trip) => (
              <article className="trip-card" key={trip.id}>
                <div><h3>{trip.name}</h3><p>{trip.destination}</p></div>
                <span>{trip.start_date ?? "Data por definir"}{trip.end_date ? ` — ${trip.end_date}` : ""}</span>
              </article>
            ))}
          </div>
        )}
      </section>
    </main>
  );
}
