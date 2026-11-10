"use client";

import Link from "next/link";
import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";

export default function RegisterPage() {
  const router = useRouter();
  const [displayName, setDisplayName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    setLoading(true);

    try {
      const response = await fetch("/api/auth/register", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ display_name: displayName, email, password }),
      });
      const data = await response.json();
      if (!response.ok) {
        setError(data.detail ?? "Não foi possível criar a conta.");
        return;
      }
      router.push("/login?registered=1");
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
        <p className="eyebrow">COMEÇA A PLANEAR</p>
        <h1>Criar conta</h1>
        <p className="auth-description">Cria a tua conta SKY e mantém as tuas viagens organizadas.</p>
        <form className="auth-form" onSubmit={handleSubmit}>
          <label>Nome<input type="text" autoComplete="name" minLength={2} maxLength={120} required value={displayName} onChange={(event) => setDisplayName(event.target.value)} /></label>
          <label>Email<input type="email" autoComplete="email" required value={email} onChange={(event) => setEmail(event.target.value)} /></label>
          <label>Palavra-passe<input type="password" autoComplete="new-password" minLength={12} maxLength={128} required value={password} onChange={(event) => setPassword(event.target.value)} /><span className="field-hint">Utiliza pelo menos 12 caracteres.</span></label>
          {error && <p className="form-error" role="alert">{error}</p>}
          <button className="primary-button" type="submit" disabled={loading}>{loading ? "A criar conta..." : "Criar conta"}</button>
        </form>
        <p className="auth-switch">Já tens conta? <Link href="/login">Iniciar sessão</Link></p>
      </section>
    </main>
  );
}
