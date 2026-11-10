"use client";

import Link from "next/link";
import { FormEvent, useEffect, useState } from "react";

export default function AcceptInvitationPage() {
  const [token, setToken] = useState("");
  const [tokenReady, setTokenReady] = useState(false);
  useEffect(() => {
    setToken(new URLSearchParams(window.location.search).get("token") ?? "");
    setTokenReady(true);
  }, []);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const loginUrl = "/login?next=" + encodeURIComponent("/invitations/accept?token=" + token);

  async function accept(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setLoading(true);
    setError("");
    setMessage("");
    try {
      const response = await fetch("/api/backend/invitations/accept", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ token }),
      });
      const data = await response.json().catch(() => ({}));
      if (response.status === 401) {
        setError("Inicia sessão com a conta de email que recebeu o convite.");
        return;
      }
      if (!response.ok) {
        setError(typeof data.detail === "string" ? data.detail : "Não foi possível aceitar o convite.");
        return;
      }
      setMessage("A tua conta foi associada à lista de participantes desta viagem. O acesso partilhado à área da viagem ainda não está disponível.");
    } catch {
      setError("Não foi possível contactar a API. Tenta novamente.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="auth-shell">
      <Link className="brand auth-brand" href="/">SKY<span>.</span></Link>
      <section className="auth-card">
        <p className="eyebrow">CONVITE DE VIAGEM</p>
        <h1>Aderir à viagem</h1>
        <p className="auth-description">Aceita o convite para te associares à viagem e participares na gestão das despesas.</p>
        {!tokenReady ? <p className="notice">A validar o link...</p> : !token ? <p className="form-error" role="alert">O link não contém um token de convite válido.</p> : (
          <form className="auth-form" onSubmit={accept}>
            {error && <p className="form-error" role="alert">{error}</p>}
            {message && <p className="invitation-success" role="status">{message}</p>}
            <button className="primary-button" type="submit" disabled={loading || Boolean(message)}>
              {loading ? "A validar convite..." : "Aceitar convite"}
            </button>
          </form>
        )}
        <p className="auth-switch"><Link href={loginUrl}>Iniciar sessão com a conta convidada</Link></p>
        <p className="auth-footnote">O convite é pessoal, de utilização única e expira ao fim de 7 dias.</p>
      </section>
    </main>
  );
}
