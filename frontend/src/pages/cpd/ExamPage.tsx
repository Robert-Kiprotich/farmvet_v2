import { useCallback, useEffect, useRef, useState } from "react";
import type { ReactNode } from "react";
import { useNavigate, useParams } from "react-router-dom";
import API from "../../services/api";
import { all_routes } from "../../routes/all_routes"; // same path as in CpdPage
import { showConfirm, showError } from "../../components/alerts/Alerts";
import { MAX_FAILED, PASS_MARK, downloadBlob, errorMessage, fmtDateTime } from "./shared";
const EXAM_MINUTES = 30; // set to however long the exam should be
const EXAM_MS = EXAM_MINUTES * 60 * 1000;
const mmss = (s: number) =>
  `${String(Math.floor(s / 60)).padStart(2, "0")}:${String(s % 60).padStart(2, "0")}`;

export function apiPath(absPath: string) {
  try {
    const base = new URL(String(API.defaults.baseURL || "/"), window.location.origin).pathname
      .replace(/\/+$/, "");
    return base && absPath.startsWith(base + "/") ? absPath.slice(base.length + 1) : absPath.replace(/^\/+/, "");
  } catch {
    return absPath.replace(/^\/+/, "");
  }
}

type Saved = { endAt: number; answers: Record<string, string>; idx: number };
const storeKey = (sectionId: string) => `cpd_exam_${sectionId}`;
function readSaved(sectionId: string): Saved | null {
  try {
    const raw = localStorage.getItem(storeKey(sectionId));
    return raw ? JSON.parse(raw) : null;
  } catch { return null; }
}
function writeSaved(sectionId: string, s: Saved) {
  try { localStorage.setItem(storeKey(sectionId), JSON.stringify(s)); } catch { /* ignore */ }
}
function clearSaved(sectionId: string) {
  try { localStorage.removeItem(storeKey(sectionId)); } catch { /* ignore */ }
}

export default function ExamPage() {
  const { tutorialId } = useParams();
  const navigate = useNavigate();

  const [sectionId, setSectionId] = useState("");
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const [started, setStarted] = useState(false);
  const [idx, setIdx] = useState(0);
  const [answers, setAnswers] = useState<Record<string, string>>({});
  const [remaining, setRemaining] = useState(EXAM_MINUTES * 60);
  const [submitting, setSubmitting] = useState(false);
  const [result, setResult] = useState<any>(null);
  const [certBusy, setCertBusy] = useState(false);

  const endRef = useRef(0);
  const answersRef = useRef(answers);
  answersRef.current = answers;
  const submittedRef = useRef(false);

  const questions: any[] = data?.questions || [];
  const locked = !!data?.disable_submit || Number(data?.failed_attempts || 0) >= MAX_FAILED;
  const inProgress = !!data && started && !locked && !result && questions.length > 0;

  /* ── load exam (and resume a running attempt after refresh) ── */
  const load = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const access = await API.get(`exam-access/${tutorialId}/`);
      if (access.data?.locked) throw { response: { data: access.data } };
      const sid = access.data?.section_id;
      const url = access.data?.exam_url;
      if (!sid || !url) { setError("The exam is not available right now."); return; }

      const res = await API.get(apiPath(url));
      setSectionId(String(sid));
      setData(res.data);

      const saved = readSaved(String(sid));
      if (saved?.endAt) {
        endRef.current = saved.endAt;
        setAnswers(saved.answers || {});
        setIdx(Math.min(saved.idx || 0, Math.max(0, (res.data?.questions?.length || 1) - 1)));
        setRemaining(Math.max(0, Math.ceil((saved.endAt - Date.now()) / 1000)));
        setStarted(true); // resume: if time already ran out, the countdown effect auto-submits
      }
    } catch (err: any) {
      if (err.response?.status === 401) { window.location.href = "/login"; return; }
      const d = err.response?.data;
      const reasons: Record<string, string> = {
        not_authenticated: "Please sign in again.",
        payment_required: "Payment is required before you can sit the exam.",
        time_locked: `The exam unlocks on ${fmtDateTime(d?.unlock_time)}.`,
        no_sections: "This lesson has no sections yet.",
      };
      setError(reasons[d?.reason] || errorMessage(err, "Could not load the exam."));
    } finally {
      setLoading(false);
    }
  }, [tutorialId]);

  useEffect(() => { load(); }, [load]);

  /* ── persist progress ── */
  useEffect(() => {
    if (!started || !sectionId || result) return;
    writeSaved(sectionId, { endAt: endRef.current, answers, idx });
  }, [answers, idx, started, sectionId, result]);

  /* ── start ── */
  function startExam() {
    const endAt = Date.now() + EXAM_MS;
    endRef.current = endAt;
    setRemaining(EXAM_MINUTES * 60);
    setAnswers({});
    setIdx(0);
    setStarted(true);
    writeSaved(sectionId, { endAt, answers: {}, idx: 0 });
  }

  /* ── submit ── */
  const submit = useCallback(async (auto = false) => {
    if (submittedRef.current) return;
    submittedRef.current = true;
    setSubmitting(true);
    try {
      // QuizSubmit reads request.POST["answers[<question_id>]"] → form-encoded
      const body = new URLSearchParams();
      Object.entries(answersRef.current).forEach(([qid, cid]) => body.append(`answers[${qid}]`, cid));
      const res = await API.post(`questions/submit/${sectionId}/`, body);
      clearSaved(sectionId);
      setResult(res.data);
    } catch (err: any) {
      submittedRef.current = false;
      showError(errorMessage(err, "Could not submit your answers."), auto ? "Time is up – submit failed" : "Submit failed", 6000);
    } finally {
      setSubmitting(false);
    }
  }, [sectionId]);

  /* ── countdown (computed from the stored end time, so it can't drift or reset) ── */
  useEffect(() => {
    if (!inProgress) return;
    const tick = () => {
      const left = Math.max(0, Math.ceil((endRef.current - Date.now()) / 1000));
      setRemaining(left);
      if (left <= 0) { clearInterval(t); submit(true); }
    };
    const t = setInterval(tick, 1000);
    tick();
    return () => clearInterval(t);
  }, [inProgress, submit]);

  /* ── warn on tab close / reload while exam is running ── */
  useEffect(() => {
    if (!inProgress) return;
    const h = (e: BeforeUnloadEvent) => { e.preventDefault(); e.returnValue = ""; };
    window.addEventListener("beforeunload", h);
    return () => window.removeEventListener("beforeunload", h);
  }, [inProgress]);

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

  async function leave() {
    if (inProgress) {
      const ok = await showConfirm("Your exam timer keeps running while you are away.", "Leave the exam?", "Yes, leave");
      if (!ok) return;
    }
    navigate(all_routes.cpd);
  }

  function retake() {
    submittedRef.current = false;
    clearSaved(sectionId);
    setResult(null);
    setAnswers({});
    setIdx(0);
    setStarted(false);
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

  /* ─────────── render ─────────── */
  const shell = (body: ReactNode, footer?: ReactNode) => (
    <div className="page-wrapper">
      <div className="content">
        <div className="d-flex align-items-center justify-content-between mb-3 flex-wrap gap-2">
          <div>
            <h4 className="fw-semibold mb-1">Online CPD exam</h4>
            <p className="text-muted fs-13 mb-0">
              {data?.combined_name && <>{data.combined_name}</>}
            </p>
          </div>
          <button className="btn btn-outline-secondary btn-sm" onClick={leave}>
            <i className="ti ti-arrow-left me-1" />Back to lessons
          </button>
        </div>
        <div className="card shadow-none border mx-auto" style={{ maxWidth: 820 }}>
          <div className="card-body fs-13">{body}</div>
          {footer && <div className="card-footer border-top p-3 d-flex justify-content-between align-items-center gap-2">{footer}</div>}
        </div>
      </div>
    </div>
  );

  if (loading && !data) {
    return shell(
      <div className="d-flex align-items-center justify-content-center py-5 text-muted">
        <span className="spinner-border spinner-border-sm me-2" />Loading exam…
      </div>
    );
  }

  if (error && !data) {
    return shell(
      <div className="text-center py-5">
        <i className="ti ti-alert-circle fs-1 text-danger d-block mb-2" />
        <p className="mb-3">{error}</p>
        <button className="btn btn-outline-secondary btn-sm" onClick={load}>
          <i className="ti ti-refresh me-1" />Try again
        </button>
      </div>
    );
  }

  /* ── result ── */
  if (result) {
    const passed = result.passed === "pass";
    const score = Math.round(Number(result.score) * 10) / 10;
    const failedNow = Number(result.failed_attempts || 0) + (passed ? 0 : 1); // API returns attempts *before* this one
    const attemptsLeft = Math.max(0, MAX_FAILED - failedNow);
    return shell(
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
            <button className="btn btn-primary" onClick={retake}><i className="ti ti-refresh me-1" />Retake exam</button>
          </>
        ) : (
          <div className="alert alert-danger fs-13 py-2">You have used all your attempts, so this exam is now locked.</div>
        )}
      </div>
    );
  }

  /* ── locked / empty ── */
  if (locked) {
    return shell(
      <div className="text-center py-5">
        <i className="ti ti-lock fs-1 text-danger d-block mb-2" />
        <h6 className="fw-semibold">This exam is locked</h6>
        <p className="text-muted mb-0">You have already failed this exam {MAX_FAILED} times and can no longer retake it.</p>
      </div>
    );
  }
  if (questions.length === 0) {
    return shell(
      <div className="text-center py-5 text-muted">
        <i className="ti ti-help-circle fs-1 d-block mb-2" />There are no questions for this section yet.
      </div>
    );
  }

  /* ── intro (before Start) ── */
  if (!started) {
    const attemptsUsed = Number(data?.failed_attempts || 0);
    return shell(
      <div className="text-center py-4">
        <i className="ti ti-certificate fs-1 text-primary d-block mb-2" />
        <h5 className="fw-semibold mb-3">Ready to begin?</h5>
        <ul className="list-unstyled text-start mx-auto mb-4" style={{ maxWidth: 360 }}>
          <li className="mb-2"><i className="ti ti-help-circle me-2 text-primary" />{questions.length} questions, one at a time</li>
          <li className="mb-2"><i className="ti ti-clock me-2 text-primary" />{EXAM_MINUTES} minutes, starting when you click Start</li>
          <li className="mb-2"><i className="ti ti-target me-2 text-primary" />Pass mark {PASS_MARK}%</li>
          <li className="mb-2"><i className="ti ti-repeat me-2 text-primary" />{Math.max(0, MAX_FAILED - attemptsUsed)} attempt(s) left</li>
          <li><i className="ti ti-refresh me-2 text-primary" />The timer keeps running if you refresh or leave</li>
        </ul>
        <button className="btn btn-success" onClick={startExam}>
          <i className="ti ti-player-play me-1" />Start exam
        </button>
      </div>
    );
  }

  /* ── quiz ── */
  const q = questions[idx];
  const choices: any[] = q?.choices || q?.choice_set || [];
  const answered = Object.keys(answers).length;
  const lowTime = remaining <= 60;
  const timeUp = remaining <= 0;

  return shell(
    <>
      <div className="d-flex align-items-center justify-content-between mb-3">
        <div className="text-muted fs-12">{answered} of {questions.length} answered</div>
        <span className={`badge fs-13 px-3 py-2 ${lowTime ? "bg-danger" : "bg-primary"}`}>
          <i className="ti ti-clock me-1" />{mmss(remaining)}
        </span>
      </div>

      {timeUp && (
        <div className="alert alert-warning fs-12 py-2">
          Time is up. {submitting ? "Submitting your answers…" : "Your answers could not be submitted automatically. Please submit now."}
        </div>
      )}

      <div className="progress mb-3" style={{ height: 6 }}>
        <div className="progress-bar" style={{ width: `${((idx + 1) / questions.length) * 100}%` }} />
      </div>
      <span className="badge bg-info-transparent text-info mb-2">Question {idx + 1} of {questions.length}</span>
      <h6 className="fw-semibold mb-3">{q.question_text}</h6>

      <div className="d-flex flex-column gap-2">
        {choices.map(c => {
          const selected = answers[String(q.id)] === String(c.id);
          return (
            <label key={c.id}
              className={`d-flex align-items-center gap-2 border rounded p-3 ${selected ? "border-primary bg-primary-transparent" : ""}`}
              style={{ cursor: "pointer" }}>
              <input type="radio" className="form-check-input mt-0" name={`q_${q.id}`} checked={selected}
                disabled={submitting}
                onChange={() => setAnswers(a => ({ ...a, [String(q.id)]: String(c.id) }))} />
              <span>{c.choice_text}</span>
            </label>
          );
        })}
      </div>
    </>,
    <>
      <button className="btn btn-outline-secondary btn-sm" disabled={idx === 0 || submitting || timeUp}
        onClick={() => setIdx(i => i - 1)}>
        <i className="ti ti-chevron-left me-1" />Previous
      </button>
      {idx < questions.length - 1 && !timeUp ? (
        <button className="btn btn-info btn-sm" disabled={submitting} onClick={() => setIdx(i => i + 1)}>
          Next<i className="ti ti-chevron-right ms-1" />
        </button>
      ) : (
        <button className="btn btn-success btn-sm" disabled={submitting} onClick={timeUp ? () => submit(true) : handleSubmit}>
          {submitting ? <span className="spinner-border spinner-border-sm me-1" /> : <i className="ti ti-check me-1" />}
          Submit answers
        </button>
      )}
    </>
  );
}