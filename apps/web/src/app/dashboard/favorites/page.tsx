"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";

type HotelFavorite = {
  id: string;
  provider: string;
  hotel_id: string;
  hotel_name: string;
  location: string;
  created_at: string;
};

type TripOption = {
  id: string;
  name: string;
  destination: string;
  role: "owner" | "editor" | "viewer";
};

async function fetchHotelFavorites(): Promise<HotelFavorite[]> {
  const response = await fetch("/api/backend/hotels/favorites", { cache: "no-store" });
  const payload = await response.json().catch(() => null);
  if (response.status === 401) throw new Error("SESSION_EXPIRED");
  if (!response.ok) {
    throw new Error(payload && typeof payload.detail === "string" ? payload.detail : "Não foi possível carregar os hotéis favoritos.");
  }
  if (!Array.isArray(payload) || !payload.every((item) =>
    item && typeof item.id === "string" && typeof item.hotel_id === "string"
    && typeof item.hotel_name === "string" && typeof item.location === "string"
  )) {
    throw new Error("A resposta dos favoritos tem um formato inválido.");
  }
  return payload as HotelFavorite[];
}

export default function HotelFavoritesPage() {
  const router = useRouter();
  const [favorites, setFavorites] = useState<HotelFavorite[]>([]);
  const [search, setSearch] = useState("");
  const [sort, setSort] = useState<"name" | "newest">("name");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [removingId, setRemovingId] = useState<string | null>(null);
  const [notice, setNotice] = useState("");
  const [trips, setTrips] = useState<TripOption[]>([]);
  const [tripsLoading, setTripsLoading] = useState(true);
  const [selectedTripId, setSelectedTripId] = useState("");
  const [stayCheckIn, setStayCheckIn] = useState("");
  const [stayCheckOut, setStayCheckOut] = useState("");
  const [stayPrice, setStayPrice] = useState("");
  const [stayCurrency, setStayCurrency] = useState("EUR");
  const [addingToTripId, setAddingToTripId] = useState<string | null>(null);

  async function loadFavorites() {
    setLoading(true);
    setError("");
    try {
      setFavorites(await fetchHotelFavorites());
    } catch (cause) {
      if (cause instanceof Error && cause.message === "SESSION_EXPIRED") {
        router.replace("/login");
        return;
      }
      setError(cause instanceof Error ? cause.message : "Ocorreu um erro ao carregar os favoritos.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    let active = true;
    fetchHotelFavorites()
      .then((items) => {
        if (active) {
          setFavorites(items);
          setError("");
        }
      })
      .catch((cause: unknown) => {
        if (!active) return;
        if (cause instanceof Error && cause.message === "SESSION_EXPIRED") {
          router.replace("/login");
          return;
        }
        setError(cause instanceof Error ? cause.message : "Ocorreu um erro ao carregar os favoritos.");
      })
      .finally(() => {
        if (active) setLoading(false);
      });
    return () => { active = false; };
  }, [router]);

  useEffect(() => {
    let active = true;
    fetch("/api/backend/trips", { cache: "no-store" })
      .then(async (response) => {
        const payload = await response.json().catch(() => null);
        if (response.status === 401) throw new Error("SESSION_EXPIRED");
        if (!response.ok || !Array.isArray(payload)) {
          throw new Error("Não foi possível carregar as viagens.");
        }
        return payload as TripOption[];
      })
      .then((items) => {
        if (!active) return;
        const editableTrips = items.filter((trip) => trip.role === "owner" || trip.role === "editor");
        setTrips(editableTrips);
        setSelectedTripId((current) => current || editableTrips[0]?.id || "");
      })
      .catch((cause: unknown) => {
        if (!active) return;
        if (cause instanceof Error && cause.message === "SESSION_EXPIRED") {
          router.replace("/login");
          return;
        }
        setError(cause instanceof Error ? cause.message : "Não foi possível carregar as viagens.");
      })
      .finally(() => {
        if (active) setTripsLoading(false);
      });
    return () => { active = false; };
  }, [router]);

  const visibleFavorites = useMemo(() => {
    const normalizeSearchText = (value: string) => value
      .normalize("NFD")
      .replace(/[\u0300-\u036f]/g, "")
      .toLocaleLowerCase("pt-PT")
      .trim();
    const term = normalizeSearchText(search);
    return [...favorites]
      .filter((favorite) => !term
        || normalizeSearchText(favorite.hotel_name).includes(term)
        || normalizeSearchText(favorite.location).includes(term))
      .sort((first, second) => sort === "name"
        ? first.hotel_name.localeCompare(second.hotel_name, "pt-PT")
        : second.created_at.localeCompare(first.created_at));
  }, [favorites, search, sort]);

  async function addFavoriteToTrip(favorite: HotelFavorite) {
    if (!selectedTripId || !stayCheckIn || !stayCheckOut || stayCheckOut <= stayCheckIn
      || (stayPrice !== "" && (!Number.isFinite(Number(stayPrice)) || Number(stayPrice) <= 0))) {
      setError("Seleciona uma viagem, datas válidas e, se indicares um preço, um valor superior a zero.");
      return;
    }
    setAddingToTripId(favorite.id);
    setError("");
    setNotice("");
    try {
      const response = await fetch("/api/backend/trips/" + selectedTripId + "/accommodations", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          provider: favorite.provider,
          name: favorite.hotel_name,
          location: favorite.location,
          check_in: stayCheckIn,
          check_out: stayCheckOut,
          price_amount: stayPrice === "" ? null : Number(stayPrice),
          price_currency: stayCurrency,
        }),
      });
      if (response.status === 401) {
        router.replace("/login");
        return;
      }
      const payload = await response.json().catch(() => ({}));
      if (!response.ok) {
        throw new Error(typeof payload.detail === "string" ? payload.detail : "Não foi possível adicionar o hotel à viagem.");
      }
      const selectedTrip = trips.find((trip) => trip.id === selectedTripId);
      setNotice(favorite.hotel_name + " foi adicionado à viagem " + (selectedTrip?.name ?? "") + ". O preço não foi definido.");
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Ocorreu um erro ao adicionar o hotel à viagem.");
    } finally {
      setAddingToTripId(null);
    }
  }

  async function removeFavorite(favorite: HotelFavorite) {
    setRemovingId(favorite.id);
    setError("");
    setNotice("");
    try {
      const response = await fetch("/api/backend/hotels/favorites/" + favorite.id, { method: "DELETE" });
      if (response.status === 401) {
        router.replace("/login");
        return;
      }
      if (!response.ok) {
        const payload = await response.json().catch(() => ({}));
        throw new Error(typeof payload.detail === "string" ? payload.detail : "Não foi possível remover este favorito.");
      }
      setFavorites((current) => current.filter((item) => item.id !== favorite.id));
      setNotice(favorite.hotel_name + " foi retirado dos favoritos.");
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Ocorreu um erro ao remover o favorito.");
    } finally {
      setRemovingId(null);
    }
  }

  return (
    <main className="dashboard-shell">
      <header className="dashboard-header">
        <Link className="brand" href="/">SKY<span>.</span></Link>
        <nav aria-label="Navegação da conta">
          <Link className="text-button" href="/dashboard">As minhas viagens</Link>
        </nav>
      </header>
      <section className="dashboard-content">
        <p className="eyebrow">A TUA ÁREA PESSOAL</p>
        <h1>Hotéis favoritos.</h1>
        <p className="intro dashboard-intro">Guarda alojamentos interessantes e encontra-os novamente sem teres de repetir a pesquisa.</p>

        <div className="dashboard-stats">
          <article className="stat-card"><span>Hotéis guardados</span><strong>{loading ? "—" : favorites.length}</strong></article>
          <article className="stat-card"><span>Resultados filtrados</span><strong>{loading ? "—" : visibleFavorites.length}</strong></article>
        </div>

        <div className="section-heading">
          <div><p className="eyebrow">A TUA COLEÇÃO</p><h2>Os meus hotéis</h2></div>
          <Link className="edit-button" href="/dashboard">Voltar ao dashboard</Link>
        </div>

        <section className="trip-create-form" aria-label="Adicionar favoritos a uma viagem">
          <h3>Reutilizar um hotel numa viagem</h3>
          <p className="budget-description">Escolhe uma viagem e as datas da estadia. Podes indicar o preço que confirmaste externamente; o favorito não guarda tarifas nem disponibilidade atualizadas.</p>
          <div className="trip-form-grid">
            <label>Viagem
              <select value={selectedTripId} onChange={(event) => setSelectedTripId(event.target.value)} disabled={tripsLoading || trips.length === 0}>
                {trips.length === 0 && <option value="">{tripsLoading ? "A carregar viagens..." : "Não tens viagens editáveis"}</option>}
                {trips.map((trip) => <option key={trip.id} value={trip.id}>{trip.name} — {trip.destination}</option>)}
              </select>
            </label>
            <label>Check-in<input type="date" value={stayCheckIn} onChange={(event) => setStayCheckIn(event.target.value)} /></label>
            <label>Check-out<input type="date" min={stayCheckIn || undefined} value={stayCheckOut} onChange={(event) => setStayCheckOut(event.target.value)} /></label>
            <label>Preço total (opcional)<input type="number" min="0.01" step="0.01" value={stayPrice} onChange={(event) => setStayPrice(event.target.value)} placeholder="Por definir" /></label>
            <label>Moeda<select value={stayCurrency} onChange={(event) => setStayCurrency(event.target.value)}><option value="EUR">EUR</option><option value="USD">USD</option><option value="GBP">GBP</option></select></label>
          </div>
          <p className="budget-description">{tripsLoading ? "A carregar viagens..." : trips.length === 0 ? "Não existem viagens em que tenhas permissões para adicionar alojamentos." : "As viagens em que tens permissões de proprietário ou editor estão disponíveis."}</p>
        </section>

        <section className="trip-create-form" aria-label="Pesquisar e ordenar favoritos">
          <div className="trip-form-grid">
            <label>Pesquisar por hotel ou localização
              <input value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Ex.: Lisboa, Porto, hotel..." />
            </label>
            <label>Ordenar por
              <select value={sort} onChange={(event) => setSort(event.target.value as "name" | "newest")}>
                <option value="name">Nome (A–Z)</option>
                <option value="newest">Adicionados recentemente</option>
              </select>
            </label>
          </div>
          <div className="trip-form-actions">
            <button className="secondary-button" type="button" onClick={() => { setLoading(true); void loadFavorites(); }} disabled={loading}>Atualizar favoritos</button>
            {search && <button className="secondary-button" type="button" onClick={() => setSearch("")}>Limpar pesquisa</button>}
          </div>
        </section>

        {error && <p className="form-error" role="alert">{error}</p>}
        {notice && <p className="notice" role="status">{notice}</p>}
        {loading && <p className="notice" role="status">A carregar os teus hotéis favoritos...</p>}
        {!loading && !error && favorites.length === 0 && (
          <div className="empty-state">
            <h3>Ainda não guardaste hotéis.</h3>
            <p>Pesquisa alojamentos numa viagem e seleciona «Adicionar aos favoritos» para os guardar aqui.</p>
            <Link className="edit-button" href="/dashboard">Ir para as minhas viagens</Link>
          </div>
        )}
        {!loading && favorites.length > 0 && visibleFavorites.length === 0 && (
          <div className="empty-state"><h3>Não foram encontrados favoritos.</h3><p>Experimenta outro nome ou localização.</p></div>
        )}
        {!loading && visibleFavorites.length > 0 && (
          <div className="trip-list">
            {visibleFavorites.map((favorite) => (
              <article className="trip-card" key={favorite.id}>
                <div>
                  <h3>{favorite.hotel_name}</h3>
                  <p>{favorite.location}</p>
                  <p className="budget-description">Guardado em {new Intl.DateTimeFormat("pt-PT", { dateStyle: "medium" }).format(new Date(favorite.created_at))}</p>
                </div>
                <div className="trip-card-actions">
                  <div className="trip-action-buttons">
                    <button className="edit-button" type="button" disabled={!selectedTripId || !stayCheckIn || !stayCheckOut || stayCheckOut <= stayCheckIn || (stayPrice !== "" && (!Number.isFinite(Number(stayPrice)) || Number(stayPrice) <= 0)) || addingToTripId !== null || tripsLoading} onClick={() => void addFavoriteToTrip(favorite)}>
                      {addingToTripId === favorite.id ? "A adicionar..." : "Adicionar à viagem"}
                    </button>
                    <button className="delete-button" type="button" disabled={removingId !== null || addingToTripId !== null} onClick={() => void removeFavorite(favorite)}>
                      {removingId === favorite.id ? "A remover..." : "Retirar dos favoritos"}
                    </button>
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
