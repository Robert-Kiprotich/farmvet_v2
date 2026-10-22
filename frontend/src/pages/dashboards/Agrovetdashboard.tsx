/**
 * Agrovet dashboard: your original POS dashboard (sales, stock, payments),
 * rebuilt on the shared components.
 * Place in: src/pages/dashboards/AgrovetDashboard.tsx
 */
import { all_routes } from "../../routes/all_routes";
import {
  BarCard,
  COMPARE_LABEL,
  DashboardFooter,
  DashboardHeader,
  DonutCard,
  ErrorAlert,
  ListCard,
  PERIOD_PREFIX,
  StatCard,
  currency,
  formatValue,
  pctBadge,
} from "./Dashboardshared";

const paymentColors = [
  "bg-success",
  "bg-secondary",
  "bg-purple",
  "bg-danger",
  "bg-info",
  "bg-warning",
];

const AgrovetDashboard = () => {
  // Same endpoint your original dashboard used
  const { data: d, loading, error, reload, rangeType } =
    useDashboard("admin-dashboard/");

  const compareLabel = COMPARE_LABEL[rangeType] ?? "vs prior period";
  const prefix = PERIOD_PREFIX[rangeType] ?? "";

  const paymentBreakdown: any[] = d?.payment_breakdown ?? [];
  const paymentTotal =
    paymentBreakdown.reduce((s: number, p: any) => s + p.amount, 0) || 1;

  const tiles = [
    {
      label: `${prefix}Sales`,
      value: currency(d?.sales?.total),
      icon: "ti-currency-dollar",
      color: "#E41F07",
      change: d?.sales?.change_pct ?? 0,
    },
    {
      label: `${prefix}Orders`,
      value: formatValue(d?.orders?.total),
      icon: "ti-receipt",
      color: "#FFA201",
      change: d?.orders?.change_pct ?? 0,
    },
    {
      label: `${prefix}Profit`,
      value: currency(d?.profit?.total),
      icon: "ti-trending-up",
      color: "#10B981",
      change: d?.profit?.change_pct ?? 0,
    },
    {
      label: "Items Sold",
      value: formatValue(d?.items_sold?.total),
      icon: "ti-package",
      color: "#0092E4",
      change: d?.items_sold?.change_pct ?? 0,
    },
    {
      label: "Low Stock Items",
      value: formatValue(d?.low_stock?.total),
      icon: "ti-alert-triangle",
      color: "#DC2626",
      note: "Below minimum",
    },
    {
      label: "Total Customers",
      value: formatValue(d?.customers?.total),
      icon: "ti-users",
      color: "#8B5CF6",
      change: d?.customers?.change_pct ?? 0,
    },
    {
      label: "Outstanding Payments",
      value: currency(d?.outstanding_payments?.total),
      icon: "ti-file-invoice",
      color: "#F59E0B",
      note: `${d?.outstanding_payments?.count ?? 0} unpaid/credit sales`,
    },
    {
      label: "Cash in Till",
      value: currency(d?.cash_in_till?.total),
      icon: "ti-cash",
      color: "#10B981",
      note: `As of ${d?.cash_in_till?.as_of ?? "now"}`,
    },
  ];

  return (
    <div className="page-wrapper">
      <div className="content pb-0">
        <DashboardHeader
          title="Agrovet Dashboard"
          subtitle="Sales, stock and payments for your shop"
          onRefresh={reload}
        />

        {error && <ErrorAlert message={error} />}

        {/* ── KPI tiles ─────────────────────────────────────────────── */}
        <div className="row g-3 mb-4">
          {tiles.map((t) => (
            <div className="col-xl-3 col-sm-6 d-flex" key={t.label}>
              <StatCard
                label={t.label}
                value={t.value}
                icon={t.icon}
                color={t.color}
                loading={loading}
                change={t.change}
                compareLabel={compareLabel}
                note={t.note}
              />
            </div>
          ))}
        </div>

        {/* ── Charts ────────────────────────────────────────────────── */}
        {!loading && d && (
          <div className="row g-3 mb-4">
            <div className="col-lg-6 d-flex">
              <BarCard
                title="Sales Trend"
                labels={(d?.sales_trend ?? []).map((p: any) => p.date)}
                values={(d?.sales_trend ?? []).map((p: any) => p.amount)}
                color="#E41F07"
                format="currency"
                seriesName="Sales"
              />
            </div>
            <div className="col-lg-6 d-flex">
              <DonutCard
                title="Payments by Method"
                labels={paymentBreakdown.map((s: any) => s.method)}
                values={paymentBreakdown.map((s: any) => s.amount)}
                format="currency"
              />
            </div>
          </div>
        )}

        {/* ── Lists ─────────────────────────────────────────────────── */}
        <div className="row">
          <div className="col-xxl-4 col-xl-12 d-flex">
            <ListCard
              title="Top Selling Products"
              loading={loading}
              empty="No sales in this period."
              link={all_routes.sales}
              items={(d?.top_products ?? []).map((p: any) => ({
                title: p.name,
                subtitle: `${p.quantity_sold} sold · ${currency(p.revenue)}`,
              }))}
            />
          </div>

          <div className="col-xxl-4 col-xl-6 d-flex">
            <ListCard
              title="Low Stock Items"
              loading={loading}
              empty="All items are sufficiently stocked."
              link={all_routes.products}
              items={(d?.low_stock?.items ?? []).map((item: any) => ({
                title: item.name,
                value: `${item.quantity} left`,
              }))}
            />
          </div>

          {/* Payments overview with stacked bar */}
          <div className="col-xxl-4 col-xl-6 d-flex">
            <div className="card flex-fill">
              <div className="card-body">
                <div className="d-flex align-items-center justify-content-between flex-wrap gap-2 mb-3">
                  <h5 className="mb-0 fs-16 fw-bold d-inline-flex items-center">
                    <span className="line-title d-block me-2" />
                    Payments Overview
                  </h5>
                </div>

                {loading && (
                  <div className="text-muted fs-13 py-3">
                    <span className="spinner-border spinner-border-sm me-2" />
                    Loading...
                  </div>
                )}

                {!loading && d && (
                  <>
                    <div className="progress-stacked progress-md bg-white gap-1 mb-3">
                      {paymentBreakdown.slice(0, 4).map((p: any, i: number) => (
                        <div
                          key={p.method}
                          className={`progress-bar ${paymentColors[i]} rounded overflow-hidden`}
                          role="progressbar"
                          style={{
                            width: `${Math.round((p.amount / paymentTotal) * 100)}%`,
                          }}
                        />
                      ))}
                    </div>

                    <div className="mb-4">
                      <div className="d-flex align-items-center gap-2 flex-wrap mb-3">
                        <h4 className="mb-0">{currency(d.sales?.total)}</h4>
                        {pctBadge(d.sales?.change_pct ?? 0)}
                        <p className="mb-0">{compareLabel}</p>
                      </div>

                      {paymentBreakdown.map((item: any, i: number) => (
                        <div
                          key={item.method}
                          className={`p-2 d-flex align-items-center justify-content-between ${
                            i < paymentBreakdown.length - 1 ? "border-bottom" : ""
                          }`}
                        >
                          <p className="text-dark d-flex align-items-center mb-0">
                            <i
                              className={`ti ti-circle-filled ${
                                paymentColors[i]?.replace("bg-", "text-") ??
                                "text-muted"
                              } fs-8 me-1`}
                            />
                            {item.method}
                          </p>
                          <p className="text-dark mb-0">{currency(item.amount)}</p>
                        </div>
                      ))}
                    </div>

                    <div className="p-3 border rounded bg-light d-flex align-items-center justify-content-between">
                      <div>
                        <p className="mb-1">Outstanding</p>
                        <h4 className="mb-0">
                          {currency(d.outstanding_payments?.total)}
                        </h4>
                      </div>
                      <div>
                        <p className="mb-1">Cash in Till</p>
                        <h4 className="mb-0">{currency(d.cash_in_till?.total)}</h4>
                      </div>
                    </div>
                  </>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>

      <DashboardFooter />
    </div>
  );
};

export default AgrovetDashboard;
