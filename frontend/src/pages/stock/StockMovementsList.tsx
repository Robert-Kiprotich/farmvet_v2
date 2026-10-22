import { useState, useEffect, useCallback } from "react";
import * as XLSX from "xlsx";
import { Link } from "react-router";
import API from "../../services/api";
import { all_routes } from "../../routes/all_routes";

const route = all_routes;

function fmtDate(iso: string) {
  if (!iso) return "";
  return new Date(iso).toLocaleDateString("en-GB", { day: "2-digit", month: "short", year: "numeric", hour: "2-digit", minute: "2-digit" });
}

const MOVEMENT_CLS: Record<string, string> = {
  restock:      "badge bg-success-transparent text-success",
  sale:         "badge bg-danger-transparent text-danger",
  adjustment:   "badge bg-warning-transparent text-warning",
  return:       "badge bg-info-transparent text-info",
  damaged:      "badge bg-danger-transparent text-danger",
  transfer:     "badge bg-secondary-transparent text-secondary",
};

const COLUMNS = [
  { key: "product_name",     label: "Product" },
  { key: "movement_type",    label: "Type" },
  { key: "quantity_change",  label: "Qty Change" },
  { key: "note",             label: "Note" },
  { key: "created_by",       label: "By (User ID)" },
  { key: "created_at",       label: "Date" },
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
  a.download = `stock_movements_${new Date().toISOString().slice(0, 10)}.csv`;
  a.click();
}

function exportExcel(rows: any[]) {
  const headers = COLUMNS.map(c => c.label);
  const data = [headers, ...rows.map(r => COLUMNS.map(c => String(r[c.key] ?? "")))];
  const ws = XLSX.utils.aoa_to_sheet(data);
  const wb = XLSX.utils.book_new();
  XLSX.utils.book_append_sheet(wb, ws, "Stock Movements");
  XLSX.writeFile(wb, `stock_movements_${new Date().toISOString().slice(0, 10)}.xlsx`);
}

export default function StockMovementsList() {
  const [movements, setMovements] = useState<any[]>([]);
  const [filtered, setFiltered]   = useState<any[]>([]);
  const [loading, setLoading]     = useState(true);

  const [search, setSearch]             = useState("");
  const [typeFilter, setTypeFilter]     = useState("all");
  const [directionFilter, setDirectionFilter] = useState("all"); // all | in | out
  const [dateFrom, setDateFrom]         = useState("");
  const [dateTo, setDateTo]             = useState("");

  const [page, setPage]         = useState(1);
  const [pageSize, setPageSize] = useState(25);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const res = await API.get("stock-movements/");
      const raw: any[] = res.data?.results || res.data?.data || (Array.isArray(res.data) ? res.data : []);
      setMovements(raw);
    } catch (err: any) {
      if (err.response?.status === 401) window.location.href = "/login";
      else console.error("Error loading stock movements:", err);
    } finally { setLoading(false); }
  }, []);

  useEffect(() => { load(); }, [load]);
  useEffect(() => { setPage(1); }, [search, typeFilter, directionFilter, dateFrom, dateTo]);

  const types = Array.from(new Set(movements.map(m => m.movement_type))).filter(Boolean).sort();

  useEffect(() => {
    let list = movements;
    if (typeFilter !== "all") list = list.filter(m => m.movement_type === typeFilter);
    if (directionFilter === "in")  list = list.filter(m => (m.quantity_change || 0) > 0);
    if (directionFilter === "out") list = list.filter(m => (m.quantity_change || 0) < 0);
    if (dateFrom) list = list.filter(m => m.created_at >= dateFrom);
    if (dateTo)   list = list.filter(m => m.created_at <= dateTo + "T23:59:59");
    if (search.trim()) {
      const q = search.toLowerCase();
      list = list.filter(m =>
        (m.product_name || "").toLowerCase().includes(q) ||
        (m.note || "").toLowerCase().includes(q)
      );
    }
    setFiltered(list);
  }, [search, typeFilter, directionFilter, dateFrom, dateTo, movements]);

  const activeFilterCount = [
    typeFilter !== "all", directionFilter !== "all", !!dateFrom, !!dateTo,
  ].filter(Boolean).length;

  function resetFilters() {
    setTypeFilter("all"); setDirectionFilter("all"); setDateFrom(""); setDateTo(""); setSearch("");
  }

  return (
    <div className="page-wrapper">
      <div className="content">

        <div className="d-flex align-items-center justify-content-between mb-3 flex-wrap gap-2">
          <div>
            <h4 className="fw-semibold mb-1">Stock Movements</h4>
            <p className="text-muted fs-13 mb-0">Full audit trail of inventory changes.</p>
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
            <Link to={route.addStockMovement ?? "/stock-movements/new"} className="btn btn-primary btn-sm">
              <i className="ti ti-plus me-1" />Record Movement
            </Link>
          </div>
        </div>

        {!loading && movements.length > 0 && (() => {
          const totalIn  = movements.filter(m => (m.quantity_change || 0) > 0).reduce((s, m) => s + m.quantity_change, 0);
          const totalOut = movements.filter(m => (m.quantity_change || 0) < 0).reduce((s, m) => s + Math.abs(m.quantity_change), 0);
          const tiles = [
            { label: "Total Movements", value: movements.length,                                            icon: "ti-arrows-exchange", bg: "bg-primary-gradient-100", color: "text-primary" },
            { label: "Restocks",        value: movements.filter(m => m.movement_type === "restock").length, icon: "ti-truck-delivery",  bg: "bg-success-gradient-100", color: "text-success" },
            { label: "Units In",        value: totalIn,                                                      icon: "ti-arrow-down",      bg: "bg-info-gradient-100",    color: "text-info" },
            { label: "Units Out",       value: totalOut,                                                     icon: "ti-arrow-up",        bg: "bg-danger-gradient-100",  color: "text-danger" },
            { label: "Net Change",      value: totalIn - totalOut,                                           icon: "ti-scale",           bg: "bg-warning-gradient-100", color: "text-warning" },
          ];
          return (
            <div className="row g-3 mb-4">
              {tiles.map(s => (
                <div key={s.label} className="col-6 col-sm-4 col-lg-2" style={{ flex: "1 1 0" }}>
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
              <input type="text" className="form-control border-start-0 ps-1 fs-13" placeholder="Search product, note…"
                value={search} onChange={e => setSearch(e.target.value)} />
              {search && <button className="btn btn-sm btn-link text-muted px-2" onClick={() => setSearch("")}><i className="ti ti-x" /></button>}
            </div>
            <div className="d-flex gap-2 align-items-center flex-wrap">
              <select className="form-select form-select-sm fs-13" style={{ width: 150 }} value={typeFilter} onChange={e => setTypeFilter(e.target.value)}>
                <option value="all">All types</option>
                {types.map(t => <option key={t} value={t} className="text-capitalize">{t}</option>)}
              </select>
              <select className="form-select form-select-sm fs-13" style={{ width: 130 }} value={directionFilter} onChange={e => setDirectionFilter(e.target.value)}>
                <option value="all">In &amp; out</option>
                <option value="in">Stock in</option>
                <option value="out">Stock out</option>
              </select>
              <input type="date" className="form-control form-control-sm fs-13" style={{ width: 140 }} value={dateFrom} onChange={e => setDateFrom(e.target.value)} />
              <input type="date" className="form-control form-control-sm fs-13" style={{ width: 140 }} value={dateTo} onChange={e => setDateTo(e.target.value)} />
              {activeFilterCount > 0 && (
                <button className="btn btn-sm btn-outline-danger" onClick={resetFilters}>
                  <i className="ti ti-x me-1" />Clear
                </button>
              )}
            </div>
          </div>

          <div className="card-body p-0">
            {loading ? (
              <div className="d-flex align-items-center justify-content-center py-5 text-muted">
                <span className="spinner-border spinner-border-sm me-2" />Loading movements…
              </div>
            ) : filtered.length === 0 ? (
              <div className="d-flex flex-column align-items-center justify-content-center py-5 text-muted">
                <i className="ti ti-arrows-exchange fs-1 mb-2" />
                <p className="fs-14 mb-0">{movements.length === 0 ? "No stock movements found." : "No results match your filters."}</p>
                {activeFilterCount > 0 && <button className="btn btn-sm btn-link mt-2" onClick={resetFilters}>Clear filters</button>}
              </div>
            ) : (
              <div className="table-responsive">
                <table className="table table-hover mb-0 fs-13">
                  <thead className="table-light">
                    <tr>
                      {COLUMNS.map(c => <th key={c.key} className="text-nowrap">{c.label}</th>)}
                    </tr>
                  </thead>
                  <tbody>
                    {filtered.slice((page - 1) * pageSize, page * pageSize).map(m => (
                      <tr key={m.id}>
                        <td className="fw-semibold text-dark text-nowrap">{m.product_name}</td>
                        <td>
                          <span className={MOVEMENT_CLS[m.movement_type] || "badge bg-secondary-transparent text-secondary"} style={{ textTransform: "capitalize" }}>
                            {m.movement_type || "—"}
                          </span>
                        </td>
                        <td className={`fw-semibold text-nowrap ${m.quantity_change > 0 ? "text-success" : m.quantity_change < 0 ? "text-danger" : "text-muted"}`}>
                          {m.quantity_change > 0 ? `+${m.quantity_change}` : m.quantity_change}
                        </td>
                        <td className="text-truncate" style={{ maxWidth: 260 }}>{m.note || <span className="text-muted">—</span>}</td>
                        <td className="text-muted text-nowrap">{m.created_by ?? "—"}</td>
                        <td className="text-muted text-nowrap">{fmtDate(m.created_at)}</td>
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
                <span>Showing <strong>{start}–{end}</strong> of <strong>{filtered.length}</strong> movement{filtered.length !== 1 ? "s" : ""}</span>
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
