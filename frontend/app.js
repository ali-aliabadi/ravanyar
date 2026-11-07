"use strict";
// Never log anything here: phone numbers and tokens are personal data (AGENTS.md §1.4).

// shortcut: mirrors CONSENT_VERSIONS in backend settings; bump both together, or expose them
// from the API once versions change more than once.
const VERSIONS = { terms: "terms-draft-0", privacy: "privacy-draft-0" };

const DOCS = {
  terms: {
    title: "شرایط استفاده",
    body: "روان‌یار بستری برای ارتباط مراجع و درمانگر است و جایگزین خدمات اورژانسی نیست. " +
      "در صورت خطر فوری برای خود یا دیگران با ۱۱۵ یا ۱۲۳ تماس بگیرید. " +
      "این متن پیش‌نویس است و متن نهایی پیش از راه‌اندازی منتشر می‌شود.",
  },
  privacy: {
    title: "سیاست حریم خصوصی",
    body: "شمارهٔ موبایل شما پیش از ذخیره با کلیدی مخصوص خودتان رمزنگاری می‌شود. " +
      "اطلاعات شما بدون رضایت جداگانه با هیچ شخص یا سرویس دیگری به اشتراک گذاشته نمی‌شود " +
      "و با حذف حساب، کلید رمزنگاری نابود می‌شود. " +
      "این متن پیش‌نویس است و متن نهایی پیش از راه‌اندازی منتشر می‌شود.",
  },
};

const ROLES = { client: "مراجع", therapist: "درمانگر", admin: "مدیر" };

const ERRORS = {
  rate_limited: "درخواست‌ها زیاد بود. یک دقیقه صبر کنید و دوباره تلاش کنید.",
  sms_unavailable: "ارسال پیامک ممکن نشد. کمی بعد دوباره تلاش کنید.",
  code_rejected: "کد درست نیست یا منقضی شده است.",
  outdated_version: "متن‌ها به‌روز شده‌اند. صفحه را دوباره بارگذاری کنید.",
  forbidden: "اجازهٔ این کار را ندارید.",
};

const $ = (id) => document.getElementById(id);
const fa = (s) => String(s).replace(/\d/g, (d) => "۰۱۲۳۴۵۶۷۸۹"[d]);
const store = {
  get: (k) => { try { return localStorage.getItem(k); } catch { return null; } },
  set: (k, v) => { try { localStorage.setItem(k, v); } catch { /* private mode */ } },
  del: (k) => { try { localStorage.removeItem(k); } catch { /* private mode */ } },
};

let phone = "";
let resendTimer = 0;

class ApiError extends Error {
  constructor(status, detail) { super(String(status)); this.status = status; this.detail = detail; }
}

async function api(method, path, body) {
  const headers = { Accept: "application/json" };
  const token = store.get("token");
  if (token) headers.Authorization = `Bearer ${token}`;
  if (body) headers["Content-Type"] = "application/json";
  let res;
  try {
    res = await fetch(`/api${path}`, { method, headers, body: body && JSON.stringify(body) });
  } catch {
    throw new ApiError(0, "network");
  }
  const data = res.status === 204 ? null : await res.json().catch(() => null);
  if (!res.ok) throw new ApiError(res.status, data && data.detail);
  return data;
}

function message(err) {
  if (err.status === 0) return "اتصال برقرار نشد. اینترنت خود را بررسی کنید.";
  if (typeof err.detail === "string" && ERRORS[err.detail]) return ERRORS[err.detail];
  if (err.status === 422 && Array.isArray(err.detail)) {
    const field = err.detail[0] && err.detail[0].loc && err.detail[0].loc.at(-1);
    if (field === "phone") return "شمارهٔ موبایل معتبر نیست. مثل ۰۹۱۲۳۴۵۶۷۸۹ وارد کنید.";
    if (field === "code") return "کد ۶ رقم است.";
  }
  return "خطایی رخ داد. دوباره تلاش کنید.";
}

function toast(text, ok = false) {
  const el = $("toast");
  el.textContent = text;
  el.classList.toggle("ok", ok);
  el.hidden = !text;
}

function show(name) {
  for (const s of document.querySelectorAll("main > section")) s.hidden = s.id !== `screen-${name}`;
  $("logout").hidden = !(name === "home" || name === "consent");
  toast("");
  const focus = document.querySelector(`#screen-${name} input, #screen-${name} button.primary`);
  if (focus) focus.focus();
}

// Disables the button while the request runs and turns failures into a toast.
async function busy(button, work) {
  button.disabled = true;
  button.setAttribute("aria-busy", "true");
  try {
    await work();
  } catch (err) {
    if (err.status === 401) return signedOut();
    toast(message(err));
  } finally {
    button.disabled = false;
    button.removeAttribute("aria-busy");
  }
}

function signedOut() {
  store.del("token");
  show("phone");
}

function startResendCountdown() {
  clearInterval(resendTimer);
  let left = 60; // RESEND_AFTER in the backend
  const btn = $("resend");
  btn.disabled = true;
  const tick = () => {
    btn.textContent = left > 0 ? `ارسال دوباره (${fa(left)} ثانیه)` : "ارسال دوباره";
    if (left-- <= 0) { clearInterval(resendTimer); btn.disabled = false; }
  };
  tick();
  resendTimer = setInterval(tick, 1000);
}

async function sendCode() {
  await api("POST", "/auth/code", { phone });
  $("sent-to").textContent = fa(phone);
  startResendCountdown();
}

async function load() {
  try {
    const me = await api("GET", "/me");
    $("me-phone").textContent = fa(me.phone.replace(/^\+98/, "0"));
    $("me-role").textContent = ROLES[me.role] || me.role;
    $("hero-line").textContent = me.role === "therapist"
      ? "حساب درمانگری شما فعال است. امکانات بیشتر به‌زودی اضافه می‌شود."
      : "حساب شما فعال است. امکانات بیشتر به‌زودی اضافه می‌شود.";
    await renderConsents();
    show("home");
  } catch (err) {
    if (err.status === 403 && err.detail === "consent_required") return renderMissing();
    if (err.status === 401) return signedOut();
    show("phone");
    toast(message(err));
  }
}

function docItem(doc, extra) {
  const li = document.createElement("li");
  const meta = document.createElement("div");
  meta.className = "meta";
  const open = document.createElement("button");
  open.className = "link";
  open.type = "button";
  open.textContent = DOCS[doc] ? DOCS[doc].title : doc;
  open.addEventListener("click", () => openDoc(doc));
  meta.append(open);
  li.append(meta, ...extra(meta));
  return li;
}

async function renderConsents() {
  const all = await api("GET", "/me/consents");
  const list = $("consents");
  list.replaceChildren();
  for (const doc of Object.keys(VERSIONS)) {
    const active = all.find((c) => c.document === doc && !c.withdrawn_at);
    list.append(docItem(doc, (meta) => {
      const when = document.createElement("small");
      when.textContent = active
        ? `پذیرفته‌شده در ${new Date(active.given_at).toLocaleDateString("fa-IR")}`
        : "پس گرفته شده";
      meta.append(when);
      const chip = document.createElement("span");
      chip.className = active ? "chip ok" : "chip off";
      chip.textContent = active ? "فعال" : "غیرفعال";
      if (!active) return [chip];
      const btn = document.createElement("button");
      btn.className = "btn ghost small";
      btn.textContent = "پس گرفتن";
      btn.addEventListener("click", () => withdraw(doc, btn));
      return [chip, btn];
    }));
  }
}

async function renderMissing() {
  const list = $("missing");
  list.replaceChildren();
  for (const doc of Object.keys(VERSIONS)) {
    list.append(docItem(doc, () => {
      const chip = document.createElement("span");
      chip.className = "chip";
      chip.textContent = "نیاز به تأیید";
      return [chip];
    }));
  }
  show("consent");
}

function openDoc(doc) {
  $("doc-title").textContent = DOCS[doc].title;
  $("doc-body").textContent = DOCS[doc].body;
  $("doc-dialog").showModal();
}

function confirmAction(title, text, yes) {
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

async function withdraw(doc, btn) {
  const ok = await confirmAction(
    `پس گرفتن رضایت «${DOCS[doc].title}»`,
    "تا وقتی دوباره نپذیرید، به حساب خود دسترسی نخواهید داشت.",
    "پس گرفتن",
  );
  if (!ok) return;
  await busy(btn, async () => {
    await api("POST", `/me/consents/${doc}/withdraw`);
    await load();
  });
}

document.addEventListener("DOMContentLoaded", () => {
  $("phone-form").addEventListener("submit", (e) => {
    e.preventDefault();
    phone = $("phone").value.trim();
    if (!phone) return toast("شمارهٔ موبایل را وارد کنید.");
    busy(e.submitter, async () => {
      await sendCode();
      show("verify");
    });
  });

  $("verify-form").addEventListener("submit", (e) => {
    e.preventDefault();
    if (!$("agree").checked) return toast("برای ادامه باید شرایط و حریم خصوصی را بپذیرید.");
    busy(e.submitter, async () => {
      const { token } = await api("POST", "/auth/verify", {
        phone,
        code: $("code").value.trim(),
        role: new FormData(e.target).get("role"),
        terms_version: VERSIONS.terms,
        privacy_version: VERSIONS.privacy,
      });
      store.set("token", token);
      $("code").value = "";
      clearInterval(resendTimer);
      await load();
    });
  });

  $("resend").addEventListener("click", (e) => busy(e.currentTarget, async () => {
    await sendCode();
    toast("کد جدید ارسال شد.", true);
  }));

  $("change-phone").addEventListener("click", () => { clearInterval(resendTimer); show("phone"); });

  for (const btn of document.querySelectorAll("[data-doc]")) {
    btn.addEventListener("click", () => openDoc(btn.dataset.doc));
  }

  $("accept-all").addEventListener("click", (e) => busy(e.currentTarget, async () => {
    for (const [document_, version] of Object.entries(VERSIONS)) {
      await api("POST", "/me/consents", { document: document_, version });
    }
    await load();
  }));

  $("logout").addEventListener("click", (e) => busy(e.currentTarget, async () => {
    await api("POST", "/auth/logout").catch(() => null); // signing out locally is what matters
    signedOut();
  }));

  $("delete").addEventListener("click", async (e) => {
    const btn = e.currentTarget;
    const ok = await confirmAction(
      "حذف همیشگی حساب",
      "همهٔ اطلاعات شما غیرقابل بازیابی می‌شود. مطمئن هستید؟",
      "بله، حذف شود",
    );
    if (!ok) return;
    busy(btn, async () => {
      await api("DELETE", "/me");
      signedOut();
      toast("حساب شما حذف شد.", true);
    });
  });

  if (store.get("token")) load();
  else show("phone");
});
