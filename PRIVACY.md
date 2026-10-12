# Privacy and terms

This plugin connects Cursor / Grok Bot to Brew's hosted MCP server at https://brew.new/api/mcp.

- Privacy policy: https://docs.brew.new/legal/privacy-policy
- Terms of service: https://docs.brew.new/legal/terms-of-service
- Acceptable use: https://docs.brew.new/legal/acceptable-use-policy

Auth is OAuth 2.1. The user signs in with Brew and chooses a brand or organization. The issued token is bound to that choice (`brew:all`) and can be revoked in Brew under Settings → MCP.

The plugin repository contains no secrets. Brew does not receive Cursor or Grok conversation content except the tool calls the agent makes against the selected brand or organization.
