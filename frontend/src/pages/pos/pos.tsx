import { useState, useEffect, useCallback, useMemo } from "react";
import { useNavigate } from "react-router";
import API from "../../services/api";
import { all_routes } from "../../routes/all_routes";

const route = all_routes;

const PAYMENT_METHODS = ["Cash", "Card", "M-Pesa", "Bank Transfer", "Other"] as const;

type SaleItem = {
  uid: string;
  product_id: number | "";
  product_name: string;
  unit_price: number;
  tax_rate: number;
  quantity: number;
};

type Payment = {
  uid: string;
  method: typeof PAYMENT_METHODS[number];
  amount: string;
  reference: string;
  received_by: string;
};

function uid() {
  return Math.random().toString(36).slice(2, 10);
}

function money(n: number) {
  if (isNaN(n)) return "0.00";
  return n.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

export default function POS() {
  const navigate = useNavigate();

  const [customers, setCustomers] = useState<any[]>([]);
  const [products, setProducts]   = useState<any[]>([]);
  const [loadingLookups, setLoadingLookups] = useState(true);

  const [customerId, setCustomerId] = useState<number | "">("");
  const [customerSearch, setCustomerSearch] = useState("");
  const [showCustomerDropdown, setShowCustomerDropdown] = useState(false);

  const [notes, setNotes]                 = useState("");
  const [discountAmount, setDiscountAmount] = useState("0");

  const [items, setItems]       = useState<SaleItem[]>([]);
  const [productSearch, setProductSearch] = useState("");
  const [showProductDropdown, setShowProductDropdown] = useState(false);

  const [payments, setPayments] = useState<Payment[]>([
    { uid: uid(), method: "Cash", amount: "", reference: "", received_by: "" },
  ]);

  const [submitting, setSubmitting] = useState(false);
  const [error, setError]           = useState("");

  const loadLookups = useCallback(async () => {
    setLoadingLookups(true);
    try {
      const [custRes, prodRes] = await Promise.all([
        API.get("customers/"),
        API.get("products/"),
      ]);
      setCustomers(custRes.data?.results || custRes.data?.data || (Array.isArray(custRes.data) ? custRes.data : []));
      setProducts(prodRes.data?.results || prodRes.data?.data || (Array.isArray(prodRes.data) ? prodRes.data : []));
    } catch (err) {
      console.error("Error loading sale lookups:", err);
    } finally {
      setLoadingLookups(false);
    }
  }, []);

  useEffect(() => { loadLookups(); }, [loadLookups]);

  const selectedCustomer = customers.find(c => c.id === customerId);

  const filteredCustomers = useMemo(() => {
    if (!customerSearch.trim()) return customers.slice(0, 8);
    const q = customerSearch.toLowerCase();
    return customers.filter(c =>
      (c.name || "").toLowerCase().includes(q) || (c.phone || "").includes(q)
    ).slice(0, 8);
  }, [customerSearch, customers]);

  const filteredProducts = useMemo(() => {
    if (!productSearch.trim()) return products.slice(0, 8);
    const q = productSearch.toLowerCase();
    return products.filter(p =>
      (p.name || "").toLowerCase().includes(q) ||
      (p.sku  || "").toLowerCase().includes(q) ||
      (p.barcode || "").includes(q)
    ).slice(0, 8);
  }, [productSearch, products]);

  function addItem(product: any) {
    setItems(prev => {
      const existing = prev.find(i => i.product_id === product.id);
      if (existing) {
        return prev.map(i => i.product_id === product.id ? { ...i, quantity: i.quantity + 1 } : i);
      }
      return [...prev, {
        uid: uid(),
        product_id: product.id,
        product_name: product.name,
        unit_price: parseFloat(product.selling_price) || 0,
        tax_rate: parseFloat(product.tax_rate) || 0,
        quantity: 1,
      }];
    });
    setProductSearch("");
    setShowProductDropdown(false);
  }

  function updateItem(uidVal: string, patch: Partial<SaleItem>) {
    setItems(prev => prev.map(i => i.uid === uidVal ? { ...i, ...patch } : i));
  }

  function removeItem(uidVal: string) {
    setItems(prev => prev.filter(i => i.uid !== uidVal));
  }

  function addPayment() {
    setPayments(prev => [...prev, { uid: uid(), method: "Cash", amount: "", reference: "", received_by: "" }]);
  }

  function updatePayment(uidVal: string, patch: Partial<Payment>) {
    setPayments(prev => prev.map(p => p.uid === uidVal ? { ...p, ...patch } : p));
  }

  function removePayment(uidVal: string) {
    setPayments(prev => prev.filter(p => p.uid !== uidVal));
  }

  const subtotal = items.reduce((s, i) => s + i.unit_price * i.quantity, 0);
  const taxTotal  = items.reduce((s, i) => s + i.unit_price * i.quantity * (i.tax_rate / 100), 0);
  const discount  = parseFloat(discountAmount) || 0;
  const grandTotal = Math.max(subtotal + taxTotal - discount, 0);
  const amountPaid  = payments.reduce((s, p) => s + (parseFloat(p.amount) || 0), 0);
  const balance     = grandTotal - amountPaid;

  async function handleSubmit() {
    setError("");
    if (!items.length) { setError("Add at least one item to the sale."); return; }
    if (amountPaid <= 0) { setError("Record at least one payment."); return; }

    const payload = {
      customer: customerId || null,
      notes,
      discount_amount: discount,
      items: items.map(i => ({ product: i.product_id, quantity: i.quantity, unit_price: i.unit_price })),
      payments: payments
        .filter(p => parseFloat(p.amount) > 0)
        .map(p => ({ method: p.method, amount: parseFloat(p.amount) || 0, reference: p.reference, received_by: p.received_by })),
    };

    setSubmitting(true);
    try {
      const res = await API.post("sales/", payload);
      const saleId = res.data?.id ?? res.data?.data?.id;
      navigate(saleId ? `${route.saleDetail ?? "/sales"}/${saleId}` : (route.salesList ?? "/sales"));
    } catch (err: any) {
      setError(err.response?.data?.message || "Failed to complete sale. Please check the details and try again.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="page-wrapper">
      <div className="content">

        <div className="d-flex align-items-center justify-content-between mb-3 flex-wrap gap-2">
          <div>
            <h4 className="fw-semibold mb-1">New Sale</h4>
            <p className="text-muted fs-13 mb-0">Ring up items and take payment.</p>
          </div>
        </div>

        {error && (
          <div className="alert alert-danger fs-13 d-flex align-items-center">
            <i className="ti ti-alert-circle me-2" />{error}
          </div>
        )}

        <div className="row g-3">

          {/* ── Left: customer, items, notes ─────────────────────────── */}
          <div className="col-xl-8">

            {/* Customer */}
            <div className="card shadow-none border mb-3">
              <div className="card-header py-3 border-bottom">
                <h6 className="mb-0 fw-semibold fs-14"><i className="ti ti-user me-2 text-primary" />Customer</h6>
              </div>
              <div className="card-body">
                <div className="position-relative">
                  <input
                    type="text" className="form-control form-control-sm fs-13"
                    placeholder="Search customer by name or phone… (optional — walk-in if blank)"
                    value={selectedCustomer ? selectedCustomer.name : customerSearch}
                    onChange={e => { setCustomerSearch(e.target.value); setCustomerId(""); setShowCustomerDropdown(true); }}
                    onFocus={() => setShowCustomerDropdown(true)}
                  />
                  {selectedCustomer && (
                    <button className="btn btn-sm btn-link position-absolute end-0 top-0 text-muted"
                      onClick={() => { setCustomerId(""); setCustomerSearch(""); }}>
                      <i className="ti ti-x" />
                    </button>
                  )}
                  {showCustomerDropdown && !selectedCustomer && (
                    <div className="card shadow-lg border position-absolute w-100 mt-1" style={{ zIndex: 1040, maxHeight: 220, overflowY: "auto" }}>
                      {loadingLookups ? (
                        <div className="p-2 text-muted fs-12">Loading…</div>
                      ) : filteredCustomers.length === 0 ? (
                        <div className="p-2 text-muted fs-12">No customers found.</div>
                      ) : filteredCustomers.map(c => (
                        <button key={c.id} type="button" className="btn btn-link text-start w-100 fs-13 py-2 px-3 text-decoration-none text-dark"
                          onClick={() => { setCustomerId(c.id); setShowCustomerDropdown(false); }}>
                          <div className="fw-medium">{c.name}</div>
                          <div className="text-muted fs-11">{c.phone}{c.loyalty_points ? ` · ${c.loyalty_points} pts` : ""}</div>
                        </button>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            </div>

            {/* Items */}
            <div className="card shadow-none border mb-3">
              <div className="card-header py-3 border-bottom d-flex align-items-center justify-content-between">
                <h6 className="mb-0 fw-semibold fs-14"><i className="ti ti-shopping-cart me-2 text-primary" />Items</h6>
                <span className="badge bg-primary-transparent text-primary fs-11">{items.length}</span>
              </div>
              <div className="card-body">
                <div className="position-relative mb-3">
                  <input
                    type="text" className="form-control form-control-sm fs-13"
                    placeholder="Search product by name, SKU, or barcode to add…"
                    value={productSearch}
                    onChange={e => { setProductSearch(e.target.value); setShowProductDropdown(true); }}
                    onFocus={() => setShowProductDropdown(true)}
                  />
                  {showProductDropdown && (
                    <div className="card shadow-lg border position-absolute w-100 mt-1" style={{ zIndex: 1040, maxHeight: 260, overflowY: "auto" }}>
                      {loadingLookups ? (
                        <div className="p-2 text-muted fs-12">Loading…</div>
                      ) : filteredProducts.length === 0 ? (
                        <div className="p-2 text-muted fs-12">No products found.</div>
                      ) : filteredProducts.map(p => (
                        <button key={p.id} type="button" className="btn btn-link text-start w-100 fs-13 py-2 px-3 text-decoration-none text-dark d-flex justify-content-between"
                          onClick={() => addItem(p)} disabled={p.stock_quantity === 0}>
                          <span>
                            <div className="fw-medium">{p.name}</div>
                            <div className="text-muted fs-11">{p.sku} · Stock: {p.stock_quantity}</div>
                          </span>
                          <span className="fw-semibold">{money(parseFloat(p.selling_price))}</span>
                        </button>
                      ))}
                    </div>
                  )}
                </div>

                {items.length === 0 ? (
                  <div className="text-center text-muted py-4 fs-13">
                    <i className="ti ti-shopping-cart-off fs-2 d-block mb-2" />No items added yet
                  </div>
                ) : (
                  <div className="table-responsive">
                    <table className="table table-sm mb-0 fs-13">
                      <thead className="table-light">
                        <tr>
                          <th>Product</th>
                          <th style={{ width: 90 }}>Qty</th>
                          <th style={{ width: 120 }}>Unit Price</th>
                          <th style={{ width: 90 }}>Tax</th>
                          <th style={{ width: 120 }} className="text-end">Line Total</th>
                          <th style={{ width: 40 }} />
                        </tr>
                      </thead>
                      <tbody>
                        {items.map(i => (
                          <tr key={i.uid}>
                            <td className="fw-medium">{i.product_name}</td>
                            <td>
                              <input type="number" min={1} className="form-control form-control-sm"
                                value={i.quantity} onChange={e => updateItem(i.uid, { quantity: Math.max(1, Number(e.target.value)) })} />
                            </td>
                            <td>
                              <input type="number" step="0.01" min={0} className="form-control form-control-sm"
                                value={i.unit_price} onChange={e => updateItem(i.uid, { unit_price: Math.max(0, Number(e.target.value)) })} />
                            </td>
                            <td className="text-muted">{i.tax_rate}%</td>
                            <td className="text-end fw-semibold">{money(i.unit_price * i.quantity * (1 + i.tax_rate / 100))}</td>
                            <td>
                              <button className="btn btn-sm btn-link text-danger px-1" onClick={() => removeItem(i.uid)}>
                                <i className="ti ti-trash" />
                              </button>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </div>
            </div>

            {/* Notes & discount */}
            <div className="card shadow-none border mb-3">
              <div className="card-header py-3 border-bottom">
                <h6 className="mb-0 fw-semibold fs-14"><i className="ti ti-notes me-2 text-primary" />Notes &amp; Discount</h6>
              </div>
              <div className="card-body">
                <div className="row g-3">
                  <div className="col-md-8">
                    <label className="form-label fs-12 mb-1">Notes</label>
                    <textarea className="form-control fs-13" rows={3} value={notes} onChange={e => setNotes(e.target.value)}
                      placeholder="Optional notes about this sale…" />
                  </div>
                  <div className="col-md-4">
                    <label className="form-label fs-12 mb-1">Discount Amount</label>
                    <input type="number" min={0} step="0.01" className="form-control fs-13" value={discountAmount}
                      onChange={e => setDiscountAmount(e.target.value)} />
                  </div>
                </div>
              </div>
            </div>

            {/* Payments */}
            <div className="card shadow-none border mb-3">
              <div className="card-header py-3 border-bottom d-flex align-items-center justify-content-between">
                <h6 className="mb-0 fw-semibold fs-14"><i className="ti ti-credit-card me-2 text-primary" />Payments</h6>
                <button className="btn btn-sm btn-outline-primary" onClick={addPayment}>
                  <i className="ti ti-plus me-1" />Add Payment
                </button>
              </div>
              <div className="card-body">
                {payments.map((p, idx) => (
                  <div key={p.uid} className="row g-2 align-items-end mb-3 pb-3" style={{ borderBottom: idx < payments.length - 1 ? "1px dashed #eee" : "none" }}>
                    <div className="col-sm-6 col-md-3">
                      <label className="form-label fs-12 mb-1">Method</label>
                      <select className="form-select form-select-sm fs-13" value={p.method}
                        onChange={e => updatePayment(p.uid, { method: e.target.value as Payment["method"] })}>
                        {PAYMENT_METHODS.map(m => <option key={m} value={m}>{m}</option>)}
                      </select>
                    </div>
                    <div className="col-sm-6 col-md-3">
                      <label className="form-label fs-12 mb-1">Amount</label>
                      <input type="number" min={0} step="0.01" className="form-control form-control-sm fs-13"
                        value={p.amount} onChange={e => updatePayment(p.uid, { amount: e.target.value })} />
                    </div>
                    <div className="col-sm-6 col-md-3">
                      <label className="form-label fs-12 mb-1">Reference</label>
                      <input type="text" className="form-control form-control-sm fs-13" placeholder="Transaction / receipt no."
                        value={p.reference} onChange={e => updatePayment(p.uid, { reference: e.target.value })} />
                    </div>
                    <div className="col-sm-5 col-md-2">
                      <label className="form-label fs-12 mb-1">Received By</label>
                      <input type="text" className="form-control form-control-sm fs-13"
                        value={p.received_by} onChange={e => updatePayment(p.uid, { received_by: e.target.value })} />
                    </div>
                    <div className="col-sm-1 d-flex justify-content-end">
                      {payments.length > 1 && (
                        <button className="btn btn-sm btn-link text-danger px-1" onClick={() => removePayment(p.uid)}>
                          <i className="ti ti-trash" />
                        </button>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>

          </div>

          {/* ── Right: totals & submit ──────────────────────────────── */}
          <div className="col-xl-4">
            <div className="card shadow-none border mb-3" style={{ position: "sticky", top: 16 }}>
              <div className="card-header py-3 border-bottom">
                <h6 className="mb-0 fw-semibold fs-14"><i className="ti ti-receipt me-2 text-primary" />Sale Summary</h6>
              </div>
              <div className="card-body">
                <div className="d-flex justify-content-between fs-13 mb-2">
                  <span className="text-muted">Subtotal</span><span>{money(subtotal)}</span>
                </div>
                <div className="d-flex justify-content-between fs-13 mb-2">
                  <span className="text-muted">Tax</span><span>{money(taxTotal)}</span>
                </div>
                <div className="d-flex justify-content-between fs-13 mb-2">
                  <span className="text-muted">Discount</span><span className="text-danger">-{money(discount)}</span>
                </div>
                <hr />
                <div className="d-flex justify-content-between fs-15 fw-semibold mb-2">
                  <span>Total</span><span>{money(grandTotal)}</span>
                </div>
                <div className="d-flex justify-content-between fs-13 mb-2">
                  <span className="text-muted">Amount Paid</span><span className="text-success">{money(amountPaid)}</span>
                </div>
                <div className="d-flex justify-content-between fs-13 mb-3">
                  <span className="text-muted">Balance</span>
                  <span className={balance > 0 ? "text-danger fw-semibold" : "text-success fw-semibold"}>{money(Math.abs(balance))}{balance < 0 ? " (change)" : ""}</span>
                </div>
                <button className="btn btn-primary w-100" disabled={submitting || !items.length} onClick={handleSubmit}>
                  {submitting ? <span className="spinner-border spinner-border-sm me-2" /> : <i className="ti ti-check me-1" />}
                  Complete Sale
                </button>
              </div>
            </div>
          </div>

        </div>
      </div>
    </div>
  );
}
