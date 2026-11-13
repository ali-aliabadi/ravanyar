// Admin screens. SPEC-0003: review therapists' credentials, approve or reject.
import { api, busy, chip, download, faDate, h, toast, toman } from "./lib.js";
import { KINDS, REASONS, STATUS } from "./therapist.js";

let filter = "submitted";

function decisionForm(p, ctx) {
  const reason = h("select", { "aria-label": "دلیل رد" },
    Object.entries(REASONS).map(([v, t]) => h("option", { value: v }, t)));
  const decide = (approve) => (e) => busy(e.currentTarget, async () => {
    await api("POST", `/admin/therapists/${p.id}/decision`, { approve, reason: approve ? null : reason.value });
    await ctx.rerender();
    toast(approve ? "پروفایل فعال شد." : "رد شد و به درمانگر اطلاع داده می‌شود.", true);
  });
  return h("div", { class: "stack" },
    h("button", { class: "btn primary", onclick: decide(true) }, "تأیید و فعال‌سازی"),
    h("div", { class: "row" }, reason, h("button", { class: "btn danger", onclick: decide(false) }, "رد")));
}

function card(p, ctx) {
  const [label, kind] = STATUS[p.status];
  return h("div", { class: "card" },
    h("div", { class: "row" }, h("h2", { class: "grow" }, p.display_name || "بدون نام"), chip(label, kind)),
    h("dl", { class: "rows" },
      h("div", {}, h("dt", {}, "عنوان"), h("dd", {}, p.title)),
      h("div", {}, h("dt", {}, "تخصص"), h("dd", {}, p.specialties)),
      h("div", {}, h("dt", {}, "هزینه"), h("dd", {}, p.fee_rial ? toman(p.fee_rial) : "—")),
      p.submitted_at && h("div", {}, h("dt", {}, "ارسال"), h("dd", {}, faDate(p.submitted_at)))),
    p.bio && h("p", { class: "muted" }, p.bio),
    h("h2", {}, "مدارک"),
    h("p", { class: "muted" }, "هر بار باز کردن مدرک در گزارش دسترسی ثبت می‌شود."),
    h("ul", { class: "docs" }, p.credentials.map((c) => h("li", {},
      h("div", { class: "meta" }, h("span", {}, KINDS[c.kind]), h("small", {}, `${c.mime} · ${faDate(c.uploaded_at)}`)),
      h("button", { class: "btn ghost small",
        onclick: (e) => busy(e.currentTarget, () => download(`/credentials/${c.id}`, KINDS[c.kind])) },
      "دریافت")))),
    p.status === "submitted" && decisionForm(p, ctx));
}

async function renderQueue(view, ctx) {
  const queue = await api("GET", `/admin/therapists?status=${filter}`);
  const filters = h("div", { class: "segmented" }, Object.entries(STATUS).map(([v, [t]]) =>
    h("label", {}, h("input", { type: "radio", name: "f", value: v, checked: v === filter,
      onchange: () => { filter = v; ctx.rerender(); } }), h("span", {}, t))));
  view.replaceChildren(
    h("div", { class: "hero" }, h("h1", {}, "بررسی درمانگران"),
      h("p", { class: "muted" }, "مدارک را با اطلاعات پروفایل مقایسه کنید، سپس تأیید یا رد کنید.")),
    filters,
    ...(queue.length ? queue.map((p) => card(p, ctx)) : [h("p", { class: "muted" }, "موردی نیست.")]),
  );
}

export const tabs = [{ id: "review", label: "بررسی درمانگران", render: renderQueue }];
