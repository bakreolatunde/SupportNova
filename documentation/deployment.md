# Deployment

Three options, roughly in order of effort. None of these were run from this
environment (no Docker daemon, no way to hold open a public port here) — the
Dockerfile/compose file build logic and the FastAPI app itself were tested;
actually deploying needs your own hosting account.

## Option A — Docker, anywhere with a Docker host

```bash
docker compose up --build
```

Serves on `http://localhost:8000`. For an actual server (a VPS, EC2, etc.):
`docker build -t supportnova . && docker run -p 8000:80 --env-file .env supportnova`.
Swap `DATABASE_URL` in `.env` to a real Postgres instance before this leaves
your laptop — SQLite is fine for a demo, not for concurrent users.

## Option B — Render.com (free tier, fastest path to a public URL)

1. Push this repo to GitHub.
2. In Render: **New +** → **Blueprint**, point it at the repo — it reads `render.yaml`.
3. In the service's **Environment** tab, set `ANTHROPIC_API_KEY` (left blank in
   `render.yaml` deliberately — never commit a real key).
4. Deploy. Render gives you a public `https://supportnova-xxxx.onrender.com` URL —
   that's what goes in the SRS's "deployed URL + credentials" deliverable.

Free tier sleeps after inactivity and the first request after a sleep is slow —
mention that if a demo video shows a cold start.

## Option C — Railway / Fly.io

Both auto-detect the `Procfile`. Railway: `railway up` from the CLI after
`railway login`. Fly.io: `fly launch` (it'll offer to generate a `fly.toml`
from the Dockerfile — accept that, then `fly deploy`). Set the same env vars
(`ANTHROPIC_API_KEY`, `APP_SECRET_KEY`) through each platform's secrets UI,
never in a committed file.

## Before submitting

- [ ] `ANTHROPIC_API_KEY` set on the host, not in git
- [ ] `APP_SECRET_KEY` changed from the `.env.example` default
- [ ] Ran `python -m pytest` against the deployed commit, not just locally
- [ ] Created at least one admin user via `POST /auth/register` so the
      admin dashboard is reachable in the demo (there's no seed script for this yet)
- [ ] Database is NOT SQLite if more than one person will submit complaints concurrently during evaluation
