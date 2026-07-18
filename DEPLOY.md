# Deploying youtube-clipper

The app is two pieces:

- **Frontend** (`web/`, Next.js) → **Vercel** (free).
- **Backend** (`server/`, FastAPI + yt-dlp + ffmpeg) → an always-on host that
  can run ffmpeg. Serverless (including Vercel) can't run the long
  download/transcode jobs, so the backend goes on a container host or VM.

Both run in the cloud — once deployed, your laptop can be off.

## What's already set up vs. what you do

In the repo: `Dockerfile`, `docker-compose.yml`, `fly.toml`, env-driven CORS,
and a per-IP rate limit. You provide the accounts and money:

- Create the Vercel / Fly / Oracle accounts (nobody can sign up for you)
- Add a card where the host requires one (Fly and Oracle verify with one even on free)
- Buy a domain if you want a custom one (~$10/yr) — optional

## Backend — option A: Fly.io (recommended)

Fly gives the backend an `https://<app>.fly.dev` URL automatically. That matters:
a Vercel (HTTPS) frontend **cannot** call an HTTP backend — browsers block mixed
content. Fly's automatic TLS avoids needing a domain just for that.

```bash
# one time
curl -L https://fly.io/install.sh | sh
fly auth login                       # you log in

cd server
fly launch --no-deploy               # creates the app from fly.toml; pick a name
fly secrets set ALLOWED_ORIGINS=https://<your-app>.vercel.app
fly deploy
```

Backend is now at `https://<app>.fly.dev`.

## Backend — option B: any VM (Oracle Cloud Always-Free, a VPS, etc.)

Always-on and genuinely free on Oracle, but you'll need a domain + TLS for the
HTTPS frontend to reach it.

```bash
# on the VM (Ubuntu)
sudo apt update && sudo apt install -y docker.io docker-compose-plugin
git clone https://github.com/johanthecoder/youtube-clipper.git
cd youtube-clipper
ALLOWED_ORIGINS=https://<your-app>.vercel.app docker compose up -d --build
```

The API listens on port 8000. To serve it over HTTPS on a domain, put
[Caddy](https://caddyserver.com/) in front (automatic Let's Encrypt):

```
# /etc/caddy/Caddyfile
api.yourdomain.com {
    reverse_proxy localhost:8000
}
```

Point an A record for `api.yourdomain.com` at the VM's IP.

## Frontend — Vercel

1. On Vercel: **Add New Project** → import `johanthecoder/youtube-clipper`.
2. Set **Root Directory** to `web`.
3. Add env var **`NEXT_PUBLIC_API_URL`** = your backend URL
   (`https://<app>.fly.dev` or `https://api.yourdomain.com`).
4. Deploy → you get `https://<app>.vercel.app`.

Make sure the backend's `ALLOWED_ORIGINS` matches that Vercel URL exactly.

## Custom domain (optional)

- Buy it (Cloudflare Registrar is at-cost; Cloudflare does not give free domains).
- Frontend: add the domain in Vercel project settings and follow its DNS steps.
- Backend: point `api.yourdomain.com` at the VM (option B). Fly users can keep
  the `.fly.dev` URL and skip this.

## Environment variables

| Var | Where | Purpose |
|-----|-------|---------|
| `NEXT_PUBLIC_API_URL` | Vercel (frontend) | backend base URL |
| `ALLOWED_ORIGINS` | backend | comma-separated origins allowed to call the API |
| `CLIP_RATE_LIMIT` | backend | clips/min per IP (default 10, 0 = off) |

## Heads-up

- **YouTube blocks datacenter IPs.** yt-dlp from a cloud host often gets
  "confirm you're not a bot." It may work only intermittently.
- **Host AUPs** frequently ban video downloaders and can suspend on complaint.
  A VM you control is the safer bet.
- Updating: `git pull` then redeploy (`fly deploy`, or
  `docker compose up -d --build`).
