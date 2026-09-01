# Brew

Cursor plugin that connects agents to [Brew](https://brew.new), the AI-native email service provider, through Brew's official remote [Model Context Protocol](https://modelcontextprotocol.io/) server.

Generate on-brand emails, send and schedule campaigns, build automations, manage contacts and audiences, and read analytics from the signed-in Brew brand.

This listing is what makes Brew appear as a connector in Cursor and in Grok Bot.

## Install

1. Open **Cursor Settings → Plugins** (or Grok Bot connectors).
2. Search for **Brew**.
3. Click **Install**, then sign in with Brew and pick a brand.

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

Auth is OAuth 2.1 with Dynamic Client Registration and PKCE. Cursor registers itself and prompts for Brew sign-in when the plugin connects. You pick one brand; the issued token is scoped to that brand. There is no API key or client ID to configure.

Revoke the grant anytime in Brew under **Settings → MCP**.

## Before you connect

You need a Brew account with access to the brand the agent should use. Tool calls run scoped to that one brand (`brew:all`).

## What agents can do

| Category | Capabilities |
| --- | --- |
| Emails | Generate, edit, import (HTML / MJML / Figma), clone, version, and audit on-brand designs |
| Sending | Test sends, one-off campaigns, scheduled and gradual/warmup delivery, pause / resume / cancel |
| Audiences & contacts | Saved audience filters, contact CRUD, CSV import, email validation, custom fields |
| Automations | Triggered flows with waits, filters, and splits; test, publish, and run |
| Domains | Register, verify, and monitor sending-domain health (SPF / DKIM / DMARC) |
| Analytics | Brand overview, campaign and automation performance, per-recipient events |
| Brand & media | Brand identity, image search / generation, GIFs, template gallery |

The hosted runtime is the source of truth for tool names and schemas. Call `get_brew_capabilities` first to load the current catalog and guided workflows (`launch_email_campaign`, `build_segment_and_send`, `set_up_automation`, `analyze_campaign_performance`).

## Send safety

On OAuth connections, `send_email` pauses before a live send. Call it without `confirmed` first; Brew returns `confirmation_required` with the recipient count. Show that to the user, then call again with the same inputs plus `confirmed: true`. Always pass a unique `idempotency_key`.

Live sends require a verified custom domain on the brand.

## Docs

- Brew MCP overview: https://docs.brew.new/api-reference/mcp/overview
- Quickstart: https://docs.brew.new/api-reference/mcp/quickstart
- Connect your client: https://docs.brew.new/api-reference/mcp/connect-your-client
- Authentication & scoping: https://docs.brew.new/api-reference/mcp/authentication-and-scoping
- Server URL: https://brew.new/api/mcp

Logo is Brew's official mark (https://brew.new/logo.svg).

## License

MIT
