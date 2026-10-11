# Changelog

## 1.1.0 - 2026-10-11

- Repository renamed from `cursor-plugin` to `brew-mcp`: one public home for every agent client
- New Claude Code plugin and marketplace (`/plugin marketplace add GetBrew/brew-mcp`)
- New Gemini CLI extension (`gemini extensions install https://github.com/GetBrew/brew-mcp`)
- New Cursor rule, Cline install guide, Glama listing file, and MCP Registry `server.json`
- One-click install links for Cursor and VS Code in the README
- Docker MCP Registry entry prepared under `directories/docker/`
- Skill rewritten for the current tool names and the confirmation flow
- Copy now describes Brew as the AI-native email platform; image generation claims removed
- Validation and release workflows; all manifest versions move together

## 1.0.0 - 2026-08-31

- Initial Cursor Marketplace plugin for the hosted Brew MCP server
- OAuth 2.1 with Dynamic Client Registration (no API key to paste)
- Remote Streamable HTTP endpoint at https://brew.new/api/mcp
