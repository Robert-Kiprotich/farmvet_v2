import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import API from "../../services/api";
import { showConfirm, showError, showSuccess } from "../../components/alerts/Alerts";
import { asList, errorMessage, fmtDateTime, money } from "../cpd/shared";

const CERT_WAIT_MS = 4 * 24 * 3600 * 1000; // certificate opens 4 days after the meeting

/** 07XXXXXXXX, 01XXXXXXXX, 7XXXXXXXX, 2547XXXXXXXX → 254XXXXXXXXX */
function normalizePhone(raw: string): string | null {
  const d = raw.replace(/[\s+\-]/g, "");
  if (/^0[17]\d{8}$/.test(d)) return "254" + d.slice(1);
  if (/^254[17]\d{8}$/.test(d)) return d;
  if (/^[17]\d{8}$/.test(d)) return "254" + d;
  return null;
}

type Panel =
  | { type: "create" }
  | { type: "edit"; meeting: any }
  | { type: "manage"; meeting: any }
  | { type: "pay"; meeting: any }
  | { type: "points"; meeting: any };

/* ─────────────────────────── page ─────────────────────────── */

export default function ZoomPage() {
  const [meetings, setMeetings] = useState<any[]>([]);
  const [isAdmin, setIsAdmin] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [search, setSearch] = useState("");
  const [panel, setPanel] = useState<Panel | null>(null);
  const [payBusy, setPayBusy] = useState(false);
  const [rowBusy, setRowBusy] = useState<number | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const res = await API.get("zoom/meetings/");
      setIsAdmin(res.data?.is_admin === true);
      setMeetings(asList(res.data?.meetings ?? res.data));
    } catch (err: any) {
      if (err.response?.status === 401) window.location.href = "/login";
      else setError("Could not load meetings. Please refresh.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { load(); }, [load]);

  const filtered = useMemo(() => {
    const q = search.trim().toLowerCase();
    if (!q) return meetings;
    return meetings.filter(m =>
      (m.topic || "").toLowerCase().includes(q) ||
      (m.facilitator || "").toLowerCase().includes(q)
    );
  }, [meetings, search]);

  function requestClose() {
    if (payBusy) return; // payment in flight, don't abandon it
    setPanel(null);
  }

  async function handlePaid() {
    setPayBusy(false);
    setPanel(null);
    await load();
    showSuccess("Your payment was received. Access will be enabled shortly.", "Payment successful");
  }

  async function toggleAccess(m: any) {
    setRowBusy(m.id);
    try {
      await API.patch(`zoom/meetings/${m.id}/`, { access_enabled: !m.access_enabled });
      await load();
    } catch (err: any) {
      showError(errorMessage(err, "Could not change access."), "Update failed", 5000);
    } finally {
      setRowBusy(null);
    }
  }

  async function remove(m: any) {
    if (!(await showConfirm(`"${m.topic}" will be removed from this list. It is not deleted from Zoom.`,
      "Delete meeting?", "Yes, delete"))) return;
    setRowBusy(m.id);
    try {
      await API.delete(`zoom/meetings/${m.id}/`);
      await load();
    } catch (err: any) {
      showError(errorMessage(err, "Could not delete the meeting."), "Delete failed", 6000);
    } finally {
      setRowBusy(null);
    }
  }

  const panelTitle = !panel ? "" :
    panel.type === "create" ? "Schedule meeting" :
    panel.type === "edit" ? "Edit meeting" :
    panel.type === "manage" ? "Manage meeting" :
    panel.type === "pay" ? "Pay for meeting" : "Attendance & points";

  return (
    <div className="page-wrapper">
      <div className="content">
        {/* Header */}
        <div className="d-flex align-items-center justify-content-between mb-3 flex-wrap gap-2">
          <div>
            <h4 className="fw-semibold mb-1">Scheduled Meetings</h4>
            <p className="text-muted fs-13 mb-0">
              {isAdmin
                ? "Schedule Zoom meetings, control who can join, and upload attendance."
                : "Pay for a meeting, join it when access opens, then view your points and certificate."}
            </p>
          </div>
          <div className="d-flex gap-2">
            {isAdmin && (
              <button className="btn btn-primary btn-sm" onClick={() => setPanel({ type: "create" })}>
                <i className="ti ti-plus me-1" />Schedule meeting
              </button>
            )}
            <button className="btn btn-outline-secondary btn-sm" onClick={load} disabled={loading}>
              <i className={`ti ti-refresh me-1 ${loading ? "fa-spin" : ""}`} />Refresh
            </button>
          </div>
        </div>

        <div className="card shadow-none border">
          <div className="card-header border-bottom py-3">
            <div className="input-group input-group-flat" style={{ maxWidth: 300 }}>
              <span className="input-group-text bg-transparent border-end-0"><i className="ti ti-search text-muted" /></span>
              <input type="text" className="form-control border-start-0 ps-1 fs-13"
                placeholder="Search topic or facilitator…"
                value={search} onChange={e => setSearch(e.target.value)} />
              {search && <button className="btn btn-sm btn-link text-muted px-2" onClick={() => setSearch("")}><i className="ti ti-x" /></button>}
            </div>
          </div>

          <div className="card-body p-0">
            {error && <div className="alert alert-danger fs-13 m-3">{error}</div>}
            {loading && meetings.length === 0 ? (
              <div className="d-flex align-items-center justify-content-center py-5 text-muted">
                <span className="spinner-border spinner-border-sm me-2" />Loading meetings…
              </div>
            ) : filtered.length === 0 ? (
              <div className="d-flex flex-column align-items-center justify-content-center py-5 text-muted">
                <i className="ti ti-video fs-1 mb-2" />
                <p className="fs-14 mb-0">{meetings.length === 0 ? "No meetings scheduled." : "No meetings match your search."}</p>
              </div>
            ) : (
              <div className="table-responsive" style={{ opacity: loading ? 0.5 : 1 }}>
                <table className="table table-hover mb-0 fs-13">
                  <thead className="table-light">
                    <tr>
                      <th>Topic</th>
                      <th>Facilitator</th>
                      <th className="text-end">Price</th>
                      <th className="text-nowrap">Start time</th>
                      {isAdmin ? (
                        <>
                          <th className="text-end">Paid</th>
                          <th className="text-center">Access</th>
                          <th className="text-end">Actions</th>
                        </>
                      ) : (
                        <>
                          <th className="text-end">Action</th>
                          <th className="text-end">Points</th>
                        </>
                      )}
                    </tr>
                  </thead>
                  <tbody>
                    {filtered.map(m => (
                      <tr key={m.id}>
                        <td className="fw-semibold">{m.topic}</td>
                        <td>{m.facilitator || "—"}</td>
                        <td className="text-end text-nowrap">{money(m.price)}</td>
                        <td className="text-nowrap">{fmtDateTime(m.start_time)}</td>

                        {isAdmin ? (
                          <>
                            <td className="text-end">{m.paid_count ?? 0}</td>
                            <td className="text-center">
                              <div className="form-check form-switch d-inline-block mb-0">
                                <input className="form-check-input" type="checkbox" checked={!!m.access_enabled}
                                  disabled={rowBusy === m.id} onChange={() => toggleAccess(m)}
                                  title={m.access_enabled ? "Access on" : "Access off"} />
                              </div>
                            </td>
                            <td className="text-end text-nowrap">
                              <a href={m.join_url} target="_blank" rel="noopener noreferrer" className="btn btn-success btn-sm me-1">
                                <i className="ti ti-video me-1" />Join
                              </a>
                              <button className="btn btn-info btn-sm me-1" onClick={() => setPanel({ type: "manage", meeting: m })}>
                                <i className="ti ti-users me-1" />Manage
                              </button>
                              <button className="btn btn-outline-secondary btn-sm btn-icon me-1" title="Edit"
                                onClick={() => setPanel({ type: "edit", meeting: m })}>
                                <i className="ti ti-edit" />
                              </button>
                              <button className="btn btn-outline-danger btn-sm btn-icon" title="Delete"
                                disabled={rowBusy === m.id} onClick={() => remove(m)}>
                                <i className="ti ti-trash" />
                              </button>
                            </td>
                          </>
                        ) : (
                          <>
                            <td className="text-end text-nowrap">
                              {m.can_join ? (
                                <a href={m.join_url} target="_blank" rel="noopener noreferrer" className="btn btn-success btn-sm">
                                  <i className="ti ti-video me-1" />Join meeting
                                </a>
                              ) : m.is_blocked ? (
                                <button className="btn btn-danger btn-sm" disabled>Blocked</button>
                              ) : m.user_has_paid || !m.access_enabled ? (
                                <button className="btn btn-secondary btn-sm" disabled>Access disabled</button>
                              ) : (
                                <button className="btn btn-warning btn-sm" onClick={() => setPanel({ type: "pay", meeting: m })}>
                                  <i className="ti ti-credit-card me-1" />Pay now
                                </button>
                              )}
                            </td>
                            <td className="text-end text-nowrap">
                              {m.can_join ? (
                                <button className="btn btn-info btn-sm" onClick={() => setPanel({ type: "points", meeting: m })}>
                                  <i className="ti ti-award me-1" />View points
                                </button>
                              ) : (
                                <button className="btn btn-secondary btn-sm" disabled>
                                  {m.user_has_paid ? "Unavailable" : "Pay to view"}
                                </button>
                              )}
                            </td>
                          </>
                        )}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Offcanvas */}
      {panel && (
        <>
          <div className="offcanvas-backdrop fade show" onClick={requestClose} />
          <div className="offcanvas offcanvas-end show" style={{ visibility: "visible", width: "min(760px, 100vw)" }} tabIndex={-1}>
            <div className="offcanvas-header border-bottom">
              <h5 className="offcanvas-title fw-semibold">{panelTitle}</h5>
              <button type="button" className="btn-close" onClick={requestClose} disabled={payBusy} />
            </div>

            {(panel.type === "create" || panel.type === "edit") && (
              <MeetingFormPanel
                key={panel.type === "edit" ? `edit-${panel.meeting.id}` : "create"}
                meeting={panel.type === "edit" ? panel.meeting : null}
                onClose={requestClose}
                onSaved={async () => { setPanel(null); await load(); }} />
            )}
            {panel.type === "manage" && (
              <ManagePanel key={`mng-${panel.meeting.id}`} meeting={panel.meeting}
                onClose={requestClose} onChanged={load} />
            )}
            {panel.type === "pay" && (
              <ZoomPayPanel key={`pay-${panel.meeting.id}`} meeting={panel.meeting}
                onBusy={setPayBusy} onClose={requestClose} onPaid={handlePaid} />
            )}
            {panel.type === "points" && (
              <PointsPanel key={`pts-${panel.meeting.id}`} meeting={panel.meeting} onClose={requestClose} />
            )}
          </div>
        </>
      )}
    </div>
  );
}

/* ─────────────────────────── Admin: schedule / edit ─────────────────────────── */

function MeetingFormPanel({ meeting, onClose, onSaved }: {
  meeting: any | null; onClose: () => void; onSaved: () => void;
}) {
  const editing = !!meeting;
  const [form, setForm] = useState({
    topic: meeting?.topic ?? "",
    start_time: "",
    facilitator: meeting?.facilitator ?? "",
    price: meeting ? String(meeting.price ?? "") : "",
    kvb_reg_no: meeting?.kvb_reg_no ?? "",
    activity_points: meeting?.activity_points != null ? String(meeting.activity_points) : "",
    access_enabled: meeting ? !!meeting.access_enabled : true,
  });
  const [saving, setSaving] = useState(false);
  const set = (k: keyof typeof form) => (e: React.ChangeEvent<HTMLInputElement>) =>
    setForm(f => ({ ...f, [k]: e.target.value }));

  async function save() {
    if (!editing && (!form.topic.trim() || !form.start_time))
      return showError("Topic and start time are required.", "Missing details", 5000);
    if (form.price !== "" && Number(form.price) < 0)
      return showError("Price cannot be negative.", "Invalid price", 5000);

    setSaving(true);
    try {
      const common = {
        facilitator: form.facilitator.trim(),
        price: form.price || "0",
        kvb_reg_no: form.kvb_reg_no.trim(),
        activity_points: form.activity_points,
      };
      if (editing) {
        await API.patch(`zoom/meetings/${meeting.id}/`, { ...common, access_enabled: form.access_enabled });
        showSuccess("Meeting updated.", "Saved");
      } else {
        await API.post("zoom/meetings/", { ...common, topic: form.topic.trim(), start_time: form.start_time });
        showSuccess(`"${form.topic.trim()}" has been scheduled.`, "Meeting created");
      }
      onSaved();
    } catch (err: any) {
      if (err.response?.data?.error === "zoom_not_connected") {
        const ok = await showConfirm(
          "Connect your Zoom account to schedule meetings. You will be redirected to Zoom.",
          "Zoom not connected", "Connect Zoom");
        if (ok) {
          try {
            const r = await API.get("zoom/auth-url/");
            window.location.href = r.data.url;
          } catch (e: any) {
            showError(errorMessage(e, "Could not start the Zoom connection."), "Connection failed", 6000);
          }
        }
      } else {
        showError(errorMessage(err, "Could not save the meeting."), "Save failed", 6000);
      }
    } finally {
      setSaving(false);
    }
  }

  async function cancel() {
    const dirty = editing || Object.values(form).some(v => typeof v === "string" && v.trim() !== "");
    if (!editing && dirty && !(await showConfirm("Your changes will be lost.", "Discard this meeting?", "Yes, discard"))) return;
    onClose();
  }

  return (
    <>
      <div className="offcanvas-body fs-13">
        {editing && (
          <div className="alert alert-info fs-12 py-2">
            Topic and start time are set in Zoom and can't be changed here.
          </div>
        )}
        <div className="row g-3">
          <div className="col-12">
            <label className="form-label fw-medium">Topic {!editing && <span className="text-danger">*</span>}</label>
            <input className="form-control" value={form.topic} onChange={set("topic")} disabled={editing} autoFocus={!editing} />
          </div>
          {!editing && (
            <div className="col-md-6">
              <label className="form-label fw-medium">Start time <span className="text-danger">*</span></label>
              <input type="datetime-local" className="form-control" value={form.start_time} onChange={set("start_time")} />
            </div>
          )}
          <div className={editing ? "col-12" : "col-md-6"}>
            <label className="form-label fw-medium">Facilitator</label>
            <input className="form-control" value={form.facilitator} onChange={set("facilitator")} placeholder="Defaults to you" />
          </div>
          <div className="col-md-4">
            <label className="form-label fw-medium">Price (KES)</label>
            <input type="number" min={0} step="1" className="form-control" placeholder="0" value={form.price} onChange={set("price")} />
          </div>
          <div className="col-md-4">
            <label className="form-label fw-medium">KVB reg. no. (certificate)</label>
            <input className="form-control" value={form.kvb_reg_no} onChange={set("kvb_reg_no")} />
          </div>
          <div className="col-md-4">
            <label className="form-label fw-medium">Activity points</label>
            <input type="number" min={0} className="form-control" value={form.activity_points} onChange={set("activity_points")} />
          </div>
          {editing && (
            <div className="col-12">
              <div className="form-check form-switch">
                <input className="form-check-input" type="checkbox" id="accessEnabled" checked={form.access_enabled}
                  onChange={e => setForm(f => ({ ...f, access_enabled: e.target.checked }))} />
                <label className="form-check-label" htmlFor="accessEnabled">
                  Access enabled (turn off to stop everyone joining)
                </label>
              </div>
            </div>
          )}
        </div>
      </div>
      <div className="offcanvas-footer border-top p-3 d-flex justify-content-between align-items-center gap-2">
        <button className="btn btn-outline-secondary btn-sm" onClick={cancel} disabled={saving}>Cancel</button>
        <button className="btn btn-primary btn-sm" onClick={save} disabled={saving}>
          {saving ? <span className="spinner-border spinner-border-sm me-1" /> : <i className="ti ti-check me-1" />}
          {editing ? "Save changes" : "Schedule meeting"}
        </button>
      </div>
    </>
  );
}

/* ─────────────────────────── Admin: payments, blocking, attendance upload ─────────────────────────── */

function ManagePanel({ meeting, onClose, onChanged }: {
  meeting: any; onClose: () => void; onChanged: () => void;
}) {
  const [tab, setTab] = useState<"payments" | "attendance">("payments");
  const [payments, setPayments] = useState<any[]>([]);
  const [attendance, setAttendance] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [busyId, setBusyId] = useState<number | null>(null);
  const [file, setFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const fileRef = useRef<HTMLInputElement>(null);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const [p, a] = await Promise.all([
        API.get(`zoom/meetings/${meeting.id}/payments/`),
        API.get(`zoom/attendance/${meeting.meeting_id}/`),
      ]);
      setPayments(asList(p.data?.payments ?? p.data));
      setAttendance(asList(a.data?.attendance ?? a.data));
    } catch (err: any) {
      showError(errorMessage(err, "Could not load meeting details."), "Load failed", 5000);
    } finally {
      setLoading(false);
    }
  }, [meeting.id, meeting.meeting_id]);

  useEffect(() => { load(); }, [load]);

  async function toggleAccess(p: any) {
    setBusyId(p.id);
    try {
      await API.post(`zoom/payments/${p.id}/access/`, { enabled: !p.user_access_enabled });
      await load();
    } catch (err: any) {
      showError(errorMessage(err, "Could not change access."), "Update failed", 5000);
    } finally { setBusyId(null); }
  }

  async function toggleBlock(p: any) {
    if (!p.is_blocked && !(await showConfirm(
      `${p.user_name} will no longer be able to join this meeting.`, "Block this user?", "Yes, block"))) return;
    setBusyId(p.id);
    try {
      await API.post(`zoom/meetings/${meeting.id}/block/`, { user: p.user_id, blocked: !p.is_blocked });
      await load();
    } catch (err: any) {
      showError(errorMessage(err, "Could not update the block."), "Update failed", 5000);
    } finally { setBusyId(null); }
  }

  async function upload() {
    if (!file) return showError("Choose an Excel (.xlsx) file first.", "No file", 4000);
    setUploading(true);
    try {
      const fd = new FormData();
      fd.append("file", file);
      const res = await API.post(`zoom/meetings/${meeting.id}/attendance-upload/`, fd);
      const d = res.data;
      const msg = `Created ${d.created}, updated ${d.updated}` +
        (d.error_count ? `, ${d.error_count} row(s) skipped:\n${(d.errors || []).join("\n")}` : "");
      if (d.error_count) showError(msg, "Imported with errors", 9000);
      else showSuccess(msg, "Attendance imported");
      setFile(null);
      if (fileRef.current) fileRef.current.value = "";
      await load();
      onChanged();
    } catch (err: any) {
      showError(errorMessage(err, "Could not import the file."), "Import failed", 6000);
    } finally { setUploading(false); }
  }

  return (
    <>
      <div className="offcanvas-body fs-13">
        <div className="border rounded p-3 mb-3">
          <div className="fw-semibold fs-14 mb-1">{meeting.topic}</div>
          <div className="text-muted fs-12">Meeting ID {meeting.meeting_id} · {fmtDateTime(meeting.start_time)}</div>
        </div>

        <ul className="nav nav-tabs mb-3">
          <li className="nav-item">
            <button className={`nav-link ${tab === "payments" ? "active" : ""}`} onClick={() => setTab("payments")}>
              Payments &amp; access ({payments.length})
            </button>
          </li>
          <li className="nav-item">
            <button className={`nav-link ${tab === "attendance" ? "active" : ""}`} onClick={() => setTab("attendance")}>
              Attendance ({attendance.length})
            </button>
          </li>
        </ul>

        {loading ? (
          <div className="d-flex align-items-center justify-content-center py-5 text-muted">
            <span className="spinner-border spinner-border-sm me-2" />Loading…
          </div>
        ) : tab === "payments" ? (
          payments.length === 0 ? (
            <div className="text-center text-muted py-4"><i className="ti ti-credit-card-off fs-2 d-block mb-2" />No payments yet.</div>
          ) : (
            <div className="table-responsive">
              <table className="table table-hover mb-0 fs-13">
                <thead className="table-light">
                  <tr>
                    <th>User</th><th>Phone</th><th className="text-end">Amount</th>
                    <th>Status</th><th>Receipt</th><th className="text-end">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {payments.map(p => (
                    <tr key={p.id}>
                      <td className="fw-semibold">{p.user_name}{p.is_blocked && <span className="badge bg-danger ms-1">Blocked</span>}</td>
                      <td>{p.phone_number}</td>
                      <td className="text-end">{money(p.amount)}</td>
                      <td>
                        <span className={p.status === "Completed" ? "badge bg-success-transparent text-success"
                          : p.status === "Failed" ? "badge bg-danger-transparent text-danger"
                          : "badge bg-warning-transparent text-warning"}>{p.status}</span>
                      </td>
                      <td>{p.mpesa_receipt || "—"}</td>
                      <td className="text-end text-nowrap">
                        <button className={`btn btn-sm me-1 ${p.user_access_enabled ? "btn-outline-warning" : "btn-outline-success"}`}
                          disabled={busyId === p.id} onClick={() => toggleAccess(p)}>
                          {p.user_access_enabled ? "Disable access" : "Enable access"}
                        </button>
                        <button className={`btn btn-sm ${p.is_blocked ? "btn-outline-secondary" : "btn-outline-danger"}`}
                          disabled={busyId === p.id} onClick={() => toggleBlock(p)}>
                          {p.is_blocked ? "Unblock" : "Block"}
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )
        ) : (
          <>
            <div className="border rounded p-3 mb-3">
              <div className="fw-medium mb-1">Import attendance from Excel</div>
              <div className="text-muted fs-12 mb-2">
                First row must have the columns <code>user_name</code>, <code>kvb_number</code>, <code>duration</code> and <code>points</code>.
                Rows are matched by KVB number, so re-uploading updates existing ones.
              </div>
              <div className="d-flex gap-2">
                <input ref={fileRef} type="file" accept=".xlsx,.xlsm" className="form-control form-control-sm"
                  onChange={e => setFile(e.target.files?.[0] ?? null)} />
                <button className="btn btn-primary btn-sm text-nowrap" onClick={upload} disabled={uploading || !file}>
                  {uploading ? <span className="spinner-border spinner-border-sm me-1" /> : <i className="ti ti-upload me-1" />}Import
                </button>
              </div>
            </div>
            {attendance.length === 0 ? (
              <div className="text-center text-muted py-4"><i className="ti ti-file-off fs-2 d-block mb-2" />No attendance records yet.</div>
            ) : (
              <div className="table-responsive">
                <table className="table table-hover mb-0 fs-13">
                  <thead className="table-light">
                    <tr><th>Name</th><th>KVB number</th><th className="text-end">Duration (min)</th><th className="text-end">Points</th></tr>
                  </thead>
                  <tbody>
                    {attendance.map(a => (
                      <tr key={a.id}>
                        <td>{a.user_name}</td><td>{a.kvb_number || "—"}</td>
                        <td className="text-end">{a.duration}</td><td className="text-end">{a.points}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </>
        )}
      </div>

      <div className="offcanvas-footer border-top p-3 d-flex justify-content-between align-items-center gap-2">
        <button className="btn btn-outline-secondary btn-sm" onClick={onClose}>Close</button>
        <button className="btn btn-outline-secondary btn-sm" onClick={load} disabled={loading}>
          <i className={`ti ti-refresh me-1 ${loading ? "fa-spin" : ""}`} />Refresh
        </button>
      </div>
    </>
  );
}

/* ─────────────────────────── Vet: M-Pesa payment ─────────────────────────── */

type PayState = "idle" | "sending" | "waiting" | "success" | "failed";

function ZoomPayPanel({ meeting, onBusy, onClose, onPaid }: {
  meeting: any; onBusy: (b: boolean) => void; onClose: () => void; onPaid: () => void;
}) {
  const [phone, setPhone] = useState("");
  const [state, setState] = useState<PayState>("idle");
  const [msg, setMsg] = useState("");
  const [attempt, setAttempt] = useState(0);
  const timer = useRef<any>(null);
  const alive = useRef(true);
  const MAX_ATTEMPTS = 12; // × 5s = 60s

  useEffect(() => {
    alive.current = true;
    return () => { alive.current = false; clearInterval(timer.current); onBusy(false); };
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => { onBusy(state === "sending" || state === "waiting"); }, [state]); // eslint-disable-line react-hooks/exhaustive-deps

  function poll(checkoutId: string) {
    let n = 0;
    let inflight = false;
    let done = false;
    timer.current = setInterval(async () => {
      if (inflight || done) return;
      inflight = true;
      n++;
      setAttempt(n);
      try {
        const r = await API.post("mpesa/status/", new URLSearchParams({ checkout_request_id: checkoutId }));
        if (!alive.current) return;
        const st = r.data?.status;
        if (st === "Completed") {
          done = true; clearInterval(timer.current);
          setState("success");
          setTimeout(() => alive.current && onPaid(), 1500);
          return;
        }
        if (st === "Failed") {
          done = true; clearInterval(timer.current);
          setMsg("The payment failed or was cancelled on your phone. Please try again.");
          setState("failed");
          return;
        }
      } catch {
        /* transient network error, keep polling */
      } finally {
        inflight = false;
      }
      if (n >= MAX_ATTEMPTS && !done && alive.current) {
        done = true; clearInterval(timer.current);
        setMsg("We did not receive a confirmation in time. If M-Pesa charged you, your access will update shortly. Refresh the page in a minute.");
        setState("failed");
      }
    }, 5000);
  }

  async function pay() {
    setMsg("");
    const normalized = normalizePhone(phone);
    if (!normalized) return setMsg("Enter a valid M-Pesa number, e.g. 0712345678 or 254712345678.");
    setState("sending");
    try {
      const res = await API.post("mpesa/pay/", new URLSearchParams({
        phone_number: normalized,
        meeting_id: String(meeting.id), // the ZoomMeeting DB id, as zoom_mpesa_payment expects
      }));
      const r = res.data?.response;
      if (String(r?.ResponseCode) === "0" && r?.CheckoutRequestID) {
        setAttempt(0);
        setState("waiting");
        poll(r.CheckoutRequestID);
      } else {
        setMsg(r?.CustomerMessage || r?.errorMessage || "M-Pesa rejected the request. Please try again.");
        setState("failed");
      }
    } catch (err: any) {
      setMsg(errorMessage(err, "Network error. Please try again."));
      setState("failed");
    }
  }

  const busy = state === "sending" || state === "waiting";

  return (
    <>
      <div className="offcanvas-body fs-13">
        <div className="border rounded p-3 mb-4">
          <div className="fw-semibold fs-14 mb-1">{meeting.topic}</div>
          <div className="text-muted fs-12 mb-2">
            {meeting.facilitator && <>{meeting.facilitator} · </>}{fmtDateTime(meeting.start_time)}
          </div>
          <div className="d-flex justify-content-between align-items-center">
            <span className="text-muted">Amount to pay</span>
            <span className="fw-bold fs-5 text-success">{money(meeting.price)}</span>
          </div>
        </div>

        {(state === "idle" || state === "failed") && (
          <div className="mx-auto" style={{ maxWidth: 380 }}>
            {msg && <div className="alert alert-danger fs-12 py-2">{msg}</div>}
            <label className="form-label fs-13 fw-medium">M-Pesa number</label>
            <div className="input-group mb-3">
              <span className="input-group-text bg-transparent"><i className="ti ti-device-mobile text-muted" /></span>
              <input className="form-control" inputMode="tel" placeholder="e.g. 0712345678 or 254712345678"
                value={phone} onChange={e => setPhone(e.target.value)}
                onKeyDown={e => { if (e.key === "Enter") pay(); }} autoFocus />
            </div>
            <button className="btn btn-success w-100" onClick={pay}>
              <i className="ti ti-credit-card me-1" />{state === "failed" ? "Try again" : "Pay with M-Pesa"}
            </button>
            <div className="text-muted fs-12 mt-2">You will receive an STK push on this number. Enter your M-Pesa PIN to approve.</div>
          </div>
        )}

        {state === "sending" && (
          <div className="text-center py-4">
            <div className="spinner-border text-success mb-2" />
            <div>Sending the payment request…</div>
          </div>
        )}

        {state === "waiting" && (
          <div className="text-center py-4">
            <div className="spinner-border text-success mb-2" />
            <div className="fw-semibold">Check your phone</div>
            <div className="text-muted fs-12">Enter your M-Pesa PIN to complete the payment. Waiting for confirmation… ({attempt}/{MAX_ATTEMPTS})</div>
          </div>
        )}

        {state === "success" && (
          <div className="text-center py-4">
            <i className="ti ti-circle-check text-success" style={{ fontSize: 56 }} />
            <div className="fw-semibold fs-5 mt-2">Payment successful!</div>
          </div>
        )}
      </div>

      <div className="offcanvas-footer border-top p-3 d-flex justify-content-between align-items-center gap-2">
        <button className="btn btn-outline-secondary btn-sm" onClick={onClose} disabled={busy}>Close</button>
        <span className="text-muted fs-12">Secured by Safaricom M-Pesa</span>
      </div>
    </>
  );
}

/* ─────────────────────────── Vet: attendance, points, certificate ─────────────────────────── */

function PointsPanel({ meeting, onClose }: { meeting: any; onClose: () => void }) {
  const [attendance, setAttendance] = useState<any[]>([]);
  const [me, setMe] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [certBusy, setCertBusy] = useState<number | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const [att, u] = await Promise.all([
        API.get(`zoom/attendance/${meeting.meeting_id}/`),
        API.get("users/me/"),
      ]);
      setAttendance(asList(att.data?.attendance ?? att.data));
      if (att.data?.error) setError(att.data.error);
      setMe(u.data);
    } catch (err: any) {
      if (err.response?.status === 401) window.location.href = "/login";
      else setError(errorMessage(err, "Could not load attendance."));
    } finally {
      setLoading(false);
    }
  }, [meeting.meeting_id]);

  useEffect(() => { load(); }, [load]);

  async function certificate(i: number) {
    setCertBusy(i);
    try {
      const first = encodeURIComponent(me?.firstname || "-");
      const last = encodeURIComponent(me?.lastname || "-");
      const res = await API.post(
        `get-certificate/${first}/${last}/`,
        new URLSearchParams({ meeting_id: String(meeting.id) }),
        { responseType: "blob" }
      );
      const url = URL.createObjectURL(res.data);
      const a = document.createElement("a");
      a.href = url;
      a.download = `certificate-${meeting.meeting_id}.jpg`; // get_certificate returns a JPEG
      document.body.appendChild(a);
      a.click();
      a.remove();
      URL.revokeObjectURL(url);
    } catch (err: any) {
      showError(errorMessage(err, "Could not generate your certificate."), "Certificate failed", 6000);
    } finally {
      setCertBusy(null);
    }
  }

  return (
    <>
      <div className="offcanvas-body fs-13">
        <div className="border rounded p-3 mb-3">
          <div className="fw-semibold fs-14 mb-1">{meeting.topic}</div>
          <div className="text-muted fs-12">Meeting ID {meeting.meeting_id} · {fmtDateTime(meeting.start_time)}</div>
        </div>

        {error && <div className="alert alert-danger fs-12 py-2">{error}</div>}

        {loading ? (
          <div className="d-flex align-items-center justify-content-center py-5 text-muted">
            <span className="spinner-border spinner-border-sm me-2" />Loading attendance…
          </div>
        ) : attendance.length === 0 ? (
          <div className="text-center text-muted py-4">
            <i className="ti ti-file-off fs-2 d-block mb-2" />No attendance records found.
          </div>
        ) : (
          <div className="table-responsive">
            <table className="table table-hover mb-0 fs-13">
              <thead className="table-light">
                <tr>
                  <th>Name</th>
                  <th>KVB number</th>
                  <th className="text-end">Duration (min)</th>
                  <th className="text-end">Points</th>
                  <th className="text-end">Certificate</th>
                </tr>
              </thead>
              <tbody>
                {attendance.map((a, i) => {
                  // Excel-imported rows have no join_time, so fall back to the meeting's start time.
                  const base = a.join_time || meeting.start_time;
                  const eligible = base && new Date(base).getTime() <= Date.now() - CERT_WAIT_MS;
                  return (
                    <tr key={a.id ?? i}>
                      <td>{a.user_name}</td>
                      <td>{a.kvb_number || "—"}</td>
                      <td className="text-end">{a.duration}</td>
                      <td className="text-end">{a.points}</td>
                      <td className="text-end text-nowrap">
                        {eligible ? (
                          <button className="btn btn-success btn-sm" disabled={certBusy === i} onClick={() => certificate(i)}>
                            {certBusy === i
                              ? <span className="spinner-border spinner-border-sm" />
                              : <><i className="ti ti-download me-1" />Download</>}
                          </button>
                        ) : (
                          <button className="btn btn-secondary btn-sm" disabled>Available upon completion</button>
                        )}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>

      <div className="offcanvas-footer border-top p-3 d-flex justify-content-between align-items-center gap-2">
        <button className="btn btn-outline-secondary btn-sm" onClick={onClose}>Close</button>
        <button className="btn btn-outline-secondary btn-sm" onClick={load} disabled={loading}>
          <i className={`ti ti-refresh me-1 ${loading ? "fa-spin" : ""}`} />Refresh
        </button>
      </div>
    </>
  );
}
