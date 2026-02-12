# How NextAuth works in CallPilot

## Short answer: where are users and passwords stored?

**CallPilot uses Google sign-in only.** Users and passwords live in **Google's** systems. Your app never sees or stores passwords; Google tells NextAuth who the user is, and NextAuth creates a session (JWT in a cookie). No user table or password storage in your app.

---

## How NextAuth works in general

NextAuth is a **session layer**, not a user database. It:

1. Lets you plug in one or more **providers** (Google, GitHub, etc.).
2. When someone signs in, the provider says who they are.
3. NextAuth creates a **session** (by default a signed JWT in a cookie). That cookie is the proof that the user is logged in.
4. Your app and backend trust that proof because it's signed with `NEXTAUTH_SECRET`.

---

## What you have now

**Google only.** Users sign in with their Google account. Your app receives their identity (id, email, name) and stores a signed session (JWT). No user or password storage in your app. Set `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET` from [Google Cloud Console](https://console.cloud.google.com/apis/credentials).

---

## If you later want email/password sign-up

To have **your own** users and passwords you would:

1. **Store users** in a database (e.g. your existing SQLite or Postgres): table with `user_id`, `email`, `password_hash`, `name`, `created_at`, etc.
2. **Sign-up:** A form that hashes the password (e.g. with bcrypt) and inserts a row.
3. **Sign-in (Credentials):** In `authorize()`, look up the user by email, compare password with `password_hash`, and if they match return the user object.

NextAuth would still not store users or passwords; your database would. NextAuth would only create the session after your `authorize()` confirms the credentials.

---

## Summary

- **Auth:** Google sign-in only. No user or password storage in your app.
- **Sessions:** Signed JWTs in cookies; the backend verifies them with `NEXTAUTH_SECRET` and uses the `sub` (user id) for per-user data (bookings, tasks).
