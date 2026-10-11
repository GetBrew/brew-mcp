# Brew for Gemini CLI

This extension connects Gemini CLI to Brew, the AI-native email platform for modern teams and AI agents, through the hosted MCP server at `https://brew.new/api/mcp`.

On first use, run `/mcp auth brew` and sign in with Brew. Choose one brand or all brands; every tool call is scoped to that choice.

## How to work with Brew

- Call `get_brew_capabilities` first. It returns the live tool catalog for this connection. Never guess tool names or ids.
- Design with `create_email` and `edit_email`; use `clone_email` for an exact copy and `import_email` for existing HTML, MJML, React Email JSX or a Figma frame.
- Test with `send_email` and `test: true` before any live send. `audit_email` checks a design before production.
- A live send needs a verified marketing domain (`list_domains`) and an audience (`list_audiences` or `create_audience`). Pass a unique `idempotency_key`.
- Anything that emails real people or deletes contact data returns a confirmation request first. Show it to the user, and only after they approve repeat the same call with `confirmed: true` and the request's `confirmation_id`.
- Automations: `save_trigger`, `save_automation`, `test_automation`, then `fire_trigger_event` from application code.
- Analytics: `get_email_analytics`. Domain health: `get_domain_health`.
- On an organization connection, brand tools take a `brand_id` from `list_brands`.

Docs: https://docs.brew.new/api-reference/mcp/overview
