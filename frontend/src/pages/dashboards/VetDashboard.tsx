/**
 * Veterinary Officer dashboard.
 * Place in: src/pages/dashboards/VetDashboard.tsx
 * Data: GET dashboard/vet/
 */
import { useCallback, useEffect, useState } from "react";
import API from "../../services/api";
import {
  BarCard,
  DashboardFooter,
  DashboardHeader,
  DonutCard,
  ErrorAlert,
  KpiGrid,
  ListCard,
  StatusBarCard,
  chartData,
  listItems,
} from "./Dashboardshared";
import type { KpiTile } from "./Dashboardshared";

const ROW_ONE: KpiTile[] = [
  { key: "open_cases", label: "Open Cases", icon: "ti-clipboard-check", color: "#DC2626" },
  { key: "visits", label: "Farm Visits", icon: "ti-map-pin", color: "#0092E4", compare: true },
  { key: "treatments_given", label: "Treatments Given", icon: "ti-pill", color: "#8B5CF6", compare: true },
  { key: "revenue", label: "Revenue", icon: "ti-currency-dollar", color: "#E41F07", format: "currency", compare: true },
];

const ROW_TWO: KpiTile[] = [
  { key: "farms_served", label: "Farms Served", icon: "ti-home", color: "#10B981" },
  { key: "vaccinations_done", label: "Vaccinations Done", icon: "ti-vaccine", color: "#10B981", compare: true },
  { key: "pending_requests", label: "Pending Requests", icon: "ti-bell", color: "#F59E0B" },
  { key: "follow_ups_due", label: "Follow-ups Due (7 days)", icon: "ti-calendar-due", color: "#FFA201" },
];

const VetDashboard = () => {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const reload = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      // No query params: the backend does all the filtering.
      const res = await API.get("dashboard/vet/");
      if (res.data?.status === "success") {
        setData(res.data);
      } else {
        setData(null);
        setError(res.data?.message || "Could not load dashboard data.");
      }
    } catch (e: any) {
      setData(null);
      if (e?.response?.status === 404) {
        setError('The dashboard endpoint "dashboard/vet/" was not found on the server.');
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
  }, []);

  useEffect(() => {
    reload();
  }, [reload]);

  const compareLabel: string = data?.compare_label ?? "";

  const visits = chartData(data, "visits_trend");
  const conditions = chartData(data, "cases_by_condition");
  const revenue = chartData(data, "revenue_trend");
  const status = chartData(data, "case_status");

  return (
    <div className="page-wrapper">
      <div className="content pb-0">
        <DashboardHeader
          title="Veterinary Dashboard"
          subtitle="Your caseload, treatments and farm visits"
          onRefresh={reload}
        />

        {error && <ErrorAlert message={error} />}

        <KpiGrid tiles={ROW_ONE} kpis={data?.kpis} loading={loading} compareLabel={compareLabel} />
        <KpiGrid tiles={ROW_TWO} kpis={data?.kpis} loading={loading} compareLabel={compareLabel} />

        {!loading && data && (
          <>
            <div className="row g-3 mb-4">
              <div className="col-lg-8 d-flex">
                <BarCard
                  title="Farm Visits"
                  labels={visits.labels}
                  values={visits.values}
                  color="#0092E4"
                  seriesName="Visits"
                />
              </div>
              <div className="col-lg-4 d-flex">
                <DonutCard
                  title="Cases by Condition"
                  labels={conditions.labels}
                  values={conditions.values}
                />
              </div>
            </div>

            <div className="row g-3 mb-4">
              <div className="col-lg-8 d-flex">
                <BarCard
                  title="Revenue"
                  labels={revenue.labels}
                  values={revenue.values}
                  color="#E41F07"
                  format="currency"
                  seriesName="Revenue"
                />
              </div>
              <div className="col-lg-4 d-flex">
                <StatusBarCard title="Case Status" items={status.points} />
              </div>
            </div>
          </>
        )}

        <div className="row">
          <div className="col-xl-4 col-12 d-flex">
            <ListCard
              title="Pending Service Requests"
              items={listItems(data, "pending_requests")}
              empty="No pending requests."
              loading={loading}
            />
          </div>
          <div className="col-xl-4 col-12 d-flex">
            <ListCard
              title="Follow-ups Due"
              items={listItems(data, "follow_ups_due")}
              empty="No follow-ups due."
              loading={loading}
            />
          </div>
          <div className="col-xl-4 col-12 d-flex">
            <ListCard
              title="Recent Cases"
              items={listItems(data, "recent_cases")}
              empty="No cases in this period."
              loading={loading}
              valueFormat="currency"
            />
          </div>
        </div>
      </div>

      <DashboardFooter />
    </div>
  );
};

export default VetDashboard;
