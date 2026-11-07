# Deploy

One VPS with Docker, behind the host's existing nginx (Cloudflare + origin cert do TLS).
The stack listens on `127.0.0.1:18082` only; nginx proxies `/api/` to it.

```bash
git clone https://github.com/ali-aliabadi/ravanyar && cd ravanyar/deploy
cp .env.example .env   # fill every empty value
docker compose up -d --build
```

Then add `nginx-margin.conf` to the margin server block, create the htpasswd file it names,
and `nginx -t && systemctl reload nginx`.

Update: `git pull && docker compose up -d --build`. Migrations run first, as the owner role.

The app connects as `DB_APP_USER`, which owns no tables, so it cannot drop the access log's
append-only trigger. `db-init.sh` only runs on an empty data volume.

Back up `.env` (above all the two keys) somewhere other than this server.
