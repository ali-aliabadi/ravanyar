// Client screens. SPEC-0004: find an approved therapist and read their public profile.
// The search text says what someone needs help with: it stays in memory, never in the URL.
import { api, busy, h, toman } from "./lib.js";

const PAGE_SIZE = 20; // the API's page size (api_search.py)
let query = "";

const facts = (p) => h("dl", { class: "rows" },
  h("div", {}, h("dt", {}, "عنوان"), h("dd", {}, p.title)),
  p.specialties && h("div", {}, h("dt", {}, "تخصص"), h("dd", {}, p.specialties)),
  h("div", {}, h("dt", {}, "هزینهٔ هر جلسه"), h("dd", {}, p.fee_rial ? toman(p.fee_rial) : "—")));

const card = (p) => h("div", { class: "card" },
  h("div", { class: "row" }, h("h2", { class: "grow" }, p.display_name),
    h("button", { class: "btn ghost small", onclick: () => { location.hash = `find/${p.id}`; } },
      "مشاهدهٔ پروفایل")),
  facts(p));

async function renderProfile(view, id) {
  const p = await api("GET", `/therapists/${encodeURIComponent(id)}`);
  view.replaceChildren(
    h("div", { class: "row" },
      h("button", { class: "btn ghost small", onclick: () => { location.hash = "find"; } }, "بازگشت به نتایج")),
    h("div", { class: "card" }, h("h1", {}, p.display_name), facts(p), p.bio && h("p", {}, p.bio)),
  );
}

async function renderSearch(view) {
  const id = location.hash.split("/")[1];
  if (id) return renderProfile(view, id);

  let page = 1;
  const results = h("div", { class: "stack" });
  const more = h("button", { class: "btn ghost block", type: "button", hidden: true }, "نتایج بیشتر");
  async function load(reset) {
    if (reset) page = 1;
    const data = await api("POST", `/therapists/search?page=${page}`, { q: query });
    const cards = data.items.map(card);
    if (!reset) results.append(...cards);
    else results.replaceChildren(...(cards.length ? cards
      : [h("p", { class: "muted" }, "درمانگری با این مشخصات پیدا نشد.")]));
    more.hidden = page * PAGE_SIZE >= data.count;
  }
  more.addEventListener("click", (e) => busy(e.currentTarget, async () => { page += 1; await load(false); }));

  const input = h("input", {
    type: "search", name: "q", maxlength: 100, value: query, class: "grow",
    placeholder: "نام، عنوان یا تخصص؛ مثلاً اضطراب", "aria-label": "جست‌وجوی درمانگر",
  });
  const form = h("form", { class: "row", role: "search" }, input,
    h("button", { class: "btn primary", type: "submit" }, "جست‌وجو"));
  form.addEventListener("submit", (e) => {
    e.preventDefault();
    query = input.value.trim();
    busy(e.submitter, () => load(true));
  });

  view.replaceChildren(
    h("div", { class: "hero" }, h("h1", {}, "یافتن درمانگر"),
      h("p", { class: "muted" }, "همهٔ درمانگران این فهرست مدارکشان بررسی و تأیید شده است.")),
    form, results, more,
  );
  await load(true);
}

export const tabs = [{ id: "find", label: "یافتن درمانگر", render: renderSearch }];
