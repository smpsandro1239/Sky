"use client";

import { useEffect, useState } from "react";

type Notification = {
  id: string;
  notification_type: string;
  title: string;
  message: string;
  link: string | null;
  read_at: string | null;
  created_at: string;
};

type NotificationPage = {
  items: Notification[];
  unread_count: number;
  has_more: boolean;
};

export default function NotificationsBell() {
  const [items, setItems] = useState<Notification[]>([]);
  const [unreadCount, setUnreadCount] = useState(0);
  const [open, setOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function loadNotifications() {
    setLoading(true);
    setError("");
    try {
      const response = await fetch("/api/backend/notifications?limit=20", { cache: "no-store" });
      const payload = await response.json().catch(() => ({}));
      if (!response.ok) throw new Error(typeof payload.detail === "string" ? payload.detail : "Não foi possível carregar as notificações.");
      const data = payload as NotificationPage;
      setItems(data.items ?? []);
      setUnreadCount(data.unread_count ?? 0);
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Erro ao carregar notificações.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void loadNotifications();
  }, []);

  async function markRead(notification: Notification) {
    if (notification.read_at) return;
    const response = await fetch("/api/backend/notifications/" + notification.id + "/read", { method: "PATCH" });
    const payload = await response.json().catch(() => ({}));
    if (!response.ok) {
      setError(typeof payload.detail === "string" ? payload.detail : "Não foi possível atualizar a notificação.");
      return;
    }
    setItems((current) => current.map((item) => item.id === notification.id ? payload as Notification : item));
    setUnreadCount((current) => Math.max(0, current - 1));
  }

  async function markAllRead() {
    const response = await fetch("/api/backend/notifications/read-all", { method: "POST" });
    const payload = await response.json().catch(() => ({}));
    if (!response.ok) {
      setError(typeof payload.detail === "string" ? payload.detail : "Não foi possível marcar as notificações.");
      return;
    }
    setItems((current) => current.map((item) => ({ ...item, read_at: item.read_at ?? new Date().toISOString() })));
    setUnreadCount(0);
  }

  return (
    <div className="notifications-root">
      <button
        className="text-button notifications-trigger"
        type="button"
        aria-label={unreadCount ? `Notificações, ${unreadCount} por ler` : "Notificações"}
        aria-expanded={open}
        aria-controls="sky-notifications-panel"
        onClick={() => { setOpen((value) => !value); if (!open) void loadNotifications(); }}
      >
        <span aria-hidden="true">🔔</span> Notificações
        {unreadCount > 0 && <span className="notifications-count">{unreadCount > 99 ? "99+" : unreadCount}</span>}
      </button>
      {open && (
        <section className="notifications-panel" id="sky-notifications-panel" aria-label="Centro de notificações">
          <div className="notifications-panel-heading">
            <strong>Notificações</strong>
            <button type="button" className="text-button" onClick={() => void markAllRead()} disabled={unreadCount === 0}>Marcar todas como lidas</button>
          </div>
          {error && <p className="form-error" role="alert">{error}</p>}
          {loading && <p className="budget-description">A carregar...</p>}
          {!loading && items.length === 0 && <p className="budget-description">Ainda não tens notificações.</p>}
          <div className="notifications-list">
            {items.map((item) => (
              <article className={"notification-item" + (item.read_at ? "" : " notification-unread")} key={item.id}>
                <div>
                  <strong>{item.title}</strong>
                  <p>{item.message}</p>
                  <small>{new Date(item.created_at).toLocaleString("pt-PT", { dateStyle: "short", timeStyle: "short" })}</small>
                </div>
                <div className="notification-actions">
                  {!item.read_at && <button type="button" className="secondary-button" onClick={() => void markRead(item)}>Marcar como lida</button>}
                  {item.link && <a className="edit-button" href={item.link}>Abrir</a>}
                </div>
              </article>
            ))}
          </div>
        </section>
      )}
    </div>
  );
}
