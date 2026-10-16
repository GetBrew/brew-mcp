# Brew MCP

Brew MCP server, agent plugins and skills for Claude, Cursor, Codex, Gemini, VS Code and more.

[Brew](https://brew.new) is the AI-native email platform for modern teams and AI agents. This repository is the single public home of Brew's official remote [Model Context Protocol](https://modelcontextprotocol.io/) integration: one hosted server, three skills, and a ready-made plugin or extension for each client.

Design on-brand emails, send and schedule campaigns, build automations, manage contacts and audiences, check sending domains, and read analytics within the Brew brand or organization you connect, all from your agent.

```
https://brew.new/api/mcp
```

Auth is OAuth 2.1 with Dynamic Client Registration and PKCE. Your client registers itself and opens Brew to sign in, and you choose one brand or your whole organization. There is no API key or client ID to configure, and you can revoke the grant anytime in Brew under **Settings → MCP**.

## Install

Pick your client. Every option below connects to the same server.

### Claude

**Claude.ai and Claude Desktop (connector).** Open **Settings → Connectors**, choose **Add custom connector**, paste `https://brew.new/api/mcp`, then **Connect** and sign in with Brew.

**Claude Code (plugin).** The plugin adds the MCP server and the Brew skills:

```
/plugin marketplace add GetBrew/brew-mcp
/plugin install brew@brew-mcp
```

Or in one step on Claude Code 2.1.275 or later:

```
/plugin install brew --marketplace GetBrew/brew-mcp
```

Prefer only the MCP server? Run `claude mcp add --transport http brew https://brew.new/api/mcp`.

### Cursor

[<img src="https://cursor.com/deeplink/mcp-install-dark.svg" alt="Add Brew to Cursor" height="32">](https://cursor.com/en/install-mcp?name=brew&config=eyJ1cmwiOiJodHRwczovL2JyZXcubmV3L2FwaS9tY3AifQ)

Install in Cursor with one click, or add the server by hand: put this in `~/.cursor/mcp.json` (or `.cursor/mcp.json` for one project):

```json
{
  "mcpServers": {
    "brew": {
      "url": "https://brew.new/api/mcp"
    }
  }
}
```

Cursor opens your browser to sign in with Brew.

### VS Code

[![Install in VS Code](https://img.shields.io/badge/VS_Code-Install_Server-0098FF?style=flat-square&logo=visualstudiocode&logoColor=white)](https://insiders.vscode.dev/redirect/mcp/install?name=brew&config=%7B%22type%22%3A%22http%22%2C%22url%22%3A%22https%3A%2F%2Fbrew.new%2Fapi%2Fmcp%22%7D)
[![Install in VS Code Insiders](https://img.shields.io/badge/VS_Code_Insiders-Install_Server-24bfa5?style=flat-square&logo=visualstudiocode&logoColor=white)](https://insiders.vscode.dev/redirect/mcp/install?name=brew&config=%7B%22type%22%3A%22http%22%2C%22url%22%3A%22https%3A%2F%2Fbrew.new%2Fapi%2Fmcp%22%7D&quality=insiders)

Or create `.vscode/mcp.json` (requires GitHub Copilot agent mode):

```json
{
  "servers": {
    "brew": {
      "type": "http",
      "url": "https://brew.new/api/mcp"
    }
  }
}
```

Click **Start** in the `mcp.json` gutter and sign in with Brew when prompted.

### Codex and ChatGPT

**Codex.** Add this to `~/.codex/config.toml`, then run `codex mcp login brew` and sign in with Brew:

```toml
[mcp_servers.brew]
url = "https://brew.new/api/mcp"
```

**ChatGPT.** Enable Developer mode under **Settings → Security and login**. Open **Settings → Plugins**, select **+**, create **Brew** with the server URL `https://brew.new/api/mcp` and OAuth authentication, then enable **@Brew** in a new chat.

### Gemini CLI

```
gemini extensions install https://github.com/GetBrew/brew-mcp
```

Then run `/mcp auth brew` in Gemini CLI and sign in with Brew. The extension also loads [`GEMINI.md`](GEMINI.md) so Gemini knows how to work with Brew safely.

### Windsurf and Devin

**Windsurf.** Open **Settings → Cascade → MCP Servers → View raw config** and add:

```json
{
  "mcpServers": {
    "brew": {
      "serverUrl": "https://brew.new/api/mcp"
    }
  }
}
```

Click **Refresh** in the MCP panel and sign in with Brew when prompted.

**Devin.** Open **Customize → MCPs**, choose **Add MCP** then **Add custom MCP**, pick the **HTTP** transport, paste `https://brew.new/api/mcp`, set authentication to **OAuth**, save, and click **Connect**.

### Cline

Add the server under **MCP Servers → Configure MCP Servers**. The step-by-step guide Cline follows is in [`llms-install.md`](llms-install.md).

```json
{
  "mcpServers": {
    "brew": {
      "url": "https://brew.new/api/mcp",
      "type": "streamableHttp",
      "disabled": false
    }
  }
}
```

### Goose

Run `goose configure`, choose **Add Extension → Remote Extension (Streamable HTTP)**, name it `brew`, paste `https://brew.new/api/mcp`, then sign in with Brew.

### Any other client

Add Brew to your client's MCP server map with the URL:

```json
{
  "mcpServers": {
    "brew": {
      "url": "https://brew.new/api/mcp"
    }
  }
}
```

If your client cannot complete the OAuth handshake, create an API key in Brew under **Settings → API** and send it as `Authorization: Bearer brew_...` instead.

## Skills

Three skills teach an agent how to work with Brew:

| Skill | Use it to |
| --- | --- |
| `brew` | Design, test, confirm, send and measure: the safe order of operations for emails, campaigns, automations, audiences and domains |
| `brew-add-email-to-app` | Add auth and lifecycle email to an app: set up the keyed emails, wire them into Better Auth, Auth.js, Supabase, Clerk, Firebase or custom auth with `@brew.new/sdk`, and verify with a sandbox send |
| `brew-migrate-from-resend` | Move an app from Resend: inventory the sends, import React Email files and Resend Templates, set up each email by key, swap the code, move contacts and cut over |

Install them into Claude Code, Cursor, Codex and many other agents with the open [skills CLI](https://skills.sh):

```
npx skills add GetBrew/brew-mcp
```

Working from a terminal or CI instead? The Brew CLI has its own skill: `npx skills add GetBrew/brew-cli`.

## What agents can do

| Category | Capabilities |
| --- | --- |
| Emails | Design from a prompt, edit, import (HTML, MJML, React Email, Figma), clone, version, and audit on-brand emails |
| Sending | Test sends, one-off campaigns, scheduled and gradual delivery, pause, resume and cancel |
| Audiences and contacts | Saved audience filters, contact updates, CSV updates, email validation, custom fields |
| Automations | Triggered flows with waits, filters and splits; test, publish, run, and fire events from app code |
| App emails | Auth and lifecycle emails set up by trigger key, sent from code with `brew.send`, with a team-only sandbox until a domain verifies; React Email files and Resend templates imported as designs |
| Domains | Register, verify and monitor sending-domain health (SPF, DKIM, DMARC) and inbox placement |
| Analytics | Overview, per-send and per-recipient engagement, automation performance, insights |
| Brand and templates | Brand identity, the brand image library, and the public template and sequence gallery |

The hosted runtime is the source of truth for tool names and schemas. Call `get_brew_capabilities` first to load the current catalog and the guided workflows (`launch_email_campaign`, `build_segment_and_send`, `set_up_automation`, `wire_trigger_from_code`, `analyze_campaign_performance`, `personalize_with_crm`, `improve_deliverability`, `configure_brand`, `run_audience_automation` and, on organization connections, `onboard_brand`).

## Send safety

On OAuth and organization connections, anything that emails real people or deletes contact data pauses first. Call the tool, such as `send_email`, and Brew returns a confirmation request with the recipient count. Show it to the user. After they approve, call again with the same inputs plus `confirmed: true` and the request's `confirmation_id`. Use a new `idempotency_key` for each intended operation, and reuse the same `idempotency_key` on retries so a retry never sends twice. Confirmation requirements also cover other sends and destructive operations; see [Authentication and scoping](https://docs.brew.new/api-reference/mcp/authentication-and-scoping). Brand API-key connections do not pause, so get the user's approval before the first live call.

One-off live sends require a verified marketing-purpose domain and existing opted-in contacts. Event-triggered transactional mail follows its automation and domain-purpose contract.

## Before you connect

You need a Brew account with access to the brand the agent should use. The public OAuth scope is `brew:all`. A brand connection acts on its bound brand. An organization connection requires `brand_id` for brand-scoped tools; call `list_brands` and clarify the target when necessary.

## Docs

- Brew MCP overview: https://docs.brew.new/api-reference/mcp/overview
- Quickstart: https://docs.brew.new/api-reference/mcp/quickstart
- Connect your client: https://docs.brew.new/api-reference/mcp/connect-your-client
- Authentication and scoping: https://docs.brew.new/api-reference/mcp/authentication-and-scoping
- Server URL: https://brew.new/api/mcp
- Privacy and terms: [`PRIVACY.md`](PRIVACY.md)

Logo is Brew's official mark (https://brew.new/logo.svg).

## For maintainers

One version number moves across the plugin manifests (`.claude-plugin/plugin.json`, `.cursor-plugin/plugin.json`, `.grok-plugin/plugin.json`, `plugin.json`, `gemini-extension.json`) and `CHANGELOG.md`. `server.json` versions separately: it mirrors the registry entry brew.new serves at `/.well-known/mcp/server.json`, so its version follows `MCP_SERVER_JSON_VERSION` in the Brew app and the registry refuses a version it already has. Every pull request runs `python3 scripts/validate.py`, and a `v*` tag publishes a GitHub release.

| Path | Used by |
| --- | --- |
| `.claude-plugin/`, `.mcp.json` | Claude Code plugin and marketplace |
| `.cursor-plugin/`, `mcp.json`, `rules/` | Cursor plugin (also Grok Bot via `.grok-plugin/`) |
| `plugin.json` | agent-plugins.org manifest |
| `gemini-extension.json`, `GEMINI.md` | Gemini CLI extension |
| `llms-install.md` | Cline |
| `server.json` | Official MCP Registry entry (`new.brew/mcp`) |
| `glama.json` | Glama |
| `directories/docker/` | Files for a `servers/brew` pull request to docker/mcp-registry |
| `skills/` | Every client, and `npx skills add` |

## License

MIT
