# HodgeGuard MCP (`hodgeguard-mcp`)

A lightweight Model Context Protocol (MCP) client over `stdio` JSON-RPC that checks AI coding agent steps against the HodgeGuard Cloud Brain to detect repetitive command/livelock loops and enforce step quotas.

## How It Works

`hodgeguard-mcp` acts as a local MCP client/proxy (`hodgeguard_mcp/client.py`) between your AI coding agent (such as OpenCode, Claude Code, or Cursor) and the HodgeGuard Cloud Brain (`https://hodgeguard-cloud-brain.onrender.com`):

1. **Local SHA-256 Fingerprinting**: Before calling the Cloud Brain, `client.py` hashes tool/command targets (`vertex_hash`) and command/state fingerprints (`state_hash`) locally using SHA-256 so raw command payloads remain private on your machine.
2. **Manifold Livelock Check (`/v1/step`)**: Every step reports hashes and progress state to the Cloud Brain, which tracks trajectory and edge weights (`curl_energy`) to spot repetitive loops, alternating retry cycles (A-B-A-B), and embedded shell loops (`for`, `while`, `until`, or repeated command chains in `hg_bash`).
3. **Hard Halt on Livelock**: When the Cloud Brain returns `halted: true`, `hg_bash` and `hodgeguard_check_step` block execution and return a halt message (`isError: true`) so the agent stops burning tokens on a dead-end loop.
4. **Session Reset (`/v1/reset`)**: Clears the active manifold session state for your key when starting a fresh task.

### Exposed Tools

* `hg_bash`: Executes a shell command after checking the command and loop heuristics with `/v1/step`. *(For strict enforcement, disable or avoid falling back to raw/native shell tools when `hg_bash` is available.)*
* `hodgeguard_check_step`: Manually checks a `(tool_name, target, state_fingerprint, verified_progress)` step against `/v1/step`.
* `hodgeguard_reset`: Resets the current Hodge manifold session via `/v1/reset`.

---

## Installation with `pipx`

### From Local Clone or Git

```bash
git clone [https://github.com/zshor/hodgeguard-mcp.git](https://github.com/zshor/hodgeguard-mcp.git)
cd hodgeguard-mcp
pipx install --force .
```

### Environment Variables

* `HODGEGUARD_API_KEY` *(optional)*: Your Pro license key (`hg_pro_...`). If omitted, `hodgeguard-mcp` automatically derives a machine-bound anonymous key (`hg_anon_<hash>`) from hostname and MAC/node ID.
* `HODGEGUARD_API_URL` *(optional)*: Defaults to `https://hodgeguard-cloud-brain.onrender.com`.

### Example MCP Client Configuration

Add `hodgeguard-mcp` to your MCP client config (for example, `opencode.jsonc`):

```json
{
  "mcp": {
    "hodgeguard": {
      "type": "local",
      "command": ["hodgeguard-mcp"],
      "enabled": true,
      "environment": {
        "HODGEGUARD_API_KEY": "hg_pro_your_key_here"
      }
    }
  }
}
```

---

## How HodgeGuard Compares

Most MCP security tools focus on prompt injection or static command allowlists, whereas `hodgeguard-mcp` is purpose-built to stop **autonomous token-burning livelocks**:

| Tool / Platform | Primary Focus | Livelock / Trajectory Manifold | Local SHA-256 Privacy | Pricing |
| :--- | :--- | :--- | :--- | :--- |
| **HodgeGuard MCP** | **Livelock & loop circuit-breaker** | **Yes (`curl_energy` graph)** | **Yes (hashes locally)** | **Free (250 steps) / $9 Pro** |
| **MCP Guard** | Prompt & SQL/command injection | No | N/A | Open-source |
| **ShellGuard** | Read-only AST bash allowlists | No | N/A | Open-source |
| **Preloop / Gopher** | Enterprise MCP control planes | Budget/rate limits only | Cloud gateway | $12/mo – $999/mo |

---

## Free vs. Pro

| Feature | Free (`hg_anon_...`) | Pro (`hg_pro_...`) |
| :--- | :--- | :--- |
| **Onboarding** | Automatic machine-bound key on first run | License key issued upon checkout |
| **Step Quota** | Capped at **250 steps** (`FREE_LIMIT_REACHED` paywall on exhaustion) | High / unlimited step allowance |
| **Livelock Protection** | Full `/v1/step` manifold checks & `hg_bash` loop detection | Full `/v1/step` manifold checks & `hg_bash` loop detection |
| **Session Reset** | Supported via `/v1/reset` | Supported via `/v1/reset` |

### Upgrading to Pro

Upgrade at: **[https://buymeacoffee.com/zshor/e/597895](https://buymeacoffee.com/zshor/e/597895)**

Once you receive your Pro key, set `HODGEGUARD_API_KEY` in your MCP environment configuration and restart your agent client.
