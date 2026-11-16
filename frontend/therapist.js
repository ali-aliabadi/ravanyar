// Therapist screens. SPEC-0003: profile, credential upload, submit for review.
// SPEC-0004: publish free times and see which are booked (never by whom).
import {
  MAX_SPECIALTIES, SPECIALTIES, api, busy, byDay, chip, confirmAction, download, fa, faDate, faDay,
  faTime, field, h, tehranDay, tehranIso, toast,
} from "./lib.js";

export const STATUS = {
  draft: ["پیش‌نویس", ""],
  submitted: ["در انتظار بررسی", "warn"],
  approved: ["فعال", "ok"],
  rejected: ["نیاز به اصلاح", "off"],
};
export const KINDS = { license: "پروانهٔ نظام روان‌شناسی", degree: "مدرک تحصیلی", national_id: "کارت ملی" };
export const REASONS = {
  unreadable: "تصویر مدارک خوانا نیست.",
  license_invalid: "پروانه معتبر نیست یا منقضی شده است.",
  mismatch: "اطلاعات پروفایل با مدارک یکسان نیست.",
  incomplete: "مدارک یا اطلاعات کامل نیست.",
};
const STEPS = ["ثبت‌نام", "ارسال مدارک", "بررسی ناظر", "فعال‌سازی پروفایل"];
const STEP_OF = { draft: 1, rejected: 1, submitted: 2, approved: 4 };

function steps(status) {
  const at = STEP_OF[status];
  return h("ol", { class: "steps" }, STEPS.map((s, i) =>
    h("li", { class: i < at ? "done" : i === at ? "now" : "" }, s)));
}

async function renderProfile(view, ctx) {
  const p = await api("GET", "/therapist/profile");
  const editable = p.status !== "submitted";
  const docsEditable = p.status === "draft" || p.status === "rejected";
  const [label, kind] = STATUS[p.status];

  const input = (name, attrs = {}) => h("input", {
    type: "text", name, value: p[name] ?? "", disabled: !editable, ...attrs,
  });
  const form = h("form", { novalidate: true },
    field("نام نمایشی", input("display_name", { maxlength: 80, required: true })),
    field("عنوان حرفه‌ای", input("title", { maxlength: 80, placeholder: "مثلاً روان‌شناس بالینی" })),
    h("fieldset", { class: "field" }, h("legend", {}, "حوزه‌های تخصصی"),
      h("div", { class: "checks" }, Object.entries(SPECIALTIES).map(([code, label]) => h("label", {},
        h("input", { type: "checkbox", name: "specialties", value: code, disabled: !editable,
          checked: p.specialties.includes(code) }), h("span", {}, label)))),
      h("small", { class: "muted" }, `حداکثر ${fa(MAX_SPECIALTIES)} مورد.`)),
    field("معرفی", h("textarea", { name: "bio", maxlength: 2000, disabled: !editable }, p.bio)),
    field("هزینهٔ هر جلسه (تومان)", input("fee", {
      type: "number", min: 1000, step: 1000, dir: "ltr",
      value: p.fee_rial ? p.fee_rial / 10 : "",
    })),
    editable && h("button", { class: "btn primary", type: "submit" }, "ذخیره"),
  );
  form.addEventListener("submit", (e) => {
    e.preventDefault();
    const d = new FormData(form);
    const specialties = d.getAll("specialties");
    if (specialties.length > MAX_SPECIALTIES) return toast(`حداکثر ${fa(MAX_SPECIALTIES)} تخصص انتخاب کنید.`);
    busy(e.submitter, async () => {
      const fee = Number(d.get("fee"));
      await api("PUT", "/therapist/profile", {
        display_name: d.get("display_name").trim(),
        title: d.get("title").trim(),
        bio: d.get("bio").trim(),
        specialties,
        fee_rial: fee ? fee * 10 : null,
      });
      await ctx.rerender();
      toast(p.status === "approved" ? "ذخیره شد. تغییر نام، عنوان، معرفی یا تخصص دوباره بررسی می‌شود." : "ذخیره شد.", true);
    });
  });

  const docs = h("ul", { class: "docs" }, p.credentials.map((c) => h("li", {},
    h("div", { class: "meta" },
      h("button", { class: "link", type: "button",
        onclick: (e) => busy(e.currentTarget, () => download(`/credentials/${c.id}`, KINDS[c.kind])) },
      KINDS[c.kind]),
      h("small", {}, `بارگذاری ${faDate(c.uploaded_at)}`)),
    docsEditable && h("button", { class: "btn ghost small", onclick: async (e) => {
      const btn = e.currentTarget;
      if (!await confirmAction("حذف مدرک", "این فایل حذف شود؟", "حذف")) return;
      busy(btn, async () => { await api("DELETE", `/therapist/credentials/${c.id}`); await ctx.rerender(); });
    } }, "حذف"))));

  const upload = h("form", { class: "row" },
    h("select", { name: "kind", "aria-label": "نوع مدرک" },
      Object.entries(KINDS).map(([v, t]) => h("option", { value: v }, t))),
    h("input", { type: "file", name: "file", accept: "application/pdf,image/jpeg,image/png", required: true, class: "grow" }),
    h("button", { class: "btn ghost", type: "submit" }, "بارگذاری"));
  upload.addEventListener("submit", (e) => {
    e.preventDefault();
    const file = upload.file.files[0];
    if (!file) return toast("فایلی انتخاب نشده است.");
    if (file.size > 5 * 1024 * 1024) return toast("حداکثر حجم فایل ۵ مگابایت است.");
    busy(e.submitter, async () => {
      await api("POST", "/therapist/credentials", new FormData(upload));
      await ctx.rerender();
    });
  });

  const submit = h("button", { class: "btn primary block", onclick: (e) => busy(e.currentTarget, async () => {
    await api("POST", "/therapist/submit");
    await ctx.rerender();
    toast("برای بررسی ارسال شد.", true);
  }) }, "ارسال برای بررسی");

  view.replaceChildren(
    h("div", { class: "hero" }, h("h1", {}, "پروفایل حرفه‌ای"),
      h("p", { class: "muted" }, p.status === "approved"
        ? "پروفایل شما فعال است و مراجعان آن را در جست‌وجو می‌بینند."
        : "پس از تأیید مدارک، پروفایل شما برای مراجعان نمایش داده می‌شود.")),
    h("div", { class: "card" },
      h("div", { class: "row" }, h("h2", { class: "grow" }, "وضعیت"), chip(label, kind)),
      steps(p.status),
      p.status === "rejected" && h("p", { class: "toast" }, REASONS[p.reject_reason] || REASONS.incomplete)),
    h("div", { class: "card" }, h("h2", {}, "اطلاعات پروفایل"), form),
    h("div", { class: "card" }, h("h2", {}, "مدارک"),
      h("p", { class: "muted" }, "فایل‌ها پیش از ذخیره با کلید مخصوص شما رمزنگاری می‌شوند و فقط ناظر آن‌ها را می‌بیند. پروانه الزامی است."),
      docs, docsEditable && upload),
    docsEditable && submit,
  );
}

// SPEC-0004. A Jalali week picker built from fa-IR formatting: <input type="date"> would be
// Gregorian, and a calendar library would be a dependency (ADR 0006).
const DAY_MS = 86_400_000;
const LAST_WEEK = 8; // the API refuses slots more than 60 days ahead
const HOURS = Array.from({ length: 36 }, (_, i) => {
  const minutes = 6 * 60 + i * 30; // 06:00 .. 23:30
  return `${String(Math.floor(minutes / 60)).padStart(2, "0")}:${minutes % 60 ? "30" : "00"}`;
});
const SLOT_STATE = { open: ["آزاد", ""], booked: ["رزرو شده", "ok"], cancelled: ["لغو شده", "off"] };
let week = 0;
let pickedDay = "";
let pickedTime = "17:00";
let pickedWeeks = 1;
const WEEKS = { 1: "فقط همین روز", 2: "۲ هفته", 4: "۴ هفته", 8: "۸ هفته" };

function slotItem(s, ctx) {
  const [label, kind] = SLOT_STATE[s.state];
  const act = (title, text, yes, method, path, done) => h("button", { class: "btn ghost small", onclick: async (e) => {
    const btn = e.currentTarget;
    if (!await confirmAction(title, text, yes)) return;
    busy(btn, async () => { await api(method, path); await ctx.rerender(); toast(done, true); });
  } }, yes);
  return h("li", {},
    h("div", { class: "meta" }, h("span", {}, faTime(s.start_at)), chip(label, kind),
      s.client_name && h("small", {}, s.client_name)),
    s.state === "open" && act("حذف زمان", "این زمان از فهرست زمان‌های آزاد حذف شود؟", "حذف",
      "DELETE", `/therapist/slots/${s.id}`, "حذف شد."),
    s.state === "booked" && act("لغو جلسه", "این جلسه رزرو شده است. لغو شود؟ این زمان دوباره پیشنهاد نمی‌شود.",
      "لغو جلسه", "POST", `/therapist/slots/${s.id}/cancel`, "جلسه لغو شد."));
}

async function renderSlots(view, ctx) {
  const p = await api("GET", "/therapist/profile");
  const hero = h("div", { class: "hero" }, h("h1", {}, "زمان‌های من"),
    h("p", { class: "muted" }, "زمان‌هایی که برای جلسه آزادید. ساعت‌ها به وقت تهران و هر جلسه ۵۰ دقیقه است."));
  if (p.status !== "approved") {
    view.replaceChildren(hero, h("div", { class: "card" },
      h("p", { class: "muted" }, "پس از تأیید پروفایل می‌توانید زمان‌های آزاد خود را اعلام کنید.")));
    return;
  }
  const slots = await api("GET", "/therapist/slots");
  const days = Array.from({ length: 7 }, (_, i) => tehranDay(Date.now() + (week * 7 + i) * DAY_MS));
  if (!days.includes(pickedDay)) pickedDay = days[0];
  const go = (w) => () => { week = w; ctx.rerender(); };
  const picker = h("div", { class: "stack" },
    h("div", { class: "row" },
      h("button", { class: "btn ghost small", type: "button", disabled: week === 0, onclick: go(week - 1) }, "هفتهٔ قبل"),
      h("span", { class: "grow" }),
      h("button", { class: "btn ghost small", type: "button", disabled: week === LAST_WEEK, onclick: go(week + 1) }, "هفتهٔ بعد")),
    h("div", { class: "row", role: "group", "aria-label": "روز" }, days.map((d) => h("button", {
      type: "button", class: d === pickedDay ? "btn primary small" : "btn ghost small",
      "aria-pressed": d === pickedDay ? "true" : "false",
      onclick: () => { pickedDay = d; ctx.rerender(); },
    }, faDay(tehranIso(d, "12:00"))))));
  const time = h("select", { "aria-label": "ساعت" },
    HOURS.map((t) => h("option", { value: t, selected: t === pickedTime }, fa(t))));
  const repeat = h("select", { "aria-label": "تکرار هفتگی" },
    Object.entries(WEEKS).map(([n, t]) => h("option", { value: n, selected: Number(n) === pickedWeeks }, t)));
  const add = h("div", { class: "row" }, time, repeat, h("button", { class: "btn primary", type: "button",
    onclick: (e) => busy(e.currentTarget, async () => {
      [pickedTime, pickedWeeks] = [time.value, Number(repeat.value)];
      const start_at = tehranIso(pickedDay, pickedTime);
      let done = "زمان اضافه شد.";
      if (pickedWeeks === 1) await api("POST", "/therapist/slots", { start_at });
      else {
        const r = await api("POST", "/therapist/slots/weekly", { start_at, weeks: pickedWeeks });
        done = `${fa(r.created.length)} زمان اضافه شد.` + (r.skipped ? ` ${fa(r.skipped)} هفته با زمان دیگری هم‌پوشانی داشت یا بیش از ۶۰ روز بعد بود.` : "");
      }
      await ctx.rerender();
      toast(done, true);
    }) }, "افزودن زمان"));
  const list = [...byDay(slots)].map(([, items]) => h("div", { class: "stack" },
    h("h3", {}, faDay(items[0].start_at)), h("ul", { class: "docs" }, items.map((s) => slotItem(s, ctx)))));
  view.replaceChildren(hero,
    h("div", { class: "card" }, h("h2", {}, "افزودن زمان آزاد"), picker, add),
    h("div", { class: "card" }, h("h2", {}, "زمان‌های پیش رو"),
      ...(list.length ? list : [h("p", { class: "muted" }, "هنوز زمانی اعلام نکرده‌اید.")])));
}

export const tabs = [
  { id: "profile", label: "پروفایل حرفه‌ای", render: renderProfile },
  { id: "slots", label: "زمان‌های من", render: renderSlots },
];
