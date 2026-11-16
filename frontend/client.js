// Client screens. SPEC-0004: find an approved therapist and read their public profile.
// SPEC-0004: book one of their free times, and see or cancel your bookings.
// The search text says what someone needs help with: it stays in memory, never in the URL.
import {
  SPECIALTIES, api, busy, byDay, chip, confirmAction, faDay, faTime, h, specialtyNames, toast, toman,
} from "./lib.js";

const PAGE_SIZE = 20; // the API's page size (api_search.py)
let query = "";
let specialty = "";
let justBooked = false;
const when = (iso) => `${faDay(iso)}، ساعت ${faTime(iso)}`;

const facts = (p) => h("dl", { class: "rows" },
  h("div", {}, h("dt", {}, "عنوان"), h("dd", {}, p.title)),
  p.specialties.length > 0 && h("div", {}, h("dt", {}, "تخصص"), h("dd", {}, specialtyNames(p.specialties))),
  h("div", {}, h("dt", {}, "هزینهٔ هر جلسه"), h("dd", {}, p.fee_rial ? toman(p.fee_rial) : "—")));

const card = (p) => h("div", { class: "card" },
  h("div", { class: "row" }, h("h2", { class: "grow" }, p.display_name),
    h("button", { class: "btn ghost small", onclick: () => { location.hash = `find/${p.id}`; } },
      "مشاهدهٔ پروفایل")),
  facts(p));

async function bookSlot(button, p, slot) {
  if (!await confirmAction("رزرو جلسه", `جلسه با ${p.display_name}، ${when(slot.start_at)}؟`, "رزرو")) return;
  busy(button, async () => {
    await api("POST", "/bookings", { slot_id: slot.id });
    justBooked = true;
    location.hash = "bookings";
  });
}

async function renderProfile(view, id) {
  const path = `/therapists/${encodeURIComponent(id)}`;
  const [p, slots] = await Promise.all([api("GET", path), api("GET", `${path}/slots`)]);
  const days = [...byDay(slots)].map(([, list]) => h("div", { class: "stack" },
    h("h3", {}, faDay(list[0].start_at)),
    h("div", { class: "row" }, list.map((s) => h("button", {
      class: "btn ghost small", onclick: (e) => bookSlot(e.currentTarget, p, s),
    }, faTime(s.start_at))))));
  view.replaceChildren(
    h("div", { class: "row" },
      h("button", { class: "btn ghost small", onclick: () => { location.hash = "find"; } }, "بازگشت به نتایج")),
    h("div", { class: "card" }, h("h1", {}, p.display_name), facts(p), p.bio && h("p", {}, p.bio)),
    h("div", { class: "card" }, h("h2", {}, "زمان‌های آزاد"),
      h("p", { class: "muted" }, "ساعت‌ها به وقت تهران است. هر جلسه ۵۰ دقیقه است."),
      ...(days.length ? days : [h("p", { class: "muted" }, "فعلاً زمان آزادی اعلام نشده است.")])),
  );
}

const STATUS = { booked: ["رزرو شده", "ok"], cancelled: ["لغو شده", "off"] };
const BY = { client: "توسط شما", therapist: "توسط درمانگر", system: "" };

async function renderBookings(view, ctx) {
  const all = await api("GET", "/me/bookings"); // latest first
  const now = Date.now();
  const upcoming = all.filter((b) => b.status === "booked" && new Date(b.start_at) > now).reverse();
  const rest = all.filter((b) => !upcoming.includes(b));
  const item = (b, ...end) => h("li", {},
    h("div", { class: "meta" }, h("span", {}, b.therapist_name || "درمانگر"), h("small", {}, when(b.start_at))), ...end);
  const cancel = (b) => h("button", { class: "btn ghost small", onclick: async (e) => {
    const btn = e.currentTarget;
    if (!await confirmAction("لغو جلسه", `جلسهٔ ${when(b.start_at)} لغو شود؟`, "لغو جلسه")) return;
    busy(btn, async () => { await api("POST", `/bookings/${b.id}/cancel`); await ctx.rerender(); toast("جلسه لغو شد.", true); });
  } }, "لغو");
  view.replaceChildren(
    h("div", { class: "hero" }, h("h1", {}, "نوبت‌های من")),
    h("div", { class: "card" }, h("h2", {}, "جلسه‌های پیش رو"),
      upcoming.length ? h("ul", { class: "docs" }, upcoming.map((b) => item(b, cancel(b))))
        : h("div", { class: "stack" }, h("p", { class: "muted" }, "جلسهٔ رزرو شده‌ای ندارید."),
          h("button", { class: "btn primary", onclick: () => { location.hash = "find"; } }, "یافتن درمانگر"))),
    ...(rest.length ? [h("div", { class: "card" }, h("h2", {}, "گذشته و لغو شده"),
      h("ul", { class: "docs" }, rest.map((b) => item(b,
        chip(`${STATUS[b.status][0]} ${BY[b.cancelled_by] || ""}`.trim(), STATUS[b.status][1])))))] : []),
  );
  if (justBooked) { justBooked = false; toast("جلسه رزرو شد.", true); }
}

async function renderSearch(view) {
  const id = location.hash.split("/")[1];
  if (id) return renderProfile(view, id);

  let page = 1;
  const results = h("div", { class: "stack" });
  const more = h("button", { class: "btn ghost block", type: "button", hidden: true }, "نتایج بیشتر");
  async function load(reset) {
    if (reset) page = 1;
    const data = await api("POST", `/therapists/search?page=${page}`, { q: query, specialty: specialty || null });
    const cards = data.items.map(card);
    if (!reset) results.append(...cards);
    else results.replaceChildren(...(cards.length ? cards
      : [h("p", { class: "muted" }, "درمانگری با این مشخصات پیدا نشد.")]));
    more.hidden = page * PAGE_SIZE >= data.count;
  }
  more.addEventListener("click", (e) => busy(e.currentTarget, async () => { page += 1; await load(false); }));

  const input = h("input", {
    type: "search", name: "q", maxlength: 100, value: query, class: "grow",
    placeholder: "نام یا عنوان درمانگر", "aria-label": "جست‌وجوی درمانگر",
  });
  const pick = h("select", { name: "specialty", "aria-label": "تخصص" },
    h("option", { value: "" }, "همهٔ تخصص‌ها"),
    Object.entries(SPECIALTIES).map(([v, t]) => h("option", { value: v, selected: v === specialty }, t)));
  const form = h("form", { class: "row", role: "search" }, input, pick,
    h("button", { class: "btn primary", type: "submit" }, "جست‌وجو"));
  form.addEventListener("submit", (e) => {
    e.preventDefault();
    query = input.value.trim();
    specialty = pick.value;
    busy(e.submitter, () => load(true));
  });

  view.replaceChildren(
    h("div", { class: "hero" }, h("h1", {}, "یافتن درمانگر"),
      h("p", { class: "muted" }, "همهٔ درمانگران این فهرست مدارکشان بررسی و تأیید شده است.")),
    form, results, more,
  );
  await load(true);
}

export const tabs = [
  { id: "find", label: "یافتن درمانگر", render: renderSearch },
  { id: "bookings", label: "نوبت‌های من", render: renderBookings },
];
