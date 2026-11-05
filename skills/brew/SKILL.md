---
name: brew
description: Use when working with the Brew email platform — generating and sending emails, scheduling, automations, audiences/segments, analytics, or connecting the Brew MCP. Always use this skill when the user mentions Brew, even for simple tasks like "send a campaign".
---

# Brew

Brew is the AI-native email platform. Agents talk to it over the hosted MCP at `https://brew.new/api/mcp`. The connection is OAuth 2.1: the user signs in with Brew and chooses a brand or organization. A brand connection acts on its bound brand; an organization connection requires `brand_id` for every brand-scoped tool. Call `get_brew_capabilities` to discover the connection scope and `list_brands` before choosing a brand.

Start with `get_brew_capabilities`. It returns the live tool catalog, credit costs, and guided workflows.

## Create then send

1. `create_email` from a prompt. Iterate with `edit_email`.
2. `send_email` with the `emailId`, a `subject`, `test: true` and one `to` address to QA. A test reaches only a teammate with access to the brand, an address on a verified sending domain of the brand, or, on an OAuth connection (not an API key), the signed-in person's own address or one on their company domain; anyone else is refused with `TEST_RECIPIENT_NOT_ALLOWED`. On OAuth and organization connections a test to anyone but the signed-in person first returns `confirmation_required`, handled as in step 5.
3. `list_domains` (need a verified sender) and `list_audiences` (or `create_audience`).
4. For a live send, call `send_email` with the `emailId`, a `subject` (the design's `subjectLine` from `get_email` reuses it), `audienceId`, `domainId`, and a unique `idempotency_key`, but **omit `confirmed`**.
5. Brew returns `confirmation_required` plus the recipient count. Show that to the user. Only after they approve, call again with the same inputs, `confirmed: true`, and the returned `confirmation_id`.
6. `get_email_analytics` with `report: { kind: "sends" }` after it goes out.

Never send to a live audience without that confirmation step. Live sends require a verified marketing domain and opted-in recipients. Transactional mail uses an event-triggered automation and a transactional-purpose domain; follow the current hosted contract.

## Other workflows

- **Segment and send:** `search_contacts` → `create_audience` with filters → design → send.
- **Automation:** `save_trigger` → design emails → `save_automation` → `test_automation` → `save_automation { published: true }`. Publishing can require confirmation: show the returned request and repeat only after approval with `confirmed: true` and its `confirmation_id`.
- **Analyze:** `get_email_analytics` with the `overview`, `sends`, and `events` report kinds. Summarize wins, deliverability issues, and the next experiment.

Docs: https://docs.brew.new/api-reference/mcp/overview
