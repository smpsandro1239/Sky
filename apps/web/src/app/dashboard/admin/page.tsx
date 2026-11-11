"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";

type PlatformRole = "traveler" | "support" | "admin";
type Profile = { id: string; email: string; display_name: string | null; role: PlatformRole };
type AdminUser = {
  id: string;
  email: string;
  display_name: string | null;
  role: PlatformRole;
  is_active: boolean;
  is_verified: boolean;
  created_at: string;
};

const roleLabels: Record<PlatformRole, string> = {
  traveler: "Viajante",
  support: "Suporte",
  admin: "Administrador",
};

export default function AdminPage() {
  const router = useRouter();
  const [profile, setProfile] = useState<Profile | null>(null);
  const [users, setUsers] = useState<AdminUser[]>([]);
  const [loading, setLoading] = useState(true);
  const [savingId, setSavingId] = useState<string | null>(null);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");

  useEffect(() => {
    let active = true;

    async function load() {
      try {
        const profileResponse = await fetch("/api/backend/auth/me", { cache: "no-store" });
        if (profileResponse.status === 401) {
          router.replace("/login");
          return;
        }
        if (!profileResponse.ok) throw new Error("Não foi possível validar a sessão.");
        const currentProfile = await profileResponse.json() as Profile;
        if (!active) return;
        setProfile(currentProfile);

        if (currentProfile.role !== "admin" && currentProfile.role !== "support") {
          setError("Não tens permissões para consultar esta área.");
          return;
        }

        const usersResponse = await fetch("/api/backend/admin/users?limit=100", { cache: "no-store" });
        const payload = await usersResponse.json().catch(() => ({}));
        if (!usersResponse.ok) {
          throw new Error(typeof payload.detail === "string" ? payload.detail : "Não foi possível carregar as contas.");
        }
        if (active) setUsers(payload as AdminUser[]);
      } catch (cause) {
        if (active) setError(cause instanceof Error ? cause.message : "Ocorreu um erro inesperado.");
      } finally {
        if (active) setLoading(false);
      }
    }

    void load();
    return () => { active = false; };
  }, [router]);

  async function changeRole(user: AdminUser, nextRole: PlatformRole) {
    if (profile?.role !== "admin" || user.role === nextRole || user.id === profile.id) return;
    setSavingId(user.id);
    setError("");
    setNotice("");
    try {
      const response = await fetch("/api/backend/admin/users/" + user.id + "/role", {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ role: nextRole }),
      });
      const payload = await response.json().catch(() => ({}));
      if (!response.ok) {
        throw new Error(typeof payload.detail === "string" ? payload.detail : "Não foi possível alterar o papel.");
      }
      const updated = payload as AdminUser;
      setUsers((current) => current.map((item) => item.id === updated.id ? updated : item));
      setNotice("Papel de acesso atualizado.");
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Não foi possível alterar o papel.");
    } finally {
      setSavingId(null);
    }
  }

  return (
    <main className="dashboard-shell">
      <header className="dashboard-header">
        <Link className="brand" href="/">SKY<span>.</span></Link>
        <nav aria-label="Navegação da administração">
          <Link className="text-button" href="/dashboard">Voltar ao dashboard</Link>
        </nav>
      </header>
      <section className="dashboard-content">
        <Link className="back-link" href="/dashboard">← Dashboard</Link>
        <p className="eyebrow">CONTROLO DA PLATAFORMA</p>
        <h1>Gestão de acessos</h1>
        <p className="intro dashboard-intro">
          Consulta as contas e gere os papéis globais da plataforma. As permissões são sempre validadas pela API.
        </p>

        {profile && <p className="notice">Sessão: {profile.email} · {roleLabels[profile.role]}</p>}
        {error && <p className="form-error" role="alert">{error}</p>}
        {notice && <p className="notice" role="status">{notice}</p>}
        {loading && <p className="notice">A carregar contas...</p>}

        {!loading && !error && (
          <section aria-labelledby="users-heading">
            <div className="section-heading">
              <div><p className="eyebrow">CONTAS</p><h2 id="users-heading">Utilizadores ({users.length})</h2></div>
            </div>
            <div className="admin-user-list">
              {users.map((user) => (
                <article className="admin-user-card" key={user.id}>
                  <div className="admin-user-details">
                    <strong>{user.display_name || "Sem nome apresentado"}</strong>
                    <span>{user.email}</span>
                    <small>
                      {user.is_active ? "Conta ativa" : "Conta inativa"} · {user.is_verified ? "Email verificado" : "Email por verificar"} · Registo {new Date(user.created_at).toLocaleDateString("pt-PT")}
                    </small>
                  </div>
                  <div className="admin-user-role">
                    <label htmlFor={"role-" + user.id}>Papel global</label>
                    {profile?.role === "admin" ? (
                      <select
                        id={"role-" + user.id}
                        value={user.role}
                        disabled={savingId === user.id || user.id === profile.id}
                        onChange={(event) => void changeRole(user, event.target.value as PlatformRole)}
                      >
                        <option value="traveler">Viajante</option>
                        <option value="support">Suporte</option>
                        <option value="admin">Administrador</option>
                      </select>
                    ) : (
                      <strong>{roleLabels[user.role]}</strong>
                    )}
                    {user.id === profile?.id && <small>Não podes alterar o teu próprio papel.</small>}
                  </div>
                </article>
              ))}
              {users.length === 0 && <div className="empty-state"><h3>Sem contas registadas</h3><p>As contas aparecerão aqui depois de concluírem o registo.</p></div>}
            </div>
          </section>
        )}
      </section>
    </main>
  );
}
