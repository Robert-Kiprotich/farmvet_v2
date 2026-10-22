import API from "../../services/api";

export const MAX_FAILED = 2;    

export const PASS_MARK = 80;

export const asList = (data: any): any[] =>
  data?.results || data?.data || (Array.isArray(data) ? data : []);

export function errorMessage(err: any, fallback = "Something went wrong. Please try again.") {
  const data = err?.response?.data;
  if (!data) return fallback;
  if (typeof data === "string") return data.length > 300 ? fallback : data;
  if (data.error || data.detail || data.message) return data.error || data.detail || data.message;
  const first = Object.entries(data)[0] as [string, any];
  if (first) {
    const msg = Array.isArray(first[1]) ? first[1][0] : first[1];
    return first[0] === "non_field_errors" ? String(msg) : `${first[0]}: ${msg}`;
  }
  return fallback;
}

export const fmtDate = (d?: string | null) => {
  if (!d) return "—";
  const x = new Date(d);
  return isNaN(x.getTime()) ? String(d) : x.toLocaleDateString("en-GB");
};

export const fmtDateTime = (d?: string | null) => {
  if (!d) return "—";
  const x = new Date(d);
  return isNaN(x.getTime()) ? String(d) : x.toLocaleString("en-GB", { dateStyle: "medium", timeStyle: "short" });
};

export const money = (n: any) =>
  `KES ${Number(n || 0).toLocaleString("en-KE", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;

/** Download an authenticated file (blob) through the API client. */
export async function downloadBlob(url: string, fallbackName: string, params?: any) {
  const res = await API.get(url, { responseType: "blob", params });
  const cd: string = res.headers?.["content-disposition"] || "";
  const m = /filename\*?=(?:UTF-8'')?"?([^";]+)"?/i.exec(cd);
  const name = m ? decodeURIComponent(m[1]) : fallbackName;
  const href = URL.createObjectURL(res.data);
  const a = document.createElement("a");
  a.href = href;
  a.download = name;
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(href);
}
