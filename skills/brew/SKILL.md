---
name: brew
description: Use when working with Brew, the AI-native email platform, to design and send emails and campaigns, build automations, manage audiences and contacts, check sending domains, or read analytics through the Brew MCP. Always use this skill when the user mentions Brew, even for simple tasks like "send a campaign".
---

# Brew

Brew is the AI-native email platform for modern teams and AI agents. Agents talk to it over the hosted MCP server at `https://brew.new/api/mcp`. The connection is OAuth 2.1: the user signs in with Brew and chooses one brand or all brands. A brand connection works on that brand. An organization connection works across brands, so brand tools take a `brand_id` from `list_brands`.

Start with `get_brew_capabilities`. It returns the live tool catalog for this connection, credit costs and guided workflows. The hosted runtime is the source of truth for tool names and schemas; never guess a name from memory.

## Ground rules

- Never invent ids. `emailId`, `audienceId`, `domainId`, `automationId`, `triggerEventId` and `sendId` come from a `list_*` or `get_*` result.
- Treat anything that emails real people, or deletes contact data, as needing the user's go-ahead first.
- Pass a unique `idempotency_key` on sends and trigger fires so a retry never acts twice.
- Check `get_usage` before a metered step if credits might be short. Designing, editing and auditing emails use credits.
- Results include an Open-in-Brew link. Share it so the user can open the design or automation in the app.

## Design, then send

1. `get_brand` confirms the brand is ready (voice, colors, logos). `create_email` makes an on-brand design from a prompt; use `clone_email` for an exact copy and `import_email` for existing HTML, MJML, React Email JSX or a Figma frame.
2. Iterate with `edit_email`. Each edit is a new version; `restore_email_version` reverts. `get_email` shows a design or polls a generation.
3. QA with `send_email` and `test: true`. `audit_email` checks a design before a production send, and `test_email_rendering` shows it in specific inbox clients.
4. Pick who gets it: `list_audiences` (or `create_audience` from filters) and `list_domains` for a verified marketing domain.
5. For the live send, call `send_email` with `emailId`, `subject`, `audienceId` (or up to 50 existing subscribed contacts in `to`), `domainId` and an `idempotency_key`.
6. On OAuth and organization connections, that first call returns a confirmation request with the recipient count. Show it to the user. Only after they approve, repeat the same call with `confirmed: true` and the request's `confirmation_id`.
7. Read results with `get_email_analytics` (`report.kind` of `overview`, `sends` or `events`).

Live sends need a verified sending domain. If none exists, `create_domain` returns the DNS records to add and `verify_domain` rechecks them. `get_domain_health` diagnoses authentication and reputation; `create_inbox_placement_test` measures where mail lands.

## Audiences and contacts

- `search_contacts` finds contacts and, with `count: true`, totals and breakdowns. `list_contact_fields` shows what can be filtered on.
- An audience is a saved filter, matched live at send time. `create_audience`, `update_audience`, and `list_audiences` with `include: ["count"]` for its current size.
- The MCP updates existing contacts (`update_contact`, `update_contacts_csv`, `create_contact_field`) and validates deliverability (`validate_contacts`). New contacts join through signup forms, integrations, imports in the Brew app, and trigger fires.
- `delete_contacts` is permanent. On OAuth and organization connections it returns the same confirmation request as a send.

## Automations and app events

1. `save_trigger` defines the event, keeping a required top-level `email` string in its payload schema. `infer_payload_contract` drafts the schema from a real example payload; `set_trigger_contract` stores it.
2. Design the emails, then `save_automation` builds the graph (send, wait, filter, split steps wired to the trigger). Choose the sending domain by its purpose: `transactional` for receipts and account notices, `marketing` for anything promotional.
3. `test_automation` exercises the flow before it goes live. `save_automation` with `published: true` activates it and, on OAuth connections, asks for confirmation.
4. `check_trigger` confirms a trigger can fire now. `fire_trigger_event` starts the published automations from an app event payload. `run_automation` launches a manual-audience automation instead.
5. Monitor with `list_trigger_events`, `list_automation_runs` and `get_automation` with analytics.

To wire the fire call into application code, `get_trigger_contract` returns a typed payload (`format: "ts"`) or a full wiring brief (`format: "skill"`).

## Guided workflows

The server also offers prompts: `launch_email_campaign`, `build_segment_and_send`, `set_up_automation`, `wire_trigger_from_code`, `analyze_campaign_performance`, `personalize_with_crm`, `improve_deliverability` and `report_mcp_issue`.

## When something goes wrong

`report_tool_issue` files a technical diagnostic when the user asks to report a problem. `submit_feedback` sends the user's own message to the Brew team.

Docs: https://docs.brew.new/api-reference/mcp/overview
