"use client";

import { useEffect, useMemo, useState } from "react";

type PriceObservation = {
  id: string;
  item_key: string;
  item_name: string;
  amount: string;
  currency: string;
  is_available: boolean;
  captured_at: string;
};

type PriceHistoryResponse = {
  observations_count: number;
  observations: PriceObservation[];
};

type PriceHistoryItem = { key: string; label: string };

type PriceAlert = {
  id: string;
  search_type: "flight" | "hotel";
  search_key: string;
  item_key: string;
  item_name: string;
  currency: string;
  target_price: string;
  is_active: boolean;
  triggered_price: string | null;
  triggered_at: string | null;
};

export default function PriceHistoryPanel({
  searchType,
  searchKey,
  items,
}: {
  searchType: "flight" | "hotel";
  searchKey: string;
  items: PriceHistoryItem[];
}) {
  const [selectedKey, setSelectedKey] = useState(items[0]?.key ?? "");
  const [history, setHistory] = useState<PriceHistoryResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [alerts, setAlerts] = useState<PriceAlert[]>([]);
  const [targetPrice, setTargetPrice] = useState("");
  const [alertBusy, setAlertBusy] = useState(false);
  const [alertMessage, setAlertMessage] = useState("");
  const [alertError, setAlertError] = useState("");

  useEffect(() => {
    setSelectedKey(items[0]?.key ?? "");
  }, [searchKey, items]);

  useEffect(() => {
    if (!searchKey || !selectedKey) {
      setHistory(null);
      return;
    }
    const controller = new AbortController();
    setLoading(true);
    setError("");
    fetch(
      "/api/backend/prices/history?" +
        new URLSearchParams({
          search_type: searchType,
          search_key: searchKey,
          item_key: selectedKey,
          limit: "100",
        }).toString(),
      { cache: "no-store", signal: controller.signal },
    )
      .then(async (response) => {
        const payload = await response.json().catch(() => ({}));
        if (response.status === 404) {
          return { observations_count: 0, observations: [] } as PriceHistoryResponse;
        }
        if (!response.ok) {
          throw new Error(
            typeof payload.detail === "string"
              ? payload.detail
              : "Não foi possível consultar o histórico de preços.",
          );
        }
        return payload as PriceHistoryResponse;
      })
      .then(setHistory)
      .catch((cause: unknown) => {
        if (!controller.signal.aborted) {
          setHistory(null);
          setError(
            cause instanceof Error
              ? cause.message
              : "Ocorreu um erro ao consultar o histórico.",
          );
        }
      })
      .finally(() => {
        if (!controller.signal.aborted) setLoading(false);
      });
    return () => controller.abort();
  }, [searchType, searchKey, selectedKey]);


  useEffect(() => {
    if (!searchKey || !selectedKey) {
      setAlerts([]);
      return;
    }
    const controller = new AbortController();
    fetch("/api/backend/prices/alerts", { cache: "no-store", signal: controller.signal })
      .then(async (response) => {
        const payload = await response.json().catch(() => []);
        if (!response.ok) throw new Error("Não foi possível carregar os alertas de preço.");
        return Array.isArray(payload) ? payload as PriceAlert[] : [];
      })
      .then(setAlerts)
      .catch((cause: unknown) => {
        if (!controller.signal.aborted) setAlertError(cause instanceof Error ? cause.message : "Erro ao carregar alertas.");
      });
    return () => controller.abort();
  }, [searchKey, selectedKey]);

  async function createAlert() {
    const observations = history?.observations ?? [];
    const latestObservation = observations[observations.length - 1];
    const target = Number(targetPrice);
    if (!latestObservation || !Number.isFinite(target) || target <= 0) {
      setAlertError("Indica um preço-alvo válido e aguarda uma observação de preço.");
      return;
    }
    setAlertBusy(true);
    setAlertError("");
    setAlertMessage("");
    try {
      const response = await fetch("/api/backend/prices/alerts", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          search_type: searchType,
          search_key: searchKey,
          item_key: selectedKey,
          item_name: items.find((item) => item.key === selectedKey)?.label ?? selectedKey,
          currency: latestObservation.currency,
          target_price: target.toFixed(2),
        }),
      });
      const payload = await response.json().catch(() => ({}));
      if (!response.ok) throw new Error(typeof payload.detail === "string" ? payload.detail : "Não foi possível criar o alerta.");
      setAlerts((current) => [payload as PriceAlert, ...current]);
      setTargetPrice("");
      setAlertMessage("Alerta criado. Será avaliado quando esta pesquisa voltar a ser executada.");
    } catch (cause) {
      setAlertError(cause instanceof Error ? cause.message : "Ocorreu um erro ao criar o alerta.");
    } finally {
      setAlertBusy(false);
    }
  }

  async function toggleAlert(alert: PriceAlert) {
    setAlertBusy(true);
    setAlertError("");
    try {
      const response = await fetch("/api/backend/prices/alerts/" + alert.id, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ is_active: !alert.is_active }),
      });
      const payload = await response.json().catch(() => ({}));
      if (!response.ok) throw new Error(typeof payload.detail === "string" ? payload.detail : "Não foi possível atualizar o alerta.");
      setAlerts((current) => current.map((item) => item.id === alert.id ? payload as PriceAlert : item));
    } catch (cause) {
      setAlertError(cause instanceof Error ? cause.message : "Ocorreu um erro ao atualizar o alerta.");
    } finally {
      setAlertBusy(false);
    }
  }

  async function deleteAlert(alert: PriceAlert) {
    setAlertBusy(true);
    setAlertError("");
    try {
      const response = await fetch("/api/backend/prices/alerts/" + alert.id, { method: "DELETE" });
      if (!response.ok) throw new Error("Não foi possível eliminar o alerta.");
      setAlerts((current) => current.filter((item) => item.id !== alert.id));
    } catch (cause) {
      setAlertError(cause instanceof Error ? cause.message : "Ocorreu um erro ao eliminar o alerta.");
    } finally {
      setAlertBusy(false);
    }
  }

  const points = useMemo(() => {
    const observations = history?.observations ?? [];
    const values = observations
      .map((item) => Number(item.amount))
      .filter((value) => Number.isFinite(value) && value > 0);
    if (values.length === 0) return [];
    const min = Math.min(...values);
    const max = Math.max(...values);
    const spread = max - min || Math.max(max * 0.02, 1);
    return observations.map((item, index) => {
      const value = Number(item.amount);
      const x = observations.length === 1 ? 320 : 24 + (index / (observations.length - 1)) * 592;
      const y = 18 + ((max - value) / spread) * 164;
      return { ...item, value, x, y };
    });
  }, [history]);

  const values = points.map((point) => point.value);
  const minimum = values.length ? Math.min(...values) : null;
  const maximum = values.length ? Math.max(...values) : null;
  const latest = points.length ? points[points.length - 1] : null;
  const currency = latest?.currency ?? "EUR";
  const money = (value: number) =>
    new Intl.NumberFormat("pt-PT", { style: "currency", currency }).format(value);
  const dateLabel = (value: string) =>
    new Date(value).toLocaleString("pt-PT", { dateStyle: "short", timeStyle: "short" });

  if (items.length === 0) return null;

  return (
    <section className="trip-card" aria-labelledby={searchType + "-price-history-title"}>
      <div>
        <p className="eyebrow">SKY PRICE INTELLIGENCE</p>
        <h3 id={searchType + "-price-history-title"}>Histórico de preços observados</h3>
        <p className="budget-description">
          Evolução dos preços efectivamente recolhidos nas pesquisas. Não representa uma previsão.
        </p>
      </div>
      <label>
        Oferta a acompanhar
        <select value={selectedKey} onChange={(event) => setSelectedKey(event.target.value)}>
          {items.map((item) => (
            <option key={item.key} value={item.key}>{item.label}</option>
          ))}
        </select>
      </label>

      <div className="trip-card">
        <h4>Alerta de preço</h4>
        <p className="budget-description">Define o preço máximo que pretendes pagar. O alerta só é verificado quando voltares a pesquisar esta rota ou alojamento.</p>
        <div className="trip-form-grid">
          <label>
            Preço-alvo ({history?.observations[history.observations.length - 1]?.currency ?? "—"})
            <input type="number" min="0.01" step="0.01" value={targetPrice} onChange={(event) => setTargetPrice(event.target.value)} placeholder="Ex.: 150.00" />
          </label>
          <div className="trip-form-actions">
            <button className="secondary-button" type="button" disabled={alertBusy || !history?.observations.length || !targetPrice || Number(targetPrice) <= 0} onClick={() => void createAlert()}>
              {alertBusy ? "A guardar..." : "Criar alerta"}
            </button>
          </div>
        </div>
        {alertError && <p className="notice" role="alert">{alertError}</p>}
        {alertMessage && <p className="budget-description" role="status">{alertMessage}</p>}
        {alerts.filter((alert) => alert.search_key === searchKey && alert.item_key === selectedKey).map((alert) => (
          <div key={alert.id} className="activity-heading">
            <p>
              <strong>{alert.target_price} {alert.currency}</strong>
              {" · "}
              {alert.triggered_at
                ? "Atingido por " + alert.triggered_price + " " + alert.currency + " em " + dateLabel(alert.triggered_at)
                : alert.is_active ? "Activo" : "Inactivo"}
            </p>
            <div className="trip-card-actions">
              {!alert.triggered_at && <button className="secondary-button" type="button" disabled={alertBusy} onClick={() => void toggleAlert(alert)}>{alert.is_active ? "Desactivar" : "Reactivar"}</button>}
              <button className="secondary-button" type="button" disabled={alertBusy} onClick={() => void deleteAlert(alert)}>Eliminar</button>
            </div>
          </div>
        ))}
      </div>

      {loading && <p className="budget-description" role="status">A carregar histórico...</p>}
      {error && <p className="notice" role="status">{error}</p>}
      {!loading && !error && points.length === 0 && (
        <p className="budget-description">
          Ainda não existem observações anteriores para esta oferta. O histórico cresce com novas pesquisas dos mesmos critérios.
        </p>
      )}
      {points.length > 0 && latest && (
        <>
          <div className="trip-form-grid">
            <p><strong>Último preço</strong><br />{money(latest.value)}</p>
            <p><strong>Mínimo observado</strong><br />{money(minimum ?? latest.value)}</p>
            <p><strong>Máximo observado</strong><br />{money(maximum ?? latest.value)}</p>
            <p><strong>Recolhas</strong><br />{points.length}</p>
          </div>
          <svg
            viewBox="0 0 640 210"
            role="img"
            aria-label={"Histórico de " + points.length + " observações de preço"}
            style={{ width: "100%", height: "auto", overflow: "visible" }}
          >
            {[18, 100, 182].map((y) => (
              <line key={y} x1="24" y1={y} x2="616" y2={y} stroke="currentColor" opacity="0.16" strokeDasharray="4 5" />
            ))}
            {points.length > 1 && (
              <polyline
                points={points.map((point) => point.x + "," + point.y).join(" ")}
                fill="none"
                stroke="currentColor"
                strokeWidth="3"
                strokeLinecap="round"
                strokeLinejoin="round"
              />
            )}
            {points.map((point) => (
              <circle key={point.id} cx={point.x} cy={point.y} r="5" fill="currentColor">
                <title>{money(point.value)} · {dateLabel(point.captured_at)}</title>
              </circle>
            ))}
          </svg>
          <p className="budget-description">
            Primeira recolha: {dateLabel(points[0].captured_at)} · Última recolha: {dateLabel(latest.captured_at)}
          </p>
        </>
      )}
    </section>
  );
}
