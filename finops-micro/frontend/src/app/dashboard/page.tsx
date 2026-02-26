"use client";

import { useEffect, useMemo, useState } from "react";

import { CostTimeseriesChart } from "@/components/charts/cost-timeseries-chart";
import { KpiCard } from "@/components/kpi-card";
import { fetchSummary, fetchTimeseries } from "@/lib/api";
import { SummaryResponse, TimeseriesResponse } from "@/lib/types";

function formatMoney(value: number): string {
  return new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" }).format(value);
}

function defaultRange() {
  const end = new Date();
  const start = new Date(end.getFullYear(), 0, 1);
  return {
    start: start.toISOString().slice(0, 10),
    end: end.toISOString().slice(0, 10),
  };
}

export default function DashboardPage() {
  const range = useMemo(() => defaultRange(), []);
  const [cloud, setCloud] = useState("all");
  const [start, setStart] = useState(range.start);
  const [end, setEnd] = useState(range.end);
  const [summary, setSummary] = useState<SummaryResponse | null>(null);
  const [timeseries, setTimeseries] = useState<TimeseriesResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function loadData() {
    setLoading(true);
    setError(null);
    try {
      const query = { cloud, start, end };
      const [summaryData, seriesData] = await Promise.all([
        fetchSummary(query),
        fetchTimeseries(query),
      ]);
      setSummary(summaryData);
      setTimeseries(seriesData);
    } catch (err) {
      const message = err instanceof Error ? err.message : "Falha ao carregar dados";
      setError(message);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void loadData();
    // Carga inicial do dashboard dispara ingestao automatica no backend.
  }, []);

  return (
    <main className="container">
      <h1 style={{ marginBottom: 8 }}>Dashboard FinOps</h1>
      <p style={{ marginTop: 0, color: "var(--muted)" }}>MVP multicloud REST (aws/azure/oci)</p>

      <section className="panel" style={{ padding: "1rem", marginBottom: "1rem", display: "grid", gap: "0.75rem" }}>
        <div style={{ display: "grid", gap: "0.75rem", gridTemplateColumns: "repeat(auto-fit, minmax(160px, 1fr))" }}>
          <label>
            Cloud
            <select value={cloud} onChange={(e) => setCloud(e.target.value)} style={{ width: "100%" }}>
              <option value="all">all</option>
              <option value="aws">aws</option>
              <option value="azure">azure</option>
              <option value="oci">oci</option>
            </select>
          </label>
          <label>
            Start
            <input type="date" value={start} onChange={(e) => setStart(e.target.value)} style={{ width: "100%" }} />
          </label>
          <label>
            End
            <input type="date" value={end} onChange={(e) => setEnd(e.target.value)} style={{ width: "100%" }} />
          </label>
          <button onClick={loadData} disabled={loading} style={{ alignSelf: "end", height: 34 }}>
            {loading ? "Carregando..." : "Atualizar"}
          </button>
        </div>
        {error ? <small style={{ color: "var(--danger)" }}>{error}</small> : null}
      </section>

      <section style={{ display: "grid", gap: "1rem", gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))", marginBottom: "1rem" }}>
        <KpiCard title="Total no período" value={formatMoney(summary?.total_current ?? 0)} />
        <KpiCard
          title="Delta vs período anterior"
          value={formatMoney(summary?.delta.absolute ?? 0)}
          detail={
            summary?.delta.percent != null
              ? `${summary.delta.percent.toFixed(2)}%`
              : "Sem base anterior"
          }
        />
        <KpiCard
          title="Top Service"
          value={summary?.top_services[0]?.name ?? "-"}
          detail={summary?.top_services[0] ? formatMoney(summary.top_services[0].total) : undefined}
        />
        <KpiCard
          title="Top Scope"
          value={summary?.top_scopes[0]?.name ?? "-"}
          detail={summary?.top_scopes[0] ? formatMoney(summary.top_scopes[0].total) : undefined}
        />
      </section>

      <section>
        <CostTimeseriesChart points={timeseries?.points ?? []} />
      </section>
    </main>
  );
}
