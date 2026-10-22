import React, { useState, useEffect, useCallback, useRef } from "react";
import * as XLSX from "xlsx";
import { Link } from "react-router";
import API from "../../services/api";
import { all_routes } from "../../routes/all_routes";

const route = all_routes;

function fmtDate(iso: string) {
  if (!iso) return "";
  return new Date(iso).toLocaleDateString("en-GB", { day: "2-digit", month: "short", year: "numeric" });
}

function fmtMoney(v: string | number) {
  const n = typeof v === "string" ? parseFloat(v) : v;
  if (n == null || isNaN(n)) return "";
  return n.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

// ── All available columns ─────────────────────────────────────────────────────
export const ALL_COLUMNS = [
  // Identifiers
  { key: "name",              label: "Product Name",   group: "Identifiers" },
  { key: "sku",               label: "SKU",            group: "Identifiers" },
  { key: "barcode",           label: "Barcode",        group: "Identifiers" },
  // Classification
  { key: "category",          label: "Category",       group: "Classification" },
  { key: "description",       label: "Description",    group: "Classification" },
  // Pricing
  { key: "cost_price",        label: "Cost Price",     group: "Pricing" },
  { key: "selling_price",     label: "Selling Price",  group: "Pricing" },
  { key: "margin",            label: "Margin",         group: "Pricing" },
  { key: "tax_rate",          label: "Tax Rate (%)",   group: "Pricing" },
  // Inventory
  { key: "stock_quantity",    label: "Stock Qty",      group: "Inventory" },
  { key: "reorder_level",     label: "Reorder Level",  group: "Inventory" },
  { key: "is_low_stock",      label: "Low Stock",      group: "Inventory" },
  // Status
  { key: "is_active",         label: "Active",         group: "Status" },
  // Media
  { key: "image_url",         label: "Image",          group: "Media" },
  { key: "barcode_image_url", label: "Barcode Image", group: "Media" },
  // Timestamps
  { key: "created_at",        label: "Date Created",   group: "Timestamps" },
  { key: "updated_at",        label: "Last Updated",   group: "Timestamps" },
] as const;

type ColKey = typeof ALL_COLUMNS[number]["key"];

const DEFAULT_VISIBLE: ColKey[] = [
  "name", "sku", "category", "selling_price", "stock_quantity", "is_low_stock", "is_active",
];

const BOOL_KEYS = new Set<ColKey>(["is_active", "is_low_stock"]);
const DATE_KEYS = new Set<ColKey>(["created_at", "updated_at"]);
const MONEY_KEYS = new Set<ColKey>(["cost_price", "selling_price", "margin"]);
const IMAGE_KEYS = new Set<ColKey>(["image_url", "barcode_image_url"]);

function cellValue(row: any, key: ColKey): string {
  const v = row[key];
  if (BOOL_KEYS.has(key)) return v ? "Yes" : "No";
  if (DATE_KEYS.has(key)) return fmtDate(v);
  if (MONEY_KEYS.has(key)) return fmtMoney(v);
  if (IMAGE_KEYS.has(key)) return v ? String(v) : "";
  return v == null ? "" : String(v);
}

function exportCSV(rows: any[], cols: ColKey[]) {
  const headers = cols.map(k => ALL_COLUMNS.find(c => c.key === k)!.label);
  const lines = [
    headers.join(","),
    ...rows.map(r => cols.map(k => `"${cellValue(r, k).replace(/"/g, '""')}"`).join(",")),
  ];
  const blob = new Blob([lines.join("\n")], { type: "text/csv" });
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob);
  a.download = `products_${new Date().toISOString().slice(0, 10)}.csv`;
  a.click();
}

function exportExcel(rows: any[], cols: ColKey[]) {
  const headers = cols.map(k => ALL_COLUMNS.find(c => c.key === k)!.label);
  const data = [headers, ...rows.map(r => cols.map(k => cellValue(r, k)))];
  const ws = XLSX.utils.aoa_to_sheet(data);
  const wb = XLSX.utils.book_new();
  XLSX.utils.book_append_sheet(wb, ws, "Products");
  XLSX.writeFile(wb, `products_${new Date().toISOString().slice(0, 10)}.xlsx`);
}

const GROUPS = Array.from(new Set(ALL_COLUMNS.map(c => c.group)));

export interface CategoryOption {
  id: number | string;
  name: string;
}

export interface ProductForm {
  name: string;
  sku: string;
  barcode: string;
  category: string | number;
  description: string;
  cost_price: string;
  selling_price: string;
  stock_quantity: number;
  reorder_level: number;
  tax_rate: string;
  is_active: boolean;
}

// ── Main Component ────────────────────────────────────────────────────────────
export default function ProductsList() {
  const [products, setProducts]             = useState<any[]>([]);
  const [filtered, setFiltered]             = useState<any[]>([]);
  const [categoriesList, setCategoriesList] = useState<CategoryOption[]>([]);
  const [loading, setLoading]               = useState(true);
  const [deletingId, setDeletingId]         = useState<number | string | null>(null);

  // Filters & Search
  const [search, setSearch]                 = useState("");
  const [categoryFilter, setCategoryFilter] = useState("all");
  const [statusFilter, setStatusFilter]     = useState("all");
  const [stockFilter, setStockFilter]       = useState("all");
  const [priceFrom, setPriceFrom]           = useState("");
  const [priceTo, setPriceTo]               = useState("");
  const [showFilters, setShowFilters]       = useState(false);

  // Columns & Pagination
  const [visibleCols, setVisibleCols]     = useState<ColKey[]>(DEFAULT_VISIBLE);
  const [showColPicker, setShowColPicker] = useState(false);
  const colPickerRef = useRef<HTMLDivElement>(null);

  const [page, setPage]         = useState(1);
  const [pageSize, setPageSize] = useState(25);

  // Offcanvas & Form State
  const [mode, setMode]                       = useState<"add" | "edit" | "view">("add");
  const [selectedProduct, setSelectedProduct] = useState<any | null>(null);
  const [saving, setSaving]                   = useState(false);
  const [error, setError]                     = useState("");

  const [form, setForm] = useState<ProductForm>({
    name: "",
    sku: "",
    barcode: "",
    category: "",
    description: "",
    cost_price: "0",
    selling_price: "0",
    stock_quantity: 0,
    reorder_level: 0,
    tax_rate: "0",
    is_active: true,
  });

  /** Normalise a raw API product object into the flat shape expected */
  function normalizeProduct(p: any): any {
    const catName = (c: any) => {
      if (!c) return "";
      if (typeof c === "string" || typeof c === "number") return c;
      return c.name ?? c.category_name ?? String(c);
    };
    return {
      id:                 p.id,
      name:               p.name               ?? "",
      sku:                p.sku                ?? "",
      barcode:            p.barcode            ?? "",
      barcode_image_url:  p.barcode_image_url  ?? "",
      category:           catName(p.category),
      category_id:        p.category?.id ?? (typeof p.category === "number" ? p.category : ""),
      description:        p.description        ?? "",
      cost_price:         p.cost_price         ?? "0",
      selling_price:      p.selling_price      ?? "0",
      margin:             (parseFloat(p.selling_price) - parseFloat(p.cost_price)) || 0,
      tax_rate:           p.tax_rate           ?? "0",
      stock_quantity:     p.stock_quantity     ?? 0,
      reorder_level:      p.reorder_level      ?? 0,
      image_url:          p.image_url          ?? "",
      is_active:          p.is_active          ?? true,
      is_low_stock:       p.is_low_stock       ?? false,
      created_at:         p.created_at         ?? "",
      updated_at:         p.updated_at         ?? "",
    };
  }

  // Fetch Categories from API
  const fetchCategories = useCallback(async () => {
    try {
      const res = await API.get("categories/");
      const raw: any[] = res.data?.results || res.data?.data || (Array.isArray(res.data) ? res.data : []);
      const formatted = raw.map((c: any) => ({
        id: c.id,
        name: c.name || String(c),
      }));
      setCategoriesList(formatted);
    } catch (err) {
      console.error("Error fetching categories:", err);
    }
  }, []);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      await fetchCategories();
      const res = await API.get("products/");
      const raw: any[] = res.data?.results || res.data?.data || (Array.isArray(res.data) ? res.data : []);
      setProducts(raw.map(normalizeProduct));
    } catch (err: any) {
      if (err.response?.status === 401) {
        console.error("Unauthorized - Please log in");
        window.location.href = "/login";
      } else {
        console.error("Error loading products:", err);
      }
    } finally {
      setLoading(false);
    }
  }, [fetchCategories]);

  useEffect(() => { load(); }, [load]);

  useEffect(() => {
    function handler(e: MouseEvent) {
      if (colPickerRef.current && !colPickerRef.current.contains(e.target as Node))
        setShowColPicker(false);
    }
    document.addEventListener("mousedown", handler);
    return () => document.removeEventListener("mousedown", handler);
  }, []);

  useEffect(() => { setPage(1); }, [search, categoryFilter, statusFilter, stockFilter, priceFrom, priceTo]);

  useEffect(() => {
    let list = products;
    if (categoryFilter !== "all") {
      list = list.filter(p => 
        String(p.category) === String(categoryFilter) || 
        String(p.category_id) === String(categoryFilter)
      );
    }
    if (statusFilter   !== "all") list = list.filter(p => (statusFilter === "active") === p.is_active);
    if (stockFilter === "low") list = list.filter(p => p.is_low_stock);
    if (stockFilter === "out") list = list.filter(p => p.stock_quantity === 0);
    if (stockFilter === "in")  list = list.filter(p => p.stock_quantity > 0);
    if (priceFrom) list = list.filter(p => parseFloat(p.selling_price) >= parseFloat(priceFrom));
    if (priceTo)   list = list.filter(p => parseFloat(p.selling_price) <= parseFloat(priceTo));

    if (search.trim()) {
      const q = search.toLowerCase();
      list = list.filter(p =>
        (p.name     || "").toLowerCase().includes(q) ||
        (p.sku      || "").toLowerCase().includes(q) ||
        (p.barcode  || "").includes(q) ||
        (p.category || "").toLowerCase().includes(q)
      );
    }
    setFiltered(list);
  }, [search, categoryFilter, statusFilter, stockFilter, priceFrom, priceTo, products]);

  const activeFilterCount = [
    categoryFilter !== "all", statusFilter !== "all", stockFilter !== "all", !!priceFrom, !!priceTo,
  ].filter(Boolean).length;

  function resetFilters() {
    setCategoryFilter("all"); setStatusFilter("all"); setStockFilter("all");
    setPriceFrom(""); setPriceTo(""); setSearch("");
  }

  function toggleCol(key: ColKey) {
    setVisibleCols(prev => prev.includes(key) ? prev.filter(k => k !== key) : [...prev, key]);
  }

  function toggleGroup(group: string, on: boolean) {
    const groupKeys = ALL_COLUMNS.filter(c => c.group === group).map(c => c.key);
    setVisibleCols(prev => {
      const without = prev.filter(k => !groupKeys.includes(k));
      return on ? [...without, ...groupKeys] : without;
    });
  }

  const orderedCols = ALL_COLUMNS.map(c => c.key).filter(k => visibleCols.includes(k));

  // ── Offcanvas Handlers ──────────────────────────────────────────────────────
  const handleAdd = () => {
    setMode("add");
    setSelectedProduct(null);
    setError("");
    setForm({
      name: "",
      sku: "",
      barcode: "",
      category: categoriesList[0]?.id ?? "",
      description: "",
      cost_price: "0",
      selling_price: "0",
      stock_quantity: 0,
      reorder_level: 0,
      tax_rate: "0",
      is_active: true,
    });
  };

  const handleEdit = (product: any) => {
    setMode("edit");
    setSelectedProduct(product);
    setError("");
    setForm({
      name: product.name ?? "",
      sku: product.sku ?? "",
      barcode: product.barcode ?? "",
      category: product.category_id || product.category || "",
      description: product.description ?? "",
      cost_price: String(product.cost_price ?? "0"),
      selling_price: String(product.selling_price ?? "0"),
      stock_quantity: product.stock_quantity ?? 0,
      reorder_level: product.reorder_level ?? 0,
      tax_rate: String(product.tax_rate ?? "0"),
      is_active: product.is_active ?? true,
    });
  };

  const handleView = (product: any) => {
    setMode("view");
    setSelectedProduct(product);
  };

  const handleDelete = async (product: any) => {
    if (!window.confirm(`Are you sure you want to delete "${product.name}"?`)) {
      return;
    }

    setDeletingId(product.id);
    try {
      await API.delete(`products/${product.id}/`);
      setProducts(prev => prev.filter(p => p.id !== product.id));
    } catch (err: any) {
      alert(err.response?.data?.detail || err.response?.data?.message || "Failed to delete product.");
    } finally {
      setDeletingId(null);
    }
  };

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    setError("");

    try {
      if (mode === "edit" && selectedProduct) {
        await API.put(`products/${selectedProduct.id}/`, form);
      } else {
        await API.post("products/", form);
      }
      await load();
      
      const btnClose = document.getElementById("product-offcanvas-close");
      if (btnClose) btnClose.click();
    } catch (err: any) {
      setError(err.response?.data?.detail || err.response?.data?.message || "Failed to save product.");
    } finally {
      setSaving(false);
    }
  };

  function renderCell(row: any, key: ColKey) {
    if (key === "name") return (
      <td key={key} className="ps-3 fw-semibold text-primary text-nowrap">
        <Link to={`${route.productDetail ?? "/products"}/${row.id}`}>{row.name}</Link>
      </td>
    );
    if (key === "image_url") return (
      <td key={key}>
        {row.image_url
          ? <img src={row.image_url} alt={row.name} width={36} height={36} style={{ objectFit: "cover", borderRadius: 6 }} />
          : <span className="text-muted fs-11">—</span>}
      </td>
    );
    if (key === "barcode_image_url") return (
      <td key={key}>
        {row.barcode_image_url
          ? <img src={row.barcode_image_url} alt="barcode" height={28} />
          : <span className="text-muted fs-11">—</span>}
      </td>
    );
    if (key === "is_active") return (
      <td key={key}>
        {row.is_active
          ? <span className="badge bg-success-transparent text-success">Active</span>
          : <span className="badge bg-secondary-transparent text-secondary">Inactive</span>}
      </td>
    );
    if (key === "is_low_stock") return (
      <td key={key}>
        {row.is_low_stock
          ? <span className="badge bg-danger-transparent text-danger">Low Stock</span>
          : <span className="text-muted fs-11">OK</span>}
      </td>
    );
    if (key === "stock_quantity") return (
      <td key={key} className="text-nowrap">
        {row.stock_quantity === 0
          ? <span className="badge bg-danger-transparent text-danger">Out of stock</span>
          : row.stock_quantity}
      </td>
    );
    if (MONEY_KEYS.has(key)) return (
      <td key={key} className="text-nowrap">{fmtMoney(row[key])}</td>
    );
    if (key === "tax_rate") return (
      <td key={key} className="text-nowrap">{row.tax_rate}%</td>
    );
    if (BOOL_KEYS.has(key)) return (
      <td key={key}>
        {row[key]
          ? <span className="badge bg-success-transparent text-success">Yes</span>
          : <span className="text-muted fs-11">No</span>}
      </td>
    );
    if (DATE_KEYS.has(key)) return (
      <td key={key} className="text-muted text-nowrap">{fmtDate(row[key])}</td>
    );
    const val = row[key];
    return (
      <td key={key} className="text-truncate" style={{ maxWidth: 220 }}>
        {val || <span className="text-muted">—</span>}
      </td>
    );
  }

  return (
    <div className="page-wrapper">
      <div className="content">

        {/* Header */}
        <div className="d-flex align-items-center justify-content-between mb-3 flex-wrap gap-2">
          <div>
            <h4 className="fw-semibold mb-1">Products</h4>
            <p className="text-muted fs-13 mb-0">All products in your inventory.</p>
          </div>
          <div className="d-flex gap-2 flex-wrap">
            <button className="btn btn-outline-secondary btn-sm" onClick={load} disabled={loading}>
              <i className={`ti ti-refresh me-1 ${loading ? "fa-spin" : ""}`} />Refresh
            </button>
            <button className="btn btn-outline-success btn-sm" onClick={() => exportCSV(filtered, orderedCols)} disabled={!filtered.length}>
              <i className="ti ti-file-text me-1" />CSV
            </button>
            <button className="btn btn-outline-success btn-sm" onClick={() => exportExcel(filtered, orderedCols)} disabled={!filtered.length}>
              <i className="ti ti-table me-1" />Excel
            </button>
            <button
              className="btn btn-primary btn-sm"
              data-bs-toggle="offcanvas"
              data-bs-target="#product-offcanvas"
              onClick={handleAdd}
            >
              <i className="ti ti-plus me-1" />Add Product
            </button>
          </div>
        </div>

        {/* Stats tiles */}
        {!loading && products.length > 0 && (() => {
          const stockValue = products.reduce((sum, p) => sum + (parseFloat(p.cost_price) || 0) * (p.stock_quantity || 0), 0);
          const tiles = [
            { label: "Total Products", value: products.length,                                   icon: "ti-package",        bg: "bg-primary-gradient-100", color: "text-primary"  },
            { label: "Active",         value: products.filter(p => p.is_active).length,               icon: "ti-circle-check",   bg: "bg-success-gradient-100", color: "text-success"  },
            { label: "Low Stock",      value: products.filter(p => p.is_low_stock).length,             icon: "ti-alert-triangle", bg: "bg-warning-gradient-100", color: "text-warning"  },
            { label: "Out of Stock",   value: products.filter(p => p.stock_quantity === 0).length,     icon: "ti-x",              bg: "bg-danger-gradient-100",  color: "text-danger"   },
            { label: "Categories",     value: categoriesList.length,                                  icon: "ti-category",       bg: "bg-info-gradient-100",    color: "text-info"     },
            { label: "Stock Value",    value: fmtMoney(stockValue),                                    icon: "ti-cash",           bg: "bg-pink-gradient-100",    color: "text-pink"     },
          ];
          return (
            <div className="row g-3 mb-4">
              {tiles.map(s => (
                <div key={s.label} className="col-6 col-sm-4 col-lg-2">
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
          {/* Toolbar */}
          <div className="card-header border-bottom py-3 d-flex align-items-center justify-content-between flex-wrap gap-2">
            <div className="input-group input-group-flat" style={{ maxWidth: 280 }}>
              <span className="input-group-text bg-transparent border-end-0">
                <i className="ti ti-search text-muted" />
              </span>
              <input
                type="text" className="form-control border-start-0 ps-1 fs-13"
                placeholder="Search name, SKU, barcode, category…"
                value={search} onChange={e => setSearch(e.target.value)}
              />
              {search && (
                <button className="btn btn-sm btn-link text-muted px-2" onClick={() => setSearch("")}>
                  <i className="ti ti-x" />
                </button>
              )}
            </div>

            <div className="d-flex gap-2 align-items-center flex-wrap">
              <button
                className={`btn btn-sm ${showFilters ? "btn-primary" : "btn-outline-secondary"}`}
                onClick={() => setShowFilters(v => !v)}
              >
                <i className="ti ti-filter me-1" />Filters
                {activeFilterCount > 0 && <span className="badge bg-danger ms-1 fs-10">{activeFilterCount}</span>}
              </button>
              {activeFilterCount > 0 && (
                <button className="btn btn-sm btn-outline-danger" onClick={resetFilters}>
                  <i className="ti ti-x me-1" />Clear
                </button>
              )}

              {/* Column picker */}
              <div className="position-relative" ref={colPickerRef}>
                <button className="btn btn-sm btn-outline-secondary" onClick={() => setShowColPicker(v => !v)}>
                  <i className="ti ti-columns me-1" />Columns
                  <span className="badge bg-primary ms-1 fs-10">{visibleCols.length}</span>
                </button>
                {showColPicker && (
                  <div className="card shadow-lg border-0 position-absolute end-0 mt-2 p-0"
                    style={{ zIndex: 1050, width: 380, maxHeight: "65vh", overflowY: "auto", borderRadius: "8px" }}>
                    <div className="p-3 border-bottom d-flex justify-content-between align-items-center"
                      style={{ background: "linear-gradient(135deg, #E41F07 0%, #FFA201 100%)" }}>
                      <span className="fs-12 fw-semibold text-white text-uppercase">Show / Hide Columns</span>
                      <div className="d-flex gap-2">
                        <button className="btn btn-xs btn-link fs-11 py-0 text-white" onClick={() => setVisibleCols(ALL_COLUMNS.map(c => c.key))}>All</button>
                        <span style={{ color: "rgba(255,255,255,0.3)" }}>|</span>
                        <button className="btn btn-xs btn-link fs-11 py-0 text-white" onClick={() => setVisibleCols(["name"])}>Reset</button>
                      </div>
                    </div>
                    {GROUPS.map((group, idx) => {
                      const groupCols = ALL_COLUMNS.filter(c => c.group === group);
                      const allOn = groupCols.every(c => visibleCols.includes(c.key));
                      return (
                        <div key={group} style={{ borderBottom: idx < GROUPS.length - 1 ? "1px solid #eee" : "none" }}>
                          <div className="px-3 py-2 d-flex align-items-center justify-content-between" style={{ background: "#f8f9fa" }}>
                            <span className="fs-12 fw-semibold text-uppercase text-muted" style={{ color: "#666" }}>{group}</span>
                            <div className="form-check form-switch mb-0">
                              <input className="form-check-input" type="checkbox" checked={allOn}
                                onChange={e => toggleGroup(group, e.target.checked)} />
                            </div>
                          </div>
                          <div className="px-3 py-2">
                            {groupCols.map(col => (
                              <div key={col.key} className="form-check mb-2">
                                <input className="form-check-input" type="checkbox"
                                  id={`col-${col.key}`} checked={visibleCols.includes(col.key)}
                                  onChange={() => toggleCol(col.key)} />
                                <label className="form-check-label fs-13" htmlFor={`col-${col.key}`} style={{ cursor: "pointer" }}>
                                  {col.label}
                                </label>
                              </div>
                            ))}
                          </div>
                        </div>
                      );
                    })}
                    <div className="p-3 border-top fs-12 text-muted" style={{ background: "#f8f9fa" }}>
                      <strong>{visibleCols.length}</strong> of <strong>{ALL_COLUMNS.length}</strong> columns visible
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Filter panel */}
          {showFilters && (
            <div className="card-header border-bottom py-3 bg-light">
              <div className="row g-2">
                <div className="col-sm-6 col-md-3 col-lg-3">
                  <label className="form-label fs-12 mb-1">Category</label>
                  <select className="form-select form-select-sm fs-13" value={categoryFilter} onChange={e => setCategoryFilter(e.target.value)}>
                    <option value="all">All categories</option>
                    {categoriesList.map(c => <option key={c.id} value={c.id}>{c.name}</option>)}
                  </select>
                </div>
                <div className="col-sm-6 col-md-3 col-lg-2">
                  <label className="form-label fs-12 mb-1">Status</label>
                  <select className="form-select form-select-sm fs-13" value={statusFilter} onChange={e => setStatusFilter(e.target.value)}>
                    <option value="all">All</option>
                    <option value="active">Active</option>
                    <option value="inactive">Inactive</option>
                  </select>
                </div>
                <div className="col-sm-6 col-md-3 col-lg-2">
                  <label className="form-label fs-12 mb-1">Stock</label>
                  <select className="form-select form-select-sm fs-13" value={stockFilter} onChange={e => setStockFilter(e.target.value)}>
                    <option value="all">All</option>
                    <option value="in">In stock</option>
                    <option value="low">Low stock</option>
                    <option value="out">Out of stock</option>
                  </select>
                </div>
                <div className="col-sm-6 col-md-3 col-lg-2">
                  <label className="form-label fs-12 mb-1">Price from</label>
                  <input type="number" className="form-control form-control-sm fs-13" value={priceFrom} onChange={e => setPriceFrom(e.target.value)} />
                </div>
                <div className="col-sm-6 col-md-3 col-lg-2">
                  <label className="form-label fs-12 mb-1">Price to</label>
                  <input type="number" className="form-control form-control-sm fs-13" value={priceTo} onChange={e => setPriceTo(e.target.value)} />
                </div>
              </div>
            </div>
          )}

          {/* Table */}
          <div className="card-body p-0">
            {loading ? (
              <div className="d-flex align-items-center justify-content-center py-5 text-muted">
                <span className="spinner-border spinner-border-sm me-2" />Loading products…
              </div>
            ) : filtered.length === 0 ? (
              <div className="d-flex flex-column align-items-center justify-content-center py-5 text-muted">
                <i className="ti ti-package-off fs-1 mb-2" />
                <p className="fs-14 mb-0">{products.length === 0 ? "No products found." : "No results match your filters."}</p>
                {activeFilterCount > 0 && <button className="btn btn-sm btn-link mt-2" onClick={resetFilters}>Clear filters</button>}
              </div>
            ) : (
              <div className="table-responsive">
                <table className="table table-hover mb-0 fs-13">
                  <thead className="table-light">
                    <tr>
                      {orderedCols.map(key => (
                        <th key={key} className={key === "name" ? "ps-3 text-nowrap" : "text-nowrap"}>
                          {ALL_COLUMNS.find(c => c.key === key)!.label}
                        </th>
                      ))}
                      <th className="text-end pe-3">Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {filtered.slice((page - 1) * pageSize, page * pageSize).map(p => (
                      <tr key={p.id}>
                        {orderedCols.map(key => renderCell(p, key))}
                        <td className="text-end pe-3">
                          <div className="d-inline-flex gap-1">
                            <button
                              className="btn btn-sm btn-outline-info py-1 px-2 fs-11"
                              data-bs-toggle="offcanvas"
                              data-bs-target="#product-offcanvas"
                              onClick={() => handleView(p)}
                            >
                              <i className="ti ti-eye me-1" />View
                            </button>
                            <button
                              className="btn btn-sm btn-outline-primary py-1 px-2 fs-11"
                              data-bs-toggle="offcanvas"
                              data-bs-target="#product-offcanvas"
                              onClick={() => handleEdit(p)}
                            >
                              <i className="ti ti-edit me-1" />Edit
                            </button>
                            <button
                              className="btn btn-sm btn-outline-danger py-1 px-2 fs-11"
                              onClick={() => handleDelete(p)}
                              disabled={deletingId === p.id}
                            >
                              {deletingId === p.id ? (
                                <span className="spinner-border spinner-border-sm" role="status" />
                              ) : (
                                <>
                                  <i className="ti ti-trash me-1" />Delete
                                </>
                              )}
                            </button>
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>

          {!loading && (() => {
            const totalPages = Math.ceil(filtered.length / pageSize);
            const start = filtered.length === 0 ? 0 : (page - 1) * pageSize + 1;
            const end   = Math.min(page * pageSize, filtered.length);
            const pages = Array.from({ length: totalPages }, (_, i) => i + 1);
            const visible = pages.filter(p => p === 1 || p === totalPages || Math.abs(p - page) <= 2);
            return (
              <div className="card-footer border-top py-2 px-3 d-flex align-items-center justify-content-between flex-wrap gap-2 fs-12 text-muted">
                <div className="d-flex align-items-center gap-2">
                  <span>Showing <strong>{start}–{end}</strong> of <strong>{filtered.length}</strong> product{filtered.length !== 1 ? "s" : ""}</span>
                  <select className="form-select form-select-sm fs-12 w-auto" value={pageSize}
                    onChange={e => { setPageSize(Number(e.target.value)); setPage(1); }}>
                    {[10, 25, 50, 100].map(n => <option key={n} value={n}>{n} / page</option>)}
                  </select>
                </div>
                <div className="d-flex align-items-center gap-1 flex-wrap">
                  {filtered.length > 0 && (
                    <>
                      <button className="btn btn-sm btn-outline-secondary py-0 px-2 fs-11" onClick={() => exportCSV(filtered, orderedCols)}>
                        <i className="ti ti-download me-1" />CSV
                      </button>
                      <button className="btn btn-sm btn-outline-secondary py-0 px-2 fs-11" onClick={() => exportExcel(filtered, orderedCols)}>
                        <i className="ti ti-download me-1" />Excel
                      </button>
                    </>
                  )}
                  {totalPages > 1 && (
                    <nav className="ms-2">
                      <ul className="pagination pagination-sm mb-0">
                        <li className={`page-item ${page === 1 ? "disabled" : ""}`}>
                          <button className="page-link" onClick={() => setPage(p => p - 1)}><i className="ti ti-chevron-left" /></button>
                        </li>
                        {visible.map((p, i, arr) => (
                          <React.Fragment key={p}>
                            {i > 0 && arr[i - 1] !== p - 1 && <li key={`gap-${p}`} className="page-item disabled"><span className="page-link">…</span></li>}
                            <li className={`page-item ${p === page ? "active" : ""}`}>
                              <button className="page-link" onClick={() => setPage(p)}>{p}</button>
                            </li>
                          </React.Fragment>
                        ))}
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

      {/* REUSABLE PRODUCT OFFCANVAS */}
      <div
        className="offcanvas offcanvas-end"
        tabIndex={-1}
        id="product-offcanvas"
        aria-labelledby="productOffcanvasLabel"
        style={{ width: "380px" }}
      >
        {/* HEADER */}
        <div className="offcanvas-header bg-primary text-white py-3">
          <h5 className="offcanvas-title text-white fs-15 fw-semibold" id="productOffcanvasLabel">
            {mode === "add" && "Add New Product"}
            {mode === "edit" && "Edit Product"}
            {mode === "view" && "Product Details"}
          </h5>
          <button
            id="product-offcanvas-close"
            type="button"
            className="btn-close btn-close-white"
            data-bs-dismiss="offcanvas"
            aria-label="Close"
          />
        </div>

        {/* BODY */}
        <div className="offcanvas-body">
          {error && <div className="alert alert-danger fs-13 py-2">{error}</div>}

          {mode === "view" && selectedProduct ? (
            /* VIEW MODE */
            <div className="d-flex flex-column gap-3 fs-13">
              <div>
                <label className="text-muted fs-12 fw-medium d-block mb-1">PRODUCT NAME</label>
                <span className="fw-semibold text-dark fs-14">{selectedProduct.name}</span>
              </div>
              <div>
                <label className="text-muted fs-12 fw-medium d-block mb-1">SKU</label>
                <span>{selectedProduct.sku || "—"}</span>
              </div>
              <div>
                <label className="text-muted fs-12 fw-medium d-block mb-1">BARCODE</label>
                <span>{selectedProduct.barcode || "—"}</span>
              </div>
              <div>
                <label className="text-muted fs-12 fw-medium d-block mb-1">CATEGORY</label>
                <span>{selectedProduct.category || "—"}</span>
              </div>
              <div>
                <label className="text-muted fs-12 fw-medium d-block mb-1">DESCRIPTION</label>
                <span>{selectedProduct.description || <em className="text-muted">No description</em>}</span>
              </div>
              <div>
                <label className="text-muted fs-12 fw-medium d-block mb-1">SELLING PRICE</label>
                <span className="fw-semibold text-success">{fmtMoney(selectedProduct.selling_price)}</span>
              </div>
              <div>
                <label className="text-muted fs-12 fw-medium d-block mb-1">COST PRICE</label>
                <span>{fmtMoney(selectedProduct.cost_price)}</span>
              </div>
              <div>
                <label className="text-muted fs-12 fw-medium d-block mb-1">STOCK QUANTITY</label>
                <span>{selectedProduct.stock_quantity}</span>
              </div>
              <div>
                <label className="text-muted fs-12 fw-medium d-block mb-1">STATUS</label>
                {selectedProduct.is_active ? (
                  <span className="badge bg-success-transparent text-success">Active</span>
                ) : (
                  <span className="badge bg-secondary-transparent text-secondary">Inactive</span>
                )}
              </div>
            </div>
          ) : (
            /* ADD / EDIT MODE */
            <form id="product-form" onSubmit={handleSave} className="d-flex flex-column gap-3">
              <div>
                <label htmlFor="p-name" className="form-label fs-13 fw-medium mb-1">
                  Product Name <span className="text-danger">*</span>
                </label>
                <input
                  id="p-name"
                  type="text"
                  className="form-control fs-13"
                  required
                  placeholder="Enter product name"
                  value={form.name}
                  onChange={(e) => setForm({ ...form, name: e.target.value })}
                />
              </div>

              <div>
                <label htmlFor="p-sku" className="form-label fs-13 fw-medium mb-1">SKU</label>
                <input
                  id="p-sku"
                  type="text"
                  className="form-control fs-13"
                  placeholder="Enter SKU"
                  value={form.sku}
                  onChange={(e) => setForm({ ...form, sku: e.target.value })}
                />
              </div>

              <div>
                <label htmlFor="p-barcode" className="form-label fs-13 fw-medium mb-1">Barcode</label>
                <input
                  id="p-barcode"
                  type="text"
                  className="form-control fs-13"
                  placeholder="Enter barcode number"
                  value={form.barcode}
                  onChange={(e) => setForm({ ...form, barcode: e.target.value })}
                />
              </div>

              <div>
                <label htmlFor="p-category" className="form-label fs-13 fw-medium mb-1">
                  Category <span className="text-danger">*</span>
                </label>
                <select
                  id="p-category"
                  className="form-select fs-13"
                  required
                  value={form.category}
                  onChange={(e) => setForm({ ...form, category: e.target.value })}
                >
                  <option value="">Select Category</option>
                  {categoriesList.map((c) => (
                    <option key={c.id} value={c.id}>
                      {c.name}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label htmlFor="p-desc" className="form-label fs-13 fw-medium mb-1">Description</label>
                <textarea
                  id="p-desc"
                  className="form-control fs-13"
                  rows={3}
                  placeholder="Enter product description"
                  value={form.description}
                  onChange={(e) => setForm({ ...form, description: e.target.value })}
                />
              </div>

              <div className="row g-2">
                <div className="col-6">
                  <label htmlFor="p-cost" className="form-label fs-13 fw-medium mb-1">Cost Price</label>
                  <input
                    id="p-cost"
                    type="number"
                    step="0.01"
                    className="form-control fs-13"
                    value={form.cost_price}
                    onChange={(e) => setForm({ ...form, cost_price: e.target.value })}
                  />
                </div>
                <div className="col-6">
                  <label htmlFor="p-sell" className="form-label fs-13 fw-medium mb-1">Selling Price</label>
                  <input
                    id="p-sell"
                    type="number"
                    step="0.01"
                    className="form-control fs-13"
                    value={form.selling_price}
                    onChange={(e) => setForm({ ...form, selling_price: e.target.value })}
                  />
                </div>
              </div>

              <div className="row g-2">
                <div className="col-6">
                  <label htmlFor="p-stock" className="form-label fs-13 fw-medium mb-1">Stock Quantity</label>
                  <input
                    id="p-stock"
                    type="number"
                    className="form-control fs-13"
                    value={form.stock_quantity}
                    onChange={(e) => setForm({ ...form, stock_quantity: Number(e.target.value) })}
                  />
                </div>
                <div className="col-6">
                  <label htmlFor="p-reorder" className="form-label fs-13 fw-medium mb-1">Reorder Level</label>
                  <input
                    id="p-reorder"
                    type="number"
                    className="form-control fs-13"
                    value={form.reorder_level}
                    onChange={(e) => setForm({ ...form, reorder_level: Number(e.target.value) })}
                  />
                </div>
              </div>

              <div className="form-check form-switch pt-1">
                <input
                  className="form-check-input"
                  type="checkbox"
                  role="switch"
                  id="product_is_active"
                  checked={form.is_active}
                  onChange={(e) => setForm({ ...form, is_active: e.target.checked })}
                />
                <label className="form-check-label fs-13 ms-1" htmlFor="product_is_active">
                  Active Status
                </label>
              </div>
            </form>
          )}
        </div>

        {/* FOOTER */}
        <div className="offcanvas-footer border-top p-3 d-flex justify-content-end gap-2">
          <button type="button" className="btn btn-sm btn-light border" data-bs-dismiss="offcanvas">
            {mode === "view" ? "Close" : "Cancel"}
          </button>
          {mode !== "view" && (
            <button type="submit" form="product-form" className="btn btn-sm btn-primary px-3" disabled={saving}>
              {saving && <span className="spinner-border spinner-border-sm me-1" role="status" />}
              {mode === "edit" ? "Update Product" : "Save Product"}
            </button>
          )}
        </div>
      </div>
    </div>
  );
}