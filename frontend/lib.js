// Shared helpers for every screen. Never log anything: phone numbers, tokens and everything a
// person writes here are personal data (AGENTS.md §1.4).

export const $ = (id) => document.getElementById(id);
export const fa = (s) => String(s).replace(/\d/g, (d) => "۰۱۲۳۴۵۶۷۸۹"[d]);
export const toman = (rial) => `${fa(Math.round(rial / 10).toLocaleString("en-US"))} تومان`;
export const faDate = (iso) => new Date(iso).toLocaleDateString("fa-IR");
export const faDateTime = (iso) => new Date(iso).toLocaleString("fa-IR", {
  weekday: "long", day: "numeric", month: "long", hour: "2-digit", minute: "2-digit",
});

export const store = {
  get: (k) => { try { return localStorage.getItem(k); } catch { return null; } },
  set: (k, v) => { try { localStorage.setItem(k, v); } catch { /* private mode */ } },
  del: (k) => { try { localStorage.removeItem(k); } catch { /* private mode */ } },
};

// h("button", { class: "btn", onclick }, "text", child) - text is always set as text, never HTML.
export function h(tag, props = {}, ...children) {
  const el = document.createElement(tag);
  for (const [k, v] of Object.entries(props || {})) {
    if (v === null || v === undefined || v === false) continue;
    if (k.startsWith("on")) el.addEventListener(k.slice(2), v);
    else if (k === "class") el.className = v;
    else el.setAttribute(k, v === true ? "" : v);
  }
  el.append(...children.flat().filter((c) => c !== null && c !== undefined && c !== false));
  return el;
}

export class ApiError extends Error {
  constructor(status, detail) { super(String(status)); this.status = status; this.detail = detail; }
}

// body: a plain object (sent as JSON) or FormData (sent as multipart).
export async function api(method, path, body, { raw = false } = {}) {
  const headers = { Accept: "application/json" };
  const token = store.get("token");
  if (token) headers.Authorization = `Bearer ${token}`;
  const form = body instanceof FormData;
  if (body && !form) headers["Content-Type"] = "application/json";
  let res;
  try {
    res = await fetch(`/api${path}`, { method, headers, body: body && (form ? body : JSON.stringify(body)) });
  } catch {
    throw new ApiError(0, "network");
  }
  if (raw && res.ok) return res;
  const data = res.status === 204 ? null : await res.json().catch(() => null);
  if (!res.ok) throw new ApiError(res.status, data && data.detail);
  return data;
}

const ERRORS = {
  rate_limited: "درخواست‌ها زیاد بود. یک دقیقه صبر کنید و دوباره تلاش کنید.",
  sms_unavailable: "ارسال پیامک ممکن نشد. کمی بعد دوباره تلاش کنید.",
  code_rejected: "کد درست نیست یا منقضی شده است.",
  outdated_version: "متن‌ها به‌روز شده‌اند. صفحه را دوباره بارگذاری کنید.",
  forbidden: "اجازهٔ این کار را ندارید.",
  not_found: "پیدا نشد.",
  wrong_state: "در وضعیت فعلی این کار ممکن نیست.",
  incomplete: "اطلاعات کامل نیست.",
  bad_file: "فایل باید PDF، JPG یا PNG و حداکثر ۵ مگابایت باشد.",
};

export function message(err) {
  if (err.status === 0) return "اتصال برقرار نشد. اینترنت خود را بررسی کنید.";
  if (typeof err.detail === "string" && ERRORS[err.detail]) return ERRORS[err.detail];
  if (err.status === 422 && Array.isArray(err.detail)) {
    const field = err.detail[0] && err.detail[0].loc && err.detail[0].loc.at(-1);
    if (field === "phone") return "شمارهٔ موبایل معتبر نیست. مثل ۰۹۱۲۳۴۵۶۷۸۹ وارد کنید.";
    if (field === "code") return "کد ۶ رقم است.";
    if (field === "file") return ERRORS.bad_file;
    return "یکی از فیلدها معتبر نیست.";
  }
  return "خطایی رخ داد. دوباره تلاش کنید.";
}

export function toast(text, ok = false) {
  const el = $("toast");
  el.textContent = text;
  el.classList.toggle("ok", ok);
  el.hidden = !text;
  if (text) el.scrollIntoView({ block: "nearest" });
}

let onSignedOut = () => {};
export function setSignedOutHandler(fn) { onSignedOut = fn; }

// Disables the button while the request runs and turns failures into a toast.
export async function busy(button, work) {
  if (button) { button.disabled = true; button.setAttribute("aria-busy", "true"); }
  try {
    await work();
  } catch (err) {
    if (err.status === 401) return onSignedOut();
    toast(message(err));
  } finally {
    if (button) { button.disabled = false; button.removeAttribute("aria-busy"); }
  }
}

export function confirmAction(title, text, yes) {
  const dlg = $("confirm-dialog");
  $("confirm-title").textContent = title;
  $("confirm-text").textContent = text;
  $("confirm-yes").textContent = yes;
  dlg.returnValue = "";
  dlg.showModal();
  return new Promise((resolve) => {
    dlg.addEventListener("close", () => resolve(dlg.returnValue === "yes"), { once: true });
  });
}

// Downloads an authenticated file without putting the token in a URL.
export async function download(path, name) {
  const res = await api("GET", path, null, { raw: true });
  const url = URL.createObjectURL(await res.blob());
  h("a", { href: url, download: name }).click();
  setTimeout(() => URL.revokeObjectURL(url), 10_000);
}

export const field = (label, input, hint) =>
  h("label", { class: "field" }, h("span", {}, label), input, hint && h("small", { class: "muted" }, hint));

export const chip = (text, kind = "") => h("span", { class: `chip ${kind}` }, text);
