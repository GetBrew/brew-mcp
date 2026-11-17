# Install Brew MCP

Brew is the AI-native email platform for modern teams and AI agents. Its MCP server is hosted, so there is nothing to build, clone or run locally. Connect Cline to the remote URL and sign in with OAuth.

- Server URL: `https://brew.new/api/mcp`
- Transport: Streamable HTTP
- Auth: OAuth 2.1 with Dynamic Client Registration and PKCE. No API key or client ID is needed.

## Steps

1. Open Cline, then **MCP Servers** and **Configure MCP Servers** to edit `cline_mcp_settings.json`.
2. Add the `brew` server under `mcpServers`:

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

3. Save. Cline opens the browser so the user can sign in with Brew and choose one brand or the whole organization. Ask the user to finish that sign-in; do not try to complete it for them.
4. Confirm the connection by calling the `get_brew_capabilities` tool. It lists the tools available to this connection.

## API key alternative

If the client cannot complete OAuth, create an API key in Brew under **Settings → API** and send it as a bearer header. A brand key connects to its one brand; an organization key reaches every brand.

```json
{
  "mcpServers": {
    "brew": {
      "url": "https://brew.new/api/mcp",
      "type": "streamableHttp",
      "headers": {
        "Authorization": "Bearer brew_..."
      },
      "disabled": false
    }
  }
}
```

Ask the user for the key. Never invent one, and never commit it to a repository.

## Safety

Anything that emails real people or deletes contact data returns a confirmation request on OAuth and organization connections. Show it to the user and repeat the call with `confirmed: true` and the request's `confirmation_id` only after they approve. Brand API-key connections do not pause, so get the user's approval first. Pass an `idempotency_key` when sending: a new key for each intended send, and the same key when retrying it.

Docs: https://docs.brew.new/api-reference/mcp/connect-your-client
