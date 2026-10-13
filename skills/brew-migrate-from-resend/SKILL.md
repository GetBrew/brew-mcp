---
name: brew-migrate-from-resend
description: "Use when moving an app's email from Resend to Brew. Inventories the Resend call sites, React Email files and Resend Templates, plans the sending domain, imports the designs with the Brew MCP, sets up each email by trigger key, swaps the code with @brew.new/sdk, moves contacts and unsubscribes, tests in the sandbox and cuts over without losing mail."
---

# Migrate from Resend to Brew

Resend sends a message per API call. Brew sends app email by trigger key: the app calls `brew.send('<key>', payload)`, and a published automation behind the key holds the design, the subject and the sender. A migration therefore maps each Resend send to a key, imports its design, and replaces the call. Auth library wiring (Better Auth, Auth.js, Supabase) is covered by the `brew-add-email-to-app` skill; this skill covers everything around it.

Rules for the whole migration:

- Change nothing on the Resend side until the end. Its API key, domain records, templates and webhooks stay until a real send from Brew has arrived, and the user removes them, not the agent.
- The Resend key never goes to Brew or into chat. Read it from the local environment only when a template has to be fetched.
- The Brew API key is server-only: `BREW_API_KEY`, never a `NEXT_PUBLIC_`, `VITE_` or `PUBLIC_` variable, never committed.

## 1. Inventory (read-only)

Search the code for `from 'resend'`, `new Resend(`, `RESEND_API_KEY`, `emails.send`, `batch.send`, Resend webhook routes, and `contacts`, `audiences` or `broadcasts` calls. For every send record:

- what triggers it (an auth hook, a billing event, a user action) and who receives it
- what it sends: `react` or `html`, `text`, or `template: { id, variables }`
- the fields Brew does not carry over: `attachments`, `cc`, `bcc`, `headers`, `scheduled_at`, `replyTo`, `tags`, several recipients in `to`

Find the React Email files (an `emails/` directory, `@react-email/components`) and the Resend Templates in use. Fetch each template's HTML and `variables` from the Resend dashboard or API.

Give each send a key: an auth or lifecycle email takes the matching kit key (`auth.verify-email`, `auth.password-reset`, `auth.magic-link`, `auth.otp`, `lifecycle.welcome`, `lifecycle.payment-failed` and the rest); anything else gets a key of its own such as `order.shipped`. Show the user the table of send, source and key before changing anything.

## 2. Plan the sending domain

- `list_domains` shows what Brew already has.
- Look up `resend._domainkey.<domain>` (for example `dig +short TXT resend._domainkey.acme.com`). If it exists, Resend signs that domain's mail with that selector, and Brew's DKIM record uses the same name, so adding Brew's record would break Resend's mail. Add a subdomain to Brew instead, such as `mail.acme.com`. When a domain is added, Brew warns with `DKIM_SELECTOR_IN_USE` and suggests subdomains.
- Auth, billing and other app email needs a domain with the purpose **Transactional**. The user adds it in the Brew app under **Domains** (`create_domain` over MCP adds marketing domains) and publishes the DNS records. Until it verifies, Brew sends from the team-only sandbox: organization members only, 50 sends per organization per UTC day.

## 3. Import the designs

Call `import_email` with `source: { kind: 'content', format, content }`. Each import makes an editable draft in Brew and reports how it converted, so it is the way to see the conversion before a key exists.

- **React Email** (`format: 'jsx'`): add `props: 'merge_tags'`. The root component's props become `{{ trigger.<name> }}` merge tags, and defaults and `??` literals become fallbacks. Without it, props fold into their `PreviewProps` value. Only components defined in the same file are imported, so inline any shared component first.
- **Resend Templates** (`format: 'html'`): add `placeholders: 'resend'`. `{{{NAME}}}` becomes `{{ trigger.NAME }}` and `{{{NAME|fallback}}}` keeps its fallback; `FIRST_NAME`, `LAST_NAME` and `EMAIL` read the contact. Pass the template's own fallbacks as `variables: [{ key, fallbackValue }]`.
- Set `title` and `subjectLine` so the design is easy to find.

Read the notices in the result and show them to the user:

| Notice | Meaning and next step |
| --- | --- |
| `escaping_changed` | Resend printed a placeholder as raw HTML. Brew escapes merge values; end a tag with `\| raw` only for HTML the app controls. |
| `dynamic_prop_folded` | A prop sits where a merge tag cannot go (arithmetic, an attribute, a method call), so it kept its preview or default value. Compute it in the app and send it as a payload field instead. |
| `placeholder_unmapped` | A placeholder has no Brew equivalent and was left as written. Rename it or replace it with a payload field. |
| `dynamic_control_flow_unsupported` | A loop or condition Liquid cannot express there; the preview value decided it. Restructure the section. |

The result's `variables` lists every merge variable the design reads: `trigger.*` comes from the payload the code sends, `contact.*` from the recipient. That list is the payload for step 5. Have the user open the design in Brew (the result links to it) before going on.

## 4. Set up each key

Call `set_up_app_email` with `setup: { kind: 'one', triggerKey, source: { format, content }, subject, from: { localPart, name } }`, once per key.

- `source` is the markup with `{{ trigger.<field> }}` tags already in place, so pass the converted form from step 3; the setup does not take the import options, and a React Email file with props would fold them. The fields the tags read become the key's payload contract. Pass `payloadSchema` to mark secret values (`confirmationUrl`, `otp`) with `pii: 'high'`.
- `subject` and `from` replace the per-call `subject` and `from` of Resend. A subject can use merge tags. Reply-to is a domain default (`update_domain`).
- A stock email with no design of its own (a verify email, a reset, a welcome) can take Brew's themed starter: `setup: { kind: 'one', triggerKey: 'auth.password-reset' }`. Keep the user's own design unless they ask for the starter.
- The call publishes an automation, so on OAuth and organization connections it returns a confirmation request first. Show it, and after approval repeat the same call with `confirmed: true` and the request's `confirmation_id`. A re-run changes only what differs.
- The setup builds its own design from `source`, so the draft from step 3 is a spare. Offer to delete it with `delete_email`, which is permanent, so ask first.

## 5. Swap the code

Install `@brew.new/sdk` (12.3.0 or later). Change one call site at a time, in separate commits, so each can be reverted.

Direct (the end state):

```ts
// Before
await resend.emails.send({ from: 'Acme <hi@acme.dev>', to: user.email, subject: 'Reset your password', react: <ResetPassword url={url} /> })

// After
await brew.send('auth.password-reset', { email: user.email, confirmationUrl: url })
```

Through the adapter, for call sites that already send a Resend template. Change the import and the key; the call stays as it is:

```ts
import { Resend } from '@brew.new/sdk/resend'

const resend = new Resend(process.env.BREW_API_KEY, {
  templates: { 'password-reset': 'auth.password-reset' }, // Resend template id to Brew key
})
await resend.emails.send({ to: user.email, template: { id: 'password-reset', variables: { confirmationUrl: url } } })
```

The adapter answers `{ data, error }` and never throws. It ignores `from`, `subject`, `replyTo` and `tags` with one warning, because those live in Brew now. A send with `html`, `react` or `text` and no template returns `brew_template_required`; `cc`, `bcc`, `attachments`, `headers` and `scheduledAt` return `brew_unsupported_field`; several recipients need `batch.send`.

Calls inside an auth library's hooks (Better Auth, Auth.js, Supabase) use the adapters in the `brew-add-email-to-app` skill instead. Await each send or hand it to `waitUntil` or `after` on serverless, and pass `{ idempotencyKey }` when the call can repeat. Compare the payload with the `variables` from step 3, or with `get_trigger_contract` and `format: "ts"`.

## 6. Move contacts and unsubscribes (marketing only)

An app that only sends transactional mail needs none of this: a send creates the recipient as a contact.

1. Unsubscribes and suppressions first. Export the unsubscribed contacts and the complaint and bounce suppressions from Resend, then call `import_domain_unsubscribes` with the CSV text and a marketing `domainId` from `list_domains` (a transactional domain keeps no list). An address Brew does not know is created already unsubscribed everywhere. Brew never re-subscribes an opt-out, so later imports cannot undo this.
2. Then the subscribed contacts, only those the user can show consent for. The Brew MCP updates contacts but does not create them. Create them with the contact import in the Brew app, or with `brew.contacts.importCsv({ csv, consent: { source: 'import' } })`.
3. `update_contacts_csv` fills fields and subscription state on contacts that already exist; a row for an unknown address is refused (`CONTACT_NOT_FOUND`).

Resend broadcasts and Resend automations are not migrated. Rebuild them in Brew with the user (`create_email`, `save_automation`).

## 7. Test in the sandbox

Ask for the address the user signs in to Brew with. For each key call `fire_trigger_event` with `triggerKey`, a realistic `payload` and an `idempotency_key`; on OAuth and organization connections it asks for confirmation first. Compare the arrived email with the old Resend email: links, fallbacks, escaping, subject. If nothing arrives, read `list_trigger_events` and `list_automation_runs`. Never test against a customer's address.

## 8. Cut over

1. Verify the domain: `verify_domain` until it is sendable, then run `set_up_app_email` again for each key so the sender moves from the sandbox to the domain. `lifecycle.welcome` and `lifecycle.win-back` are marketing mail and also need a verified marketing domain.
2. Switch the lifecycle emails first (welcome, trial ending, payment failed). Deploy, send a real one, and read `get_email_analytics` or `list_trigger_events` to confirm delivery.
3. Switch the auth emails last, since a failure blocks sign-in. Test each flow with a team account before and after deploy.
4. Keep Resend configured until every call site sends through Brew and a real message from the Brew domain has landed. Then hand the user the list of Resend resources they can remove: the package, `RESEND_API_KEY`, templates, webhooks and DNS records. Only once nothing sends through Resend can its `resend._domainkey` record go and the root domain be added to Brew, if the user wants the sender back on it.

## What does not carry over

Brew sends app email from a published automation, so these Resend features have no per-send equivalent:

- attachments: link to a hosted file instead
- `cc` and `bcc`: send one email per recipient
- per-send headers and a per-send `from`, `subject` or `reply-to`: set once on the key
- `scheduled_at`: a wait step in the key's automation covers a delay (`save_automation`)
- raw `html` or `text` per send: import the design and send it by key
- inbound email and Resend webhooks: not migrated; read delivery with `get_email_analytics`

List the call sites that use these and keep them on Resend, or redesign them with the user.
