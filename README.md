# Brew

Cursor plugin that connects agents to [Brew](https://brew.new), the AI-native email platform, through Brew's official remote [Model Context Protocol](https://modelcontextprotocol.io/) server.

Generate on-brand emails, send and schedule emails, build automations, manage contacts and audiences, and read analytics within the selected Brew brand or organization.

This listing is what makes Brew appear as a connector in Cursor and in Grok Bot.

## Install

1. Open **Cursor Settings → Plugins** (or Grok Bot connectors).
2. Search for **Brew**.
3. Click **Install**, then sign in with Brew and choose a brand or organization.

Or run `/add-plugin brew` in chat.

## MCP

```json
{
  "mcpServers": {
    "brew": {
      "type": "streamable-http",
      "url": "https://brew.new/api/mcp"
    }
  }
}
```

Auth is OAuth 2.1 with Dynamic Client Registration and PKCE. Cursor registers itself and prompts for Brew sign-in when the plugin connects. You choose one brand or your organization; the issued token is scoped to that choice. There is no API key or client ID to configure.

Revoke the grant anytime in Brew under **Settings → MCP**.

## Before you connect

You need a Brew account with access to the brand the agent should use. The public OAuth scope is `brew:all`. A brand connection acts on its bound brand. An organization connection requires `brand_id` for brand-scoped tools; call `list_brands` and clarify the target when necessary.

## What agents can do

| Category | Capabilities |
| --- | --- |
| Emails | Generate, edit, import (HTML / MJML / Figma), clone, version, and audit on-brand designs |
| Sending | Test sends, one-off campaigns, scheduled and gradual/warmup delivery, pause / resume / cancel |
| Audiences & contacts | Saved audience filters, search/update/delete existing contacts, CSV updates, email validation, custom fields |
| Automations | Triggered flows with waits, filters, and splits; test, publish, and run |
| Domains | Register, verify, and monitor sending-domain health (SPF / DKIM / DMARC) |
| Analytics | Brand overview, campaign and automation performance, per-recipient events |
| Brand & media | Brand identity, image search / generation, GIFs, template gallery |

The hosted runtime is the source of truth for tool names and schemas. Call `get_brew_capabilities` first to load the current catalog and guided workflows (`launch_email_campaign`, `build_segment_and_send`, `set_up_automation`, `analyze_campaign_performance`).

## Send safety

On OAuth connections, `send_email` pauses before a live send. Call it without `confirmed` first; Brew returns `confirmation_required` with the recipient count. Show that to the user, obtain approval, then call again with the same inputs plus `confirmed: true` and the returned `confirmation_id`. Use a new `idempotency_key` per intended operation and reuse it for retries. Confirmation requirements also cover other sends and destructive operations; see [Authentication & scoping](https://docs.brew.new/api-reference/mcp/authentication-and-scoping).

One-off live sends require a verified marketing-purpose domain and existing opted-in contacts. Event-triggered transactional mail follows its automation and domain-purpose contract.

## Docs

- Brew MCP overview: https://docs.brew.new/api-reference/mcp/overview
- Quickstart: https://docs.brew.new/api-reference/mcp/quickstart
- Connect your client: https://docs.brew.new/api-reference/mcp/connect-your-client
- Authentication & scoping: https://docs.brew.new/api-reference/mcp/authentication-and-scoping
- Server URL: https://brew.new/api/mcp

Logo is Brew's official mark (https://brew.new/logo.svg).

## License

MIT
