# Auth and environment variables

CallPilot uses **Google sign-in only**. You need `NEXTAUTH_SECRET`, `NEXTAUTH_URL`, `GOOGLE_CLIENT_ID`, and `GOOGLE_CLIENT_SECRET`. Create OAuth credentials at [Google Cloud Console](https://console.cloud.google.com/apis/credentials) (OAuth 2.0 Client ID, type "Web application", add your redirect URI e.g. `http://localhost:3000/api/auth/callback/google`).

---

## Fix "Server configuration" error on Cloud Run

If you see **"There is a problem with the server configuration"** when clicking **Sign in with Google** on the deployed site, the frontend service is missing or has wrong auth env vars.

**1. Get your frontend URL**

```bash
gcloud run services describe callpilot-frontend --region us-central1 --format 'value(status.url)'
```

Example: `https://callpilot-frontend-xxxxx-uc.a.run.app`

**2. Set env vars on the frontend service**

Replace placeholders and run (one line):

```bash
gcloud run services update callpilot-frontend --region us-central1 \
  --set-env-vars "NEXTAUTH_URL=https://YOUR-FRONTEND-URL.run.app,NEXTAUTH_SECRET=YOUR_SECRET,GOOGLE_CLIENT_ID=YOUR_CLIENT_ID.apps.googleusercontent.com,GOOGLE_CLIENT_SECRET=YOUR_CLIENT_SECRET"
```

- **NEXTAUTH_URL** = exact frontend URL from step 1 (no trailing slash).
- **NEXTAUTH_SECRET** = e.g. output of `openssl rand -base64 32`.
- **GOOGLE_CLIENT_ID** / **GOOGLE_CLIENT_SECRET** = from [Google Cloud Console → Credentials](https://console.cloud.google.com/apis/credentials) (OAuth 2.0 Client ID, Web application).

**3. Add redirect URI in Google Cloud Console**

In that OAuth client, under **Authorized redirect URIs**, add:

`https://YOUR-FRONTEND-URL.run.app/api/auth/callback/google`

Save, wait a minute, then try **Sign in with Google** again.

---

## Fix "Session could not be verified" / "Unauthorized" on deployed site

If you're signed in on the deployed app but the **dashboard** shows "Session could not be verified" or "Unauthorized", the **backend** cannot verify your JWT. It needs the same **NEXTAUTH_SECRET** as the frontend.

**Easiest fix** — run this from the repo root (it reads `frontend/.env.local` and pushes the secret to **both** the frontend and backend so they match):

```bash
./scripts/set-backend-auth-secret.sh
```

Then **sign out and sign in again** on the app (required so a new JWT is created with the correct secret).

**Manual fix** — if you prefer to set it yourself:

```bash
gcloud run services update callpilot-backend --region us-central1 \
  --update-env-vars "NEXTAUTH_SECRET=YOUR_SAME_SECRET_AS_FRONTEND"
```

Use the exact value of `NEXTAUTH_SECRET` from `frontend/.env.local`.

**Future deploys:** the full deploy script sets the backend's NEXTAUTH_SECRET from `frontend/.env.local` after the backend is deployed. If you only deploy the frontend, run `./scripts/set-backend-auth-secret.sh` once to sync the secret.

### Important: Cloud Run does not use `backend/.env`

Having the same `NEXTAUTH_SECRET` in `frontend/.env.local` and `backend/.env` only helps when you run **locally**. On **Cloud Run**, the backend gets its environment from **gcloud** (what you set via the deploy script or `./scripts/set-backend-auth-secret.sh`), **not** from `backend/.env`. So you must run the script (or the gcloud commands) to push the secret to the **deployed** backend and frontend.

### Verify the deployed backend has the secret

Check what the **Cloud Run backend** actually sees:

```bash
# Replace with your backend URL, e.g. from: gcloud run services describe callpilot-backend --region us-central1 --format 'value(status.url)'
curl -s https://YOUR-BACKEND-URL.run.app/api/debug/auth-configured
```

- If the response is `{"auth_configured": false}`, the **Cloud Run backend** does not have `NEXTAUTH_SECRET` set. Run `./scripts/set-backend-auth-secret.sh` and redeploy the backend if needed (the script only updates env vars; a new revision is created automatically).
- If the response is `{"auth_configured": true}` but you still see "Session could not be verified", the backend has the secret but something else is wrong (e.g. frontend signing with a different secret, or token not sent). Ensure you ran the script for **both** frontend and backend, then sign out and sign in again.

---

## Where do I get the NextAuth secret?

You **generate** it yourself—it’s not issued by NextAuth or any service. It’s a random string used to sign/encrypt session tokens.

**Generate a secret (pick one):**

```bash
# Option 1: OpenSSL (macOS/Linux)
openssl rand -base64 32

# Option 2: Node
node -e "console.log(require('crypto').randomBytes(32).toString('base64'))"
```

Copy the output and set it as `NEXTAUTH_SECRET` in your env (see below). Use **different** secrets for local vs dev/staging vs production.

---

## Env files: local vs dev deployment

### Rule of thumb

| Environment   | Where config lives                    | Notes |
|-------------|----------------------------------------|-------|
| **Local**   | `frontend/.env.local`                  | Gitignored; only on your machine. |
| **Dev deploy** | Hosting env (e.g. Vercel / Cloud Run env vars) | Set in the hosting UI or CI. |
| **Template** | `frontend/.env.local.example`          | Committed; copy to `.env.local` and fill in. |

Never commit real secrets. `.env.local` is in `.gitignore`.

### Local development

1. From repo root: `cp frontend/.env.local.example frontend/.env.local`
2. Edit `frontend/.env.local`:
   - Set `NEXTAUTH_SECRET` to the output of `openssl rand -base64 32`
   - Set `NEXTAUTH_URL=http://localhost:3000`
   - Set `NEXT_PUBLIC_API_URL=http://localhost:8080` (or your local backend URL)
3. Run the app **from the frontend directory** so `.env.local` is loaded:
   ```bash
   cd frontend && npm run dev
   ```

### Dev deployment (e.g. Vercel, Cloud Run, Netlify)

Set these in the **hosting provider’s environment** (not in a file in the repo):

| Variable | Example (dev) | Notes |
|----------|----------------|-------|
| `NEXTAUTH_SECRET` | *(same as above, new random string)* | **Required.** Generate a new one for this environment. |
| `NEXTAUTH_URL` | `https://your-app.vercel.app` | Must be the **exact** URL of the deployed frontend (no trailing slash). |
| `NEXT_PUBLIC_API_URL` | `https://callpilot-backend-xxx.run.app` | Your deployed backend URL. |

- Use a **different** `NEXTAUTH_SECRET` per environment (local, dev, prod).
- After changing env vars, redeploy or restart so the new values are picked up.

### Backend (for auth verification)

The backend verifies the same JWT that NextAuth creates. It needs the **same** secret the frontend uses for that environment:

- **Local:** In `backend/.env` set `NEXTAUTH_SECRET=<same value as in frontend/.env.local>`.
- **Dev/prod:** Set `NEXTAUTH_SECRET` in the backend’s env (e.g. Cloud Run env vars) to the same value as the frontend for that environment.

---

## Quick checklist

- [ ] `NEXTAUTH_SECRET` set in `frontend/.env.local` (local) or in hosting env (deployed).
- [ ] `NEXTAUTH_URL` = app URL (`http://localhost:3000` local, `https://...` deployed).
- [ ] Backend `NEXTAUTH_SECRET` matches frontend for that environment.
- [ ] Run `npm run dev` from the `frontend/` directory so `.env.local` is loaded.

If you still see `[next-auth][error][NO_SECRET]`, the server is not seeing `NEXTAUTH_SECRET`. Confirm the variable is in the env for the process that runs Next.js (and restart the dev server after changing `.env.local`).
