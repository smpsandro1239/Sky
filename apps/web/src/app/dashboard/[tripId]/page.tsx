"use client";

import Link from "next/link";
import { FormEvent, useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import FlightSearchPanel from "@/components/flight-search-panel";
import HotelSearchPanel from "@/components/hotel-search-panel";

type Trip = {
  id: string;
  name: string;
  destination: string;
  start_date: string | null;
  end_date: string | null;
  notes: string | null;
  budget_amount: string | null;
  budget_currency: string;
  role: "owner" | "editor" | "viewer";
};
type Flight = {
  id: string;
  provider: string | null;
  origin: string;
  destination: string;
  departure_at: string;
  arrival_at: string | null;
  price_amount: string | null;
  price_currency: string;
};
type Accommodation = {
  id: string;
  provider: string | null;
  name: string;
  location: string;
  check_in: string;
  check_out: string;
  price_amount: string | null;
  price_currency: string;
};
type Expense = { id: string; category: string; description: string; expense_date: string; amount: string; currency: string; paid_by_participant_id: string | null; notes: string | null; };
type TripBalances = { currencies: { currency: string; participants: { participant_id: string; name: string; paid: string; owed: string; settled_sent?: string; settled_received?: string; net: string }[]; suggested_transfers: { from_participant_id: string; from_name: string; to_participant_id: string; to_name: string; amount: string }[] }[] };
type TripSettlement = { id: string; from_participant_id: string; to_participant_id: string; amount: string; currency: string; paid_at: string; notes: string | null };
type Participant = { id: string; trip_id: string; name: string; email: string | null; role: "editor" | "viewer"; is_linked: boolean; created_at: string };
type Invitation = { id: string; trip_id: string; email: string; status: string; expires_at: string; accepted_at: string | null; created_at: string };
type CreatedInvitation = Invitation & { invitation_token: string; email_sent: boolean };
type ExpenseShare = { id: string; expense_id: string; participant_id: string; amount: string };
type FinancialMovement = { id: string; date: string; participant_id: string; participant_name: string; currency: string; kind: "paid" | "owed" | "sent" | "received"; amount: number; description: string };
type TripActivity = { id: string; entity_id: string | null; actor_name: string; action: string; entity_type: string; summary: string; created_at: string };
type TripActivityPage = { items: TripActivity[]; limit: number; offset: number; has_more: boolean };
type ExpenseForm = { category: string; description: string; expense_date: string; amount: string; currency: string; paid_by_participant_id: string; notes: string; };
type FlightForm = {
  provider: string;
  origin: string;
  destination: string;
  departure_at: string;
  arrival_at: string;
  price_amount: string;
  price_currency: string;
};
type AccommodationForm = {
  provider: string;
  name: string;
  location: string;
  check_in: string;
  check_out: string;
  price_amount: string;
  price_currency: string;
};

const emptyExpense: ExpenseForm = { category: "alimentacao", description: "", expense_date: new Date().toISOString().slice(0, 10), amount: "", currency: "EUR", paid_by_participant_id: "", notes: "" };
const expenseCategoryLabels: Record<string, string> = { alimentacao: "Alimentação", alojamento: "Alojamento", atividades: "Atividades", compras: "Compras", transportes: "Transportes", outros: "Outros" };
const emptyFlight: FlightForm = {
  provider: "", origin: "", destination: "", departure_at: "", arrival_at: "",
  price_amount: "", price_currency: "EUR",
};
const emptyAccommodation: AccommodationForm = {
  provider: "", name: "", location: "", check_in: "", check_out: "",
  price_amount: "", price_currency: "EUR",
};

function dateTimeInput(value: string | null) {
  if (!value) return "";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "";
  const localDate = new Date(date.getTime() - date.getTimezoneOffset() * 60_000);
  return localDate.toISOString().slice(0, 16);
}

function accommodationNights(checkIn: string, checkOut: string) {
  const start = Date.parse(`${checkIn}T00:00:00Z`);
  const end = Date.parse(`${checkOut}T00:00:00Z`);
  if (!Number.isFinite(start) || !Number.isFinite(end) || end <= start) return null;
  return Math.round((end - start) / 86_400_000);
}

export default function TripDetailPage() {
  const params = useParams<{ tripId: string }>();
  const tripId = params.tripId;
  const router = useRouter();
  const [trip, setTrip] = useState<Trip | null>(null);
  const [accessRole, setAccessRole] = useState<"owner" | "editor" | "viewer">("viewer");
  const [invitationRole, setInvitationRole] = useState<"editor" | "viewer">("viewer");
  const [flights, setFlights] = useState<Flight[]>([]);
  const [accommodations, setAccommodations] = useState<Accommodation[]>([]);
  const [expenses, setExpenses] = useState<Expense[]>([]);
  const [expenseDateFrom, setExpenseDateFrom] = useState("");
  const [expenseDateTo, setExpenseDateTo] = useState("");
  const [participants, setParticipants] = useState<Participant[]>([]);
  const [balances, setBalances] = useState<TripBalances>({ currencies: [] });
  const [settlements, setSettlements] = useState<TripSettlement[]>([]);
  const [settlementCurrency, setSettlementCurrency] = useState("EUR");
  const [settlementFrom, setSettlementFrom] = useState("");
  const [settlementTo, setSettlementTo] = useState("");
  const [settlementAmount, setSettlementAmount] = useState("");
  const [settlementNotes, setSettlementNotes] = useState("");
  const [activity, setActivity] = useState<TripActivity[]>([]);
  const [activityHasMore, setActivityHasMore] = useState(false);
  const [activityOffset, setActivityOffset] = useState(0);
  const [activityLoading, setActivityLoading] = useState(false);
  const [activityError, setActivityError] = useState("");
  const [activityExporting, setActivityExporting] = useState(false);
  const [participantName, setParticipantName] = useState("");
  const [participantEmail, setParticipantEmail] = useState("");
  const [invitations, setInvitations] = useState<Invitation[]>([]);
  const [invitationEmail, setInvitationEmail] = useState("");
  const [invitationLink, setInvitationLink] = useState("");
  const [invitationEmailSent, setInvitationEmailSent] = useState(false);
  const [activeShareExpenseId, setActiveShareExpenseId] = useState<string | null>(null);
  const [shareDraft, setShareDraft] = useState<Record<string, string>>({});
  const [expenseShares, setExpenseShares] = useState<ExpenseShare[]>([]);
  const [movementParticipant, setMovementParticipant] = useState("all");
  const [movementCurrency, setMovementCurrency] = useState("all");
  const [expenseForm, setExpenseForm] = useState<ExpenseForm>(emptyExpense);
  const [editingExpenseId, setEditingExpenseId] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [flightForm, setFlightForm] = useState<FlightForm>(emptyFlight);
  const [accommodationForm, setAccommodationForm] = useState<AccommodationForm>(emptyAccommodation);
  const [editingFlightId, setEditingFlightId] = useState<string | null>(null);
  const [editingAccommodationId, setEditingAccommodationId] = useState<string | null>(null);
  const [budgetAmount, setBudgetAmount] = useState("");
  const [budgetCurrency, setBudgetCurrency] = useState("EUR");

  const totalsByCurrency = [...flights, ...accommodations].reduce<Record<string, number>>(
    (totals, item) => {
      if (item.price_amount !== null) {
        const amount = Number(item.price_amount);
        if (Number.isFinite(amount)) {
          totals[item.price_currency] = (totals[item.price_currency] ?? 0) + Math.round(amount * 100);
        }
      }
      return totals;
    },
    {},
  );
  expenses.forEach((expense) => {
    const amount = Number(expense.amount);
    if (Number.isFinite(amount)) {
      totalsByCurrency[expense.currency] = (totalsByCurrency[expense.currency] ?? 0) + Math.round(amount * 100);
    }
  });
  const currencyTotals = Object.entries(totalsByCurrency).sort(([currencyA], [currencyB]) =>
    currencyA.localeCompare(currencyB),
  );

  const costForecast = (() => {
    if (!trip?.start_date || !trip?.end_date) return null;
    const start = Date.parse(`${trip.start_date}T00:00:00Z`);
    const end = Date.parse(`${trip.end_date}T00:00:00Z`);
    if (!Number.isFinite(start) || !Number.isFinite(end) || end < start) return null;
    const now = new Date();
    const todayString = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, "0")}-${String(now.getDate()).padStart(2, "0")}`;
    if (todayString < trip.start_date) return null;
    const today = Date.parse(`${todayString}T00:00:00Z`);
    const dayMs = 86_400_000;
    const totalDays = Math.floor((end - start) / dayMs) + 1;
    const elapsedDays = Math.min(totalDays, Math.floor((today - start) / dayMs) + 1);
    const fixedCosts: Record<string, number> = {};
    [...flights, ...accommodations].forEach((item) => {
      if (item.price_amount === null) return;
      const amount = Number(item.price_amount);
      if (Number.isFinite(amount) && amount >= 0) fixedCosts[item.price_currency] = (fixedCosts[item.price_currency] ?? 0) + Math.round(amount * 100);
    });
    const variableCosts: Record<string, number> = {};
    expenses.forEach((expense) => {
      if (expense.expense_date < trip.start_date! || expense.expense_date > trip.end_date! || expense.expense_date > todayString) return;
      const amount = Number(expense.amount);
      if (Number.isFinite(amount) && amount >= 0) variableCosts[expense.currency] = (variableCosts[expense.currency] ?? 0) + Math.round(amount * 100);
    });
    const currencies = new Set([...Object.keys(fixedCosts), ...Object.keys(variableCosts)]);
    return { totalDays, elapsedDays, rows: [...currencies].sort().map((currency) => {
      const fixed = fixedCosts[currency] ?? 0;
      const variable = variableCosts[currency] ?? 0;
      const projectedVariable = Math.round((variable / elapsedDays) * totalDays);
      return { currency, fixed, variable, projectedVariable, projectedTotal: fixed + projectedVariable, hasDailyData: variable > 0 };
    }) };
  })();
  const budgetComparison = trip?.budget_amount !== null && trip?.budget_amount !== undefined
    ? (() => {
        const budget = Number(trip.budget_amount);
        if (!Number.isFinite(budget) || budget < 0) return null;
        const budgetCents = Math.round(budget * 100);
        const spentCents = totalsByCurrency[trip.budget_currency] ?? 0;
        return { budgetCents, spentCents, differenceCents: budgetCents - spentCents, percentage: budgetCents > 0 ? (spentCents / budgetCents) * 100 : spentCents > 0 ? 100 : 0, otherCurrencies: currencyTotals.filter(([currency]) => currency !== trip.budget_currency).map(([currency]) => currency) };
      })()
    : null;
  const costTypeBreakdown = [...flights.map((item) => ({
    currency: item.price_currency,
    type: "flights",
    amount: item.price_amount,
  })), ...accommodations.map((item) => ({
    currency: item.price_currency,
    type: "accommodations",
    amount: item.price_amount,
  })), ...expenses.map((item) => ({
    currency: item.currency,
    type: "additional",
    amount: item.amount,
  }))].reduce<Record<string, Record<string, number>>>((totals, item) => {
    if (item.amount === null) return totals;
    const amount = Number(item.amount);
    if (!Number.isFinite(amount)) return totals;
    totals[item.currency] ??= {};
    totals[item.currency][item.type] = (totals[item.currency][item.type] ?? 0) + Math.round(amount * 100);
    return totals;
  }, {});

  const costTypeLabels: Record<string, string> = {
    flights: "Voos",
    accommodations: "Alojamentos",
    additional: "Despesas adicionais",
  };

  const filteredExpenses = expenses.filter((expense) => {
    if (expenseDateFrom && expense.expense_date < expenseDateFrom) return false;
    if (expenseDateTo && expense.expense_date > expenseDateTo) return false;
    return true;
  });

  const expenseTimeline = filteredExpenses.reduce<Record<string, Record<string, number>>>((totals, expense) => {
    const amount = Number(expense.amount);
    if (!Number.isFinite(amount) || expense.expense_date.length < 7) return totals;
    const month = expense.expense_date.slice(0, 7);
    totals[expense.currency] ??= {};
    totals[expense.currency][month] = (totals[expense.currency][month] ?? 0) + Math.round(amount * 100);
    return totals;
  }, {});

  const expenseBreakdown = filteredExpenses.reduce<Record<string, Record<string, number>>>(
    (totals, expense) => {
      const amount = Number(expense.amount);
      if (!Number.isFinite(amount)) return totals;
      totals[expense.currency] ??= {};
      totals[expense.currency][expense.category] =
        (totals[expense.currency][expense.category] ?? 0) + Math.round(amount * 100);
      return totals;
    },
    {},
  );

  const financialMovements: FinancialMovement[] = [
    ...expenses.flatMap((expense) => {
      const payer = participants.find((participant) => participant.id === expense.paid_by_participant_id);
      const paid = payer ? [{ id: "expense-paid-" + expense.id, date: expense.expense_date, participant_id: payer.id, participant_name: payer.name, currency: expense.currency, kind: "paid" as const, amount: Number(expense.amount), description: expense.description }] : [];
      const shares = payer ? expenseShares.filter((share) => share.expense_id === expense.id).flatMap((share) => {
        const participant = participants.find((item) => item.id === share.participant_id);
        const amount = Number(share.amount);
        return participant && Number.isFinite(amount) ? [{ id: "expense-share-" + share.id, date: expense.expense_date, participant_id: participant.id, participant_name: participant.name, currency: expense.currency, kind: "owed" as const, amount, description: expense.description }] : [];
      }) : [];
      return [...paid, ...shares];
    }),
    ...settlements.flatMap((settlement) => {
      const sender = participants.find((participant) => participant.id === settlement.from_participant_id);
      const receiver = participants.find((participant) => participant.id === settlement.to_participant_id);
      const amount = Number(settlement.amount);
      if (!Number.isFinite(amount)) return [];
      return [
        ...(sender ? [{ id: "settlement-sent-" + settlement.id, date: settlement.paid_at, participant_id: sender.id, participant_name: sender.name, currency: settlement.currency, kind: "sent" as const, amount, description: settlement.notes || "Transferência registada" }] : []),
        ...(receiver ? [{ id: "settlement-received-" + settlement.id, date: settlement.paid_at, participant_id: receiver.id, participant_name: receiver.name, currency: settlement.currency, kind: "received" as const, amount, description: settlement.notes || "Transferência registada" }] : []),
      ];
    }),
  ].filter((movement) => Number.isFinite(movement.amount) && movement.amount >= 0).sort((a, b) => a.date.localeCompare(b.date) || a.id.localeCompare(b.id));
  const movementRunningBalances = new Map<string, number>();
  const movementsWithBalance = financialMovements.map((movement) => {
    const key = movement.participant_id + ":" + movement.currency;
    const signedAmount = movement.kind === "paid" || movement.kind === "sent" ? movement.amount : -movement.amount;
    const balance = (movementRunningBalances.get(key) ?? 0) + Math.round(signedAmount * 100);
    movementRunningBalances.set(key, balance);
    return { ...movement, runningBalance: balance / 100 };
  });
  const filteredFinancialMovements = movementsWithBalance.filter((movement) => (movementParticipant === "all" || movement.participant_id === movementParticipant) && (movementCurrency === "all" || movement.currency === movementCurrency)).reverse();
  const selectedSettlementBalance = balances.currencies.find((group) => group.currency === settlementCurrency);

  const [accommodationFrom, setAccommodationFrom] = useState("");
  const [accommodationTo, setAccommodationTo] = useState("");
  const [accommodationMaxPrice, setAccommodationMaxPrice] = useState("");

  const filteredAccommodations = accommodations.filter((item) => {
    if (accommodationFrom && item.check_in < accommodationFrom) return false;
    if (accommodationTo && item.check_in > accommodationTo) return false;
    if (accommodationMaxPrice !== "") {
      if (item.price_amount === null || !Number.isFinite(Number(item.price_amount))) return false;
      if (Number(item.price_amount) > Number(accommodationMaxPrice)) return false;
    }
    return true;
  });

  useEffect(() => {
    let cancelled = false;

    async function loadTrip() {
      try {
        const [tripResponse, flightResponse, accommodationResponse, expenseResponse, participantResponse, balanceResponse, accessResponse, activityResponse, settlementResponse] = await Promise.all([
          fetch(`/api/backend/trips/${tripId}`, { cache: "no-store" }),
          fetch(`/api/backend/trips/${tripId}/flights`, { cache: "no-store" }),
          fetch(`/api/backend/trips/${tripId}/accommodations`, { cache: "no-store" }),
          fetch(`/api/backend/trips/${tripId}/expenses`, { cache: "no-store" }),
          fetch(`/api/backend/trips/${tripId}/participants`, { cache: "no-store" }),
          fetch(`/api/backend/trips/${tripId}/balances`, { cache: "no-store" }),
          fetch(`/api/backend/trips/${tripId}/access`, { cache: "no-store" }),
          fetch(`/api/backend/trips/${tripId}/activity?limit=20&offset=0`, { cache: "no-store" }),
          fetch(`/api/backend/trips/${tripId}/settlements`, { cache: "no-store" }),
        ]);

        if (cancelled) return;

        if ([tripResponse, flightResponse, accommodationResponse, expenseResponse, participantResponse, balanceResponse, accessResponse, activityResponse, settlementResponse].some((response) => response.status === 401)) {
          router.replace("/login");
          return;
        }

        if (!tripResponse.ok || !flightResponse.ok || !accommodationResponse.ok || !expenseResponse.ok || !participantResponse.ok || !balanceResponse.ok || !accessResponse.ok || !activityResponse.ok || !settlementResponse.ok) {
          throw new Error("Não foi possível carregar os dados desta viagem.");
        }

        const [tripData, flightData, accommodationData, expenseData, participantData, balanceData, accessData, activityData, settlementData] = await Promise.all([
          tripResponse.json(),
          flightResponse.json(),
          accommodationResponse.json(),
          expenseResponse.json(),
          participantResponse.json(),
          balanceResponse.json(),
          accessResponse.json(),
          activityResponse.json(),
          settlementResponse.json(),
        ]);

        if (cancelled) return;
        const invitationResponse = accessData.role === "owner"
          ? await fetch(`/api/backend/trips/${tripId}/invitations`, { cache: "no-store" })
          : null;
        if (invitationResponse && !invitationResponse.ok) throw new Error("Não foi possível carregar os convites.");
        const invitationData = invitationResponse ? await invitationResponse.json() : [];
        const shareResults = await Promise.all((expenseData as Expense[]).map(async (expense) => {
          const response = await fetch("/api/backend/trips/" + tripId + "/expenses/" + expense.id + "/shares", { cache: "no-store" });
          if (!response.ok) throw new Error("Não foi possível carregar as divisões das despesas para o histórico financeiro.");
          return await response.json() as ExpenseShare[];
        }));
        if (cancelled) return;
        setTrip({ ...tripData, role: accessData.role });
        setAccessRole(accessData.role);
        setBudgetAmount(tripData.budget_amount ?? "");
        setBudgetCurrency(tripData.budget_currency ?? "EUR");
        setFlights(flightData);
        setAccommodations(accommodationData);
        setExpenses(expenseData);
        setExpenseShares(shareResults.flat());
        setParticipants(participantData);
        setBalances(balanceData);
        setSettlements(settlementData);
        setSettlementCurrency(balanceData.currencies?.[0]?.currency ?? "EUR");
        setActivity(activityData.items ?? []);
        setActivityHasMore(Boolean(activityData.has_more));
        setActivityOffset(activityData.items?.length ?? 0);
        setInvitations(invitationData);
      } catch (cause) {
        if (!cancelled) {
          setError(cause instanceof Error ? cause.message : "Ocorreu um erro ao carregar a viagem.");
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    void loadTrip();
    return () => {
      cancelled = true;
    };
  }, [router, tripId]);

  async function refreshActivity() {
    if (activityLoading) return;
    setActivityLoading(true);
    setActivityError("");
    try {
      const response = await fetch(`/api/backend/trips/${tripId}/activity?limit=20&offset=0`, { cache: "no-store" });
      if (!response.ok) throw new Error("Não foi possível atualizar o histórico.");
      const data = await response.json() as TripActivityPage;
      setActivity(data.items);
      setActivityHasMore(data.has_more);
      setActivityOffset(data.items.length);
    } catch (cause) {
      setActivityError(cause instanceof Error ? cause.message : "Ocorreu um erro ao atualizar o histórico.");
    } finally {
      setActivityLoading(false);
    }
  }

  function csvCell(value: string) {
    const safeValue = /^[\s]*[=+\-@\t\r]/.test(value) ? "'" + value : value;
    return '"' + safeValue.replace(/"/g, '""') + '"';
  }

  async function exportActivity() {
    if (activityExporting) return;
    setActivityExporting(true);
    setActivityError("");
    try {
      const allItems: TripActivity[] = [];
      const pageSize = 100;
      let offset = 0;
      let hasMore = true;
      while (hasMore) {
        const response = await fetch("/api/backend/trips/" + tripId + "/activity?limit=" + pageSize + "&offset=" + offset, { cache: "no-store" });
        if (!response.ok) throw new Error("Não foi possível exportar o histórico completo.");
        const page = await response.json() as TripActivityPage;
        allItems.push(...page.items);
        offset += page.items.length;
        hasMore = page.has_more && page.items.length > 0;
      }
      const headers = ["Data", "Autor", "Ação", "Tipo de registo", "ID do registo", "Descrição"];
      const rows = allItems.map((item) => [
        new Date(item.created_at).toISOString(),
        item.actor_name,
        item.action,
        item.entity_type,
        item.entity_id ?? "",
        item.summary,
      ]);
      const csv = "\uFEFF" + [headers, ...rows].map((row) => row.map((value) => csvCell(String(value))).join(";")).join("\r\n");
      const blob = new Blob([csv], { type: "text/csv;charset=utf-8;" });
      const url = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = "sky-historico-" + tripId + ".csv";
      document.body.appendChild(link);
      link.click();
      link.remove();
      URL.revokeObjectURL(url);
    } catch (cause) {
      setActivityError(cause instanceof Error ? cause.message : "Não foi possível exportar o histórico.");
    } finally {
      setActivityExporting(false);
    }
  }

  function exportFinancialReport() {
    const headers = ["Secção", "Moeda", "Período ou categoria", "Participante", "Valor", "Detalhe"];
    const rows: string[][] = [];
    Object.entries(expenseBreakdown).forEach(([currency, categories]) => {
      Object.entries(categories).forEach(([category, amount]) => {
        rows.push(["Despesas por categoria", currency, expenseCategoryLabels[category] ?? category, "", (amount / 100).toFixed(2), "Despesas manuais no período selecionado"]);
      });
    });
    Object.entries(expenseTimeline).forEach(([currency, months]) => {
      Object.entries(months).forEach(([month, amount]) => {
        rows.push(["Evolução mensal", currency, month, "", (amount / 100).toFixed(2), "Despesas manuais no período selecionado"]);
      });
    });
    balances.currencies.forEach((group) => {
      group.participants.forEach((participant) => {
        rows.push(["Resumo por participante", group.currency, "", participant.name, (Number(participant.paid) || 0).toFixed(2), "Total pago"]);
        rows.push(["Resumo por participante", group.currency, "", participant.name, (Number(participant.owed) || 0).toFixed(2), "Quota atribuída"]);
        rows.push(["Resumo por participante", group.currency, "", participant.name, (Number(participant.net) || 0).toFixed(2), "Saldo líquido"]);
        rows.push(["Resumo por participante", group.currency, "", participant.name, (Number(participant.settled_sent ?? "0") || 0).toFixed(2), "Acertos enviados"]);
        rows.push(["Resumo por participante", group.currency, "", participant.name, (Number(participant.settled_received ?? "0") || 0).toFixed(2), "Acertos recebidos"]);
      });
    });
    if (budgetComparison && trip) {
      rows.push(["Orçamento", trip.budget_currency, "", "", (budgetComparison.budgetCents / 100).toFixed(2), "Orçamento definido"]);
      rows.push(["Orçamento", trip.budget_currency, "", "", (budgetComparison.spentCents / 100).toFixed(2), "Custos registados"]);
      rows.push(["Orçamento", trip.budget_currency, "", "", (budgetComparison.differenceCents / 100).toFixed(2), "Disponível (negativo significa excedido)"]);
    }
    if (rows.length === 0) return;
    const csv = "\uFEFF" + [headers, ...rows].map((row) => row.map((value) => csvCell(String(value))).join(";")).join("\r\n");
    const blob = new Blob([csv], { type: "text/csv;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = "sky-relatorio-financeiro-" + tripId + ".csv";
    document.body.appendChild(link);
    link.click();
    link.remove();
    URL.revokeObjectURL(url);
  }

  function exportFinancialMovements() {
    if (filteredFinancialMovements.length === 0) return;
    const labels: Record<FinancialMovement["kind"], string> = {
      paid: "Despesa paga",
      owed: "Quota atribuída",
      sent: "Acerto enviado",
      received: "Acerto recebido",
    };
    const signs: Record<FinancialMovement["kind"], string> = {
      paid: "+",
      owed: "-",
      sent: "+",
      received: "-",
    };
    const headers = ["Data", "Participante", "Movimento", "Descrição", "Valor", "Impacto no saldo", "Saldo acumulado", "Moeda"];
    const rows = filteredFinancialMovements.map((movement) => [
      movement.date,
      movement.participant_name,
      labels[movement.kind],
      movement.description,
      movement.amount.toFixed(2),
      (signs[movement.kind] === "+" ? movement.amount : -movement.amount).toFixed(2),
      movement.runningBalance.toFixed(2),
      movement.currency,
    ]);
    const csv = "\uFEFF" + [headers, ...rows].map((row) => row.map((value) => csvCell(String(value))).join(";")).join("\r\n");
    const blob = new Blob([csv], { type: "text/csv;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = "sky-movimentos-financeiros-" + tripId + ".csv";
    document.body.appendChild(link);
    link.click();
    link.remove();
    URL.revokeObjectURL(url);
  }

  async function loadMoreActivity() {
    if (activityLoading || !activityHasMore) return;
    setActivityLoading(true);
    setActivityError("");
    try {
      const response = await fetch(`/api/backend/trips/${tripId}/activity?limit=20&offset=${activityOffset}`, { cache: "no-store" });
      if (!response.ok) throw new Error("Não foi possível carregar atividades anteriores.");
      const data = await response.json() as TripActivityPage;
      setActivity((current) => [...current, ...data.items]);
      setActivityHasMore(data.has_more);
      setActivityOffset(activityOffset + data.items.length);
    } catch (cause) {
      setActivityError(cause instanceof Error ? cause.message : "Ocorreu um erro ao carregar o histórico.");
    } finally {
      setActivityLoading(false);
    }
  }

  async function saveSettlement(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSaving(true);
    setError("");
    try {
      const response = await fetch("/api/backend/trips/" + tripId + "/settlements", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          from_participant_id: settlementFrom,
          to_participant_id: settlementTo,
          amount: Number(settlementAmount),
          currency: settlementCurrency,
          notes: settlementNotes.trim() || null,
        }),
      });
      const data = await response.json().catch(() => ({}));
      if (!response.ok) {
        setError(typeof data.detail === "string" ? data.detail : "Não foi possível registar o acerto.");
        return;
      }
      setSettlementAmount("");
      setSettlementNotes("");
      setSettlementFrom("");
      setSettlementTo("");
      const [balanceResponse, settlementResponse] = await Promise.all([
        fetch("/api/backend/trips/" + tripId + "/balances", { cache: "no-store" }),
        fetch("/api/backend/trips/" + tripId + "/settlements", { cache: "no-store" }),
      ]);
      if (balanceResponse.ok) setBalances(await balanceResponse.json());
      if (settlementResponse.ok) setSettlements(await settlementResponse.json());
      void refreshActivity();
    } catch {
      setError("Não foi possível contactar a API. Tenta novamente.");
    } finally {
      setSaving(false);
    }
  }
  async function saveBudget(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!trip) return;
    setSaving(true);
    setError("");
    try {
      const response = await fetch(`/api/backend/trips/${tripId}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          budget_amount: budgetAmount === "" ? null : Number(budgetAmount),
          budget_currency: budgetCurrency.trim().toUpperCase(),
        }),
      });
      const data = await response.json().catch(() => ({}));
      if (!response.ok) {
        setError(typeof data.detail === "string" ? data.detail : "Não foi possível guardar o orçamento.");
        return;
      }
      setTrip(data);
      setBudgetAmount(data.budget_amount ?? "");
      setBudgetCurrency(data.budget_currency ?? "EUR");
      void refreshActivity();
    } catch {
      setError("Não foi possível contactar a API. Tenta novamente.");
    } finally {
      setSaving(false);
    }
  }

  async function addParticipant(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSaving(true);
    setError("");
    try {
      const response = await fetch(`/api/backend/trips/${tripId}/participants`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name: participantName.trim(), email: participantEmail.trim() || null }),
      });
      const data = await response.json().catch(() => ({}));
      if (!response.ok) {
        setError(typeof data.detail === "string" ? data.detail : "Não foi possível adicionar o participante.");
        return;
      }
      setParticipants((current) => [...current, data].sort((a, b) => a.name.localeCompare(b.name, "pt-PT")));
      setParticipantName("");
      setParticipantEmail("");
      const balanceResponse = await fetch(`/api/backend/trips/${tripId}/balances`, { cache: "no-store" });
      if (balanceResponse.ok) setBalances(await balanceResponse.json());
      void refreshActivity();
    } catch {
      setError("Não foi possível contactar a API. Tenta novamente.");
    } finally {
      setSaving(false);
    }
  }

  async function createInvitation(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSaving(true);
    setError("");
    setInvitationLink("");
    try {
      const response = await fetch(`/api/backend/trips/${tripId}/invitations`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email: invitationEmail.trim().toLowerCase(), role: invitationRole }),
      });
      const data = await response.json().catch(() => ({}));
      if (!response.ok) {
        setError(typeof data.detail === "string" ? data.detail : "Não foi possível criar o convite.");
        return;
      }
      const created = data as CreatedInvitation;
      setInvitations((current) => [created, ...current]);
      setInvitationLink(`${window.location.origin}/invitations/accept?token=${encodeURIComponent(created.invitation_token)}`);
      setInvitationEmailSent(created.email_sent);
      setInvitationEmail("");
      void refreshActivity();
    } catch {
      setError("Não foi possível contactar a API. Tenta novamente.");
    } finally {
      setSaving(false);
    }
  }

  async function revokeInvitation(id: string) {
    if (!window.confirm("Queres mesmo revogar este convite?")) return;
    setError("");
    try {
      const response = await fetch(`/api/backend/trips/${tripId}/invitations/${id}`, { method: "DELETE" });
      if (!response.ok) {
        const data = await response.json().catch(() => ({}));
        setError(typeof data.detail === "string" ? data.detail : "Não foi possível revogar o convite.");
        return;
      }
      setInvitations((current) => current.map((item) => item.id === id ? { ...item, status: "revoked" } : item));
      setInvitationLink("");
      void refreshActivity();
    } catch {
      setError("Não foi possível contactar a API. Tenta novamente.");
    }
  }

  async function updateParticipantRole(id: string, role: "editor" | "viewer") {
    setError("");
    try {
      const response = await fetch(`/api/backend/trips/${tripId}/participants/${id}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ role }),
      });
      const data = await response.json().catch(() => ({}));
      if (!response.ok) {
        setError(typeof data.detail === "string" ? data.detail : "Não foi possível atualizar a permissão.");
        return;
      }
      setParticipants((current) => current.map((participant) => participant.id === id ? data : participant));
      void refreshActivity();
    } catch {
      setError("Não foi possível contactar a API. Tenta novamente.");
    }
  }

  async function removeParticipant(id: string) {
    if (!window.confirm("Queres mesmo remover este participante da viagem?")) return;
    setError("");
    try {
      const response = await fetch(`/api/backend/trips/${tripId}/participants/${id}`, { method: "DELETE" });
      if (!response.ok) {
        const data = await response.json().catch(() => ({}));
        setError(typeof data.detail === "string" ? data.detail : "Não foi possível remover o participante.");
        return;
      }
      setParticipants((current) => current.filter((participant) => participant.id !== id));
      const balanceResponse = await fetch(`/api/backend/trips/${tripId}/balances`, { cache: "no-store" });
      if (balanceResponse.ok) setBalances(await balanceResponse.json());
      void refreshActivity();
    } catch {
      setError("Não foi possível contactar a API. Tenta novamente.");
    }
  }

  async function openExpenseShares(item: Expense) {
    if (activeShareExpenseId === item.id) {
      setActiveShareExpenseId(null);
      return;
    }
    setError("");
    try {
      const response = await fetch(`/api/backend/trips/${tripId}/expenses/${item.id}/shares`, { cache: "no-store" });
      const data = await response.json().catch(() => []);
      if (!response.ok) {
        setError(typeof data.detail === "string" ? data.detail : "Não foi possível carregar a divisão.");
        return;
      }
      const draft: Record<string, string> = {};
      (data as ExpenseShare[]).forEach((share) => { draft[share.participant_id] = share.amount; });
      setShareDraft(draft);
      setActiveShareExpenseId(item.id);
    } catch {
      setError("Não foi possível contactar a API. Tenta novamente.");
    }
  }

  function splitExpenseEqually(item: Expense) {
    if (participants.length === 0) {
      setError("Adiciona participantes antes de dividir esta despesa.");
      return;
    }
    const totalCents = Math.round(Number(item.amount) * 100);
    const baseCents = Math.floor(totalCents / participants.length);
    const remainder = totalCents % participants.length;
    const draft: Record<string, string> = {};
    participants.forEach((participant, index) => {
      const cents = baseCents + (index < remainder ? 1 : 0);
      draft[participant.id] = (cents / 100).toFixed(2);
    });
    setShareDraft(draft);
  }

  async function saveExpenseShares(event: FormEvent<HTMLFormElement>, expenseId: string) {
    event.preventDefault();
    setSaving(true);
    setError("");
    try {
      const shares = Object.entries(shareDraft)
        .filter(([, amount]) => amount.trim() !== "")
        .map(([participant_id, amount]) => ({ participant_id, amount: Number(amount) }));
      const response = await fetch(`/api/backend/trips/${tripId}/expenses/${expenseId}/shares`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(shares),
      });
      const data = await response.json().catch(() => ({}));
      if (!response.ok) {
        setError(typeof data.detail === "string" ? data.detail : "Não foi possível guardar a divisão.");
        return;
      }
      setExpenseShares((current) => [...current.filter((share) => share.expense_id !== expenseId), ...(data as ExpenseShare[])]);
      setActiveShareExpenseId(null);
      setShareDraft({});
      const balanceResponse = await fetch(`/api/backend/trips/${tripId}/balances`, { cache: "no-store" });
      if (balanceResponse.ok) setBalances(await balanceResponse.json());
      void refreshActivity();
    } catch {
      setError("Não foi possível contactar a API. Tenta novamente.");
    } finally {
      setSaving(false);
    }
  }

  async function saveExpense(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSaving(true);
    setError("");
    try {
      const payload = {
        ...expenseForm,
        description: expenseForm.description.trim(),
        amount: Number(expenseForm.amount),
        currency: expenseForm.currency.trim().toUpperCase(),
        paid_by_participant_id: expenseForm.paid_by_participant_id || null,
        notes: expenseForm.notes.trim() || null,
      };
      const response = await fetch(
        editingExpenseId
          ? `/api/backend/trips/${tripId}/expenses/${editingExpenseId}`
          : `/api/backend/trips/${tripId}/expenses`,
        {
          method: editingExpenseId ? "PATCH" : "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload),
        },
      );
      const data = await response.json().catch(() => ({}));
      if (!response.ok) {
        setError(typeof data.detail === "string" ? data.detail : "Não foi possível guardar a despesa.");
        return;
      }
      setExpenses((current) => editingExpenseId
        ? current.map((item) => item.id === editingExpenseId ? data : item)
        : [data, ...current]);
      setExpenseForm(emptyExpense);
      setEditingExpenseId(null);
      const balanceResponse = await fetch(`/api/backend/trips/${tripId}/balances`, { cache: "no-store" });
      if (balanceResponse.ok) setBalances(await balanceResponse.json());
      void refreshActivity();
    } catch {
      setError("Não foi possível contactar a API. Tenta novamente.");
    } finally {
      setSaving(false);
    }
  }

  function editExpense(item: Expense) {
    setEditingExpenseId(item.id);
    setExpenseForm({
      category: item.category,
      description: item.description,
      expense_date: item.expense_date,
      amount: item.amount,
      currency: item.currency,
      paid_by_participant_id: item.paid_by_participant_id ?? "",
      notes: item.notes ?? "",
    });
  }

  async function deleteExpense(id: string) {
    if (!window.confirm("Queres mesmo eliminar esta despesa?")) return;
    setError("");
    try {
      const response = await fetch(`/api/backend/trips/${tripId}/expenses/${id}`, { method: "DELETE" });
      if (!response.ok) {
        const data = await response.json().catch(() => ({}));
        setError(typeof data.detail === "string" ? data.detail : "Não foi possível eliminar a despesa.");
        return;
      }
      setExpenses((current) => current.filter((item) => item.id !== id));
      setExpenseShares((current) => current.filter((share) => share.expense_id !== id));
      const balanceResponse = await fetch(`/api/backend/trips/${tripId}/balances`, { cache: "no-store" });
      if (balanceResponse.ok) setBalances(await balanceResponse.json());
      if (editingExpenseId === id) {
        setEditingExpenseId(null);
        setExpenseForm(emptyExpense);
      }
      void refreshActivity();
    } catch {
      setError("Não foi possível contactar a API. Tenta novamente.");
    }
  }

  function resetFlight() {
    setFlightForm(emptyFlight);
    setEditingFlightId(null);
  }
  function resetAccommodation() {
    setAccommodationForm(emptyAccommodation);
    setEditingAccommodationId(null);
  }

  async function saveFlight(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSaving(true);
    setError("");
    try {
      const payload = {
        provider: flightForm.provider.trim() || null,
        origin: flightForm.origin.trim().toUpperCase(),
        destination: flightForm.destination.trim().toUpperCase(),
        departure_at: new Date(flightForm.departure_at).toISOString(),
        arrival_at: flightForm.arrival_at ? new Date(flightForm.arrival_at).toISOString() : null,
        price_amount: flightForm.price_amount ? Number(flightForm.price_amount) : null,
        price_currency: flightForm.price_currency.trim().toUpperCase(),
      };
      const response = await fetch(
        editingFlightId
          ? `/api/backend/trips/${tripId}/flights/${editingFlightId}`
          : `/api/backend/trips/${tripId}/flights`,
        {
          method: editingFlightId ? "PATCH" : "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload),
        },
      );
      const data = await response.json().catch(() => ({}));
      if (!response.ok) {
        setError(typeof data.detail === "string" ? data.detail : "Não foi possível guardar o voo.");
        return;
      }
      setFlights((current) => editingFlightId
        ? current.map((flight) => flight.id === editingFlightId ? data : flight)
        : [...current, data].sort((a, b) => a.departure_at.localeCompare(b.departure_at)));
      resetFlight();
      void refreshActivity();
    } catch {
      setError("Não foi possível contactar a API. Verifica a ligação e tenta novamente.");
    } finally {
      setSaving(false);
    }
  }

  async function saveAccommodation(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSaving(true);
    setError("");
    try {
      const payload = {
        provider: accommodationForm.provider.trim() || null,
        name: accommodationForm.name.trim(),
        location: accommodationForm.location.trim(),
        check_in: accommodationForm.check_in,
        check_out: accommodationForm.check_out,
        price_amount: accommodationForm.price_amount ? Number(accommodationForm.price_amount) : null,
        price_currency: accommodationForm.price_currency.trim().toUpperCase(),
      };
      const response = await fetch(
        editingAccommodationId
          ? `/api/backend/trips/${tripId}/accommodations/${editingAccommodationId}`
          : `/api/backend/trips/${tripId}/accommodations`,
        {
          method: editingAccommodationId ? "PATCH" : "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload),
        },
      );
      const data = await response.json().catch(() => ({}));
      if (!response.ok) {
        setError(typeof data.detail === "string" ? data.detail : "Não foi possível guardar o alojamento.");
        return;
      }
      setAccommodations((current) => editingAccommodationId
        ? current.map((item) => item.id === editingAccommodationId ? data : item)
        : [...current, data].sort((a, b) => a.check_in.localeCompare(b.check_in)));
      resetAccommodation();
      void refreshActivity();
    } catch {
      setError("Não foi possível contactar a API. Verifica a ligação e tenta novamente.");
    } finally {
      setSaving(false);
    }
  }

  function editFlight(flight: Flight) {
    setEditingFlightId(flight.id);
    setFlightForm({
      provider: flight.provider ?? "",
      origin: flight.origin,
      destination: flight.destination,
      departure_at: dateTimeInput(flight.departure_at),
      arrival_at: dateTimeInput(flight.arrival_at),
      price_amount: flight.price_amount ?? "",
      price_currency: flight.price_currency,
    });
  }

  function editAccommodation(item: Accommodation) {
    setEditingAccommodationId(item.id);
    setAccommodationForm({
      provider: item.provider ?? "",
      name: item.name,
      location: item.location,
      check_in: item.check_in,
      check_out: item.check_out,
      price_amount: item.price_amount ?? "",
      price_currency: item.price_currency,
    });
  }

  async function deleteItem(kind: "flights" | "accommodations", id: string) {
    const label = kind === "flights" ? "voo" : "alojamento";
    if (!window.confirm(`Queres mesmo eliminar este ${label}?`)) return;
    setError("");
    try {
      const response = await fetch(`/api/backend/trips/${tripId}/${kind}/${id}`, { method: "DELETE" });
      if (!response.ok) {
        const data = await response.json().catch(() => ({}));
        setError(typeof data.detail === "string" ? data.detail : `Não foi possível eliminar o ${label}.`);
        return;
      }
      if (kind === "flights") {
        setFlights((current) => current.filter((item) => item.id !== id));
        if (editingFlightId === id) resetFlight();
      } else {
        setAccommodations((current) => current.filter((item) => item.id !== id));
        if (editingAccommodationId === id) resetAccommodation();
      }
      void refreshActivity();
    } catch {
      setError("Não foi possível contactar a API. Tenta novamente.");
    }
  }

  if (loading) return <main className="dashboard-shell"><p className="notice">A carregar a viagem...</p></main>;

  return (
    <main className="dashboard-shell">
      <header className="dashboard-header">
        <Link className="brand" href="/">SKY<span>.</span></Link>
        <Link className="text-button" href="/dashboard">As minhas viagens</Link>
      </header>
      <section className="dashboard-content">
        <Link className="back-link" href="/dashboard">← Voltar às viagens</Link>
        {error && <p className="form-error" role="alert">{error}</p>}
        {trip ? (
          <>
            <p className="eyebrow">PLANEAMENTO DA VIAGEM · {accessRole === "owner" ? "PROPRIETÁRIO" : accessRole === "editor" ? "EDITOR" : "LEITOR"}</p>
            {accessRole === "viewer" && <p className="notice">Tens acesso de leitura. Podes consultar os dados e os balanços, mas não podes alterar esta viagem.</p>}
            <h1>{trip.name}</h1>
            <p className="intro dashboard-intro">{trip.destination}{trip.start_date ? ` · ${trip.start_date}` : ""}{trip.end_date ? ` — ${trip.end_date}` : ""}</p>
            {trip.notes && <p className="trip-notes">{trip.notes}</p>}
            <section className="budget-summary" aria-labelledby="trip-budget-title">
              <div>
                <p className="eyebrow">CONTROLO FINANCEIRO</p>
                <h2 id="trip-budget-title">Orçamento da viagem</h2>
                <p className="budget-description">Define o limite que pretendes gastar. O saldo é calculado apenas com custos registados na mesma moeda.</p>
              </div>
              {accessRole === "owner" && <form className="budget-editor" onSubmit={saveBudget}>
                <label>Limite de orçamento
                  <input type="number" min="0" step="0.01" value={budgetAmount} onChange={(event) => setBudgetAmount(event.target.value)} placeholder="Ex.: 1500" />
                </label>
                <label>Moeda
                  <input required minLength={3} maxLength={3} value={budgetCurrency} onChange={(event) => setBudgetCurrency(event.target.value.toUpperCase())} />
                </label>
                <button className="primary-button trip-submit" type="submit" disabled={saving}>{saving ? "A guardar..." : "Guardar orçamento"}</button>
                {trip.budget_amount !== null && (() => {
                  const spent = totalsByCurrency[trip.budget_currency] ?? 0;
                  const remaining = Math.round(Number(trip.budget_amount) * 100) - spent;
                  return (
                    <p className={remaining >= 0 ? "budget-balance" : "budget-balance budget-over"} role="status">
                      {remaining >= 0 ? "Saldo disponível: " : "Orçamento excedido em: "}
                      {(Math.abs(remaining) / 100).toLocaleString("pt-PT", { minimumFractionDigits: 2, maximumFractionDigits: 2 })} {trip.budget_currency}
                    </p>
                  );
                })()}
              </form>}
            </section>
            {budgetComparison && (
              <section className="budget-summary" aria-labelledby="budget-comparison-title">
                <div><p className="eyebrow">ORÇAMENTO VS. CUSTOS REGISTADOS</p><h2 id="budget-comparison-title">Utilização do orçamento</h2><p className="budget-description">Compara o limite definido com os custos já registados na moeda do orçamento. Não inclui estimativas de custos ainda não introduzidos.</p></div>
                <div className="budget-total-list">
                  <div className="budget-total"><span>Orçamento definido</span><strong>{(budgetComparison.budgetCents / 100).toLocaleString("pt-PT", { minimumFractionDigits: 2, maximumFractionDigits: 2 })} {trip.budget_currency}</strong></div>
                  <div className="budget-total"><span>Custos registados</span><strong>{(budgetComparison.spentCents / 100).toLocaleString("pt-PT", { minimumFractionDigits: 2, maximumFractionDigits: 2 })} {trip.budget_currency}</strong></div>
                  <div className="budget-total"><span>{budgetComparison.differenceCents >= 0 ? "Disponível" : "Acima do orçamento"}</span><strong className={budgetComparison.differenceCents >= 0 ? "budget-balance" : "budget-balance budget-over"}>{(Math.abs(budgetComparison.differenceCents) / 100).toLocaleString("pt-PT", { minimumFractionDigits: 2, maximumFractionDigits: 2 })} {trip.budget_currency}</strong></div>
                </div>
                <div className="budget-usage">
                  <div className="budget-usage-heading"><strong>{Math.round(budgetComparison.percentage)}% utilizado</strong><span>{budgetComparison.percentage > 100 ? "Limite ultrapassado" : "Do orçamento definido"}</span></div>
                  <div className="budget-usage-track" role="progressbar" aria-label="Percentagem do orçamento utilizada" aria-valuemin={0} aria-valuemax={100} aria-valuenow={Math.min(100, Math.max(0, budgetComparison.percentage))}><span className={budgetComparison.percentage > 100 ? "budget-usage-over" : ""} style={{ width: Math.min(100, Math.max(0, budgetComparison.percentage)) + "%" }} /></div>
                </div>
                {budgetComparison.otherCurrencies.length > 0 && <p className="notice">Existem também custos noutras moedas ({budgetComparison.otherCurrencies.join(", ")}), que não são incluídos nesta comparação.</p>}
              </section>
            )}
            {costForecast && costForecast.rows.length > 0 && (
              <section className="budget-summary" aria-labelledby="cost-forecast-title">
                <div><p className="eyebrow">PREVISÃO FINANCEIRA</p><h2 id="cost-forecast-title">Estimativa até ao fim da viagem</h2><p className="budget-description">Projeção dos custos conhecidos de voos e alojamentos, acrescidos da estimativa de despesas diárias. Baseia-se em {costForecast.elapsedDays} de {costForecast.totalDays} dias de viagem e nos registos até hoje. Não é uma reserva nem um custo confirmado.</p></div>
                <div className="budget-total-list">
                  {costForecast.rows.map((row) => (
                    <div className="budget-total" key={row.currency}>
                      <span>{row.currency} · {row.hasDailyData ? "estimativa total" : "custos conhecidos"}</span>
                      <strong>{(row.projectedTotal / 100).toLocaleString("pt-PT", { minimumFractionDigits: 2, maximumFractionDigits: 2 })} {row.currency}</strong>
                      <small className="budget-description">Voos e alojamentos: {(row.fixed / 100).toLocaleString("pt-PT", { minimumFractionDigits: 2, maximumFractionDigits: 2 })} {row.currency} · Despesas registadas: {(row.variable / 100).toLocaleString("pt-PT", { minimumFractionDigits: 2, maximumFractionDigits: 2 })} {row.currency} · Despesas projetadas: {(row.projectedVariable / 100).toLocaleString("pt-PT", { minimumFractionDigits: 2, maximumFractionDigits: 2 })} {row.currency}</small>
                    </div>
                  ))}
                </div>
                <p className="notice">A projeção assume que a média diária de despesas observada se mantém até ao final. Despesas fora das datas da viagem não entram no cálculo. Cada moeda é calculada separadamente.</p>
              </section>
            )}
            {(flights.length > 0 || accommodations.length > 0 || expenses.length > 0) && (
              <section className="budget-summary" aria-labelledby="budget-summary-title">
                <div>
                  <p className="eyebrow">ORÇAMENTO</p>
                  <h2 id="budget-summary-title">Resumo de custos</h2>
                  <p className="budget-description">Soma dos preços de voos e alojamentos e das despesas registadas. Os valores são apresentados separadamente por moeda. Regista em Despesas apenas custos adicionais, para não duplicares valores de voos ou alojamentos já introduzidos.</p>
                </div>
                {currencyTotals.length > 0 ? (
                  <div className="budget-total-list">
                    {currencyTotals.map(([currency, amount]) => (
                      <div className="budget-total" key={currency}>
                        <span>Total registado em {currency}</span>
                        <strong>{(amount / 100).toLocaleString("pt-PT", { minimumFractionDigits: 2, maximumFractionDigits: 2 })} {currency}</strong>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="notice">Ainda não existem preços registados.</p>
                )}
              </section>
            )}

            {Object.keys(costTypeBreakdown).length > 0 && (
              <section className="expense-breakdown" aria-labelledby="cost-type-breakdown-title">
                <div>
                  <p className="eyebrow">COMPOSIÇÃO DOS CUSTOS</p>
                  <h2 id="cost-type-breakdown-title">Onde está o orçamento</h2>
                  <p className="budget-description">Distribuição dos valores registados por tipo de custo. Cada moeda é apresentada separadamente, sem conversões cambiais.</p>
                </div>
                <div className="expense-breakdown-groups">
                  {Object.entries(costTypeBreakdown).sort(([a], [b]) => a.localeCompare(b)).map(([currency, types]) => {
                    const total = Object.values(types).reduce((sum, amount) => sum + amount, 0);
                    return (
                      <div className="expense-breakdown-group" key={currency}>
                        <div className="expense-breakdown-heading">
                          <strong>{currency}</strong>
                          <span>{(total / 100).toLocaleString("pt-PT", { minimumFractionDigits: 2, maximumFractionDigits: 2 })} {currency}</span>
                        </div>
                        {Object.entries(types).sort(([, a], [, b]) => b - a).map(([type, amount]) => (
                          <div className="expense-category-row" key={type}>
                            <div className="expense-category-label">
                              <span>{costTypeLabels[type] ?? type}</span>
                              <strong>{(amount / 100).toLocaleString("pt-PT", { minimumFractionDigits: 2, maximumFractionDigits: 2 })} {currency} · {Math.round((amount / total) * 100)}%</strong>
                            </div>
                            <div className="expense-category-track" aria-label={`${Math.round((amount / total) * 100)}% do total em ${currency}`}>
                              <span style={{ width: `${Math.max(0, Math.min(100, (amount / total) * 100))}%` }} />
                            </div>
                          </div>
                        ))}
                      </div>
                    );
                  })}
                </div>
              </section>
            )}

            {expenses.length > 0 && (
              <section className="expense-breakdown" aria-labelledby="expense-breakdown-title">
                <div>
                  <p className="eyebrow">ANÁLISE DE DESPESAS</p>
                  <h2 id="expense-breakdown-title">Onde estás a gastar</h2>
                  <p className="budget-description">Distribuição das despesas manuais por categoria. Cada moeda é analisada separadamente.</p>
                </div>
                <button className="secondary-button" type="button" onClick={exportFinancialReport} disabled={Object.keys(expenseBreakdown).length === 0 && balances.currencies.length === 0 && !budgetComparison}>Exportar relatório financeiro CSV</button>
                <div className="expense-breakdown-groups">
                  {Object.entries(expenseBreakdown).sort(([a], [b]) => a.localeCompare(b)).map(([currency, categories]) => {
                    const total = Object.values(categories).reduce((sum, amount) => sum + amount, 0);
                    return (
                      <div className="expense-breakdown-group" key={currency}>
                        <div className="expense-breakdown-heading">
                          <strong>{currency}</strong>
                          <span>{(total / 100).toLocaleString("pt-PT", { minimumFractionDigits: 2, maximumFractionDigits: 2 })} {currency}</span>
                        </div>
                        {Object.entries(categories).sort(([, a], [, b]) => b - a).map(([category, amount]) => (
                          <div className="expense-category-row" key={category}>
                            <div className="expense-category-label">
                              <span>{expenseCategoryLabels[category] ?? category}</span>
                              <strong>{(amount / 100).toLocaleString("pt-PT", { minimumFractionDigits: 2, maximumFractionDigits: 2 })} {currency}</strong>
                            </div>
                            <div className="expense-category-track" aria-label={`${Math.round((amount / total) * 100)}% do total em ${currency}`}>
                              <span style={{ width: `${Math.max(0, Math.min(100, (amount / total) * 100))}%` }} />
                            </div>
                          </div>
                        ))}
                      </div>
                    );
                  })}
                </div>
              </section>
            )}

            {Object.keys(expenseTimeline).length > 0 && (
              <section className="expense-breakdown" aria-labelledby="expense-timeline-title">
                <div><p className="eyebrow">EVOLUÇÃO TEMPORAL</p><h2 id="expense-timeline-title">Despesas por mês</h2><p className="budget-description">Evolução das despesas no período selecionado. Os meses e as moedas são apresentados separadamente.</p></div>
                <div className="expense-breakdown-groups">
                  {Object.entries(expenseTimeline).sort(([a], [b]) => a.localeCompare(b)).map(([currency, months]) => {
                    const maxAmount = Math.max(...Object.values(months));
                    return <div className="expense-breakdown-group" key={currency}>
                      <div className="expense-breakdown-heading"><strong>{currency}</strong><span>{Object.keys(months).length} meses</span></div>
                      {Object.entries(months).sort(([a], [b]) => a.localeCompare(b)).map(([month, amount]) => (
                        <div className="expense-category-row" key={month}>
                          <div className="expense-category-label"><span>{new Date(month + "-01T12:00:00").toLocaleDateString("pt-PT", { month: "long", year: "numeric" })}</span><strong>{(amount / 100).toLocaleString("pt-PT", { minimumFractionDigits: 2, maximumFractionDigits: 2 })} {currency}</strong></div>
                          <div className="expense-category-track" aria-label={(amount / 100).toFixed(2) + " " + currency + " em " + month}><span style={{ width: (maxAmount > 0 ? Math.max(0, Math.min(100, amount / maxAmount * 100)) : 0) + "%" }} /></div>
                        </div>
                      ))}
                    </div>;
                  })}
                </div>
              </section>
            )}
            <section className="participants-panel" aria-labelledby="participants-title">
              <div>
                <p className="eyebrow">VIAGEM EM GRUPO</p>
                <h2 id="participants-title">Participantes</h2>
                <p className="budget-description">Adiciona as pessoas que fazem parte desta viagem e associa-as às despesas que devem partilhar.</p>
              </div>
              {accessRole === "owner" && <form className="participant-form" onSubmit={addParticipant}>
                <label>Nome<input required minLength={2} maxLength={120} value={participantName} onChange={(event) => setParticipantName(event.target.value)} placeholder="Nome do participante" /></label>
                <label>Email (opcional)<input type="email" maxLength={320} value={participantEmail} onChange={(event) => setParticipantEmail(event.target.value)} placeholder="pessoa@exemplo.com" /></label>
                <button className="primary-button" type="submit" disabled={saving}>{saving ? "A guardar..." : "Adicionar participante"}</button>
              </form>}
              {accessRole === "owner" && <form className="participant-form" onSubmit={createInvitation}>
                <label>Convidar por email<input type="email" required maxLength={320} value={invitationEmail} onChange={(event) => setInvitationEmail(event.target.value)} placeholder="pessoa@exemplo.com" /></label>
                <label>Permissão<select value={invitationRole} onChange={(event) => setInvitationRole(event.target.value as "editor" | "viewer")}><option value="viewer">Leitor — só consulta</option><option value="editor">Editor — pode alterar dados</option></select></label>
                <button className="secondary-button" type="submit" disabled={saving}>{saving ? "A criar..." : "Criar convite"}</button>
              </form>}
              {accessRole === "owner" && invitationLink && (
                <div className="invitation-link-panel">
                  <strong>Convite criado</strong>
                  <p>{invitationEmailSent ? "O convite foi enviado por email. O link também fica disponível para partilha manual." : "O envio por email não está configurado ou falhou. Copia o link e envia-o manualmente à pessoa convidada."} O link é apresentado apenas agora.</p>
                  <input readOnly value={invitationLink} aria-label="Link do convite" />
                  <button className="secondary-button" type="button" onClick={() => void navigator.clipboard.writeText(invitationLink)}>Copiar link</button>
                </div>
              )}
              {accessRole === "owner" && invitations.length > 0 && (
                <div className="invitation-list">
                  <h3>Convites</h3>
                  {invitations.map((invitation) => (
                    <article className="participant-item" key={invitation.id}>
                      <div><strong>{invitation.email}</strong><span>{invitation.status === "pending" ? "Pendente" : invitation.status === "accepted" ? "Aceite" : invitation.status === "expired" ? "Expirado" : "Revogado"} · expira {new Date(invitation.expires_at).toLocaleDateString("pt-PT")}</span></div>
                      {invitation.status === "pending" && <button className="delete-button" type="button" onClick={() => void revokeInvitation(invitation.id)}>Revogar</button>}
                    </article>
                  ))}
                </div>
              )}
              <div className="participant-list">
                {participants.length === 0 ? <p className="notice">Ainda não foram adicionados participantes.</p> : participants.map((participant) => (
                  <article className="participant-item" key={participant.id}>
                    <div><strong>{participant.name}</strong>{participant.email && <span>{participant.email}</span>}<span>{participant.role === "editor" ? "Editor" : "Leitor"}</span></div>
                    {accessRole === "owner" && <div className="trip-action-buttons">{(participant.is_linked || invitations.some((invitation) => invitation.email.toLowerCase() === participant.email?.toLowerCase() && invitation.status === "pending")) && <label className="participant-role-control">Permissão<select value={participant.role} onChange={(event) => void updateParticipantRole(participant.id, event.target.value as "editor" | "viewer")}><option value="viewer">Leitor</option><option value="editor">Editor</option></select></label>}<button className="delete-button" type="button" onClick={() => void removeParticipant(participant.id)}>Remover</button></div>}
                  </article>
                ))}
              </div>
            </section>

            <section className="balances-panel" aria-labelledby="movement-history-title">
              <div>
                <p className="eyebrow">REGISTO CRONOLÓGICO</p>
                <h2 id="movement-history-title">Histórico de movimentos financeiros</h2>
                <p className="budget-description">Mostra despesas pagas, quotas atribuídas e transferências registadas. O saldo acumulado é reconstruído a partir dos registos atuais; alterações ou eliminações anteriores não constituem um histórico de auditoria.</p>
              </div>
              <div className="expense-filters">
                <label>Participante<select value={movementParticipant} onChange={(event) => setMovementParticipant(event.target.value)}><option value="all">Todos os participantes</option>{participants.map((participant) => <option key={participant.id} value={participant.id}>{participant.name}</option>)}</select></label>
                <label>Moeda<select value={movementCurrency} onChange={(event) => setMovementCurrency(event.target.value)}><option value="all">Todas as moedas</option>{[...new Set(financialMovements.map((movement) => movement.currency))].sort().map((currency) => <option key={currency} value={currency}>{currency}</option>)}</select></label>
                <span className="notice">{filteredFinancialMovements.length} movimentos</span>
                <button className="secondary-button" type="button" onClick={exportFinancialMovements} disabled={filteredFinancialMovements.length === 0}>Exportar movimentos CSV</button>
              </div>
              {filteredFinancialMovements.length === 0 ? <p className="notice">Ainda não existem movimentos financeiros para os filtros selecionados.</p> : (
                <div className="settlement-list">
                  {filteredFinancialMovements.map((movement) => {
                    const labels = { paid: "Despesa paga", owed: "Quota atribuída", sent: "Acerto enviado", received: "Acerto recebido" };
                    const signs = { paid: "+", owed: "−", sent: "+", received: "−" };
                    return <article className="financial-movement" key={movement.id}><div><strong>{movement.participant_name}</strong><span>{labels[movement.kind]} · {movement.description}</span><small>{new Date(movement.date).toLocaleDateString("pt-PT")}</small></div><div className="financial-movement-values"><b>{signs[movement.kind]}{movement.amount.toLocaleString("pt-PT", { minimumFractionDigits: 2, maximumFractionDigits: 2 })} {movement.currency}</b><small>Saldo acumulado: {movement.runningBalance.toLocaleString("pt-PT", { minimumFractionDigits: 2, maximumFractionDigits: 2 })} {movement.currency}</small></div></article>;
                  })}
                </div>
              )}
            </section>
            {balances.currencies.length > 0 && (
              <section className="balances-panel" aria-labelledby="balances-title">
                <div><p className="eyebrow">ACERTO DE CONTAS</p><h2 id="balances-title">Saldo entre participantes</h2><p className="budget-description">Só inclui despesas com pagador identificado e divisão guardada. Valores positivos indicam a receber; valores negativos indicam a pagar.</p></div>
                {balances.currencies.map((group) => {
                  const totalPaid = group.participants.reduce((sum, entry) => sum + Math.max(0, Number(entry.paid) || 0), 0);
                  const totalOwed = group.participants.reduce((sum, entry) => sum + Math.max(0, Number(entry.owed) || 0), 0);
                  return (
                  <div className="balance-currency" key={group.currency}>
                    <h3>{group.currency}</h3>
                    <p className="budget-description">Análise da contribuição e da quota individual. As percentagens são calculadas dentro desta moeda.</p>
                    <div className="balance-list">
                      {group.participants.map((entry) => {
                        const paid = Number(entry.paid) || 0;
                        const owed = Number(entry.owed) || 0;
                        const sent = Number(entry.settled_sent ?? "0") || 0;
                        const received = Number(entry.settled_received ?? "0") || 0;
                        const paidShare = totalPaid > 0 ? (paid / totalPaid) * 100 : 0;
                        const owedShare = totalOwed > 0 ? (owed / totalOwed) * 100 : 0;
                        return (
                        <div className="balance-row balance-analysis-row" key={entry.participant_id}>
                          <strong>{entry.name}</strong>
                          <div className="balance-analysis-metrics">
                            <span>Pagou <b>{paid.toLocaleString("pt-PT", { minimumFractionDigits: 2 })} {group.currency}</b><small>{paidShare.toLocaleString("pt-PT", { maximumFractionDigits: 1 })}% do total pago</small></span>
                            <span>Parte atribuída <b>{owed.toLocaleString("pt-PT", { minimumFractionDigits: 2 })} {group.currency}</b><small>{owedShare.toLocaleString("pt-PT", { maximumFractionDigits: 1 })}% das quotas</small></span>
                            <span>Acertos enviados <b>{sent.toLocaleString("pt-PT", { minimumFractionDigits: 2 })} {group.currency}</b></span>
                            <span>Acertos recebidos <b>{received.toLocaleString("pt-PT", { minimumFractionDigits: 2 })} {group.currency}</b></span>
                          </div>
                          <b className={Number(entry.net) >= 0 ? "balance-positive" : "balance-negative"}>{Number(entry.net) > 0 ? "A receber " : Number(entry.net) < 0 ? "A pagar " : "Saldo regularizado "}{Math.abs(Number(entry.net)).toLocaleString("pt-PT", { minimumFractionDigits: 2 })} {group.currency}</b>
                        </div>
                        );
                      })}
                    </div>
                    {group.suggested_transfers.length > 0 && (
                      <div className="settlement-list">
                        <h4>Transferências sugeridas</h4>
                        {group.suggested_transfers.map((transfer, index) => (
                          <p key={`${transfer.from_participant_id}-${transfer.to_participant_id}-${index}`}>
                            <strong>{transfer.from_name}</strong> paga <strong>{transfer.amount} {group.currency}</strong> a <strong>{transfer.to_name}</strong>
                          </p>
                        ))}
                      </div>
                    )}
                  </div>
                  );
                })}
              </section>
            )}
            {balances.currencies.length > 0 && (
              <section className="balances-panel" aria-labelledby="settlements-title">
                <div><p className="eyebrow">PAGAMENTOS REGISTADOS</p><h2 id="settlements-title">Acertos efetuados</h2><p className="budget-description">Regista transferências reais entre participantes. O saldo em aberto é recalculado automaticamente.</p></div>
                {accessRole !== "viewer" && (
                  <form className="expense-form" onSubmit={(event) => void saveSettlement(event)}>
                    <label>Moeda<select value={settlementCurrency} onChange={(event) => { setSettlementCurrency(event.target.value); setSettlementFrom(""); setSettlementTo(""); }}>{balances.currencies.map((group) => <option key={group.currency} value={group.currency}>{group.currency}</option>)}</select></label>
                    <label>Quem paga<select required value={settlementFrom} onChange={(event) => setSettlementFrom(event.target.value)}><option value="">Selecionar devedor</option>{selectedSettlementBalance?.participants.filter((entry) => Number(entry.net) < 0).map((entry) => <option key={entry.participant_id} value={entry.participant_id}>{entry.name}</option>)}</select></label>
                    <label>Quem recebe<select required value={settlementTo} onChange={(event) => setSettlementTo(event.target.value)}><option value="">Selecionar credor</option>{selectedSettlementBalance?.participants.filter((entry) => Number(entry.net) > 0).map((entry) => <option key={entry.participant_id} value={entry.participant_id}>{entry.name}</option>)}</select></label>
                    <label>Valor<input required type="number" min="0.01" step="0.01" value={settlementAmount} onChange={(event) => setSettlementAmount(event.target.value)} placeholder="0,00" /></label>
                    <label>Notas<input maxLength={1000} value={settlementNotes} onChange={(event) => setSettlementNotes(event.target.value)} placeholder="Opcional" /></label>
                    <button className="primary-button" type="submit" disabled={saving || !settlementFrom || !settlementTo || settlementFrom === settlementTo}>{saving ? "A guardar..." : "Registar pagamento"}</button>
                  </form>
                )}
                {settlements.length === 0 ? <p className="notice">Ainda não foram registados pagamentos.</p> : <div className="settlement-list">{settlements.map((item) => (
                  <p key={item.id}><strong>{participants.find((participant) => participant.id === item.from_participant_id)?.name ?? "Participante"}</strong> pagou <strong>{Number(item.amount).toLocaleString("pt-PT", { minimumFractionDigits: 2 })} {item.currency}</strong> a <strong>{participants.find((participant) => participant.id === item.to_participant_id)?.name ?? "Participante"}</strong> · {new Date(item.paid_at).toLocaleDateString("pt-PT")}{item.notes ? " · " + item.notes : ""}</p>
                ))}</div>}
              </section>
            )}
            <section className="activity-panel" aria-labelledby="activity-title">
              <div className="activity-heading">
                <div><p className="eyebrow">REGISTO DA VIAGEM</p><h2 id="activity-title">Histórico de atividade</h2><p className="budget-description">Alterações registadas nesta viagem, visíveis a todos os participantes com acesso.</p></div>
                <div className="activity-actions">
                  <button className="secondary-button" type="button" onClick={() => void exportActivity()} disabled={activityExporting || activityLoading}>
                    {activityExporting ? "A exportar..." : "Exportar CSV"}
                  </button>
                  <button className="secondary-button" type="button" onClick={() => void refreshActivity()} disabled={activityLoading || activityExporting}>
                    {activityLoading ? "A atualizar..." : "Atualizar"}
                  </button>
                </div>
              </div>
              {activityError && <p className="notice" role="alert">{activityError}</p>}
              {activity.length === 0 ? <p className="notice" aria-live="polite">{activityLoading ? "A carregar histórico..." : "Ainda não existem atividades registadas."}</p> : <ol className="activity-list" aria-live="polite">
                {activity.map((item) => <li className="activity-item" key={item.id}>
                  <span className="activity-dot" aria-hidden="true" />
                  <div><strong>{item.summary}</strong><span>{item.actor_name} · {new Date(item.created_at).toLocaleString("pt-PT", { dateStyle: "medium", timeStyle: "short" })}</span></div>
                </li>)}
              </ol>}
              {activityHasMore && <button className="secondary-button" type="button" onClick={() => void loadMoreActivity()} disabled={activityLoading}>
                {activityLoading ? "A carregar..." : "Carregar atividades anteriores"}
              </button>}
            </section>
            <div className="section-heading"><div><p className="eyebrow">GESTÃO FINANCEIRA</p><h2>Despesas</h2></div></div>
            {accessRole !== "viewer" && <form className="trip-create-form" onSubmit={saveExpense}>
              <h3>{editingExpenseId ? "Editar despesa" : "Registar despesa"}</h3>
              <div className="trip-form-grid">
                <label>Categoria<select value={expenseForm.category} onChange={(e) => setExpenseForm({ ...expenseForm, category: e.target.value })}>{Object.entries(expenseCategoryLabels).map(([value, label]) => <option value={value} key={value}>{label}</option>)}</select></label>
                <label>Descrição<input required minLength={2} maxLength={180} value={expenseForm.description} onChange={(e) => setExpenseForm({ ...expenseForm, description: e.target.value })} placeholder="Ex.: Jantar" /></label>
                <label>Data<input required type="date" value={expenseForm.expense_date} onChange={(e) => setExpenseForm({ ...expenseForm, expense_date: e.target.value })} /></label>
                <label>Valor<input required type="number" min="0.01" step="0.01" value={expenseForm.amount} onChange={(e) => setExpenseForm({ ...expenseForm, amount: e.target.value })} placeholder="0,00" /></label>
                <label>Moeda<input required minLength={3} maxLength={3} value={expenseForm.currency} onChange={(e) => setExpenseForm({ ...expenseForm, currency: e.target.value.toUpperCase() })} /></label>
                <label>Pago por<select value={expenseForm.paid_by_participant_id} onChange={(e) => setExpenseForm({ ...expenseForm, paid_by_participant_id: e.target.value })}><option value="">Não indicado</option>{participants.map((participant) => <option key={participant.id} value={participant.id}>{participant.name}</option>)}</select></label>
                <label>Notas<input maxLength={2000} value={expenseForm.notes} onChange={(e) => setExpenseForm({ ...expenseForm, notes: e.target.value })} placeholder="Opcional" /></label>
              </div>
              <div className="trip-form-actions">
                <button className="primary-button trip-submit" type="submit" disabled={saving}>{saving ? "A guardar..." : editingExpenseId ? "Guardar alterações" : "Registar despesa"}</button>
                {editingExpenseId && <button className="secondary-button" type="button" onClick={() => { setEditingExpenseId(null); setExpenseForm(emptyExpense); }}>Cancelar</button>}
              </div>
            </form>}
            <div className="expense-filters" aria-label="Filtrar despesas por data">
              <label>Data inicial<input type="date" value={expenseDateFrom} max={expenseDateTo || undefined} onChange={(event) => setExpenseDateFrom(event.target.value)} /></label>
              <label>Data final<input type="date" value={expenseDateTo} min={expenseDateFrom || undefined} onChange={(event) => setExpenseDateTo(event.target.value)} /></label>
              <div><span className="notice">{filteredExpenses.length} de {expenses.length} despesas</span><button className="secondary-button" type="button" onClick={() => { setExpenseDateFrom(""); setExpenseDateTo(""); }} disabled={!expenseDateFrom && !expenseDateTo}>Limpar datas</button></div>
            </div>
            <div className="trip-list">
              {expenses.length === 0 ? <div className="empty-state"><p>Ainda não existem despesas registadas nesta viagem.</p></div> : filteredExpenses.length === 0 ? <div className="empty-state"><p>Não existem despesas no período selecionado.</p></div> : filteredExpenses.map((item) => (
                <article className="trip-card" key={item.id}>
                  <div><h3>{item.description}</h3><p>{expenseCategoryLabels[item.category] ?? item.category} · {new Date(item.expense_date + "T12:00:00").toLocaleDateString("pt-PT")}</p>{item.paid_by_participant_id && <p>Pago por: {participants.find((participant) => participant.id === item.paid_by_participant_id)?.name ?? "Participante"}</p>}{item.notes && <p>{item.notes}</p>}</div>
                  <div className="trip-card-actions"><strong>{Number(item.amount).toLocaleString("pt-PT", { minimumFractionDigits: 2, maximumFractionDigits: 2 })} {item.currency}</strong><div className="trip-action-buttons">{accessRole !== "viewer" && <><button className="edit-button" type="button" onClick={() => editExpense(item)}>Editar</button><button className="delete-button" type="button" onClick={() => void deleteExpense(item.id)}>Eliminar</button></>}</div>{accessRole !== "viewer" && <button className="secondary-button" type="button" onClick={() => void openExpenseShares(item)}>{activeShareExpenseId === item.id ? "Fechar divisão" : "Dividir despesa"}</button>}</div>
                  {activeShareExpenseId === item.id && (
                    <form className="expense-share-editor" onSubmit={(event) => void saveExpenseShares(event, item.id)}>
                      <div><strong>Divisão de {item.description}</strong><p className="budget-description">A soma das partes tem de corresponder a {Number(item.amount).toLocaleString("pt-PT", { minimumFractionDigits: 2, maximumFractionDigits: 2 })} {item.currency}.</p></div>
                      {participants.length === 0 ? <p className="notice">Adiciona participantes à viagem para poderes dividir esta despesa.</p> : (
                        <>
                          <div className="expense-share-fields">
                            {participants.map((participant) => (
                              <label key={participant.id}>{participant.name}
                                <input type="number" min="0" step="0.01" value={shareDraft[participant.id] ?? ""} onChange={(event) => setShareDraft((current) => ({ ...current, [participant.id]: event.target.value }))} placeholder="0,00" />
                              </label>
                            ))}
                          </div>
                          <div className="trip-form-actions">
                            <button className="secondary-button" type="button" onClick={() => splitExpenseEqually(item)}>Dividir igualmente</button>
                            <button className="primary-button" type="submit" disabled={saving}>{saving ? "A guardar..." : "Guardar divisão"}</button>
                          </div>
                        </>
                      )}
                    </form>
                  )}
                </article>
              ))}
            </div>

            <FlightSearchPanel
              tripId={tripId}
              canEdit={accessRole !== "viewer"}
              onFlightsSaved={(saved) => {
                setFlights((current) => [...current, ...saved].sort((a, b) => a.departure_at.localeCompare(b.departure_at)));
                void refreshActivity();
              }}
            />

            <div className="section-heading"><div><p className="eyebrow">TRANSPORTE</p><h2>Voos</h2></div></div>
            {accessRole !== "viewer" && <form className="trip-create-form" onSubmit={saveFlight}>
              <h3>{editingFlightId ? "Editar voo" : "Adicionar voo"}</h3>
              <div className="trip-form-grid">
                <label>Companhia / fornecedor<input maxLength={80} value={flightForm.provider} onChange={(e) => setFlightForm({ ...flightForm, provider: e.target.value })} placeholder="Opcional" /></label>
                <label>Origem (IATA)<input required minLength={3} maxLength={3} value={flightForm.origin} onChange={(e) => setFlightForm({ ...flightForm, origin: e.target.value.toUpperCase() })} placeholder="OPO" /></label>
                <label>Destino (IATA)<input required minLength={3} maxLength={3} value={flightForm.destination} onChange={(e) => setFlightForm({ ...flightForm, destination: e.target.value.toUpperCase() })} placeholder="LIS" /></label>
                <label>Partida<input required type="datetime-local" value={flightForm.departure_at} onChange={(e) => setFlightForm({ ...flightForm, departure_at: e.target.value })} /></label>
                <label>Chegada<input type="datetime-local" min={flightForm.departure_at || undefined} value={flightForm.arrival_at} onChange={(e) => setFlightForm({ ...flightForm, arrival_at: e.target.value })} /></label>
                <label>Preço<input type="number" min="0.01" step="0.01" value={flightForm.price_amount} onChange={(e) => setFlightForm({ ...flightForm, price_amount: e.target.value })} placeholder="Opcional" /></label>
                <label>Moeda<input required minLength={3} maxLength={3} value={flightForm.price_currency} onChange={(e) => setFlightForm({ ...flightForm, price_currency: e.target.value.toUpperCase() })} /></label>
              </div>
              <div className="trip-form-actions">
                <button className="primary-button trip-submit" type="submit" disabled={saving}>{saving ? "A guardar..." : editingFlightId ? "Guardar alterações" : "Adicionar voo"}</button>
                {editingFlightId && <button className="secondary-button" type="button" onClick={resetFlight}>Cancelar</button>}
              </div>
            </form>}
            <div className="trip-list">
              {flights.length === 0 ? <div className="empty-state"><p>Ainda não existem voos associados a esta viagem.</p></div> : flights.map((flight) => (
                <article className="trip-card" key={flight.id}>
                  <div><h3>{flight.origin} → {flight.destination}</h3><p>{flight.provider || "Companhia por definir"} · {new Date(flight.departure_at).toLocaleString("pt-PT")}</p></div>
                  <div className="trip-card-actions"><span>{flight.price_amount ? `${flight.price_amount} ${flight.price_currency}` : "Preço por definir"}</span>{accessRole !== "viewer" && <div className="trip-action-buttons"><button className="edit-button" type="button" onClick={() => editFlight(flight)}>Editar</button><button className="delete-button" type="button" onClick={() => void deleteItem("flights", flight.id)}>Eliminar</button></div>}</div>
                </article>
              ))}
            </div>

            <div className="section-heading"><div><p className="eyebrow">ESTADIA</p><h2>Alojamentos</h2></div></div>
            <HotelSearchPanel
              tripId={tripId}
              canEdit={accessRole !== "viewer"}
              onAccommodationSaved={(accommodation) => {
                setAccommodations((current) => [...current, accommodation].sort((a, b) => a.check_in.localeCompare(b.check_in)));
                void refreshActivity();
              }}
            />
            {accessRole !== "viewer" && <form className="trip-create-form" onSubmit={saveAccommodation}>
              <h3>{editingAccommodationId ? "Editar alojamento" : "Adicionar alojamento"}</h3>
              <div className="trip-form-grid">
                <label>Nome<input required minLength={2} maxLength={180} value={accommodationForm.name} onChange={(e) => setAccommodationForm({ ...accommodationForm, name: e.target.value })} placeholder="Nome do hotel ou alojamento" /></label>
                <label>Localização<input required minLength={2} maxLength={180} value={accommodationForm.location} onChange={(e) => setAccommodationForm({ ...accommodationForm, location: e.target.value })} placeholder="Cidade ou morada" /></label>
                <label>Fornecedor<input maxLength={80} value={accommodationForm.provider} onChange={(e) => setAccommodationForm({ ...accommodationForm, provider: e.target.value })} placeholder="Opcional" /></label>
                <label>Check-in<input required type="date" value={accommodationForm.check_in} onChange={(e) => setAccommodationForm({ ...accommodationForm, check_in: e.target.value })} /></label>
                <label>Check-out<input required type="date" min={accommodationForm.check_in || undefined} value={accommodationForm.check_out} onChange={(e) => setAccommodationForm({ ...accommodationForm, check_out: e.target.value })} /></label>
                <label>Preço total<input type="number" min="0.01" step="0.01" value={accommodationForm.price_amount} onChange={(e) => setAccommodationForm({ ...accommodationForm, price_amount: e.target.value })} placeholder="Opcional" /></label>
                <label>Moeda<input required minLength={3} maxLength={3} value={accommodationForm.price_currency} onChange={(e) => setAccommodationForm({ ...accommodationForm, price_currency: e.target.value.toUpperCase() })} /></label>
              </div>
              <div className="trip-form-actions">
                <button className="primary-button trip-submit" type="submit" disabled={saving}>{saving ? "A guardar..." : editingAccommodationId ? "Guardar alterações" : "Adicionar alojamento"}</button>
                {editingAccommodationId && <button className="secondary-button" type="button" onClick={resetAccommodation}>Cancelar</button>}
              </div>
            </form>}
            {accommodations.length > 0 && (
              <section className="trip-create-form accommodation-filters" aria-label="Filtrar alojamentos guardados">
                <h3>Filtrar alojamentos</h3>
                <div className="trip-form-grid">
                  <label>Check-in a partir de<input type="date" value={accommodationFrom} max={accommodationTo || undefined} onChange={(event) => setAccommodationFrom(event.target.value)} /></label>
                  <label>Check-in até<input type="date" value={accommodationTo} min={accommodationFrom || undefined} onChange={(event) => setAccommodationTo(event.target.value)} /></label>
                  <label>Preço máximo total<input type="number" min="0.01" step="0.01" value={accommodationMaxPrice} onChange={(event) => setAccommodationMaxPrice(event.target.value)} placeholder="Sem limite" /></label>
                </div>
                <div className="trip-form-actions">
                  <p className="budget-description" role="status">{filteredAccommodations.length} de {accommodations.length} alojamentos. O filtro de preço mostra apenas alojamentos com preço registado.</p>
                  <button className="secondary-button" type="button" onClick={() => { setAccommodationFrom(""); setAccommodationTo(""); setAccommodationMaxPrice(""); }}>Limpar filtros</button>
                </div>
              </section>
            )}
            <div className="trip-list">
              {accommodations.length === 0 ? <div className="empty-state"><p>Ainda não existem alojamentos associados a esta viagem.</p></div> : filteredAccommodations.length === 0 ? <div className="empty-state"><p>Não existem alojamentos que correspondam aos filtros. Ajusta os critérios ou limpa os filtros.</p></div> : filteredAccommodations.map((item) => (
                <article className="trip-card" key={item.id}>
                  <div>
                    <h3>{item.name}</h3>
                    <p>{item.location} · {item.check_in} — {item.check_out}</p>
                    {item.provider && <p>Fornecedor: {item.provider}</p>}
                    {accommodationNights(item.check_in, item.check_out) !== null && <p>{accommodationNights(item.check_in, item.check_out)} {accommodationNights(item.check_in, item.check_out) === 1 ? "noite" : "noites"}</p>}
                  </div>
                  <div className="trip-card-actions">
                    <span>
                      {item.price_amount !== null && Number.isFinite(Number(item.price_amount))
                        ? `${Number(item.price_amount).toLocaleString("pt-PT", { minimumFractionDigits: 2, maximumFractionDigits: 2 })} ${item.price_currency}`
                        : "Preço por definir"}
                      {item.price_amount !== null && accommodationNights(item.check_in, item.check_out) !== null && (
                        <small className="accommodation-nightly-price">
                          Média: {(Number(item.price_amount) / accommodationNights(item.check_in, item.check_out)!).toLocaleString("pt-PT", { minimumFractionDigits: 2, maximumFractionDigits: 2 })} {item.price_currency}/noite
                        </small>
                      )}
                    </span>
                    {accessRole !== "viewer" && <div className="trip-action-buttons"><button className="edit-button" type="button" onClick={() => editAccommodation(item)}>Editar</button><button className="delete-button" type="button" onClick={() => void deleteItem("accommodations", item.id)}>Eliminar</button></div>}
                  </div>
                </article>
              ))}
            </div>
          </>
        ) : <div className="empty-state"><h2>Viagem não encontrada</h2><p>Não foi possível encontrar esta viagem ou não tens acesso a ela.</p><Link href="/dashboard">Voltar ao dashboard</Link></div>}
      </section>
    </main>
  );
}
