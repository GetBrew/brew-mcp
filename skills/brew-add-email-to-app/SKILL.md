---
name: brew-add-email-to-app
description: "Use when adding sign-up, email verification, password reset, magic link, one-time code or welcome emails to an app through Brew, or when an app needs to send transactional or lifecycle email from code. Sets up the keyed app emails with the Brew MCP, wires them into Better Auth, Auth.js, Supabase, Clerk, Firebase or custom auth with @brew.new/sdk, and verifies with a sandbox send."
---

# Add email to an app

Brew sends app email by trigger key. The app calls `brew.send('<key>', payload)`. The key names a trigger with a published automation, and that automation holds the design, the subject and the sender. `set_up_app_email` creates all of it in one idempotent call, so the work splits into setting up the keys in Brew and calling them from the app's code. To move an app off Resend, use the `brew-migrate-from-resend` skill.

## 1. Confirm the connection and the brand

- Call `get_brew_capabilities`. If `set_up_app_email` is not in the catalog, this Brew deployment predates app emails; tell the user and stop.
- A brand connection acts on its brand. An organization connection has no default brand: take a `brand_id` from `list_brands` and confirm with the user which brand the app belongs to.
- Call `get_brand`. The starter designs take their colors, logo and voice from the brand, so a brand that is not set up produces generic emails. Say so before going on.

## 2. Detect the stack

Read `package.json` for the auth library, then pick the `stack` value:

| Dependency | `stack` |
| --- | --- |
| `better-auth` | `better-auth` |
| `next-auth`, `@auth/core` | `authjs` |
| `@supabase/supabase-js`, `@supabase/ssr` | `supabase` |
| `@clerk/*` | `clerk` |
| `firebase`, `firebase-admin` | `firebase` |
| anything else, or hand-rolled auth | `custom` |

Also look for an existing sender (Resend, SendGrid, Postmark, Nodemailer). Its call sites are what Brew replaces, inside the same auth hooks, so the app never sends the same email twice.

## 3. Set up the emails in Brew

Call `set_up_app_email` with `setup: { kind: 'kit', stack: '<stack>' }`. It creates a trigger, a design and a published automation for each key the stack sends, plus the lifecycle keys. Narrow it with `keys` (exact kit keys) or `sets` (`auth`, `lifecycle`) when the app needs fewer.

- The call publishes automations that email the person named in each payload, so on OAuth and organization connections it returns a confirmation request first. Show it to the user. After they approve, repeat the same call with `confirmed: true` and the request's `confirmation_id`.
- Each entry in `results` is `ok: true` with its `sender`, `payloadSchema` and `fireExample`, or `ok: false` with an `error`. One failing key does not stop the others; run the call again to finish them. `stack.snippets` holds code for the chosen library.
- A re-run changes only what differs. A design someone edited in Brew is kept unless the call passes `overwrite: true` (otherwise `409 APP_EMAIL_EDITED_IN_BREW`).
- For a key of the app's own, such as `order.shipped`, use `setup: { kind: 'one', triggerKey, source: { format: 'jsx' | 'html' | 'mjml', content } }`, with `{{ trigger.<field> }}` merge tags in the source. To declare the payload, pass `payloadSchema: { fields: [{ key, type }] }`, and mark a field that carries a one-time code or sign-in link `secret: true`: Brew uses it to render the email and keeps it out of contacts, logs and analytics. Keys are lowercase letters, digits, `.`, `_` and `-`; `kit`, `by-key`, `brew.*` and any `auth.*` outside the kit are reserved.
- `list_triggers` shows every key with its `appEmail` link.

## 4. Explain the sandbox

Until a sending domain verifies, app emails send from Brew's sandbox. The sandbox reaches members of the user's Brew organization only, at most 50 sends per organization per UTC day, and the mail is marked as sandbox mail. A fire for anyone else is refused with `DOMAIN_REQUIRED` (422), and the send after the daily cap with `SANDBOX_DAILY_LIMIT` (429, with `Retry-After`). Tell the user that a sign-up with a non-member address fails in development until a domain verifies, so they test with team addresses.

## 5. Install the SDK and wire the app

Install `@brew.new/sdk` (13.2.0 or later; `brew.send` alone needs 13.1.0) with the project's package manager.

The user creates an API key in Brew under **Settings → API**; the `automations` scope is enough to send. It lives in `BREW_API_KEY`:

- in git-ignored `.env.local` and the host's environment settings, with an empty `BREW_API_KEY=` line in `.env.example`
- read on the server only: never a `NEXT_PUBLIC_`, `VITE_` or `PUBLIC_` variable, never in client code, a commit, or the chat

Create the client once:

```ts
// lib/brew.ts
import { createBrewClient } from '@brew.new/sdk'

export const brew = createBrewClient({ apiKey: process.env.BREW_API_KEY! })
```

If the build runs without the variable, give the adapters a function instead (`client: () => createBrewClient({ apiKey: process.env.BREW_API_KEY! })`); it runs on the first send, so a missing key fails that send, not the build.

**Better Auth** (`@brew.new/sdk/better-auth`). The callbacks send `auth.verify-email`, `auth.password-reset`, `auth.email-change`, `auth.magic-link`, `auth.otp` and `lifecycle.welcome`. On serverless, pass `waitUntil` so the response does not wait for Brew:

```ts
import { brewAuthEmails } from '@brew.new/sdk/better-auth'
import { waitUntil } from '@vercel/functions' // or: (promise) => after(() => promise) from next/server
import { brew } from './brew'

const emails = brewAuthEmails({ client: brew, waitUntil })

export const auth = betterAuth({
  emailVerification: { sendOnSignUp: true, sendVerificationEmail: emails.sendVerificationEmail },
  emailAndPassword: { enabled: true, sendResetPassword: emails.sendResetPassword },
  databaseHooks: { user: { create: { after: emails.onUserCreated } } },
  // plugins: magicLink({ sendMagicLink: emails.sendMagicLink }), emailOTP({ sendVerificationOTP: emails.sendVerificationOTP })
})
```

**Auth.js** (`@brew.new/sdk/next-auth`, also `@brew.new/sdk/auth-js`). Email sign-in needs a database adapter. On next-auth v4, pass `id: 'email'`.

```ts
import { BrewEmail } from '@brew.new/sdk/next-auth'

providers: [BrewEmail({ client: brew })] // signIn('brew', { email })
```

**Supabase.** Run the Send Email Hook as an Edge Function. The kit result for `supabase` carries the same hook in `stack.snippets`.

```ts
// supabase/functions/send-email/index.ts
import { createBrewClient } from 'npm:@brew.new/sdk@^13.2.0'
import { createSupabaseSendEmailHook } from 'npm:@brew.new/sdk@^13.2.0/supabase'

Deno.serve(createSupabaseSendEmailHook({
  client: createBrewClient({ apiKey: Deno.env.get('BREW_API_KEY')! }),
  secret: Deno.env.get('SEND_EMAIL_HOOK_SECRET')!, // v1,whsec_...
}))
```

Deploy with `supabase functions deploy send-email --no-verify-jwt`. The user then points **Authentication > Hooks > Send Email** at the function and stores `BREW_API_KEY` and the hook secret as function secrets. The hook maps each `email_action_type` to its kit key.

**Clerk.** Lifecycle only for now: Clerk keeps sending its own auth emails, and the kit for `clerk` sets up only the lifecycle keys. Send the welcome email from the `user.created` webhook with `await brew.send('lifecycle.welcome', { email, userName })`. Auth emails delivered from Clerk to Brew are coming.

**Firebase and custom auth.** Generate the link or code in the app, then send it. For Firebase, call the Admin SDK link generators (`generatePasswordResetLink`, `generateEmailVerificationLink`) instead of Firebase's own email methods:

```ts
await brew.send('auth.password-reset', { email, confirmationUrl })
```

**Lifecycle emails** come from the app's own events, for example a sign-up handler (`lifecycle.welcome`) or billing webhooks (`lifecycle.trial-ending`, `lifecycle.payment-failed`).

### Sending rules

- Await `brew.send`, or hand its promise to `waitUntil` (Vercel `@vercel/functions`, Cloudflare `ctx.waitUntil`) or Next.js `after`. A serverless function can freeze after the response, before the send leaves.
- The SDK adds an idempotency key to every call, so its own retries never send twice. Pass `{ idempotencyKey }` when the call itself can repeat (a webhook redelivery, a job retry), derived from the business event. Hash any token or code before it goes into a key.
- A refused send throws `BrewApiError` with a `code`: `TRIGGER_KEY_NOT_FOUND` (404, the key is not set up in this brand), `INVALID_PAYLOAD` (400), `NO_PUBLISHED_AUTOMATION` (422), `DOMAIN_REQUIRED` and `SANDBOX_DAILY_LIMIT` as above. Each brand holds its own keys, so a staging brand needs its own setup.

## Keys and payload fields

Every payload needs `email`, the recipient. Every other field is template data and is never written to the contact.

| Key | Fields |
| --- | --- |
| `auth.verify-email`, `auth.magic-link`, `auth.password-reset` | `confirmationUrl` or `otp`, `userName`, `expiresInMinutes` |
| `auth.otp`, `auth.reauthentication` | `otp`, `userName`, `expiresInMinutes` |
| `auth.invite` | `confirmationUrl`, `inviterName`, `organizationName` |
| `auth.email-change` | `newEmail`, `confirmationUrl` or `otp` |
| `auth.security-notice` | `noticeType` such as `password_changed` |
| `lifecycle.welcome` | `userName`, `ctaUrl` |
| `lifecycle.trial-ending` | `trialEndsAt` (required ISO date), `daysLeft`, `upgradeUrl` |
| `lifecycle.payment-failed` | `amount` (formatted, such as `$29.00`), `updatePaymentUrl` |
| `lifecycle.win-back` | `returnUrl` |

All of them also take `appName` and `userName`; the designs fall back to the brand name and a plain greeting when they are missing. `confirmationUrl`, `otp` and `newEmail` are secret fields: Brew keeps them out of logs, stored copies and contact records, and the app should not log them either. `get_trigger_contract` with `format: "ts"` returns the typed payload for a key.

## 6. Verify

1. Ask for the address the user signs in to Brew with, an organization member.
2. Call `fire_trigger_event` with `triggerKey`, `payload: { email, confirmationUrl: 'https://example.com/test' }` and an `idempotency_key`. On OAuth and organization connections it asks for confirmation first, like the setup.
3. If nothing arrives, read `list_trigger_events` for the match state and `list_automation_runs` for the run.
4. Run the real flow in the app, a sign-up or a password reset, with a team address.

Never send a test to a customer's address.

## 7. Go to production

1. The user adds a sending domain in Brew under **Domains** with the purpose **Transactional**, preferably a subdomain such as `mail.<their domain>`, and adds the DNS records at their DNS provider. `create_domain` over MCP adds a marketing domain; a transactional one is added in the Brew app.
2. Call `verify_domain` until the domain is sendable, and `get_domain_health` if it is not.
3. Call `set_up_app_email` again with the same input (it asks for confirmation again). The sandbox sender moves to the verified domain, and `sender.mode` becomes `domain`.
4. `lifecycle.welcome` and `lifecycle.win-back` are marketing mail with an unsubscribe link. They stay on the sandbox until a verified marketing domain exists (`list_domains`).

Leave the old provider's configuration in place until a real send from the Brew domain has arrived.
