"use client";

import Link from "next/link";
import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    setLoading(true);

    try {
      const response = await fetch("/api/auth/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password }),
      });
      const data = await response.json();
      if (!response.ok) {
        setError(data.detail ?? "Não foi possível iniciar sessão.");
        return;
      }
      router.replace("/dashboard");
      router.refresh();
    } catch {
      setError("Não foi possível contactar o serviço. Tenta novamente.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="auth-shell">
      <Link className="brand auth-brand" href="/">SKY<span>.</span></Link>
      <section className="auth-card">
        <p className="eyebrow">BEM-VINDO DE VOLTA</p>
        <h1>Iniciar sessão</h1>
        <p className="auth-description">Entra na tua conta para continuares a planear as tuas viagens.</p>
        <form className="auth-form" onSubmit={handleSubmit}>
          <label>Email<input type="email" autoComplete="email" required value={email} onChange={(event) => setEmail(event.target.value)} /></label>
          <label>Palavra-passe<input type="password" autoComplete="current-password" required value={password} onChange={(event) => setPassword(event.target.value)} /></label>
          {error && <p className="form-error" role="alert">{error}</p>}
          <button className="primary-button" type="submit" disabled={loading}>{loading ? "A entrar..." : "Entrar"}</button>
        </form>
        <p className="auth-switch">Ainda não tens conta? <Link href="/register">Criar conta</Link></p>
        <p className="auth-footnote">A palavra-passe nunca é guardada no navegador.</p>
      </section>
    </main>
  );
}
