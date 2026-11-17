# hodgeguard-mcp

Guardrail MCP server (`stdio`) that detects and halts non-convergent tool/shell loops ("livelocks") before autonomous coding agents burn excessive tokens and retries.

## How It Works
1. **Invariant Target & Command Normalization (Client):** Normalizes shell wrappers, whitespace, and target paths/endpoints into canonical signatures, hashing state locally via SHA-256 before sending telemetry to the cloud manifold service.
2. **Orthogonal Flow & Cycle Detection (Server):** Tracks forward milestones (`verified_progress=true` gradient reset) separately from repeated target activity, self-loops, 2-cycles, and 3-step/harmonic return patterns.
3. **Transparent Loop & Token Telemetry:** Reports exact `loops_stopped` alongside configurable estimated tokens saved (`HODGEGUARD_EST_TOKENS_PER_HALT`, default `1500` tokens per prevented loop step).

## Installation

### Via `pipx` (Recommended)
```bash
pipx install hodgeguard-mcp
```

### MCP Client Configuration
Add `hodgeguard-mcp` to your MCP client config (for example, OpenCode, Claude Code, or Cursor):

```json
{
  "mcpServers": {
    "hodgeguard": {
      "command": "hodgeguard-mcp",
      "env": {
        "HODGEGUARD_API_KEY": "your_optional_pro_key_or_leave_unset_for_anon_key",
        "HODGEGUARD_EST_TOKENS_PER_HALT": "1500"
      }
    }
  }
}
```

> **Enforcement Note:** `hg_bash` guards commands executed through the MCP tool. For strict enforcement against shell loop evasion, disable or restrict raw/native shell tools in your agent harness so commands route through `hg_bash`.

## Benchmark Comparison (`v0.3.2`)
Run the local comparison suite:

```bash
python3 benchmarks/run_benchmarks.py
```

| Scenario | What It Tests | HodgeGuard (Halt Step) | Exact-Match Blocker | Consecutive Error Counter (3x) |
| :--- | :--- | :---: | :---: | :---: |
| **BM-01** | Exact Retry Storm | **2** | 2 | 3 |
| **BM-02** | Syntax / Binary Evasion | **5** | None | None |
| **BM-03** | Version Thrashing (`v1`..`v4`) | **2** | None | None |
| **BM-04** | Parameter Drift on Missing Target | **2** | None | 3 |
| **BM-05** | 3-Cycle / Alternating Probes | **3** | 3 | 3 |
| **BM-06** | Progress Reset + Spin | **4** | 4 | 5 |

## Pro License
- Anonymous keys (`hg_anon_*`) start on the free tier (`250` steps).
- Upgrade options and details: [HodgeGuard Pro](https://buymeacoffee.com/zshor/e/597895)
