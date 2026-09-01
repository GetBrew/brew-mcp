---
name: brew
description: Use when working with the Brew email platform — generating and sending campaigns, scheduling, automations, audiences/segments, analytics, or connecting the Brew MCP. Always use this skill when the user mentions Brew, even for simple tasks like "send a campaign".
---

# Brew

Brew is the AI-native email service provider. Agents talk to it over the hosted MCP at `https://brew.new/api/mcp`. The connection is OAuth 2.1: the user signs in with Brew and picks one brand. Every tool call is scoped to that brand.

Start with `get_brew_capabilities`. It returns the live tool catalog, credit costs, and guided workflows.

## Create then send

1. `create_email_design` from a prompt. Iterate with `edit_email_with_ai`.
2. `send_email` with `test: true` to QA.
3. `list_domains` (need a verified sender) and `list_audiences` (or `create_audience`).
4. For a live send, call `send_email` with `audienceId`, `domainId`, and a unique `idempotency_key`, but **omit `confirmed`**.
5. Brew returns `confirmation_required` plus the recipient count. Show that to the user. Only after they approve, call again with the same inputs and `confirmed: true`.
6. `get_send_analytics` / `get_campaign_analytics` after it goes out.

Never send to a live audience without that confirmation step. Live sends require a verified custom domain.

## Other workflows

- **Segment and send:** `search_contacts` → `create_audience` with filters → design → send.
- **Automation:** `create_trigger` → design emails → `create_automation` → `test_automation` → `update_automation { published: true }`.
- **Analyze:** `get_send_analytics` → `get_campaign_analytics` → `get_event_analytics`. Summarize wins, deliverability issues, and the next experiment.

Docs: https://docs.brew.new/api-reference/mcp/overview
