/**
 * Renders any role's dashboard from its config.
 * Place in: src/pages/dashboards/RoleDashboard.tsx
 *
 * Data is fetched straight from config.endpoint with no query params.
 * Any filtering (date range, branch, user...) is done by the backend.
 */
import { useCallback, useEffect, useState } from "react";
import API from "../../services/api";
import {
  BarCard,
  DashboardFooter,
  DashboardHeader,
  DonutCard,
  ErrorAlert,
  ListCard,
  StatCard,
  formatValue,
} from "./Dashboardshared";
import type { ListItem } from "./Dashboardshared";
import { DASHBOARD_CONFIGS } from "./Dashboardconfig";
import type { RoleKey } from "./Dashboardconfig";

const RoleDashboard = ({ roleKey }: { roleKey: RoleKey }) => {
  const config = DASHBOARD_CONFIGS[roleKey];

  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const reload = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await API.get(config.endpoint);

      if (res.data?.status === "success") {
        setData(res.data);
      } else {
        setData(null);
        setError(res.data?.message || "Could not load dashboard data.");
      }
    } catch (e: any) {
      setData(null);
      if (e?.response?.status === 404) {
        setError(`The dashboard endpoint "${config.endpoint}" was not found on the server.`);
      } else {
        setError(
          e?.response?.data?.message ||
            e?.response?.data?.detail ||
            "Could not load dashboard data."
        );
      }
    } finally {
      setLoading(false);
    }
  }, [config.endpoint]);

  useEffect(() => {
    reload();
  }, [reload]);

  // Optional: let the backend send e.g. "vs previous month" as `compare_label`.
  const compareLabel: string = data?.compare_label ?? "";

  return (
    <div className="page-wrapper">
      <div className="content pb-0">
        <DashboardHeader
          title={config.title}
          subtitle={config.subtitle}
          onRefresh={reload}
        />

        {error && <ErrorAlert message={error} />}

        {/* ── KPI tiles ───────────────────────────────────────────────── */}
        <div className="row g-3 mb-4">
          {config.kpis.map((kpi) => {
            const item = data?.kpis?.[kpi.key];
            return (
              <div className="col-xl-3 col-sm-6 d-flex" key={kpi.key}>
                <StatCard
                  label={kpi.label}
                  value={formatValue(item?.value, kpi.format ?? "number")}
                  icon={kpi.icon}
                  color={kpi.color}
                  loading={loading}
                  change={kpi.compare ? item?.change_pct : null}
                  compareLabel={compareLabel}
                  note={item?.note}
                />
              </div>
            );
          })}
        </div>

        {/* ── Charts ──────────────────────────────────────────────────── */}
        {!loading && data && config.charts.length > 0 && (
          <div className="row g-3 mb-4">
            {config.charts.map((chart) => {
              const points: { label: string; value: number }[] =
                data?.charts?.[chart.key] ?? [];
              const labels = points.map((p) => String(p.label));
              const values = points.map((p) => Number(p.value));

              return (
                <div
                  className={`col-lg-${chart.span ?? 6} d-flex`}
                  key={chart.key}
                >
                  {chart.type === "bar" ? (
                    <BarCard
                      title={chart.title}
                      labels={labels}
                      values={values}
                      color={chart.color}
                      format={chart.format}
                    />
                  ) : (
                    <DonutCard
                      title={chart.title}
                      labels={labels}
                      values={values}
                      format={chart.format}
                    />
                  )}
                </div>
              );
            })}
          </div>
        )}

        {/* ── Lists ───────────────────────────────────────────────────── */}
        {config.lists.length > 0 && (
          <div className="row">
            {config.lists.map((list) => {
              const items: ListItem[] = data?.lists?.[list.key] ?? [];
              return (
                <div
                  className={`col-xl-${list.span ?? 6} col-12 d-flex`}
                  key={list.key}
                >
                  <ListCard
                    title={list.title}
                    items={items}
                    empty={list.empty}
                    loading={loading}
                    valueFormat={list.valueFormat}
                  />
                </div>
              );
            })}
          </div>
        )}
      </div>

      <DashboardFooter />
    </div>
  );
};

export default RoleDashboard;
