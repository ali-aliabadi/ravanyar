# Deploy

One VPS with Docker. Caddy gets the TLS certificate itself once DNS points at the server.

```bash
git clone https://github.com/ali-aliabadi/ravanyar && cd ravanyar/deploy
cp .env.example .env   # fill every empty value
docker compose up -d --build
```

Update: `git pull && docker compose up -d --build`. Migrations run first, as the owner role.

The app connects as `DB_APP_USER`, which owns no tables, so it cannot drop the access log's
append-only trigger. `db-init.sh` only runs on an empty data volume.

Back up `.env` (above all the two keys) somewhere other than this server.
