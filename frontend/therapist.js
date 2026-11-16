// Therapist screens. SPEC-0003: profile, credential upload, submit for review.
import { api, busy, chip, confirmAction, download, faDate, field, h, toast } from "./lib.js";

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
    field("حوزه‌های تخصصی", input("specialties", { maxlength: 200 }), "با ویرگول جدا کنید."),
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
    busy(e.submitter, async () => {
      const fee = Number(d.get("fee"));
      await api("PUT", "/therapist/profile", {
        display_name: d.get("display_name").trim(),
        title: d.get("title").trim(),
        bio: d.get("bio").trim(),
        specialties: d.get("specialties").trim(),
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

export const tabs = [{ id: "profile", label: "پروفایل حرفه‌ای", render: renderProfile }];
