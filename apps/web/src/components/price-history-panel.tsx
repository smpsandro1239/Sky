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
