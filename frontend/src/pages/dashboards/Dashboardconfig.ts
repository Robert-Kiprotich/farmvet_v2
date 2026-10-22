
import type { ValueFormat } from "./Dashboardshared";

export type RoleKey =
  | "administrator"
  | "official"
  | "farmer"
  | "vet"
  | "cooperative"
  | "slaughterhouse";

export type DashboardKey = RoleKey | "agrovet";

export type KpiDef = {
  key: string;
  label: string;
  icon: string; // tabler icon class, e.g. "ti-users"
  color: string;
  format?: ValueFormat;
  compare?: boolean; // show the % change badge
};

export type ChartDef = {
  key: string;
  title: string;
  type: "bar" | "donut";
  format?: ValueFormat;
  color?: string;
  span?: number; // bootstrap columns out of 12
};

export type ListDef = {
  key: string;
  title: string;
  empty: string;
  valueFormat?: ValueFormat;
  span?: number;
};

export type RoleDashboardConfig = {
  title: string;
  subtitle: string;
  endpoint: string;
  showDateFilter?: boolean;
  kpis: KpiDef[];
  charts: ChartDef[];
  lists: ListDef[];
};

const RED = "#E41F07";
const ORANGE = "#FFA201";
const BLUE = "#0092E4";
const GREEN = "#10B981";
const PURPLE = "#8B5CF6";
const ROSE = "#DC2626";
const AMBER = "#F59E0B";

export const DASHBOARD_CONFIGS: Record<RoleKey, RoleDashboardConfig> = {
  // ───────────────────────────────────────────────────────────────────────
  administrator: {
    title: "Administrator Dashboard",
    subtitle: "System-wide overview of users, sales and activity",
    endpoint: "dashboard/administrator/",
    kpis: [
      { key: "total_users", label: "Total Users", icon: "ti-users", color: PURPLE },
      { key: "new_registrations", label: "New Registrations", icon: "ti-user-plus", color: GREEN, compare: true },
      { key: "pending_verifications", label: "Pending Verifications", icon: "ti-user-check", color: AMBER },
      { key: "disabled_accounts", label: "Disabled Accounts", icon: "ti-user-off", color: ROSE },
      { key: "total_sales", label: "Total Sales", icon: "ti-currency-dollar", color: RED, format: "currency", compare: true },
      { key: "total_orders", label: "Orders", icon: "ti-receipt", color: ORANGE, compare: true },
      { key: "low_stock_items", label: "Low Stock Items", icon: "ti-alert-triangle", color: ROSE },
      { key: "outstanding_payments", label: "Outstanding Payments", icon: "ti-file-invoice", color: AMBER, format: "currency" },
    ],
    charts: [
      { key: "users_by_role", title: "Users by Role", type: "donut", span: 4 },
      { key: "registrations_trend", title: "Registrations Trend", type: "bar", color: GREEN, span: 4 },
      { key: "sales_trend", title: "Sales Trend", type: "bar", format: "currency", color: RED, span: 4 },
    ],
    lists: [
      { key: "pending_verifications", title: "Pending Verifications", empty: "No accounts waiting for review.", span: 6 },
      { key: "recent_activity", title: "Recent Activity", empty: "No recent activity.", span: 6 },
    ],
  },

  // ───────────────────────────────────────────────────────────────────────
  official: {
    title: "Official Dashboard",
    subtitle: "Oversight of registered stakeholders, disease reports and licences",
    endpoint: "dashboard/official/",
    kpis: [
      { key: "registered_farmers", label: "Registered Farmers", icon: "ti-users", color: GREEN },
      { key: "registered_vets", label: "Registered Vets", icon: "ti-stethoscope", color: BLUE },
      { key: "registered_agrovets", label: "Registered Agrovets", icon: "ti-building-store", color: PURPLE },
      { key: "registered_cooperatives", label: "Cooperatives", icon: "ti-building-community", color: ORANGE },
      { key: "open_disease_reports", label: "Open Disease Reports", icon: "ti-virus", color: ROSE },
      { key: "vaccinations_done", label: "Vaccinations Done", icon: "ti-vaccine", color: GREEN, compare: true },
      { key: "animals_slaughtered", label: "Animals Slaughtered", icon: "ti-paw", color: RED, compare: true },
      { key: "licences_expiring", label: "Licences Expiring Soon", icon: "ti-certificate", color: AMBER },
    ],
    charts: [
      { key: "disease_reports_trend", title: "Disease Reports Trend", type: "bar", color: ROSE, span: 4 },
      { key: "reports_by_disease", title: "Reports by Disease", type: "donut", span: 4 },
      { key: "registrations_by_county", title: "Registrations by County", type: "bar", color: BLUE, span: 4 },
    ],
    lists: [
      { key: "recent_disease_reports", title: "Recent Disease Reports", empty: "No disease reports in this period.", span: 6 },
      { key: "licences_expiring", title: "Licences Expiring Soon", empty: "No licences expiring soon.", span: 6 },
    ],
  },

  // ───────────────────────────────────────────────────────────────────────
  farmer: {
    title: "My Farm",
    subtitle: "Your animals, health records and production",
    endpoint: "dashboard/farmer/",
    kpis: [
      { key: "total_animals", label: "Total Animals", icon: "ti-paw", color: GREEN },
      { key: "milk_production", label: "Milk Production", icon: "ti-droplet", color: BLUE, compare: true },
      { key: "vet_visits", label: "Vet Visits", icon: "ti-stethoscope", color: PURPLE, compare: true },
      { key: "active_treatments", label: "Active Treatments", icon: "ti-pill", color: ROSE },
      { key: "upcoming_vaccinations", label: "Upcoming Vaccinations", icon: "ti-vaccine", color: AMBER },
      { key: "expenses", label: "Farm Expenses", icon: "ti-cash", color: RED, format: "currency", compare: true },
    ],
    charts: [
      { key: "milk_trend", title: "Milk Production (litres)", type: "bar", color: BLUE, span: 4 },
      { key: "animals_by_type", title: "Animals by Type", type: "donut", span: 4 },
      { key: "expenses_by_category", title: "Expenses by Category", type: "donut", format: "currency", span: 4 },
    ],
    lists: [
      { key: "upcoming_vaccinations", title: "Upcoming Vaccinations", empty: "No vaccinations due soon.", span: 6 },
      { key: "recent_vet_visits", title: "Recent Vet Visits", empty: "No vet visits recorded.", span: 6 },
    ],
  },

  // ───────────────────────────────────────────────────────────────────────
  vet: {
    title: "Veterinary Dashboard",
    subtitle: "Your caseload, treatments and farm visits",
    endpoint: "dashboard/vet/",
    kpis: [
      { key: "farms_served", label: "Farms Served", icon: "ti-home", color: GREEN },
      { key: "visits", label: "Farm Visits", icon: "ti-map-pin", color: BLUE, compare: true },
      { key: "open_cases", label: "Open Cases", icon: "ti-clipboard-check", color: ROSE },
      { key: "treatments_given", label: "Treatments Given", icon: "ti-pill", color: PURPLE, compare: true },
      { key: "vaccinations_done", label: "Vaccinations Done", icon: "ti-vaccine", color: GREEN, compare: true },
      { key: "pending_requests", label: "Pending Requests", icon: "ti-bell", color: AMBER },
      { key: "revenue", label: "Revenue", icon: "ti-currency-dollar", color: RED, format: "currency", compare: true },
      { key: "follow_ups_due", label: "Follow-ups Due", icon: "ti-calendar-due", color: ORANGE },
    ],
    charts: [
      { key: "visits_trend", title: "Visits Trend", type: "bar", color: BLUE, span: 4 },
      { key: "cases_by_disease", title: "Cases by Condition", type: "donut", span: 4 },
      { key: "revenue_trend", title: "Revenue Trend", type: "bar", format: "currency", color: RED, span: 4 },
    ],
    lists: [
      { key: "pending_requests", title: "Pending Service Requests", empty: "No pending requests.", span: 6 },
      { key: "follow_ups_due", title: "Follow-ups Due", empty: "No follow-ups due.", span: 6 },
    ],
  },

  // ───────────────────────────────────────────────────────────────────────
  cooperative: {
    title: "Cooperative Dashboard",
    subtitle: "Members, milk collection and payments",
    endpoint: "dashboard/cooperative/",
    kpis: [
      { key: "member_farmers", label: "Member Farmers", icon: "ti-users", color: GREEN },
      { key: "new_members", label: "New Members", icon: "ti-user-plus", color: PURPLE, compare: true },
      { key: "milk_collected", label: "Milk Collected", icon: "ti-droplet", color: BLUE, compare: true },
      { key: "avg_price_per_litre", label: "Avg Price / Litre", icon: "ti-tag", color: ORANGE, format: "currency" },
      { key: "payments_made", label: "Payments Made", icon: "ti-cash", color: GREEN, format: "currency", compare: true },
      { key: "payments_due", label: "Payments Due", icon: "ti-file-invoice", color: AMBER, format: "currency" },
    ],
    charts: [
      { key: "collection_trend", title: "Milk Collection (litres)", type: "bar", color: BLUE, span: 6 },
      { key: "payments_by_status", title: "Payments by Status", type: "donut", format: "currency", span: 6 },
    ],
    lists: [
      { key: "top_suppliers", title: "Top Suppliers", empty: "No deliveries in this period.", span: 6 },
      { key: "pending_payments", title: "Pending Payments", empty: "No pending payments.", span: 6 },
    ],
  },

  // ───────────────────────────────────────────────────────────────────────
  slaughterhouse: {
    title: "Slaughterhouse Dashboard",
    subtitle: "Throughput, inspections and condemnations",
    endpoint: "dashboard/slaughterhouse/",
    kpis: [
      { key: "animals_received", label: "Animals Received", icon: "ti-truck-delivery", color: BLUE, compare: true },
      { key: "animals_slaughtered", label: "Animals Slaughtered", icon: "ti-paw", color: RED, compare: true },
      { key: "pending_inspections", label: "Pending Inspections", icon: "ti-clipboard-check", color: AMBER },
      { key: "condemned_carcasses", label: "Condemned Carcasses", icon: "ti-alert-triangle", color: ROSE, compare: true },
      { key: "revenue", label: "Revenue", icon: "ti-currency-dollar", color: GREEN, format: "currency", compare: true },
      { key: "licence_days_left", label: "Licence Validity", icon: "ti-certificate", color: PURPLE },
    ],
    charts: [
      { key: "slaughter_trend", title: "Slaughter Trend", type: "bar", color: RED, span: 4 },
      { key: "by_species", title: "By Species", type: "donut", span: 4 },
      { key: "condemnation_reasons", title: "Condemnation Reasons", type: "donut", span: 4 },
    ],
    lists: [
      { key: "pending_inspections", title: "Pending Inspections", empty: "No inspections waiting.", span: 6 },
      { key: "recent_batches", title: "Recent Batches", empty: "No batches in this period.", span: 6 },
    ],
  },
};

// ─────────────────────────────────────────────────────────────────────────────
// Which dashboard does a logged-in user get?
// ─────────────────────────────────────────────────────────────────────────────

const NAME_MAP: Record<string, DashboardKey> = {
  administrator: "administrator",
  official: "official",
  farmer: "farmer",
  "vet officer": "vet",
  agrovet: "agrovet",
  cooperative: "cooperative",
  slaughterhouse: "slaughterhouse",
};

// Flags returned by the login endpoint (checked if the role name is unknown)
const FLAG_MAP: [string, DashboardKey][] = [
  ["is_admin", "administrator"],
  ["is_official", "official"],
  ["is_farmer", "farmer"],
  ["is_vet_officer", "vet"],
  ["is_agrovet", "agrovet"],
  ["is_cooperative", "cooperative"],
  ["is_slaughterhouse", "slaughterhouse"],
];

export function resolveDashboardKey(user: any): DashboardKey | null {
  const name = String(user?.role ?? "").trim().toLowerCase();
  if (NAME_MAP[name]) return NAME_MAP[name];

  for (const [flag, key] of FLAG_MAP) {
    if (user?.[flag]) return key;
  }
  return null;
}
