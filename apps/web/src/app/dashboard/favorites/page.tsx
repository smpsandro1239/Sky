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

export default function HotelFavoritesPage() {
  const router = useRouter();
  const [favorites, setFavorites] = useState<HotelFavorite[]>([]);
  const [search, setSearch] = useState("");
  const [sort, setSort] = useState<"name" | "newest">("name");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [removingId, setRemovingId] = useState<string | null>(null);
  const [notice, setNotice] = useState("");

  async function loadFavorites() {
    try {
      const response = await fetch("/api/backend/hotels/favorites", { cache: "no-store" });
      const payload = await response.json().catch(() => null);
      if (response.status === 401) {
        router.replace("/login");
        return;
      }
      if (!response.ok) {
        throw new Error(payload && typeof payload.detail === "string" ? payload.detail : "Não foi possível carregar os hotéis favoritos.");
      }
      if (!Array.isArray(payload) || !payload.every((item) =>
        item && typeof item.id === "string" && typeof item.hotel_id === "string"
        && typeof item.hotel_name === "string" && typeof item.location === "string"
      )) {
        throw new Error("A resposta dos favoritos tem um formato inválido.");
      }
      setFavorites(payload as HotelFavorite[]);
      setError("");
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Ocorreu um erro ao carregar os favoritos.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void loadFavorites();
  }, []);

  const visibleFavorites = useMemo(() => {
    const term = search.trim().toLocaleLowerCase("pt-PT");
    return [...favorites]
      .filter((favorite) => !term
        || favorite.hotel_name.toLocaleLowerCase("pt-PT").includes(term)
        || favorite.location.toLocaleLowerCase("pt-PT").includes(term))
      .sort((first, second) => sort === "name"
        ? first.hotel_name.localeCompare(second.hotel_name, "pt-PT")
        : second.created_at.localeCompare(first.created_at));
  }, [favorites, search, sort]);

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
                  <button className="delete-button" type="button" disabled={removingId !== null} onClick={() => void removeFavorite(favorite)}>
                    {removingId === favorite.id ? "A remover..." : "Retirar dos favoritos"}
                  </button>
                </div>
              </article>
            ))}
          </div>
        )}
      </section>
    </main>
  );
}
