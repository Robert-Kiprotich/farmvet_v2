import { useState, useEffect, useCallback } from "react";
import * as XLSX from "xlsx";
import { Link } from "react-router";
import API from "../../services/api";
import { all_routes } from "../../routes/all_routes";

const route = all_routes;

function fmtDate(iso: string) {
  if (!iso) return "";
  return new Date(iso).toLocaleDateString("en-GB", { day: "2-digit", month: "short", year: "numeric" });
}

const COLUMNS = [
  { key: "name",           label: "Name" },
  { key: "phone",          label: "Phone" },
  { key: "email",          label: "Email" },
  { key: "address",        label: "Address" },
  { key: "loyalty_points", label: "Loyalty Points" },
  { key: "created_at",     label: "Date Added" },
] as const;

function exportCSV(rows: any[]) {
  const headers = COLUMNS.map(c => c.label);
  const lines = [
    headers.join(","),
    ...rows.map(r => COLUMNS.map(c => `"${String(r[c.key] ?? "").replace(/"/g, '""')}"`).join(",")),
  ];
  const blob = new Blob([lines.join("\n")], { type: "text/csv" });
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob);
  a.download = `customers_${new Date().toISOString().slice(0, 10)}.csv`;
  a.click();
}

function exportExcel(rows: any[]) {
  const headers = COLUMNS.map(c => c.label);
  const data = [headers, ...rows.map(r => COLUMNS.map(c => String(r[c.key] ?? "")))];
  const ws = XLSX.utils.aoa_to_sheet(data);
  const wb = XLSX.utils.book_new();
  XLSX.utils.book_append_sheet(wb, ws, "Customers");
  XLSX.writeFile(wb, `customers_${new Date().toISOString().slice(0, 10)}.xlsx`);
}

export default function CustomersList() {
  const [customers, setCustomers] = useState<any[]>([]);
  const [filtered, setFiltered]   = useState<any[]>([]);
  const [loading, setLoading]     = useState(true);

  const [search, setSearch]           = useState("");
  const [loyaltyFilter, setLoyaltyFilter] = useState("all"); // all | has | none

  const [page, setPage]         = useState(1);
  const [pageSize, setPageSize] = useState(25);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const res = await API.get("customers/");
      const raw: any[] = res.data?.results || res.data?.data || (Array.isArray(res.data) ? res.data : []);
      setCustomers(raw);
    } catch (err: any) {
      if (err.response?.status === 401) window.location.href = "/login";
      else console.error("Error loading customers:", err);
    } finally { setLoading(false); }
  }, []);

  useEffect(() => { load(); }, [load]);
  useEffect(() => { setPage(1); }, [search, loyaltyFilter]);

  useEffect(() => {
    let list = customers;
    if (loyaltyFilter === "has")  list = list.filter(c => (c.loyalty_points || 0) > 0);
    if (loyaltyFilter === "none") list = list.filter(c => !(c.loyalty_points > 0));
    if (search.trim()) {
      const q = search.toLowerCase();
      list = list.filter(c =>
        (c.name    || "").toLowerCase().includes(q) ||
        (c.phone   || "").includes(q) ||
        (c.email   || "").toLowerCase().includes(q)
      );
    }
    setFiltered(list);
  }, [search, loyaltyFilter, customers]);

  const activeFilterCount = [loyaltyFilter !== "all"].filter(Boolean).length;

  return (
    <div className="page-wrapper">
      <div className="content">

        <div className="d-flex align-items-center justify-content-between mb-3 flex-wrap gap-2">
          <div>
            <h4 className="fw-semibold mb-1">Customers</h4>
            <p className="text-muted fs-13 mb-0">Everyone who has shopped with you.</p>
          </div>
          <div className="d-flex gap-2 flex-wrap">
            <button className="btn btn-outline-secondary btn-sm" onClick={load} disabled={loading}>
              <i className={`ti ti-refresh me-1 ${loading ? "fa-spin" : ""}`} />Refresh
            </button>
            <button className="btn btn-outline-success btn-sm" onClick={() => exportCSV(filtered)} disabled={!filtered.length}>
              <i className="ti ti-file-text me-1" />CSV
            </button>
            <button className="btn btn-outline-success btn-sm" onClick={() => exportExcel(filtered)} disabled={!filtered.length}>
              <i className="ti ti-table me-1" />Excel
            </button>
            <Link to={route.addCustomer ?? "/customers/new"} className="btn btn-primary btn-sm">
              <i className="ti ti-plus me-1" />Add Customer
            </Link>
          </div>
        </div>

        {!loading && customers.length > 0 && (() => {
          const weekAgo = new Date(); weekAgo.setDate(weekAgo.getDate() - 7);
          const totalPoints = customers.reduce((s, c) => s + (c.loyalty_points || 0), 0);
          const tiles = [
            { label: "Total Customers", value: customers.length,                                                              icon: "ti-users",        bg: "bg-primary-gradient-100", color: "text-primary" },
            { label: "New This Week",   value: customers.filter(c => c.created_at && new Date(c.created_at) >= weekAgo).length, icon: "ti-user-plus",    bg: "bg-success-gradient-100", color: "text-success" },
            { label: "Loyalty Points",  value: totalPoints,                                                                    icon: "ti-star",         bg: "bg-warning-gradient-100", color: "text-warning" },
            { label: "Avg Points",      value: customers.length ? Math.round(totalPoints / customers.length) : 0,              icon: "ti-chart-bar",    bg: "bg-info-gradient-100",    color: "text-info" },
          ];
          return (
            <div className="row g-3 mb-4">
              {tiles.map(s => (
                <div key={s.label} className="col-6 col-sm-3">
                  <div className="card mb-0 shadow-none border">
                    <div className="card-body p-3 position-relative">
                      <p className="fw-medium mb-1 fs-13">{s.label}</p>
                      <h4 className={`mb-0 ${s.color}`}>{s.value}</h4>
                      <div className={`avatar avatar-rounded avatar-sm ${s.bg} position-absolute top-0 end-0 m-2 d-flex align-items-center justify-content-center`}>
                        <i className={`ti ${s.icon} fs-5 ${s.color}`} />
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          );
        })()}

        <div className="card shadow-none border">
          <div className="card-header border-bottom py-3 d-flex align-items-center justify-content-between flex-wrap gap-2">
            <div className="input-group input-group-flat" style={{ maxWidth: 260 }}>
              <span className="input-group-text bg-transparent border-end-0"><i className="ti ti-search text-muted" /></span>
              <input type="text" className="form-control border-start-0 ps-1 fs-13" placeholder="Search name, phone, email…"
                value={search} onChange={e => setSearch(e.target.value)} />
              {search && <button className="btn btn-sm btn-link text-muted px-2" onClick={() => setSearch("")}><i className="ti ti-x" /></button>}
            </div>
            <div className="d-flex gap-2 align-items-center flex-wrap">
              <select className="form-select form-select-sm fs-13" style={{ width: 170 }} value={loyaltyFilter} onChange={e => setLoyaltyFilter(e.target.value)}>
                <option value="all">All customers</option>
                <option value="has">Has loyalty points</option>
                <option value="none">No loyalty points</option>
              </select>
              {activeFilterCount > 0 && (
                <button className="btn btn-sm btn-outline-danger" onClick={() => setLoyaltyFilter("all")}>
                  <i className="ti ti-x me-1" />Clear
                </button>
              )}
            </div>
          </div>

          <div className="card-body p-0">
            {loading ? (
              <div className="d-flex align-items-center justify-content-center py-5 text-muted">
                <span className="spinner-border spinner-border-sm me-2" />Loading customers…
              </div>
            ) : filtered.length === 0 ? (
              <div className="d-flex flex-column align-items-center justify-content-center py-5 text-muted">
                <i className="ti ti-users fs-1 mb-2" />
                <p className="fs-14 mb-0">{customers.length === 0 ? "No customers found." : "No results match your filters."}</p>
              </div>
            ) : (
              <div className="table-responsive">
                <table className="table table-hover mb-0 fs-13">
                  <thead className="table-light">
                    <tr>
                      {COLUMNS.map(c => <th key={c.key} className="text-nowrap">{c.label}</th>)}
                      <th />
                    </tr>
                  </thead>
                  <tbody>
                    {filtered.slice((page - 1) * pageSize, page * pageSize).map(c => (
                      <tr key={c.id}>
                        <td className="fw-semibold text-primary">
                          <Link to={`${route.customerDetail ?? "/customers"}/${c.id}`}>{c.name}</Link>
                        </td>
                        <td className="text-nowrap">{c.phone || <span className="text-muted">—</span>}</td>
                        <td className="text-truncate" style={{ maxWidth: 200 }}>{c.email || <span className="text-muted">—</span>}</td>
                        <td className="text-truncate" style={{ maxWidth: 180 }}>{c.address || <span className="text-muted">—</span>}</td>
                        <td>
                          <span className="badge bg-warning-transparent text-warning">
                            <i className="ti ti-star me-1" />{c.loyalty_points ?? 0}
                          </span>
                        </td>
                        <td className="text-muted text-nowrap">{fmtDate(c.created_at)}</td>
                        <td>
                          <Link to={`${route.customerDetail ?? "/customers"}/${c.id}`} className="btn btn-sm btn-outline-primary py-1 px-2 fs-11">
                            <i className="ti ti-eye me-1" />View
                          </Link>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>

          {!loading && filtered.length > 0 && (() => {
            const totalPages = Math.ceil(filtered.length / pageSize);
            const start = (page - 1) * pageSize + 1;
            const end   = Math.min(page * pageSize, filtered.length);
            return (
              <div className="card-footer border-top py-2 px-3 d-flex align-items-center justify-content-between flex-wrap gap-2 fs-12 text-muted">
                <span>Showing <strong>{start}–{end}</strong> of <strong>{filtered.length}</strong> customer{filtered.length !== 1 ? "s" : ""}</span>
                <div className="d-flex align-items-center gap-1">
                  <select className="form-select form-select-sm fs-12 w-auto" value={pageSize}
                    onChange={e => { setPageSize(Number(e.target.value)); setPage(1); }}>
                    {[10, 25, 50, 100].map(n => <option key={n} value={n}>{n} / page</option>)}
                  </select>
                  {totalPages > 1 && (
                    <nav className="ms-2">
                      <ul className="pagination pagination-sm mb-0">
                        <li className={`page-item ${page === 1 ? "disabled" : ""}`}>
                          <button className="page-link" onClick={() => setPage(p => p - 1)}><i className="ti ti-chevron-left" /></button>
                        </li>
                        <li className="page-item disabled"><span className="page-link">{page} / {totalPages}</span></li>
                        <li className={`page-item ${page === totalPages ? "disabled" : ""}`}>
                          <button className="page-link" onClick={() => setPage(p => p + 1)}><i className="ti ti-chevron-right" /></button>
                        </li>
                      </ul>
                    </nav>
                  )}
                </div>
              </div>
            );
          })()}
        </div>
      </div>
    </div>
  );
}
