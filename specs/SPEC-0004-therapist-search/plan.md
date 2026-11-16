---
id: SPEC-0004
---

## Approach

1. **Service:** `core/search.py`, two functions over `TherapistProfile`. The base queryset is
   `status=approved`, `account__is_active=True`, ordered by `-reviewed_at, pk` so pages stay
   stable.
   - `search(q)`: when `q` is given, filter `display_name`, `title` and `specialties` with
     `icontains` on a normalised form of both sides. Arabic ي→ی and ك→ک, and ZWNJ removed, via
     Django's `Replace` on the column and the same mapping in Python on `q`. No migration, no
     new column.
   - `public_profile(id)`: one approved profile, or `NotFoundError`.
2. **API:** `core/api_search.py`, thin views on the default `consented` auth.
   - `POST /api/therapists/search`, body `{q: str ≤ 100}`, paginated with ninja's built-in
     `@paginate` (20 a page; `limit` and `offset` in the query string are not sensitive).
     POST keeps the search text out of URLs, so out of nginx, uvicorn and Cloudflare logs.
   - `GET /api/therapists/{id}`.
   - `PublicProfileOut` has only `id`, `display_name`, `title`, `specialties`, `bio`,
     `fee_rial`: never status, credentials or review fields.
3. **Web:** `frontend/client.js` with one tab, "یافتن درمانگر": a search box, result cards
   (name, title, specialties, fee in toman), and a profile view. `app.js` sets
   `TABS.client` to it, as `therapist.js` and `admin.js` do now. No booking button; that
   comes with booking.
4. **Seed:** the four invented approved therapists from SPEC-0003 already cover staging.
   Add one draft so staging shows the filter working (a draft stays out of the admin
   review queue, unlike one in review with no documents).

## Alternatives rejected

- `GET ?q=`: the search text would land in every access log on the way.
- A normalised copy of each field stored at write time: needs a migration and a backfill to
  save a `Replace` on a few hundred rows.
- Listing every approved profile and filtering in the browser: simplest today, but it sends
  the whole directory on every visit.

## Risks

- Substring search on free-text specialties misses spellings the normalisation does not
  cover. A fixed specialty list is a SPEC-0005 candidate.
