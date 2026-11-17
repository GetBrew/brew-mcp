# Privacy and terms

The plugins, extensions and configuration in this repository connect your AI client (Claude, Cursor, Grok Bot, Gemini CLI, VS Code, Codex and others) to Brew's hosted MCP server at https://brew.new/api/mcp.

- Privacy policy: https://docs.brew.new/legal/privacy-policy
- Terms of service: https://docs.brew.new/legal/terms-of-service
- Acceptable use: https://docs.brew.new/legal/acceptable-use-policy

Auth is OAuth 2.1. The user signs in with Brew and chooses a brand or organization. The issued token is bound to that choice (`brew:all`) and can be revoked in Brew under Settings → MCP.

This repository contains no secrets. Brew does not receive your AI client's conversation content except the tool calls the agent makes against the selected brand or organization.
