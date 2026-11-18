# 🛡️ hodgeguard-mcp
[![Listed on mcpservers.org](https://mcpservers.org/badge.svg)](https://mcpservers.org/servers/zshor/hodgeguard-mcp)

**Zero-Knowledge Topological Circuit-Breaker for Autonomous Coding Agents (OpenCode, Claude Code, Cursor)**

[![PyPI version](https://img.shields.io/pypi/v/hodgeguard-mcp.svg)](https://pypi.org/project/hodgeguard-mcp/)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![MCP Protocol](https://img.shields.io/badge/MCP-2024--11--05-purple.svg)](https://modelcontextprotocol.io)

Autonomous coding agents regularly trap themselves in **non-convergent edit–verify–fail livelocks**—burning 50k–200k+ tokens while mutating syntax, swapping shell binaries, or polling broken states while convinced they are "almost there."

**`hodgeguard-mcp`** is a drop-in MCP (`stdio`) firewall that detects and halts multi-step agent livelocks in real time using **Invariant Target Normalization** and **Orthogonal Hodge Manifold Cycle Detection**—without ever seeing your raw code or commands.

---

## 🔥 Why Naive Agent Guardrails Fail

Most agent harnesses rely on two brittle heuristics that LLMs trivially bypass:

1. **Exact-Command / Exact-Hash Matchers Fail on Syntax Evasion:**
   When blocked once, an LLM simply rewrites `echo "fix" > app.py` as `printf "fix\n" > app.py`, `tee app.py <<< "fix"`, or wraps it inside `python3 -c "..."`. To an exact-hash blocker, every mutation looks like a brand-new action.
2. **Consecutive Error Counters (`max_retries=3`) Fail on "Silent" Loops:**
   Overwriting a config file with `v1`, `v2`, `v3`, `v4` returns exit code `0` (success) on every write, resetting consecutive failure counters while the agent spins indefinitely in an $A \leftrightarrow B$ edit-test cycle.

**How HodgeGuard Solves It:**
Instead of matching raw strings or counting non-zero exit codes, `hodgeguard-mcp` extracts canonical target/verb invariants locally and projects the agent's trajectory onto a directed transition graph:
* **Gradient Flow ($\nabla \phi$):** Verified test passes (`verified_progress=true`) advance potential and dissipate accumulated loop tension (`GRADIENT_RESET`).
* **Rotational Curl & Harmonic Energy:** Self-loops ($A \to A$), alternating 2-cycles ($A \leftrightarrow B$), triangular 3-cycles ($A \to B \to C \to A$), and sliding-window target thrashing accumulate curl energy until the circuit breaker trips (`curl_energy >= 2.0`).

---

## 🔒 Zero-Knowledge Privacy Architecture

Your source code, file paths, and shell outputs **never leave your machine**:
* `hodgeguard-mcp` normalizes targets locally and computes truncated **16-character SHA-256 digests** (`vertex_hash` and `state_hash`) on your device.
* The Cloud Manifold evaluates pure topological graph transitions over opaque hashes (`{"vertex_hash": "8f3a...", "state_hash": "c19b...", "verified_progress": false}`).

---

## 📊 Benchmark Comparison (`v0.3.2+`)

Reproduce the side-by-side comparison against an **Exact-Match Blocker** and a **3x Consecutive Error Counter** in under 1 second:

```bash
git clone [https://github.com/zshor/hodgeguard-mcp.git](https://github.com/zshor/hodgeguard-mcp.git)
cd hodgeguard-mcp
python3 benchmarks/run_benchmarks.py
```

| ID | Livelock Archetype | What the Agent Does | HodgeGuard (Halt Step) | Exact-Match Blocker | Error Counter (3x) |
| :--- | :--- | :--- | :---: | :---: | :---: |
| **BM-01** | **Exact Retry Storm** | Repeats identical failing check (`grep ... /etc/hosts`) | **Step 2** | Step 2 | Step 3 |
| **BM-02** | **Syntax & Binary Evasion** | Swaps `echo` $\to$ `printf` $\to$ `cat << EOF` and `bash` $\to$ `sh` on same target | **Step 5** | ❌ *Bypassed* | ❌ *Bypassed* |
| **BM-03** | **Version Thrashing** | Overwrites `/tmp/hg_proof.txt` with `v1`, `v2`, `v3`, `v4` (exit code `0`) | **Step 2** | ❌ *Bypassed* | ❌ *Bypassed* |
| **BM-04** | **Parameter Drift Probe** | Probes missing resource via `stat` $\to$ `ls -ld` $\to$ `file` $\to$ `wc -c` | **Step 2** | ❌ *Bypassed* | Step 3 |
| **BM-05** | **Alternating 2/3-Cycle** | Oscillates between `localhost:9001` and `localhost:9002` health checks | **Step 3** | Step 3 | Step 3 |
| **BM-06** | **Milestone Reset + Spin** | Passes test (`verified_progress=true`), resets state, then enters new spin | **Step 4** *(0 false positives)* | Step 4 | Step 5 |

---

## 🖥️ Real Live Trace (Nemotron 3 Ultra 550B in OpenCode)

Watch what happens when an autonomous coding agent attempts to evade `hodgeguard-mcp` by changing payload versions (`v1` $\to$ `v3`), writing a Bash `for` loop script, and switching to inline `python3 -c`:

```text
⚙ hodgeguard_hg_bash [command=echo "v1" > /tmp/hg_proof.txt && grep -q "READY_MARKER" /tmp/hg_proof.txt]
⚙ hodgeguard_hg_bash [command=echo "v2" > /tmp/hg_proof.txt && grep -q "READY_MARKER" /tmp/hg_proof.txt]
🛑 HODGEGUARD BLOCKED: LIVELOCK HALTED (LIVELOCK): Stop repeating this action.
   [Loops stopped: 1 | Est. tokens saved: ~1,500]

Thought: The firewall blocked me. Let me try a different approach using a Python script.
⚙ hodgeguard_hg_bash [command=python3 -c "for v in ['v1','v2','v3']: open('/tmp/hg_proof.txt','w').write(v)..."]
🛑 HODGEGUARD BLOCKED: LIVELOCK HALTED (LIVELOCK): Stop repeating this action.
   [Loops stopped: 2 | Est. tokens saved: ~3,000] (Shell loop construct detected. Repeated target activity.)
```

---

## ⚡ Quickstart (Install in 30 Seconds)

### 1. Install via `pipx` (Recommended)
```bash
pipx install hodgeguard-mcp
```

### 2. Add to Your MCP Client (`OpenCode`, `Claude Code`, `Cursor`)
```json
{
  "mcpServers": {
    "hodgeguard": {
      "command": "hodgeguard-mcp",
      "env": {
        "HODGEGUARD_API_KEY": "",
        "HODGEGUARD_EST_TOKENS_PER_HALT": "1500"
      }
    }
  }
}
```
*(Leave `HODGEGUARD_API_KEY` empty to auto-provision a free machine-bound anonymous key `hg_anon_<hash>` with 250 free steps.)*

> **🔒 Strict Enforcement Tip:** To prevent an agent from falling back to its built-in bash tool when halted, disable the native bash tool in your agent profile so all shell execution routes through `hg_bash`.

---

## 🧪 Try It Yourself: 30-Second Live Verification Prompt

Paste this prompt into your MCP-enabled coding agent to watch **Gradient Reset** (`verified_progress=true`) and **Livelock Halting** work back-to-back:

```text
You must use the `hg_bash` tool for all shell commands. Do not use your native bash tool.
First call `hodgeguard_reset`.
1. Create `/tmp/hg_demo.txt` with `READY_MARKER` and verify it via `hg_bash`.
2. Call `hodgeguard_check_step` with `tool_name: "hg_bash"`, `target: "/tmp/hg_demo.txt"`, `state_fingerprint: "PASSED"`, and `verified_progress: true`.
3. Now check `grep -q "MISSING_MARKER" /tmp/hg_demo.txt` via `hg_bash` and retry checking `/tmp/hg_demo.txt` using different commands (`cat`, `file`, `wc -c`) 3 times via `hg_bash`.
```

---

## 🛠️ Exposed MCP Tools

| Tool Name | Purpose |
| :--- | :--- |
| **`hg_bash`** | Drop-in guarded shell executor. Normalizes targets, detects shell/Python loop constructs, checks the Hodge manifold before execution, and blocks livelocks. |
| **`hodgeguard_check_step`** | Check or record state transitions for non-shell tools (`edit_file`, `read_file`). Pass `verified_progress: true` when a test suite passes to trigger a `GRADIENT_RESET`. |
| **`hodgeguard_reset`** | Clears the local trajectory window and cloud manifold session when starting a brand-new task. |

---

## 💎 Free Tier & HodgeGuard Pro

* **Free Anonymous Tier (`hg_anon_*`):** Auto-provisioned out of the box (`250` manifold steps included).
* **HodgeGuard Pro ($9 One-Time):** Unlimited manifold steps for heavy daily agent workflows.
  👉 **[Get a Pro License Key ($9)](https://buymeacoffee.com/zshor/e/597895)** *(Instant automated license delivery via email).*
