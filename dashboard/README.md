<div align="center">

```
███████╗██╗   ██╗██████╗  ██████╗ ██╗  ██╗
╚══███╔╝╚██╗ ██╔╝██╔══██╗██╔═══██╗╚██╗██╔╝
  ███╔╝  ╚████╔╝ ██████╔╝██║   ██║ ╚███╔╝ 
 ███╔╝    ╚██╔╝  ██╔══██╗██║   ██║ ██╔██╗ 
███████╗   ██║   ██║  ██║╚██████╔╝██╔╝ ██╗
╚══════╝   ╚═╝   ╚═╝  ╚═╝ ╚═════╝ ╚═╝  ╚═╝
```

<h3>ZyroX Dashboard — Next.js Web Interface</h3>

<a href="https://nexiohost.in"><img src="https://img.shields.io/badge/⭐%20PREMIUM%20HOSTING-NexioHost-FFD700?style=for-the-badge&labelColor=1a1a2e&color=FFD700&logoColor=FFD700"/></a>

<p>
  <a href="https://nextjs.org"><img src="https://img.shields.io/badge/Next.js-14+-000000?style=for-the-badge&logo=nextdotjs&logoColor=white"/></a>
  <a href="https://typescriptlang.org"><img src="https://img.shields.io/badge/TypeScript-5+-3178C6?style=for-the-badge&logo=typescript&logoColor=white"/></a>
  <a href="https://tailwindcss.com"><img src="https://img.shields.io/badge/Tailwind_CSS-3-06B6D4?style=for-the-badge&logo=tailwindcss&logoColor=white"/></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-MIT-red?style=for-the-badge"/></a>
</p>
<p>
  <a href="https://discord.gg/codexdev"><img src="https://img.shields.io/badge/Discord-Join_Server-5865F2?style=for-the-badge&logo=discord&logoColor=white"/></a>
  <a href="https://youtube.com/@CodeXDevs"><img src="https://img.shields.io/badge/YouTube-CodeXDevs-FF0000?style=for-the-badge&logo=youtube&logoColor=white"/></a>
  <a href="https://github.com/RayExo"><img src="https://img.shields.io/badge/GitHub-RayExo-181717?style=for-the-badge&logo=github&logoColor=white"/></a>
</p>

</div>

---

## ✦ Overview

This folder contains the ZyroX web dashboard built with `Next.js 14` (App Router), `TypeScript`, and `Tailwind CSS`. It connects to the bot's FastAPI backend via a permanent Cloudflare Tunnel HTTPS URL and lets server admins manage all bot settings through a sleek, branded UI.

```
dashboard/
├── app/                       App Router pages & API routes
│   ├── api/auth/              NextAuth OAuth callback
│   ├── dashboard/             Main dashboard area
│   │   ├── admin/             Admin-only panel
│   │   ├── guilds/            Server selection
│   │   └── guild/[guildId]/   Per-server settings pages
│   │       ├── antinuke/
│   │       ├── automod/
│   │       ├── leveling/
│   │       ├── logging/
│   │       ├── tickets/
│   │       ├── welcome/
│   │       └── …more
│   ├── docs/                  Documentation page
│   ├── privacy/               Privacy policy
│   └── terms/                 Terms of service
├── components/
│   ├── dashboard/             Feature-specific form components
│   └── ui/                    Base UI components (button, card, input…)
├── hooks/                     Custom React hooks
├── lib/                       API client, auth config, utilities
└── types/                     TypeScript type definitions
```

---

## ✦ Features

- **Discord OAuth2 login** — secure sign-in, session managed by NextAuth
- **Per-server management** — antinuke, automod, leveling, logging, tickets, welcome, and more
- **Live bot stats** — real-time metrics pulled from the FastAPI backend
- **Admin panel** — owner-only configuration and announcements
- **Fully branded** — name, logo, and colours via environment variables
- **HTTPS ready** — connects to the bot's permanent Cloudflare Tunnel URL
- **Vercel-ready** — deploys in minutes with zero config changes

---

## ✦ Prerequisites

| Requirement | Notes |
|---|---|
| Node.js 18+ | — |
| ZyroX bot running | with `API_ENABLED=true` and `TUNNEL_ENABLED=true` |
| Discord OAuth app | from [Discord Developer Portal](https://discord.com/developers/applications) |

---

## ✦ Setup

### 1 — Install dependencies

```bash
npm install
```

### 2 — Configure environment

Create a `.env.local` file in this folder:

```env
# ── Bot API ───────────────────────────────────────────────────────
# Use the Cloudflare Tunnel URL from the bot's console output
NEXT_PUBLIC_API_URL           = https://api.yourdomain.com/api/v1
NEXT_PUBLIC_DASHBOARD_API_KEY = your_shared_api_key   # must match bot's DASHBOARD_API_KEY

# ── NextAuth ──────────────────────────────────────────────────────
NEXTAUTH_URL                  = http://localhost:3000
NEXTAUTH_SECRET               = a_long_random_string   # generate: openssl rand -base64 32

# ── Discord OAuth ─────────────────────────────────────────────────
DISCORD_CLIENT_ID             = your_discord_oauth_client_id
DISCORD_CLIENT_SECRET         = your_discord_oauth_client_secret

# ── Branding ──────────────────────────────────────────────────────
NEXT_PUBLIC_ADMIN_IDS         = your_discord_user_id
NEXT_PUBLIC_BRAND_NAME        = "ZyroX"
NEXT_PUBLIC_BRAND_NAME_WORD   = "ZX"
```

### 3 — Run locally

```bash
npm run dev
```

Open [http://localhost:3000](http://localhost:3000)

---

## ✦ Environment Reference

| Variable | Description |
|---|---|
| `NEXT_PUBLIC_API_URL` | Full URL to the bot's FastAPI backend — use the Cloudflare Tunnel URL |
| `NEXT_PUBLIC_DASHBOARD_API_KEY` | Must exactly match `DASHBOARD_API_KEY` in the bot `.env` |
| `NEXTAUTH_URL` | Your dashboard's public URL (Vercel domain in production) |
| `NEXTAUTH_SECRET` | Random secret for NextAuth session signing |
| `DISCORD_CLIENT_ID` | Discord OAuth2 client ID |
| `DISCORD_CLIENT_SECRET` | Discord OAuth2 client secret |
| `NEXT_PUBLIC_ADMIN_IDS` | Comma-separated Discord user IDs with admin panel access |
| `NEXT_PUBLIC_BRAND_NAME` | Bot name shown in the dashboard UI |
| `NEXT_PUBLIC_BRAND_NAME_WORD` | Short abbreviation shown in the dashboard (e.g. `ZX`) |

---

## ✦ Deployment (Vercel)

**Step 1 — Connect your repo**

Go to [vercel.com](https://vercel.com) → **Add New Project** → connect your GitHub repo → set root directory to `dashboard/`

Vercel auto-detects Next.js — no build settings needed.

**Step 2 — Add environment variables**

In **Settings → Environment Variables**, add all keys from the table above.

| Variable | Production Value |
|---|---|
| `NEXT_PUBLIC_API_URL` | `https://api.yourdomain.com/api/v1` |
| `NEXTAUTH_URL` | `https://your-app.vercel.app` |
| `NEXTAUTH_SECRET` | [generate one](https://generate-secret.vercel.app/32) |
| `DISCORD_CLIENT_ID` | from [Discord Developer Portal](https://discord.com/developers/applications) |

**Step 3 — Add redirect URI in Discord**

In your Discord app → **OAuth2 → Redirects** → add:

```
https://your-app.vercel.app/api/auth/callback/discord
```

**Step 4 — Deploy**

Hit **Deploy**. Vercel builds and publishes automatically. ✓

---

## ✦ Connecting to the Bot API

The dashboard reads the API URL from `NEXT_PUBLIC_API_URL`.

| Environment | Value |
|---|---|
| Local dev | `http://localhost:8000/api/v1` |
| Production | `https://api.yourdomain.com/api/v1` (Cloudflare Tunnel URL) |

The bot prints the confirmed URL on every startup:
```
◈ Tunnel: API is live at  https://api.yourdomain.com
  ↳ NEXT_PUBLIC_API_URL = https://api.yourdomain.com/api/v1
```

This URL is permanent — it never changes between restarts as long as the Cloudflare Tunnel token stays the same.

---

## ✦ Troubleshooting

| Problem | Fix |
|---|---|
| Auth error on login | Check Discord OAuth client ID/secret and redirect URI in Developer Portal |
| Dashboard can't load data | Confirm bot is running with `API_ENABLED=true` and `NEXT_PUBLIC_API_URL` is correct |
| CORS error in browser | Add your Vercel URL to `CORS_ORIGINS` in the bot's `.env` |
| `NEXTAUTH_SECRET` error | Make sure `NEXTAUTH_SECRET` is set and non-empty |
| API key rejected (401) | `NEXT_PUBLIC_DASHBOARD_API_KEY` must exactly match `DASHBOARD_API_KEY` in the bot |
| Tunnel URL changed | Cloudflare named tunnels always produce the same URL — check `CF_TUNNEL_TOKEN` is valid |

---

<div align="center">

## ✦ CodeX Devs

*Built for protection. Designed for style.*

<a href="https://discord.gg/codexdev"><img src="https://discord.com/api/guilds/1301573144817045524/widget.png?style=banner2" alt="CodeX Development Discord Server" width="480"/></a>

<p>
  <a href="https://discord.gg/codexdev"><img src="https://img.shields.io/badge/Discord-Join_Server-5865F2?style=for-the-badge&logo=discord&logoColor=white"/></a>
  <a href="https://youtube.com/@CodeXDevs"><img src="https://img.shields.io/badge/YouTube-CodeXDevs-FF0000?style=for-the-badge&logo=youtube&logoColor=white"/></a>
  <a href="https://github.com/RayExo"><img src="https://img.shields.io/badge/GitHub-RayExo-181717?style=for-the-badge&logo=github&logoColor=white"/></a>
  <a href="https://nexiohost.in"><img src="https://img.shields.io/badge/⭐%20PREMIUM%20HOSTING-NexioHost-FFD700?style=for-the-badge&labelColor=1a1a2e&color=FFD700&logoColor=FFD700"/></a>
</p>

© 2026 CodeX Devs — MIT License

</div>
