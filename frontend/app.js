// Sign-in, consents, the account screen and the role-based tabs. Each role's screens live in
// their own module. Never log anything here: phone numbers and tokens are personal data.
import {
  $, api, busy, confirmAction, fa, h, message, setSignedOutHandler, store, toast,
} from "./lib.js";
import { tabs as adminTabs } from "./admin.js";
import { tabs as therapistTabs } from "./therapist.js";

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
const ACCOUNT = { id: "account", label: "حساب" };
const TABS = { client: [], therapist: therapistTabs, admin: adminTabs };

let phone = "";
let me = null;
let testMode = false;
let resendTimer = 0;

function show(name) {
  for (const sec of document.querySelectorAll("main > section")) sec.hidden = sec.id !== `screen-${name}`;
  const signedIn = name === "account" || name === "view" || name === "consent";
  $("logout").hidden = !signedIn;
  $("tabs").hidden = !(name === "account" || name === "view");
  toast("");
  const focus = document.querySelector(`#screen-${name} input, #screen-${name} button.primary`);
  if (focus) focus.focus();
}

// Tabs: the role's own screens, then the account screen. The hash remembers the open tab.
function renderTabs() {
  const tabs = [...TABS[me.role] || [], ACCOUNT];
  const want = location.hash.slice(1).split("/")[0];
  const active = tabs.find((t) => t.id === want) || tabs[0];
  $("tabs").replaceChildren(...tabs.map((t) => h("button", {
    class: t === active ? "tab active" : "tab",
    "aria-current": t === active ? "page" : null,
    onclick: () => { location.hash = t.id; },
  }, t.label)));
  return active;
}

async function route() {
  if (!me) return;
  const tab = renderTabs();
  if (tab === ACCOUNT) {
    await renderConsents();
    return show("account");
  }
  const view = $("screen-view");
  view.replaceChildren(h("p", { class: "muted" }, "در حال بارگذاری…"));
  show("view");
  try {
    await tab.render(view, { me, testMode, rerender: route });
  } catch (err) {
    if (err.status === 401) return signedOut();
    view.replaceChildren();
    toast(message(err));
  }
}

function signedOut() {
  store.del("token");
  me = null;
  show("phone");
}
setSignedOutHandler(signedOut);

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
    me = await api("GET", "/me");
    $("me-phone").textContent = fa(me.phone.replace(/^\+98/, "0"));
    $("me-role").textContent = ROLES[me.role] || me.role;
    await route();
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

  // SPEC-0002: staging banner when the backend runs with test numbers.
  // Test numbers may also sign in as admin there (SPEC-0003).
  api("GET", "/health").then((health) => {
    testMode = Boolean(health && health.test_mode);
    $("staging").hidden = !testMode;
    $("role-admin").hidden = !testMode;
  }).catch(() => null);
  window.addEventListener("hashchange", route);

  if (store.get("token")) load();
  else show("phone");
});
