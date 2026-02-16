# Deploy guide

Five things to deploy. Each one is independent.

```
pruv.dev          → Marketing site   (Vercel)
app.pruv.dev      → Dashboard        (Vercel)
api.pruv.dev      → API backend      (Railway)
docs.pruv.dev     → Documentation    (Mintlify)
PyPI              → xycore + pruv    (pip publish)
```

---

## 1. Prerequisites

You need accounts on:
- [Vercel](https://vercel.com) — frontend hosting
- [Railway](https://railway.app) — API + Postgres + Redis
- [Mintlify](https://mintlify.com) — docs hosting
- [Supabase](https://supabase.com) — or any PostgreSQL provider (Railway has built-in Postgres)
- [Stripe](https://stripe.com) — payments
- [Cloudflare](https://cloudflare.com) — DNS + R2 storage

Domain: `pruv.dev` with DNS on Cloudflare.

---

## 2. Environment variables

Create a `.env` file for local development. **Never commit this file.**

```bash
# ─── Core ───
PRUV_ENV=production
DEBUG=false

# ─── Database (PostgreSQL) ───
DATABASE_URL=postgresql://user:password@host:5432/pruv

# ─── Redis ───
REDIS_URL=redis://default:password@host:6379

# ─── Auth ───
JWT_SECRET=          # openssl rand -hex 32
JWT_ALGORITHM=HS256

# ─── OAuth ───
GITHUB_CLIENT_ID=
GITHUB_CLIENT_SECRET=
GITHUB_CALLBACK_URL=https://api.pruv.dev/v1/auth/oauth/github
GOOGLE_CLIENT_ID=
GOOGLE_CLIENT_SECRET=

# ─── Stripe ───
STRIPE_SECRET_KEY=sk_live_...
STRIPE_WEBHOOK_SECRET=whsec_...

# ─── Cloudflare R2 (S3-compatible storage) ───
R2_BUCKET=pruv-receipts
R2_ACCESS_KEY=
R2_SECRET_KEY=
R2_ENDPOINT=https://<account-id>.r2.cloudflarestorage.com

# ─── Frontend ───
NEXT_PUBLIC_API_URL=https://api.pruv.dev
NEXTAUTH_URL=https://app.pruv.dev
NEXTAUTH_SECRET=     # openssl rand -hex 32
```

Generate secrets:
```bash
openssl rand -hex 32   # JWT_SECRET
openssl rand -hex 32   # NEXTAUTH_SECRET
```

---

## 3. Database setup

### Option A: Railway (easiest)

1. Create a new project in Railway
2. Click **+ New** → **Database** → **PostgreSQL**
3. Copy the `DATABASE_URL` from the Variables tab
4. Do the same for Redis: **+ New** → **Database** → **Redis**

### Option B: Supabase

1. Create a project at supabase.com
2. Go to Settings → Database → Connection string
3. Copy the URI (starts with `postgresql://`)

### Run migrations

```bash
cd apps/api
pip install -e ".[prod]"
alembic upgrade head
```

This creates all tables: `users`, `api_keys`, `chains`, `entries`, `checkpoints`, `receipts`, `webhooks`.

---

## 4. Deploy the API — `api.pruv.dev`

### Railway

The API depends on `xycore` (installed from the local `packages/xycore` during Docker build). The build must run from the **repo root** so the Dockerfile can access both `packages/xycore` and `apps/api`. A `railway.toml` at the repo root and `Dockerfile` in `apps/api/` handle this automatically.

1. Connect your GitHub repo in Railway
2. **Do NOT set a root directory** — leave it as the repo root so the Dockerfile can reach `packages/xycore`
3. Railway will detect `railway.toml` at the repo root, which points the build to `apps/api/Dockerfile`
4. Add all environment variables from section 2
5. Add custom domain: `api.pruv.dev`
6. In Cloudflare DNS, add a CNAME record pointing `api` to Railway's domain

### Verify

```bash
curl https://api.pruv.dev/health
# {"status":"ok","version":"1.0.0"}
```

---

## 5. Deploy the Dashboard — `app.pruv.dev`

### Vercel

1. Import repo in Vercel
2. Set **Root Directory** to `apps/dashboard`
3. Framework preset: **Next.js**
4. Add environment variables:

```
NEXT_PUBLIC_API_URL=https://api.pruv.dev
NEXTAUTH_URL=https://app.pruv.dev
NEXTAUTH_SECRET=<your-secret>
```

5. Deploy
6. Add custom domain: `app.pruv.dev`
7. In Cloudflare DNS, add a CNAME record pointing `app` to Vercel's domain

The `next.config.ts` already has `output: "standalone"` and rewrites `/api/*` to your API.

---

## 6. Deploy the Marketing Site — `pruv.dev`

### Stack

- **Next.js 15+** (App Router, static export)
- **No Tailwind** — pure CSS custom properties in `globals.css`
- **No framer-motion** — CSS animations only
- **Fonts:** JetBrains Mono + Instrument Sans (Google Fonts, loaded via CSS `@import`)
- **Interactive chain demo:** React client component (`chain-demo.tsx`)

### Routes

| Route            | Content                              |
|------------------|--------------------------------------|
| `/`              | Homepage — hero, live chain demo, receipt, comparison, industries, install |
| `/how-it-works`  | XY primitive spec, step-by-step, chain rule, verification, properties |
| `/pricing`       | 4-tier pricing grid, rate limits, FAQ |
| `/industries`    | 8-industry grid with X:/Y: labels + per-industry detail |
| `/security`      | Data protection spec, auto-redaction patterns, infrastructure |
| `/privacy`       | Privacy policy                       |
| `/terms`         | Terms of service                     |

### Vercel

1. Same Vercel project or a new one
2. Set **Root Directory** to `apps/web`
3. Framework preset: **Next.js**
4. No special env vars needed — site is fully static
5. Deploy
6. Add custom domain: `pruv.dev`
7. In Cloudflare DNS, point the root domain to Vercel

### Notes

- The build produces 100% static pages (no server-side rendering needed)
- The only client component is the interactive chain demo on the homepage
- Reference design is saved as `pruv-site.html` in the repo root
- Design language: dark protocol-spec aesthetic — no gradient heroes, no feature cards with icons, no testimonial carousels

---

## 7. Deploy Docs — `docs.pruv.dev`

### Mintlify

1. Go to [mintlify.com](https://mintlify.com) and connect your repo
2. Set the docs directory to `docs/`
3. Mintlify reads `mint.json` and deploys automatically on push
4. Add custom domain: `docs.pruv.dev`
5. In Cloudflare DNS, add a CNAME for `docs` pointing to Mintlify

---

## 8. Publish Python packages to PyPI

Publishing is automated via GitHub Actions. The workflow uses **PyPI Trusted Publishers** (OIDC) — no API tokens to manage.

### One-time setup on PyPI

For each package (`xycore` and `pruv`), add a trusted publisher on PyPI:

1. Go to https://pypi.org/manage/account/publishing/
2. Click "Add a new pending publisher" (for first publish) or go to the package settings
3. Fill in:
   - **PyPI project name**: `xycore` (then repeat for `pruv`)
   - **Owner**: `pruv-dev`
   - **Repository**: `pruv`
   - **Workflow name**: `publish.yml`
   - **Environment name**: `pypi`
4. Save

### Publishing

**Option A: Create a GitHub release** (recommended)

Create a release on GitHub — both packages build and publish automatically.

**Option B: Manual trigger**

Go to Actions → "Publish to PyPI" → Run workflow → pick `xycore`, `pruv`, or `both`.

### Manual publish (fallback)

```bash
pip install build twine

# xycore first
cd packages/xycore
python -m build
twine upload dist/*

# then pruv
cd ../pruv
python -m build
twine upload dist/*
```

### Verify

```bash
pip install xycore        # primitive only
pip install pruv          # full SDK
```

---

## 9. DNS — Cloudflare

Add these records in Cloudflare DNS for `pruv.dev`:

| Type  | Name   | Target                         | Proxy |
|-------|--------|--------------------------------|-------|
| CNAME | `@`    | `cname.vercel-dns.com`         | DNS only |
| CNAME | `www`  | `cname.vercel-dns.com`         | DNS only |
| CNAME | `app`  | `cname.vercel-dns.com`         | DNS only |
| CNAME | `api`  | `<your-app>.up.railway.app`    | DNS only |
| CNAME | `docs` | `<your-subdomain>.mintlify.dev`| DNS only |

Turn off Cloudflare proxy (orange cloud) for Vercel and Railway domains — they handle their own TLS.

---

## 10. Stripe webhooks

1. In Stripe Dashboard → Developers → Webhooks
2. Add endpoint: `https://api.pruv.dev/v1/webhooks/stripe`
3. Select events: `checkout.session.completed`, `customer.subscription.*`
4. Copy the signing secret → set as `STRIPE_WEBHOOK_SECRET`

---

## 11. OAuth setup

### GitHub

1. Go to GitHub → Settings → Developer settings → OAuth Apps → New
2. Homepage URL: `https://pruv.dev`
3. Callback URL: `https://api.pruv.dev/v1/auth/oauth/github`
4. Copy Client ID → `GITHUB_CLIENT_ID`
5. Generate secret → `GITHUB_CLIENT_SECRET`
6. Set `GITHUB_CALLBACK_URL=https://api.pruv.dev/v1/auth/oauth/github` (must match step 3)

### Google

1. Go to Google Cloud Console → APIs & Services → Credentials
2. Create OAuth 2.0 Client ID (Web application)
3. Authorized redirect URI: `https://api.pruv.dev/v1/auth/oauth/google`
4. Copy Client ID → `GOOGLE_CLIENT_ID`
5. Copy Client Secret → `GOOGLE_CLIENT_SECRET`

---

## 12. Post-deploy checklist

Run these checks after deploying:

```bash
# Health check
curl https://api.pruv.dev/health

# Create a test chain
curl -X POST https://api.pruv.dev/v1/chains \
  -H "Authorization: Bearer pv_live_YOUR_KEY" \
  -H "Content-Type: application/json" \
  -d '{"name": "deploy-test"}'

# Verify CORS headers
curl -I -X OPTIONS https://api.pruv.dev/v1/chains \
  -H "Origin: https://app.pruv.dev" \
  -H "Access-Control-Request-Method: POST"

# Check security headers
curl -I https://api.pruv.dev/health
# Should include: Strict-Transport-Security, X-Content-Type-Options,
# X-Frame-Options, Content-Security-Policy

# Verify rate limiting
curl -I https://api.pruv.dev/v1/chains \
  -H "Authorization: Bearer pv_live_YOUR_KEY"
# Should include: X-RateLimit-Limit, X-RateLimit-Remaining

# Dashboard loads
curl -s https://app.pruv.dev | head -1

# Docs load
curl -s https://docs.pruv.dev | head -1
```

---

## 13. Monitoring

### Logs

Railway streams logs automatically. The API outputs structured JSON:

```json
{"timestamp":1707936000,"level":"info","request_id":"abc-123",
 "method":"POST","path":"/v1/chains","status_code":200,
 "duration_ms":4.52,"client_ip":"1.2.3.4"}
```

### Alerts to set up

| What                     | Threshold        | Where       |
|--------------------------|------------------|-------------|
| API health check fails   | 1 failure        | UptimeRobot / Betterstack |
| p99 latency              | > 2 seconds      | Railway metrics |
| Error rate               | > 1%             | Railway metrics |
| Database connections      | > 80% pool       | Supabase / Railway |
| Redis memory             | > 80%            | Railway |

---

## Quick reference

| Service       | URL                    | Platform  | Directory          |
|---------------|------------------------|-----------|--------------------|
| API           | api.pruv.dev           | Railway   | `apps/api`         |
| Dashboard     | app.pruv.dev           | Vercel    | `apps/dashboard`   |
| Marketing     | pruv.dev               | Vercel    | `apps/web`         |
| Docs          | docs.pruv.dev          | Mintlify  | `docs`             |
| xycore        | pypi.org/project/xycore| PyPI      | `packages/xycore`  |
| pruv SDK      | pypi.org/project/pruv  | PyPI      | `packages/pruv`    |
