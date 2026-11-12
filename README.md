# HodgeGuard MCP (`hodgeguard-mcp`)

[![PyPI version](https://img.shields.io/pypi/v/hodgeguard-mcp.svg)](https://pypi.org/project/hodgeguard-mcp/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**HodgeGuard** is a **0.1ms, Zero-LLM Circuit-Breaker** for autonomous coding agents (OpenCode, Claude Code, Cursor, LangGraph). It prevents agents from getting trapped in non-convergent `edit -> test -> fail` loops, saving you money on runaway API token burn.

---

## 🚀 Installation

Install the package globally using `pipx` or `pip`:

```bash
pipx install hodgeguard-mcp
```

---

## ⚙️ Configuration

To use HodgeGuard with your Model Context Protocol (MCP) client, add it to your MCP configuration file (`~/.config/opencode/config.json` or `.opencode.json`):

```json
{
  "mcpServers": {
    "hodgeguard": {
      "command": "hodgeguard-mcp",
      "env": {
        "HODGEGUARD_API_URL": "[https://hodgeguard-brain.onrender.com](https://hodgeguard-brain.onrender.com)",
        "HODGEGUARD_API_KEY": "hg_free_demo123"
      }
    }
  }
}
```

### Support Development (Buy Me a Coffee)
HodgeGuard provisions a free tier locally automatically. To unlock unlimited Pro usage and support the developer, buy me a coffee!
☕ **[Buy Me a Coffee — HodgeGuard Pro](https://buymeacoffee.com/zshor)**
