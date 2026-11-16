# HodgeGuard MCP (`hodgeguard-mcp`)

**HodgeGuard** is a Zero-LLM circuit-breaker MCP client for autonomous coding agents (OpenCode, Claude Code, Cursor, LangGraph) that helps detect non-convergent `edit -> test -> fail` loops while hashing step/state identifiers locally before calling the cloud service.

## Installation

Install using `pipx` or `pip`:

```bash
pipx install hodgeguard-mcp
```

## Configuration

Add `hodgeguard-mcp` to your MCP configuration file:

```json
{
  "mcpServers": {
    "hodgeguard": {
      "command": "hodgeguard-mcp",
      "env": {
        "HODGEGUARD_API_URL": "https://hodgeguard-cloud-brain.onrender.com"
      }
    }
  }
}
```

If `HODGEGUARD_API_KEY` is not set, the client automatically generates a local anonymous key (`hg_anon_...`) for the free trial quota. Set `HODGEGUARD_API_KEY` when using a Pro license key.

## HodgeGuard Pro License

Get HodgeGuard Pro License Key: https://buymeacoffee.com/zshor/e/597895
