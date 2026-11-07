# Deploy

One VPS with Docker, behind the host's existing nginx (Cloudflare + origin cert do TLS).
The stack listens on `127.0.0.1:18082` only; nginx proxies `/api/` to it.

```bash
git clone https://github.com/ali-aliabadi/ravanyar && cd ravanyar/deploy
cp .env.example .env   # fill every empty value
docker compose up -d --build
```

Then follow `nginx-margin.conf` (a rate-limit zone in conf.d, locations in the margin server
block) and `nginx -t && systemctl reload nginx`.

Update: `git pull && docker compose up -d --build`. Migrations run first, as the owner role.

The app connects as `DB_APP_USER`, which owns no tables, so it cannot drop the access log's
append-only trigger. `db-init.sh` only runs on an empty data volume.

Back up `.env` (above all the two keys) somewhere other than this server.

## Automatic deploys

Every push to `main` that passes CI runs `deploy/update.sh` on the server (the `deploy` job in
`.github/workflows/ci.yml`). One-time setup, as root on the server:

1. A `ravanyar` user in the `docker` group owns the checkout and `.env`.
2. Its `~/.ssh/authorized_keys` holds the CI public key, pinned to the script:
   `command="/srv/ravanyar/deploy/update.sh",restrict ssh-ed25519 AAAA... ci-deploy`
3. The GitHub environment `production` holds the secrets `DEPLOY_SSH_KEY` (private key),
   `DEPLOY_KNOWN_HOSTS` (`ssh-keyscan -p PORT HOST`), `DEPLOY_TARGET` (`ravanyar@HOST`) and
   `DEPLOY_PORT`.

The `docker` group is root-equivalent, so anyone who can merge to `main` can run code on this
server. Pre-launch that is acceptable; the production server should not share a host.
