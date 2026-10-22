import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import API from "../../services/api";
import { showConfirm, showError, showSuccess } from "../../components/alerts/Alerts";
import {
  MAX_FAILED, PASS_MARK,
  asList, downloadBlob, errorMessage, fmtDate, fmtDateTime, money,
} from "./shared";
import { useNavigate } from "react-router-dom";
import { all_routes } from "../../routes/all_routes";


// Field name your CommentSerializer expects for the comment body – adjust if different.
const COMMENT_FIELD = "content";
const commentText = (c: any) => c.content ?? c.text ?? c.body ?? c.comment ?? "";
const commentAuthor = (c: any) =>
  c.author_name || (typeof c.author === "object" ? c.author?.username : c.author) || "User";


function formatCountdown(ms: number) {
  if (ms <= 0) return "now";
  const s = Math.floor(ms / 1000);
  const d = Math.floor(s / 86400);
  const h = Math.floor((s % 86400) / 3600);
  const m = Math.floor((s % 3600) / 60);
  return [d ? `${d}d` : "", h ? `${h}h` : "", `${m}m`].filter(Boolean).join(" ");
}

/** Accepts 07XXXXXXXX, 01XXXXXXXX, 7XXXXXXXX, 2547XXXXXXXX (spaces/+/- ignored) → 254XXXXXXXXX */
function normalizePhone(raw: string): string | null {
  const d = raw.replace(/[\s+\-]/g, "");
  if (/^0[17]\d{8}$/.test(d)) return "254" + d.slice(1);
  if (/^254[17]\d{8}$/.test(d)) return d;
  if (/^[17]\d{8}$/.test(d)) return "254" + d;
  return null;
}
const saleBalance = (sale: any) =>
  Number(sale?.total_amount || 0) - Number(sale?.amount_paid || 0);

async function loadAllTutorials() {
  const all: any[] = [];
  let page = 1;
  while (page <= 50) {
    const res = await API.get("tutorials/list/", { params: { page } });
    all.push(...asList(res.data));
    if (!res.data?.next) break;
    page++;
  }
  return all;
}
function useIsAdmin() {
  const [isAdmin, setIsAdmin] = useState(false);
  useEffect(() => {
    let alive = true;
    API.get("users/me/")
      .then(res => {
        const u = res.data;
        const role = String(u?.role?.role_name || "").toLowerCase();
        if (alive) setIsAdmin(u?.is_admin === true || role.includes("admin"));
      })
      .catch(() => { if (alive) setIsAdmin(false); });
    return () => { alive = false; };
  }, []);
  return isAdmin;
}
type Panel =
  | { type: "create" }
  | { type: "manage"; tutorial: any }
  | { type: "pay"; tutorial: any }
  | { type: "lesson"; tutorial: any };            // exam removed

type Guard = "none" | "pay"; 
export default function CpdPage() {
  const [tutorials, setTutorials] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const [search, setSearch] = useState("");
  const [accessFilter, setAccessFilter] = useState<"all" | "paid" | "unpaid">("all");
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(25);
    const [panel, setPanel] = useState<Panel | null>(null); 
const [guard, setGuard] = useState<Guard>("none");
  const navigate = useNavigate();
const isAdmin = useIsAdmin();


  // For admins every lesson counts as paid/unlocked
  const items = useMemo(
    () => tutorials.map(t => ({ ...t, has_paid: isAdmin || t.has_paid })),
    [tutorials, isAdmin]
  );
  const load = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      setTutorials(await loadAllTutorials());
    } catch (err: any) {
      if (err.response?.status === 401) window.location.href = "/login";
      else setError("Could not load lessons. Please refresh.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { load(); }, [load]);
  useEffect(() => { setPage(1); }, [search, accessFilter]);

  const filtered = useMemo(() => {
        let list = items;
    if (accessFilter === "paid") list = list.filter(t => t.has_paid);
    if (accessFilter === "unpaid") list = list.filter(t => !t.has_paid);
    const q = search.trim().toLowerCase();
    if (q) {
      list = list.filter(t =>
        (t.lesson || "").toLowerCase().includes(q) ||
        (t.cpd_number || "").toLowerCase().includes(q) ||
        (t.presented_by || "").toLowerCase().includes(q)
      );
    }
    return list;
  }, [tutorials, search, accessFilter]);

 function requestClose() {
  if (guard === "pay") return; // payment in flight – don't abandon it
  setGuard("none");
  setPanel(null);
}

  async function handlePaid(tutorial: any) {
    setGuard("none");
    await load();
    setPanel({ type: "lesson", tutorial: { ...tutorial, has_paid: true } });
  }

  const tiles = [
    { label: "Lessons", value: tutorials.length, icon: "ti-books", bg: "bg-primary-gradient-100", color: "text-primary" },
    { label: "Unlocked", value: tutorials.filter(t => t.has_paid).length, icon: "ti-lock-open", bg: "bg-success-gradient-100", color: "text-success" },
    { label: "Awaiting payment", value: tutorials.filter(t => t.lesson && !t.has_paid).length, icon: "ti-lock", bg: "bg-warning-gradient-100", color: "text-warning" },
    { label: "Points unlocked", value: tutorials.filter(t => t.has_paid).reduce((a, t) => a + Number(t.points || 0), 0), icon: "ti-award", bg: "bg-success-gradient-100", color: "text-success" },
  ];

  const totalPages = Math.max(1, Math.ceil(filtered.length / pageSize));
  const start = filtered.length ? (page - 1) * pageSize + 1 : 0;
  const end = Math.min(page * pageSize, filtered.length);

const panelTitle = !panel ? "" :
  panel.type === "create" ? "Create tutorial" :
  panel.type === "manage" ? `Manage: ${panel.tutorial.lesson}` :
  panel.type === "pay" ? "Pay for lesson" :
  (panel.tutorial.lesson || "Lesson");

  return (
    <div className="page-wrapper">
      <div className="content">
        {/* Header */}
        <div className="d-flex align-items-center justify-content-between mb-3 flex-wrap gap-2">
          <div>
            <h4 className="fw-semibold mb-1">Online CPD Lessons</h4>
            <p className="text-muted fs-13 mb-0">Pay for a lesson to unlock its materials, then sit the exam to earn your certificate.</p>
          </div>
         <div className="d-flex gap-2">
  {isAdmin && (
    <button className="btn btn-primary btn-sm" onClick={() => setPanel({ type: "create" })}>
      <i className="ti ti-plus me-1" />Create tutorial
    </button>
  )}
  <button className="btn btn-outline-secondary btn-sm" onClick={load} disabled={loading}>
    <i className={`ti ti-refresh me-1 ${loading ? "fa-spin" : ""}`} />Refresh
  </button>
</div>
        </div>

        {/* Stat tiles */}
        {!loading && tutorials.length > 0 && (
          <div className="row g-3 mb-4">
            {tiles.map(t => (
              <div key={t.label} className="col-6 col-xl-3">
                <div className="card mb-0 shadow-none border">
                  <div className="card-body p-3 position-relative">
                    <p className="fw-medium mb-1 fs-13">{t.label}</p>
                    <h5 className={`mb-0 ${t.color}`}>{t.value}</h5>
                    <div className={`avatar avatar-rounded avatar-sm ${t.bg} position-absolute top-0 end-0 m-2 d-flex align-items-center justify-content-center`}>
                      <i className={`ti ${t.icon} fs-5 ${t.color}`} />
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Table card */}
        <div className="card shadow-none border">
          <div className="card-header border-bottom py-3 d-flex align-items-center justify-content-between flex-wrap gap-2">
            <div className="input-group input-group-flat" style={{ maxWidth: 300 }}>
              <span className="input-group-text bg-transparent border-end-0"><i className="ti ti-search text-muted" /></span>
              <input type="text" className="form-control border-start-0 ps-1 fs-13"
                placeholder="Search lesson, CPD number, presenter…"
                value={search} onChange={e => setSearch(e.target.value)} />
              {search && <button className="btn btn-sm btn-link text-muted px-2" onClick={() => setSearch("")}><i className="ti ti-x" /></button>}
            </div>
            <select className="form-select form-select-sm fs-13" style={{ width: 160 }}
              value={accessFilter} onChange={e => setAccessFilter(e.target.value as any)}>
              <option value="all">All lessons</option>
              <option value="paid">Unlocked</option>
              <option value="unpaid">Not paid</option>
            </select>
          </div>

          <div className="card-body p-0">
            {error && <div className="alert alert-danger fs-13 m-3">{error}</div>}
            {loading ? (
              <div className="d-flex align-items-center justify-content-center py-5 text-muted">
                <span className="spinner-border spinner-border-sm me-2" />Loading lessons…
              </div>
            ) : filtered.length === 0 ? (
              <div className="d-flex flex-column align-items-center justify-content-center py-5 text-muted">
                <i className="ti ti-books fs-1 mb-2" />
                <p className="fs-14 mb-0">{tutorials.length === 0 ? "No lessons available yet." : "No lessons match your filters."}</p>
              </div>
            ) : (
              <div className="table-responsive">
                <table className="table table-hover mb-0 fs-13">
                  <thead className="table-light">
                    <tr>
                      <th>Lesson</th>
                      <th className="text-nowrap">CPD number</th>
                      <th className="text-end text-nowrap">Unit price</th>
                      <th className="text-nowrap">Starts</th>
                      <th className="text-nowrap">Ends</th>
                      <th className="text-end text-nowrap">Contact hours</th>
                      <th className="text-end">Points</th>
                      <th>Presented by</th>
                      <th className="text-end">Action</th>
                    </tr>
                  </thead>
                  <tbody>
                    {filtered.slice((page - 1) * pageSize, page * pageSize).map(t => {
                      const comingSoon = !t.lesson || !String(t.lesson).trim();
                      return (
                        <tr key={t.id}>
                          <td className="fw-semibold">
                            {comingSoon ? <span className="text-muted">—</span> : (
                              <a href="#" className={t.has_paid ? "text-success" : "text-danger"}
                                onClick={e => { e.preventDefault(); setPanel({ type: (isAdmin || t.has_paid) ? "lesson" : "pay", tutorial: t }); }}>
                                {t.lesson}
                              </a>
                            )}
                          </td>
                          <td className="text-nowrap">{t.cpd_number || "—"}</td>
                          <td className="text-end text-nowrap">{money(t.unit_price)}</td>
                          <td className="text-nowrap">{fmtDate(t.start)}</td>
                          <td className="text-nowrap">{fmtDate(t.stop)}</td>
                          <td className="text-end">{t.contact_hours ?? "—"}</td>
                          <td className="text-end">{t.points ?? "—"}</td>
                          <td>{t.presented_by || "—"}</td>
                         <td className="text-end text-nowrap">
  {isAdmin && !comingSoon && (
    <button className="btn btn-outline-primary btn-sm me-1" onClick={() => setPanel({ type: "manage", tutorial: t })}>
      <i className="ti ti-settings me-1" />Manage
    </button>
  )}
  {comingSoon ? (
    <span className="badge bg-secondary-transparent text-secondary">Coming soon</span>
  ) : (isAdmin || t.has_paid) ? (
    <button className="btn btn-success btn-sm" onClick={() => setPanel({ type: "lesson", tutorial: t })}>
      <i className="ti ti-folder-open me-1" />Open lesson
    </button>
  ) : (
    <button className="btn btn-warning btn-sm" onClick={() => setPanel({ type: "pay", tutorial: t })}>
      <i className="ti ti-credit-card me-1" />Pay now
    </button>
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

          {!loading && filtered.length > 0 && (
            <div className="card-footer border-top py-2 px-3 d-flex align-items-center justify-content-between flex-wrap gap-2 fs-12 text-muted">
              <span>Showing <strong>{start}–{end}</strong> of <strong>{filtered.length}</strong> lesson{filtered.length !== 1 ? "s" : ""}</span>
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
          )}
        </div>
      </div>

      {/* ================= Offcanvas (Pay / Lesson / Exam) ================= */}
      {panel && (
        <>
          <div className="offcanvas-backdrop fade show" onClick={requestClose} />
          <div className="offcanvas offcanvas-end show" style={{ visibility: "visible", width: "min(760px, 100vw)" }} tabIndex={-1}>
                      <div className="offcanvas-header border-bottom">
              {panel.type === "manage" ? (
                <select
                  className="form-select fw-semibold"
                  style={{ maxWidth: 420 }}
                  value={String(panel.tutorial.id)}
                  onChange={e => {
                    const t = tutorials.find(x => String(x.id) === e.target.value);
                    if (t) setPanel({ type: "manage", tutorial: t });
                  }}
                >
                  {tutorials.filter(t => String(t.lesson || "").trim()).map(t => (
                    <option key={t.id} value={String(t.id)}>
                      {t.lesson}{t.cpd_number ? ` (${t.cpd_number})` : ""}
                    </option>
                  ))}
                </select>
              ) : (
                <h5 className="offcanvas-title fw-semibold">{panelTitle}</h5>
              )}
              <button type="button" className="btn-close" onClick={requestClose} disabled={guard === "pay"} />
            </div>
     {panel.type === "create" && (
     <CreateTutorialPanel
       onClose={requestClose}
       onCreated={async () => { await load(); setPanel(null); }}
     />
   )}
          {panel.type === "manage" && (
  <ManagePanel key={`manage-${panel.tutorial.id}`} tutorial={panel.tutorial} onClose={requestClose} />
)}
            {panel.type === "pay" && (
              <PayPanel key={`pay-${panel.tutorial.id}`} tutorial={panel.tutorial}
                onGuard={setGuard} onClose={requestClose} onPaid={() => handlePaid(panel.tutorial)} />
            )}
          
            {panel.type === "lesson" && (
  <LessonPanel key={`lesson-${panel.tutorial.id}`} tutorial={panel.tutorial} isAdmin={isAdmin}
    onClose={requestClose}
    onPay={() => setPanel({ type: "pay", tutorial: panel.tutorial })}
    onExam={() => navigate(`${all_routes.exam}/${panel.tutorial.id}`)} />
)}
          </div>
        </>
      )}
    </div>
  );
}

/* ─────────────────────────── M-Pesa payment ─────────────────────────── */

type PayState = "idle" | "sending" | "waiting" | "success" | "failed";

function PayPanel({ tutorial, onGuard, onClose, onPaid }: {
  tutorial: any; onGuard: (g: Guard) => void; onClose: () => void; onPaid: () => void;
}) {
  const [phone, setPhone] = useState("");
  const [state, setState] = useState<PayState>("idle");
  const [msg, setMsg] = useState("");
  const [attempt, setAttempt] = useState(0);
  const timer = useRef<any>(null);
  const alive = useRef(true);
  const MAX_ATTEMPTS = 12; // × 5s = 60s, same as the old page

  useEffect(() => {
    alive.current = true;
    return () => { alive.current = false; clearInterval(timer.current); onGuard("none"); };
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => { onGuard(state === "sending" || state === "waiting" ? "pay" : "none"); }, [state]); // eslint-disable-line react-hooks/exhaustive-deps

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
        /* transient network error – keep polling */
      } finally {
        inflight = false;
      }
      if (n >= MAX_ATTEMPTS && !done && alive.current) {
        done = true; clearInterval(timer.current);
        setMsg("We did not receive a confirmation in time. If M-Pesa charged you, the lesson will unlock shortly – refresh the page in a minute.");
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
     const res = await API.post(
  "mpesa/initiate/",
  new URLSearchParams({
    phone_number: normalized,
    lesson_id: String(tutorial.id),
  }),
  {
    headers: {
      "Content-Type": "application/x-www-form-urlencoded",
    },
  }
);
      const r = res.data?.response;
      if (r?.ResponseCode === "0" && r?.CheckoutRequestID) {
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
          <div className="fw-semibold fs-14 mb-1">{tutorial.lesson}</div>
          <div className="text-muted fs-12 mb-2">
            {tutorial.cpd_number && <>CPD {tutorial.cpd_number} · </>}
            {tutorial.points != null && <>{tutorial.points} points · </>}
            {tutorial.contact_hours != null && <>{tutorial.contact_hours} contact hours</>}
          </div>
          <div className="d-flex justify-content-between align-items-center">
            <span className="text-muted">Amount to pay</span>
            <span className="fw-bold fs-5 text-success">{money(tutorial.unit_price)}</span>
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
            <div className="text-muted fs-12">Opening your lesson…</div>
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


function LessonPanel({
  tutorial,
  isAdmin,
  onClose,
  onPay,
  onExam,
}: {
  tutorial: any;
  isAdmin: boolean;
  onClose: () => void;
  onPay: () => void;
 onExam: () => void;
}) {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [nowTs, setNowTs] = useState(Date.now());

  const [commentSection, setCommentSection] = useState("");
  const [commentBody, setCommentBody] = useState("");
  const [posting, setPosting] = useState(false);

  const [examBusy, setExamBusy] = useState(false);
  const [examMsg, setExamMsg] = useState("");
  const [downloadingId, setDownloadingId] = useState<number | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const res = await API.get(`sections/${tutorial.id}/`);
      setData(res.data);
      const first = res.data?.sections?.[0]?.id;
      setCommentSection(s => s || (first ? String(first) : ""));
    } catch (err: any) {
      if (err.response?.status === 401) window.location.href = "/login";
      else setError(errorMessage(err, "Could not load this lesson."));
    } finally {
      setLoading(false);
    }
  }, [tutorial.id]);

  useEffect(() => { load(); }, [load]);
  useEffect(() => {
    const t = setInterval(() => setNowTs(Date.now()), 30000);
    return () => clearInterval(t);
  }, []);

  const sections: any[] = data?.sections || [];
  const comments: any[] = data?.comments || [];
    const paid = isAdmin || data?.is_admin === true || !!data?.payment_date;
  const unlockMs = !isAdmin && data?.unlock_time ? new Date(data.unlock_time).getTime() : null;
  const timeLeft = unlockMs ? unlockMs - nowTs : null;
  async function handleDownload(s: any) {
    setDownloadingId(s.id);
    try {
      await downloadBlob(`download/${s.id}/`, `${s.title || s.name || "section"}-${s.id}`);
    } catch (err: any) {
      showError(errorMessage(err, "Could not download this file."), "Download failed", 6000);
    } finally {
      setDownloadingId(null);
    }
  }

  async function postComment() {
    if (!commentBody.trim() || !commentSection) return;
    setPosting(true);
    try {
      // Django redirects (302) to the comment list after creating; axios follows it.
      await API.post(`sections/comments/create/${commentSection}/`, { [COMMENT_FIELD]: commentBody.trim() });
      setCommentBody("");
      await load();
    } catch (err: any) {
      showError(errorMessage(err, "Could not post your comment."), "Comment failed", 6000);
    } finally {
      setPosting(false);
    }
  }

 async function startExam() {
  setExamBusy(true);
  setExamMsg("");
  try {
    const res = await API.get(`exam-access/${tutorial.id}/`);
    if (res.data?.locked) throw { response: { data: res.data } };
    onExam();
  } catch (err: any) {
    const d = err.response?.data;
    const reasons: Record<string, string> = {
      not_authenticated: "Please sign in again.",
      payment_required: "Payment is required before you can sit the exam.",
      time_locked: `The exam unlocks on ${fmtDateTime(d?.unlock_time)}.`,
      no_sections: "This lesson has no sections yet.",
    };
    setExamMsg(reasons[d?.reason] || errorMessage(err, "The exam is not available right now."));
  } finally {
    setExamBusy(false);
  }
}

  return (
    <>
      <div className="offcanvas-body fs-13">
        {loading && !data ? (
          <div className="d-flex align-items-center justify-content-center py-5 text-muted">
            <span className="spinner-border spinner-border-sm me-2" />Loading lesson…
          </div>
        ) : (
          <>
            {error && <div className="alert alert-danger fs-13 py-2">{error}</div>}

            <div className="row g-3 mb-3">
              <div className="col-6 col-md-3"><div className="text-muted fs-12">CPD number</div><div className="fw-semibold">{tutorial.cpd_number || "—"}</div></div>
              <div className="col-6 col-md-3"><div className="text-muted fs-12">Points</div><div className="fw-semibold">{tutorial.points ?? "—"}</div></div>
              <div className="col-6 col-md-3"><div className="text-muted fs-12">Contact hours</div><div className="fw-semibold">{tutorial.contact_hours ?? "—"}</div></div>
              <div className="col-6 col-md-3"><div className="text-muted fs-12">Presented by</div><div className="fw-semibold">{tutorial.presented_by || "—"}</div></div>
            </div>

            {data && !paid ? (
              <div className="border rounded text-center py-5">
                <i className="ti ti-lock fs-1 text-warning d-block mb-2" />
                <h6 className="fw-semibold">This lesson is locked</h6>
                <p className="text-muted fs-13">Complete payment to access the materials and exam.</p>
                <button className="btn btn-warning btn-sm" onClick={onPay}>
                  <i className="ti ti-credit-card me-1" />Pay now
                </button>
              </div>
            ) : data && (
              <>
             

                {/* Materials */}
                <div className="card shadow-none border mb-3">
                  <div className="card-header border-bottom py-2 d-flex align-items-center gap-2">
                    <i className="ti ti-files text-primary" />
                    <h6 className="mb-0 fw-semibold fs-14">Lesson materials</h6>
                    <span className="badge bg-primary-transparent text-primary fs-11">{sections.length}</span>
                  </div>
                  <div className="card-body p-0">
                    {sections.length === 0 ? (
                      <div className="text-center text-muted py-4">
                        <i className="ti ti-file-off fs-2 d-block mb-2" />No materials have been uploaded yet.
                      </div>
                    ) : (
                      <ul className="list-group list-group-flush">
                        {sections.map((s, i) => (
                          <li key={s.id} className="list-group-item d-flex align-items-start justify-content-between gap-3 py-3">
                            <div>
                              <div className="fw-semibold">{i + 1}. {s.title || s.name || `Section ${s.id}`}</div>
                              {s.content && <div className="text-muted fs-12 mt-1" style={{ whiteSpace: "pre-line" }}>{s.content}</div>}
                            </div>
                            {s.file && (
                              <button className="btn btn-sm btn-outline-primary text-nowrap"
                                disabled={downloadingId === s.id} onClick={() => handleDownload(s)}>
                                {downloadingId === s.id
                                  ? <span className="spinner-border spinner-border-sm" />
                                  : <><i className="ti ti-download me-1" />Download</>}
                              </button>
                            )}
                          </li>
                        ))}
                      </ul>
                    )}
                  </div>
                </div>

                {/* Comments */}
                <div className="card shadow-none border mb-0">
                  <div className="card-header border-bottom py-2 d-flex align-items-center gap-2">
                    <i className="ti ti-messages text-primary" />
                    <h6 className="mb-0 fw-semibold fs-14">Recent comments</h6>
                  </div>
                  <div className="card-body">
                    {sections.length > 0 && (
                      <div className="row g-2 mb-3">
                        {sections.length > 1 && (
                          <div className="col-md-4">
                            <select className="form-select form-select-sm fs-13" value={commentSection}
                              onChange={e => setCommentSection(e.target.value)}>
                              {sections.map((s, i) => (
                                <option key={s.id} value={String(s.id)}>{s.title || s.name || `Section ${i + 1}`}</option>
                              ))}
                            </select>
                          </div>
                        )}
                        <div className={sections.length > 1 ? "col-md-8" : "col-12"}>
                          <div className="input-group input-group-sm">
                            <input className="form-control fs-13" placeholder="Write a comment…"
                              value={commentBody} onChange={e => setCommentBody(e.target.value)}
                              onKeyDown={e => { if (e.key === "Enter") postComment(); }} />
                            <button className="btn btn-primary" disabled={posting || !commentBody.trim()} onClick={postComment}>
                              {posting ? <span className="spinner-border spinner-border-sm" /> : <i className="ti ti-send" />}
                            </button>
                          </div>
                        </div>
                      </div>
                    )}
                    {comments.length === 0 ? (
                      <div className="text-muted text-center py-2">No comments yet.</div>
                    ) : comments.map(c => (
                      <div key={c.id} className="border-bottom pb-2 mb-2">
                        <div className="d-flex justify-content-between">
                          <span className="fw-semibold">{commentAuthor(c)}</span>
                          <span className="text-muted fs-12">{fmtDateTime(c.created_at)}</span>
                        </div>
                        <div style={{ whiteSpace: "pre-line" }}>{commentText(c)}</div>
                      </div>
                    ))}
                  </div>
                </div>

                   {/* Exam card */}
                <div className="card shadow-none border mb-3">
                  <div className="card-header border-bottom py-2 d-flex align-items-center gap-2">
                    <i className="ti ti-certificate text-primary" />
                    <h6 className="mb-0 fw-semibold fs-14">CPD exam</h6>
                  </div>
                  <div className="card-body">
                    <div className="row g-2 mb-2">
                     <div className="col-6"><div className="text-muted fs-12">Paid on</div>
  <div>{isAdmin ? "Admin access" : fmtDateTime(data.payment_date)}</div></div>
<div className="col-6"><div className="text-muted fs-12">Exam unlocks</div>
  <div>{isAdmin ? "Always open" : fmtDateTime(data.unlock_time)}</div></div>
                    </div>
                    {timeLeft !== null && timeLeft > 0 && (
                      <div className="alert alert-warning fs-12 py-2">
                        <i className="ti ti-clock me-1" />Available in {formatCountdown(timeLeft)}
                      </div>
                    )}
                    {examMsg && <div className="alert alert-danger fs-12 py-2">{examMsg}</div>}
                    <button className="btn btn-primary btn-sm" disabled={examBusy || (timeLeft !== null && timeLeft > 0)} onClick={startExam}>
                      {examBusy ? <span className="spinner-border spinner-border-sm me-1" /> : <i className="ti ti-pencil me-1" />}
                      Take exam
                    </button>
                    <span className="text-muted fs-12 ms-2">Pass mark {PASS_MARK}% · {MAX_FAILED} attempts</span>
                  </div>
                </div>
              </>
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

/* ─────────────────────────── Exam + result ─────────────────────────── */

function ExamPanel({
  tutorial,
  sectionId,
  examPath,
  onGuard,
  onBack,
  onClose,
}: {
  tutorial: any;
  sectionId: string;
  examPath: string;
  onGuard: (guard: Guard) => void;
  onBack: () => void;
  onClose: () => void;
}) {
  const KEY = `cpd_quiz_end_${sectionId}`;

  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [idx, setIdx] = useState(0);
  const [answers, setAnswers] = useState<Record<string, string>>({});
  const [remaining, setRemaining] = useState(QUIZ_MINUTES * 60);
  const [submitting, setSubmitting] = useState(false);
  const [result, setResult] = useState<any>(null);
  const [certBusy, setCertBusy] = useState(false);

  const endRef = useRef<number>(0);
  const answersRef = useRef(answers);
  answersRef.current = answers;
  const submittedRef = useRef(false);

  const questions: any[] = data?.questions || [];
  const locked = !!data?.disable_submit || Number(data?.failed_attempts || 0) >= MAX_FAILED;
  const inProgress = !!data && !locked && !result && questions.length > 0;

  useEffect(() => { onGuard(inProgress ? "exam" : "none"); }, [inProgress]); // eslint-disable-line react-hooks/exhaustive-deps
  useEffect(() => () => onGuard("none"), []); // eslint-disable-line react-hooks/exhaustive-deps

  const load = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const res = await API.get(examPath);
      setData(res.data);
      const stored = Number(localStorage.getItem(KEY));
      const now = Date.now();
      endRef.current = stored > now ? stored : now + QUIZ_MINUTES * 60 * 1000;
      try { localStorage.setItem(KEY, String(endRef.current)); } catch { /* ignore */ }
      setRemaining(Math.max(0, Math.floor((endRef.current - now) / 1000)));
    } catch (err: any) {
      if (err.response?.status === 401) window.location.href = "/login";
      else setError(errorMessage(err, "Could not load the exam."));
    } finally {
      setLoading(false);
    }
  }, [sectionId, KEY]);

  useEffect(() => { load(); }, [load]);

  const submit = useCallback(async (auto = false) => {
    if (submittedRef.current) return;
    submittedRef.current = true;
    setSubmitting(true);
    try {
      // QuizSubmit reads request.POST["answers[<question_id>]"] → send form-encoded
      const body = new URLSearchParams();
      Object.entries(answersRef.current).forEach(([qid, cid]) => body.append(`answers[${qid}]`, cid));
      const res = await API.post(`questions/submit/${sectionId}/`, body);
      try { localStorage.removeItem(KEY); } catch { /* ignore */ }
      setResult(res.data);
    } catch (err: any) {
      submittedRef.current = false;
      showError(errorMessage(err, "Could not submit your answers."), auto ? "Time is up – submit failed" : "Submit failed", 6000);
    } finally {
      setSubmitting(false);
    }
  }, [sectionId, KEY]);

  // countdown; auto-submits at zero
  useEffect(() => {
    if (!inProgress) return;
    const t = setInterval(() => {
      const left = Math.max(0, Math.floor((endRef.current - Date.now()) / 1000));
      setRemaining(left);
      if (left <= 0) { clearInterval(t); submit(true); }
    }, 1000);
    return () => clearInterval(t);
  }, [inProgress, submit]);

  async function handleSubmit() {
    const unanswered = questions.filter(q => !answers[String(q.id)]).length;
    if (unanswered > 0) {
      const ok = await showConfirm(
        `You have ${unanswered} unanswered question${unanswered !== 1 ? "s" : ""}. Unanswered questions score zero.`,
        "Submit anyway?",
        "Yes, submit"
      );
      if (!ok) return;
    }
    submit(false);
  }

  function retake() {
    submittedRef.current = false;
    try { localStorage.removeItem(KEY); } catch { /* ignore */ }
    setResult(null);
    setAnswers({});
    setIdx(0);
    load();
  }

  async function certificate() {
    setCertBusy(true);
    try {
      await downloadBlob(
        `generate-certificate/${encodeURIComponent(result.first_name || "-")}/${encodeURIComponent(result.last_name || "-")}/`,
        "certificate.jpg",
        { tutorial_id: result.tutorial_id }
      );
    } catch (err: any) {
      showError(errorMessage(err, "Could not generate your certificate."), "Certificate failed", 6000);
    } finally {
      setCertBusy(false);
    }
  }

  /* ── result view ── */
  if (result) {
    const passed = result.passed === "pass";
    const score = Math.round(Number(result.score) * 10) / 10;
    // the API returns failed attempts *before* this one was recorded
    const failedNow = Number(result.failed_attempts || 0) + (passed ? 0 : 1);
    const attemptsLeft = Math.max(0, MAX_FAILED - failedNow);
    return (
      <>
        <div className="offcanvas-body fs-13">
          <div className="text-center py-4">
            <div className={`avatar avatar-xl avatar-rounded mx-auto mb-3 d-flex align-items-center justify-content-center ${passed ? "bg-success-gradient-100" : "bg-danger-gradient-100"}`}>
              <i className={`ti ${passed ? "ti-circle-check text-success" : "ti-circle-x text-danger"} fs-1`} />
            </div>
            <h4 className="fw-semibold mb-1">{passed ? "You passed!" : "Not quite there"}</h4>
            <h1 className={`fw-bold mb-1 ${passed ? "text-success" : "text-danger"}`}>{score}%</h1>
            <p className="text-muted fs-12 mb-4">Pass mark: {PASS_MARK}%</p>

            {passed ? (
              <>
                <p>Congratulations! You can download your certificate now.</p>
                {result.tutorial_id ? (
                  <button className="btn btn-success" disabled={certBusy} onClick={certificate}>
                    {certBusy ? <span className="spinner-border spinner-border-sm me-1" /> : <i className="ti ti-download me-1" />}
                    Download certificate
                  </button>
                ) : (
                  <div className="alert alert-warning fs-12 py-2">No tutorial is linked to this section.</div>
                )}
              </>
            ) : attemptsLeft > 0 ? (
              <>
                <p>You did not reach the pass mark. You have <strong>{attemptsLeft}</strong> attempt{attemptsLeft !== 1 ? "s" : ""} left.</p>
                <button className="btn btn-primary" onClick={retake}><i className="ti ti-refresh me-1" />Retake quiz</button>
              </>
            ) : (
              <div className="alert alert-danger fs-13 py-2">You have used all your attempts, so this quiz is now locked.</div>
            )}
          </div>
        </div>
        <div className="offcanvas-footer border-top p-3 d-flex justify-content-between align-items-center gap-2">
          <button className="btn btn-outline-secondary btn-sm" onClick={onClose}>Close</button>
          <button className="btn btn-outline-secondary btn-sm" onClick={onBack}><i className="ti ti-arrow-left me-1" />Back to lesson</button>
        </div>
      </>
    );
  }

  /* ── quiz view ── */
  const q = questions[idx];
  const choices: any[] = q?.choices || q?.choice_set || [];
  const answered = Object.keys(answers).length;
  const lowTime = remaining <= 60;

  return (
    <>
      <div className="offcanvas-body fs-13">
        {loading ? (
          <div className="d-flex align-items-center justify-content-center py-5 text-muted">
            <span className="spinner-border spinner-border-sm me-2" />Loading exam…
          </div>
        ) : (
          <>
            {error && <div className="alert alert-danger fs-13 py-2">{error}</div>}

            <div className="d-flex align-items-center justify-content-between mb-3">
              <div className="text-muted fs-12">
                {data?.combined_name && <>{data.combined_name} · </>}{tutorial.lesson}
              </div>
              {inProgress && (
                <span className={`badge fs-13 px-3 py-2 ${lowTime ? "bg-danger" : "bg-primary"}`}>
                  <i className="ti ti-clock me-1" />{mmss(remaining)}
                </span>
              )}
            </div>

            {locked ? (
              <div className="border rounded text-center py-5">
                <i className="ti ti-lock fs-1 text-danger d-block mb-2" />
                <h6 className="fw-semibold">This exam is locked</h6>
                <p className="text-muted">You have already failed this quiz {MAX_FAILED} times and can no longer retake it.</p>
              </div>
            ) : questions.length === 0 ? (
              <div className="border rounded text-center py-5 text-muted">
                <i className="ti ti-help-circle fs-1 d-block mb-2" />There are no questions for this section yet.
              </div>
            ) : (
              <>
                <div className="progress mb-3" style={{ height: 6 }}>
                  <div className="progress-bar" style={{ width: `${((idx + 1) / questions.length) * 100}%` }} />
                </div>
                <div className="d-flex justify-content-between mb-2">
                  <span className="badge bg-info-transparent text-info">Question {idx + 1} of {questions.length}</span>
                  <span className="text-muted fs-12">{answered} of {questions.length} answered</span>
                </div>
                <h6 className="fw-semibold mb-3">{q.question_text}</h6>
                <div className="d-flex flex-column gap-2">
                  {choices.map(c => {
                    const selected = answers[String(q.id)] === String(c.id);
                    return (
                      <label key={c.id}
                        className={`d-flex align-items-center gap-2 border rounded p-3 ${selected ? "border-primary bg-primary-transparent" : ""}`}
                        style={{ cursor: "pointer" }}>
                        <input type="radio" className="form-check-input mt-0" name={`q_${q.id}`} checked={selected}
                          onChange={() => setAnswers(a => ({ ...a, [String(q.id)]: String(c.id) }))} />
                        <span>{c.choice_text}</span>
                      </label>
                    );
                  })}
                </div>
              </>
            )}
          </>
        )}
      </div>

      <div className="offcanvas-footer border-top p-3 d-flex justify-content-between align-items-center gap-2">
        {inProgress ? (
          <>
            <button className="btn btn-outline-secondary btn-sm" disabled={idx === 0 || submitting} onClick={() => setIdx(i => i - 1)}>
              <i className="ti ti-chevron-left me-1" />Previous
            </button>
            {idx < questions.length - 1 ? (
              <button className="btn btn-info btn-sm" onClick={() => setIdx(i => i + 1)}>
                Next<i className="ti ti-chevron-right ms-1" />
              </button>
            ) : (
              <button className="btn btn-success btn-sm" disabled={submitting} onClick={handleSubmit}>
                {submitting ? <span className="spinner-border spinner-border-sm me-1" /> : <i className="ti ti-check me-1" />}
                Submit answers
              </button>
            )}
          </>
        ) : (
          <>
            <button className="btn btn-outline-secondary btn-sm" onClick={onClose}>Close</button>
            <button className="btn btn-outline-secondary btn-sm" onClick={onBack}><i className="ti ti-arrow-left me-1" />Back to lesson</button>
          </>
        )}
      </div>
    </>
  );
}
const EMPTY_FORM = {
  lesson: "", cpd_number: "", theme: "", unit_price: "", start: "", stop: "",
  contact_hours: "", points: "", presented_by: "",
};

const REQUIRED: (keyof typeof EMPTY_FORM)[] = [
  "lesson", "cpd_number", "theme", "unit_price", "start", "stop", "points", "presented_by",
];

function CreateTutorialPanel({ onClose, onCreated }: {
  onClose: () => void; onCreated: () => void;
}) {
  const [form, setForm] = useState(EMPTY_FORM);
  const [saving, setSaving] = useState(false);

  const set = (k: keyof typeof EMPTY_FORM) =>
    (e: React.ChangeEvent<HTMLInputElement>) => setForm(f => ({ ...f, [k]: e.target.value }));

  const dirty = Object.values(form).some(v => String(v).trim() !== "");

  async function save() {
    const missing = REQUIRED.filter(k => !String(form[k]).trim());
    if (missing.length) {
      return showError(
        `Please fill in: ${missing.join(", ").replace(/_/g, " ")}.`,
        "Missing details",
        5000
      );
    }
    if (form.stop < form.start) {
      return showError("The end date cannot be before the start date.", "Invalid dates", 5000);
    }

    const payload: Record<string, any> = {};
    Object.entries(form).forEach(([k, v]) => { if (String(v).trim() !== "") payload[k] = String(v).trim(); });

    setSaving(true);
    try {
      await API.post("tutorials/create/", payload); // ADJUST: your create endpoint
      showSuccess(`"${form.lesson.trim()}" has been created.`, "Tutorial created"); // not awaited, so the panel closes right away
      onCreated();
    } catch (err: any) {
      showError(errorMessage(err, "Could not create the tutorial."), "Create failed", 6000);
    } finally {
      setSaving(false);
    }
  }

  async function cancel() {
    if (dirty) {
      const ok = await showConfirm(
        "Your changes will be lost.",
        "Discard this tutorial?",
        "Yes, discard"
      );
      if (!ok) return;
    }
    onClose();
  }

  const req = <span className="text-danger">*</span>;

  return (
    <>
      <div className="offcanvas-body fs-13">
        <div className="row g-3">
          <div className="col-12">
            <label className="form-label fw-medium">Lesson title {req}</label>
            <input className="form-control" value={form.lesson} onChange={set("lesson")} autoFocus />
          </div>
          <div className="col-md-6">
            <label className="form-label fw-medium">CPD number {req}</label>
            <input className="form-control" maxLength={30} value={form.cpd_number} onChange={set("cpd_number")} />
          </div>
          <div className="col-md-6">
            <label className="form-label fw-medium">Theme {req}</label>
            <input className="form-control" maxLength={100} value={form.theme} onChange={set("theme")} />
          </div>
          <div className="col-md-6">
            <label className="form-label fw-medium">Unit price (KES) {req}</label>
            <input type="number" min={0} step="0.01" className="form-control" value={form.unit_price} onChange={set("unit_price")} />
          </div>
          <div className="col-md-6">
            <label className="form-label fw-medium">Points {req}</label>
            <input type="number" min={0} step={1} className="form-control" value={form.points} onChange={set("points")} />
          </div>
          <div className="col-md-6">
            <label className="form-label fw-medium">Starts {req}</label>
            <input type="datetime-local" className="form-control" value={form.start} onChange={set("start")} />
          </div>
          <div className="col-md-6">
            <label className="form-label fw-medium">Ends {req}</label>
            <input type="datetime-local" className="form-control" value={form.stop} onChange={set("stop")} />
          </div>
          <div className="col-md-6">
            <label className="form-label fw-medium">Contact hours</label>
            <input className="form-control" maxLength={50} placeholder="0" value={form.contact_hours} onChange={set("contact_hours")} />
          </div>
          <div className="col-md-6">
            <label className="form-label fw-medium">Presented by {req}</label>
            <input className="form-control" maxLength={100} value={form.presented_by} onChange={set("presented_by")} />
          </div>
        </div>
      </div>

      <div className="offcanvas-footer border-top p-3 d-flex justify-content-between align-items-center gap-2">
        <button className="btn btn-outline-secondary btn-sm" onClick={cancel} disabled={saving}>Cancel</button>
        <button className="btn btn-primary btn-sm" onClick={save} disabled={saving}>
          {saving ? <span className="spinner-border spinner-border-sm me-1" /> : <i className="ti ti-check me-1" />}
          Create tutorial
        </button>
      </div>
    </>
  );
}/* ─────────────────────────── Admin: manage sections & questions ─────────────────────────── */

function ManagePanel({ tutorial, onClose }: { tutorial: any; onClose: () => void }) {
  const [tab, setTab] = useState<"sections" | "questions">("sections");
  const [sections, setSections] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  const loadSections = useCallback(async () => {
    setLoading(true);
    try {
      const res = await API.get(`admin/tutorials/${tutorial.id}/sections/`);
      setSections(asList(res.data));
    } catch (err: any) {
      showError(errorMessage(err, "Could not load sections."), "Load failed", 6000);
    } finally {
      setLoading(false);
    }
  }, [tutorial.id]);

  useEffect(() => { loadSections(); }, [loadSections]);

  return (
    <>
      <div className="offcanvas-body fs-13">
        <ul className="nav nav-tabs mb-3">
          <li className="nav-item">
            <button className={`nav-link ${tab === "sections" ? "active" : ""}`} onClick={() => setTab("sections")}>
              <i className="ti ti-files me-1" />Sections <span className="badge bg-primary-transparent text-primary ms-1">{sections.length}</span>
            </button>
          </li>
          <li className="nav-item">
            <button className={`nav-link ${tab === "questions" ? "active" : ""}`} onClick={() => setTab("questions")}>
              <i className="ti ti-help-circle me-1" />Questions &amp; answers
            </button>
          </li>
        </ul>

        {tab === "sections"
          ? <SectionsTab tutorialId={tutorial.id} sections={sections} loading={loading} reload={loadSections} />
          : <QuestionsTab sections={sections} loading={loading} />}
      </div>

      <div className="offcanvas-footer border-top p-3 d-flex justify-content-between align-items-center gap-2">
        <button className="btn btn-outline-secondary btn-sm" onClick={onClose}>Close</button>
        <button className="btn btn-outline-secondary btn-sm" onClick={loadSections} disabled={loading}>
          <i className={`ti ti-refresh me-1 ${loading ? "fa-spin" : ""}`} />Refresh
        </button>
      </div>
    </>
  );
}

/* ── Sections ── */
const ALLOWED_EXT = [".pdf", ".doc", ".docx"];
const ALLOWED_MIME = [
  "application/pdf",
  "application/msword",
  "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
];

function isAllowedDoc(f: File) {
  const name = f.name.toLowerCase();
  return ALLOWED_EXT.some(ext => name.endsWith(ext)) &&
    (!f.type || ALLOWED_MIME.includes(f.type)); // some browsers leave type empty
}
function SectionsTab({ tutorialId, sections, loading, reload }: {
  tutorialId: number; sections: any[]; loading: boolean; reload: () => Promise<void>;
}) {
  const [title, setTitle] = useState("");
  const [content, setContent] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [fileKey, setFileKey] = useState(0); // changing the key clears the file input
  const [saving, setSaving] = useState(false);
  const [deletingId, setDeletingId] = useState<number | null>(null);

  async function add() {
    if (!title.trim() || !content.trim() || !file)
      return showError("Title, content and a file are all required.", "Missing details", 5000);
        if (!isAllowedDoc(file))
      return showError("Only PDF and Word documents are allowed.", "Invalid file", 5000);
    const fd = new FormData();
    fd.append("title", title.trim());
    fd.append("content", content.trim());
    fd.append("file", file);

    setSaving(true);
    try {
     await API.post(`admin/tutorials/${tutorialId}/sections/`, fd, {
  headers: { "Content-Type": "multipart/form-data" },
});
      showSuccess(`"${title.trim()}" was added.`, "Section added");
      setTitle(""); setContent(""); setFile(null); setFileKey(k => k + 1);
      await reload();
    } catch (err: any) {
      showError(errorMessage(err, "Could not add the section."), "Add failed", 6000);
    } finally {
      setSaving(false);
    }
  }

  async function remove(s: any) {
    const ok = await showConfirm(
      "Its questions and comments will be deleted too.",
      `Delete "${s.title}"?`,
      "Yes, delete"
    );
    if (!ok) return;
    setDeletingId(s.id);
    try {
      await API.delete(`admin/sections/${s.id}/`);
      await reload();
    } catch (err: any) {
      showError(errorMessage(err, "Could not delete the section."), "Delete failed", 6000);
    } finally {
      setDeletingId(null);
    }
  }

  return (
    <>
      <div className="card shadow-none border mb-3">
        <div className="card-header border-bottom py-2"><h6 className="mb-0 fw-semibold fs-14">Add section</h6></div>
        <div className="card-body">
          <div className="row g-3">
            <div className="col-12">
              <label className="form-label fw-medium">Title <span className="text-danger">*</span></label>
              <input className="form-control" maxLength={255} value={title} onChange={e => setTitle(e.target.value)} />
            </div>
            <div className="col-12">
              <label className="form-label fw-medium">Content <span className="text-danger">*</span></label>
              <textarea className="form-control" rows={4} value={content} onChange={e => setContent(e.target.value)} />
            </div>
            <div className="col-12">
              <label className="form-label fw-medium">File <span className="text-danger">*</span></label>
              <input
                key={fileKey}
                type="file"
                className="form-control"
                accept=".pdf,.doc,.docx,application/pdf,application/msword,application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                onChange={e => {
                  const f = e.target.files?.[0] ?? null;
                  if (f && !isAllowedDoc(f)) {
                    showError("Only PDF and Word documents (.pdf, .doc, .docx) are allowed.", "Invalid file", 5000);
                    setFile(null);
                    setFileKey(k => k + 1);
                    return;
                  }
                  setFile(f);
                }}
              />
              <div className="text-muted fs-12 mt-1">PDF or Word documents only (.pdf, .doc, .docx).</div>
            </div>

            <div className="col-12 text-end">
              <button className="btn btn-primary btn-sm" disabled={saving} onClick={add}>
                {saving ? <span className="spinner-border spinner-border-sm me-1" /> : <i className="ti ti-plus me-1" />}
                Add section
              </button>
            </div>
          </div>
        </div>
      </div>

      <div className="card shadow-none border mb-0">
        <div className="card-header border-bottom py-2"><h6 className="mb-0 fw-semibold fs-14">Existing sections</h6></div>
        <div className="card-body p-0">
          {loading ? (
            <div className="text-center text-muted py-4"><span className="spinner-border spinner-border-sm me-2" />Loading…</div>
          ) : sections.length === 0 ? (
            <div className="text-center text-muted py-4">No sections yet.</div>
          ) : (
            <ul className="list-group list-group-flush">
              {sections.map((s, i) => (
                <li key={s.id} className="list-group-item d-flex justify-content-between align-items-start gap-3 py-3">
                  <div>
                    <div className="fw-semibold">{i + 1}. {s.title}</div>
                    <div className="text-muted fs-12 mt-1" style={{ whiteSpace: "pre-line" }}>{s.content}</div>
                    {s.file && <a href={s.file} target="_blank" rel="noopener noreferrer" className="fs-12"><i className="ti ti-paperclip me-1" />View file</a>}
                  </div>
                  <button className="btn btn-outline-danger btn-sm text-nowrap" disabled={deletingId === s.id} onClick={() => remove(s)}>
                    {deletingId === s.id ? <span className="spinner-border spinner-border-sm" /> : <i className="ti ti-trash" />}
                  </button>
                </li>
              ))}
            </ul>
          )}
        </div>
      </div>
    </>
  );
}

/* ── Questions & answers ── */

type ChoiceDraft = { choice_text: string; is_correct: boolean };
const blankChoices = (): ChoiceDraft[] => [
  { choice_text: "", is_correct: true },
  { choice_text: "", is_correct: false },
  { choice_text: "", is_correct: false },
  { choice_text: "", is_correct: false },
];

function QuestionsTab({ sections, loading: sectionsLoading }: { sections: any[]; loading: boolean }) {
  const [sectionId, setSectionId] = useState("");
  const [questions, setQuestions] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);

  const [text, setText] = useState("");
  const [choices, setChoices] = useState<ChoiceDraft[]>(blankChoices());
  const [saving, setSaving] = useState(false);
  const [deletingId, setDeletingId] = useState<number | null>(null);

  // default to the first section once sections arrive
  useEffect(() => {
    if (!sectionId && sections.length) setSectionId(String(sections[0].id));
  }, [sections, sectionId]);

  const loadQuestions = useCallback(async () => {
    if (!sectionId) return;
    setLoading(true);
    try {
      const res = await API.get(`admin/sections/${sectionId}/questions/`);
      setQuestions(asList(res.data));
    } catch (err: any) {
      showError(errorMessage(err, "Could not load questions."), "Load failed", 6000);
    } finally {
      setLoading(false);
    }
  }, [sectionId]);

  useEffect(() => { loadQuestions(); }, [loadQuestions]);

  const setChoiceText = (i: number, v: string) =>
    setChoices(cs => cs.map((c, j) => j === i ? { ...c, choice_text: v } : c));
  const setCorrect = (i: number) =>
    setChoices(cs => cs.map((c, j) => ({ ...c, is_correct: j === i })));
  const addChoice = () => setChoices(cs => cs.length < 6 ? [...cs, { choice_text: "", is_correct: false }] : cs);
  const removeChoice = (i: number) =>
    setChoices(cs => {
      if (cs.length <= 2) return cs;
      const next = cs.filter((_, j) => j !== i);
      if (!next.some(c => c.is_correct)) next[0].is_correct = true; // always keep one correct answer
      return next;
    });

  async function add() {
    if (!text.trim()) return showError("Enter the question text.", "Missing details", 5000);
    if (choices.some(c => !c.choice_text.trim()))
      return showError("Fill in every choice, or remove the empty ones.", "Missing details", 5000);
   
    setSaving(true);
    try {
      await API.post(`admin/sections/${sectionId}/questions/`, {
        question_text: text.trim(),
        choices: choices.map(c => ({ choice_text: c.choice_text.trim(), is_correct: c.is_correct })),
      });
      showSuccess("The question was added.", "Question added");
      setText("");
      setChoices(blankChoices());
      await loadQuestions();
    } catch (err: any) {
      showError(errorMessage(err, "Could not add the question."), "Add failed", 6000);
    } finally {
      setSaving(false);
    }
  }

  async function remove(q: any) {
    const ok = await showConfirm("This cannot be undone.", "Delete this question?", "Yes, delete");
    if (!ok) return;
    setDeletingId(q.id);
    try {
      await API.delete(`admin/questions/${q.id}/`);
      await loadQuestions();
    } catch (err: any) {
      showError(errorMessage(err, "Could not delete the question."), "Delete failed", 6000);
    } finally {
      setDeletingId(null);
    }
  }

  if (sectionsLoading) {
    return <div className="text-center text-muted py-4"><span className="spinner-border spinner-border-sm me-2" />Loading…</div>;
  }
  if (sections.length === 0) {
    return <div className="alert alert-warning fs-12 py-2">Add a section first. Questions belong to a section.</div>;
  }

  return (
    <>
      <div className="mb-3">
        <label className="form-label fw-medium">Section</label>
        <select className="form-select form-select-sm fs-13" value={sectionId} onChange={e => setSectionId(e.target.value)}>
          {sections.map((s, i) => <option key={s.id} value={String(s.id)}>{i + 1}. {s.title}</option>)}
        </select>
      </div>

      <div className="card shadow-none border mb-3">
        <div className="card-header border-bottom py-2"><h6 className="mb-0 fw-semibold fs-14">Add question</h6></div>
        <div className="card-body">
          <label className="form-label fw-medium">Question <span className="text-danger">*</span></label>
          <input className="form-control mb-3" maxLength={255} value={text} onChange={e => setText(e.target.value)} />

          <label className="form-label fw-medium">Choices <span className="text-muted fw-normal">(select the correct one)</span></label>
          <div className="d-flex flex-column gap-2 mb-2">
            {choices.map((c, i) => (
              <div key={i} className="input-group input-group-sm">
                <span className="input-group-text bg-transparent">
                  <input type="radio" className="form-check-input mt-0" name="correct" checked={c.is_correct}
                    onChange={() => setCorrect(i)} title="Correct answer" />
                </span>
                <input className="form-control fs-13" maxLength={255} placeholder={`Choice ${i + 1}`}
                  value={c.choice_text} onChange={e => setChoiceText(i, e.target.value)} />
                <button className="btn btn-outline-secondary" type="button" disabled={choices.length <= 2}
                  onClick={() => removeChoice(i)}><i className="ti ti-x" /></button>
              </div>
            ))}
          </div>

          <div className="d-flex justify-content-between align-items-center">
            <button className="btn btn-outline-secondary btn-sm" disabled={choices.length >= 6} onClick={addChoice}>
              <i className="ti ti-plus me-1" />Add choice
            </button>
            <button className="btn btn-primary btn-sm" disabled={saving} onClick={add}>
              {saving ? <span className="spinner-border spinner-border-sm me-1" /> : <i className="ti ti-check me-1" />}
              Save question
            </button>
          </div>
        </div>
      </div>

      <div className="card shadow-none border mb-0">
        <div className="card-header border-bottom py-2 d-flex align-items-center gap-2">
          <h6 className="mb-0 fw-semibold fs-14">Questions in this section</h6>
          <span className="badge bg-primary-transparent text-primary fs-11">{questions.length}</span>
        </div>
        <div className="card-body p-0">
          {loading ? (
            <div className="text-center text-muted py-4"><span className="spinner-border spinner-border-sm me-2" />Loading…</div>
          ) : questions.length === 0 ? (
            <div className="text-center text-muted py-4">No questions yet.</div>
          ) : (
            <ul className="list-group list-group-flush">
              {questions.map((q, i) => (
                <li key={q.id} className="list-group-item py-3">
                  <div className="d-flex justify-content-between align-items-start gap-3">
                    <div className="fw-semibold">{i + 1}. {q.question_text}</div>
                    <button className="btn btn-outline-danger btn-sm" disabled={deletingId === q.id} onClick={() => remove(q)}>
                      {deletingId === q.id ? <span className="spinner-border spinner-border-sm" /> : <i className="ti ti-trash" />}
                    </button>
                  </div>
                  <ul className="list-unstyled mb-0 mt-2">
                    {(q.choices || []).map((c: any) => (
                      <li key={c.id} className={c.is_correct ? "text-success fw-medium" : "text-muted"}>
                        <i className={`ti ${c.is_correct ? "ti-circle-check" : "ti-circle"} me-1`} />{c.choice_text}
                      </li>
                    ))}
                  </ul>
                </li>
              ))}
            </ul>
          )}
        </div>
      </div>
    </>
  );
}