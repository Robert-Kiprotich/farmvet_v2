/**
 * Shared building blocks for all dashboards.
 * Place in: src/pages/dashboards/dashboardShared.tsx
 */
import { Link } from "react-router";
import Chart from "react-apexcharts";
import type { ApexOptions } from "apexcharts";

// ─────────────────────────────────────────────────────────────────────────────
// Formatting
// ─────────────────────────────────────────────────────────────────────────────

export type ValueFormat = "number" | "currency" | "percent" | "text";

export const PALETTE = [
  "#E41F07",
  "#FFA201",
  "#0092E4",
  "#10B981",
  "#8B5CF6",
  "#FF6B9D",
];

export const currency = (value: number | undefined | null): string => {
  if (value == null) return "—";
  return new Intl.NumberFormat("en-KE", {
    style: "currency",
    currency: "KES",
    maximumFractionDigits: 0,
  }).format(value);
};

export const formatValue = (value: any, format: ValueFormat = "number"): string => {
  if (value == null || value === "") return "—";
  switch (format) {
    case "currency":
      return currency(Number(value));
    case "percent":
      return `${Number(value).toFixed(1)}%`;
    case "text":
      return String(value);
    default:
      return new Intl.NumberFormat("en-KE").format(Number(value));
  }
};

export const pctBadge = (pct: number | null | undefined) => {
  if (pct == null) return null;
  return pct >= 0 ? (
    <span className="d-inline-flex align-items-center badge rounded-pill badge-soft-success border-0">
      +{pct}%
    </span>
  ) : (
    <span className="d-inline-flex align-items-center badge rounded-pill badge-soft-danger border-0">
      {pct}%
    </span>
  );
};

export const COMPARE_LABEL: Record<string, string> = {
  today: "vs yesterday",
  week: "vs previous week",
  month: "vs previous month",
  year: "vs previous year",
  custom: "vs prior period",
  all: "",
};

export const PERIOD_PREFIX: Record<string, string> = {
  today: "Today's ",
  week: "This Week's ",
  month: "This Month's ",
  year: "This Year's ",
  custom: "Period ",
  all: "Total ",
};

// ─────────────────────────────────────────────────────────────────────────────
// Current user (saved by the login page in sessionStorage)
// ─────────────────────────────────────────────────────────────────────────────

export const getStoredUser = (): any | null => {
  try {
    const raw = sessionStorage.getItem("user");
    return raw ? JSON.parse(raw) : null;
  } catch {
    return null;
  }
};

// ─────────────────────────────────────────────────────────────────────────────
// Header
// ─────────────────────────────────────────────────────────────────────────────

export const DashboardHeader = ({
  title,
  subtitle,
  onRefresh,
}: {
  title: string;
  subtitle?: string;
  onRefresh: () => void;
}) => (
  <div className="d-flex align-items-center justify-content-between gap-2 mb-4 flex-wrap">
    <div>
      <h4 className="mb-0">{title}</h4>
      {subtitle && <p className="text-muted fs-13 mb-0">{subtitle}</p>}
    </div>

    <div className="gap-2 d-flex align-items-center flex-wrap">
      <button
        type="button"
        className="btn btn-icon btn-outline-light shadow"
        onClick={onRefresh}
        title="Refresh"
      >
        <i className="ti ti-refresh" />
      </button>
      <Link
        to="#"
        className="btn btn-icon btn-outline-light shadow"
        id="collapse-header"
      >
        <i className="ti ti-transition-top" />
      </Link>
    </div>
  </div>
);

// ─────────────────────────────────────────────────────────────────────────────
// Small pieces
// ─────────────────────────────────────────────────────────────────────────────

export const ErrorAlert = ({ message }: { message: string }) => (
  <div className="alert alert-danger d-flex align-items-center gap-2 fs-13 py-2 mb-3">
    <i className="ti ti-circle-x fs-5 flex-shrink-0" />
    {message}
  </div>
);

export const EmptyState = ({ text = "No data for this period." }: { text?: string }) => (
  <div className="text-muted fs-13 py-5 text-center">
    <i className="ti ti-chart-bar fs-3 d-block mb-1" />
    {text}
  </div>
);

export const DashboardFooter = () => (
  <footer className="footer d-block d-md-flex justify-content-between text-md-start text-center">
    <p className="mb-md-0 mb-1">
      Copyright © {new Date().getFullYear()} Soinvet Agrovet POS
    </p>
    <div className="d-flex align-items-center gap-2 footer-links justify-content-center justify-content-md-end">
      <Link to="#">About</Link>
      <Link to="#">Terms</Link>
      <Link to="#">Contact Us</Link>
    </div>
  </footer>
);

// ─────────────────────────────────────────────────────────────────────────────
// KPI card
// ─────────────────────────────────────────────────────────────────────────────

export const StatCard = ({
  label,
  value,
  icon,
  color,
  loading,
  change,
  compareLabel,
  note,
}: {
  label: string;
  value: string;
  icon: string;
  color: string;
  loading?: boolean;
  change?: number | null;
  compareLabel?: string;
  note?: string;
}) => (
  <div
    className="card flex-fill border-0 shadow-sm"
    style={{ borderTop: `3px solid ${color}` }}
  >
    <div className="card-body position-relative">
      <p className="fw-medium mb-1 text-muted">{label}</p>
      <h4 className="mb-3 text-dark" style={{ fontSize: "1.7rem" }}>
        {loading ? "—" : value}
      </h4>
      <div className="d-flex align-items-center gap-2 flex-wrap">
        {!loading && change != null && pctBadge(change)}
        {!loading && change != null && compareLabel && (
          <p className="text-muted mb-0 fs-13">{compareLabel}</p>
        )}
        {!loading && change == null && note && (
          <p className="text-muted mb-0 fs-13">{note}</p>
        )}
      </div>
      <div className="custom-card-icon">
        <div
          className="avatar avatar-rounded avatar-lg"
          style={{
            background: `${color}22`,
            position: "absolute",
            top: 0,
            insetInlineEnd: 0,
          }}
        >
          <i className={`ti ${icon} fs-4`} style={{ color }} />
        </div>
      </div>
    </div>
  </div>
);

// ─────────────────────────────────────────────────────────────────────────────
// Charts
// ─────────────────────────────────────────────────────────────────────────────

export const BarCard = ({
  title,
  labels,
  values,
  color = "#E41F07",
  format = "number",
  seriesName = "Total",
  height = 300,
}: {
  title: string;
  labels: string[];
  values: number[];
  color?: string;
  format?: ValueFormat;
  seriesName?: string;
  height?: number;
}) => {
  const options = {
    chart: {
      type: "bar",
      toolbar: { show: false },
      animations: { enabled: true, speed: 800 },
    },
    colors: [color],
    plotOptions: {
      bar: { columnWidth: "55%", borderRadius: 6, dataLabels: { position: "top" } },
    },
    dataLabels: {
      enabled: values.length <= 10,
      offsetY: -20,
      formatter: (val: number) => formatValue(val, format),
      style: { fontSize: "11px", fontWeight: 600, colors: [color] },
    },
    grid: { borderColor: "#E8E8E8", strokeDashArray: 4 },
    xaxis: {
      categories: labels,
      labels: { style: { fontSize: "12px", fontWeight: 600, colors: "#666" } },
    },
    yaxis: {
      labels: {
        style: { fontSize: "12px", fontWeight: 600 },
        formatter: (val: number) => formatValue(val, format),
      },
    },
    tooltip: {
      theme: "light",
      y: { formatter: (val: number) => formatValue(val, format) },
    },
  } as ApexOptions;

  return (
    <div
      className="card flex-fill border-0 shadow-sm"
      style={{ borderTop: `3px solid ${color}` }}
    >
      <div className="card-body">
        <div className="d-flex align-items-center justify-content-between mb-3">
          <h5 className="mb-0 fw-bold">{title}</h5>
          <span className="badge bg-light text-dark fs-10">{labels.length} points</span>
        </div>
        {values.length === 0 ? (
          <EmptyState />
        ) : (
          <Chart
            options={options}
            series={[{ name: seriesName, data: values }]}
            type="bar"
            height={height}
          />
        )}
      </div>
    </div>
  );
};

export const DonutCard = ({
  title,
  labels,
  values,
  format = "number",
  height = 300,
}: {
  title: string;
  labels: string[];
  values: number[];
  format?: ValueFormat;
  height?: number;
}) => {
  const empty = values.length === 0 || values.every((v) => !v);

  const options = {
    chart: { type: "donut", animations: { enabled: true, speed: 800 } },
    colors: PALETTE,
    labels,
    plotOptions: {
      pie: {
        donut: {
          size: "65%",
          labels: {
            show: true,
            name: { fontSize: "12px", fontWeight: 600 },
            value: {
              fontSize: "16px",
              fontWeight: 700,
              formatter: (val: string) => formatValue(Number(val), format),
            },
            total: {
              show: true,
              label: "Total",
              formatter: (w: any) =>
                formatValue(
                  w.globals.seriesTotals.reduce((a: number, b: number) => a + b, 0),
                  format
                ),
            },
          },
        },
      },
    },
    dataLabels: {
      enabled: true,
      formatter: (val: number) => `${Math.round(val)}%`,
      style: { fontSize: "12px", fontWeight: 600 },
    },
    legend: { position: "bottom", fontSize: "12px", fontWeight: 600 },
    tooltip: {
      theme: "light",
      y: { formatter: (val: number) => formatValue(val, format) },
    },
  } as ApexOptions;

  return (
    <div
      className="card flex-fill border-0 shadow-sm"
      style={{ borderTop: "3px solid #0092E4" }}
    >
      <div className="card-body">
        <div className="d-flex align-items-center justify-content-between mb-3">
          <h5 className="mb-0 fw-bold">{title}</h5>
          <span className="badge bg-light text-dark fs-10">{labels.length} groups</span>
        </div>
        {empty ? (
          <EmptyState />
        ) : (
          <Chart options={options} series={values} type="donut" height={height} />
        )}
      </div>
    </div>
  );
};

// ─────────────────────────────────────────────────────────────────────────────
// List card
// ─────────────────────────────────────────────────────────────────────────────

export type ListItem = {
  title: string;
  subtitle?: string;
  value?: string | number;
  badge?: string;
  badge_type?: "success" | "danger" | "warning" | "info" | "primary";
};

export const ListCard = ({
  title,
  items,
  empty,
  loading,
  valueFormat = "number",
  link,
}: {
  title: string;
  items: ListItem[];
  empty: string;
  loading?: boolean;
  valueFormat?: ValueFormat;
  link?: string;
}) => (
  <div className="card flex-fill">
    <div className="card-body">
      <div className="d-flex align-items-center justify-content-between flex-wrap gap-2 mb-3">
        <h5 className="mb-0 fs-16 fw-bold d-inline-flex items-center">
          <span className="line-title d-block me-2" />
          {title}
        </h5>
        {link && (
          <Link to={link} className="btn btn-sm btn-icon btn-outline-light">
            <i className="ti ti-arrow-right" />
          </Link>
        )}
      </div>

      {loading ? (
        <div className="text-muted fs-13">
          <span className="spinner-border spinner-border-sm me-2" />
          Loading...
        </div>
      ) : items.length === 0 ? (
        <div className="text-muted fs-13 py-3 text-center">
          <i className="ti ti-check fs-4 d-block mb-1 text-success" />
          {empty}
        </div>
      ) : (
        items.map((item, i) => (
          <div
            key={`${item.title}-${i}`}
            className={`p-2 d-flex align-items-center justify-content-between gap-2 ${
              i < items.length - 1 ? "border-bottom" : ""
            }`}
          >
            <div className="d-flex align-items-center overflow-hidden">
              <i className="ti ti-circle-filled text-primary fs-8 me-2 flex-shrink-0" />
              <div className="overflow-hidden">
                <p className="text-dark mb-0 text-truncate">{item.title}</p>
                {item.subtitle && (
                  <p className="fs-12 text-muted mb-0 text-truncate">{item.subtitle}</p>
                )}
              </div>
            </div>

            {item.badge ? (
              <span
                className={`badge rounded-pill badge-soft-${
                  item.badge_type ?? "info"
                } border-0 flex-shrink-0`}
              >
                {item.badge}
              </span>
            ) : item.value != null ? (
              <p className="text-dark mb-0 flex-shrink-0">
                {typeof item.value === "number"
                  ? formatValue(item.value, valueFormat)
                  : item.value}
              </p>
            ) : null}
          </div>
        ))
      )}
    </div>
  </div>
);
