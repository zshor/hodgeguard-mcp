#!/usr/bin/env python3
"""
PUBLIC OPEN-SOURCE MCP CLIENT: hodgeguard-mcp
- Auto-provisions a machine-bound anonymous key (hg_anon_<hash>) when HODGEGUARD_API_KEY is unset.
- Hashes tool/target and state fingerprints locally via SHA-256 over MCP stdio JSON-RPC.
- Pro license shop: https://buymeacoffee.com/zshor/e/597895
"""

import hashlib
import json
import os
import platform
import re
import subprocess
import sys
import urllib.error
import urllib.request
import uuid
from typing import Optional

DEFAULT_API_URL = "https://hodgeguard-cloud-brain.onrender.com"
API_URL = os.environ.get("HODGEGUARD_API_URL", DEFAULT_API_URL).rstrip("/")
SHOP_URL = "https://buymeacoffee.com/zshor/e/597895"

SHELL_LOOP_PATTERNS = [
    re.compile(r"\bfor\s+[a-zA-Z_][a-zA-Z0-9_]*\s+in\b", re.IGNORECASE),
    re.compile(r"\bwhile\s+", re.IGNORECASE),
    re.compile(r"\buntil\s+", re.IGNORECASE),
]


def has_shell_loop_construct(command: str) -> bool:
    if not command or not command.strip():
        return False
    if any(pattern.search(command) for pattern in SHELL_LOOP_PATTERNS):
        return True
    # Also detect repeated semicolon/&& chains invoking the same command token 3+ times
    parts = [p.strip() for p in re.split(r"(?:&&|\|\||;)", command) if p.strip()]
    if len(parts) >= 3:
        cmds = [p.split()[0].lower() for p in parts if p.split()]
        for cmd in set(cmds):
            if cmds.count(cmd) >= 3:
                return True
    return False


def get_default_anon_key() -> str:
    node_fingerprint = f"{platform.node()}-{uuid.getnode()}"
    digest = hashlib.sha256(node_fingerprint.encode("utf-8")).hexdigest()[:16]
    return f"hg_anon_{digest}"


API_KEY = os.environ.get("HODGEGUARD_API_KEY") or get_default_anon_key()

TOOLS = [
    {
        "name": "hodgeguard_check_step",
        "description": (
            "Call before or after executing a shell/edit tool to verify the agent is not "
            "trapped in a non-convergent edit-test-fail livelock. Local SHA-256 privacy."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "tool_name": {"type": "string", "description": "e.g., bash, edit_file, read_file"},
                "target": {"type": "string", "description": "File path or command signature"},
                "state_fingerprint": {"type": "string", "description": "Optional error output or file snippet"},
                "verified_progress": {"type": "boolean", "description": "True ONLY if a new test passed"},
            },
            "required": ["tool_name", "target"],
        },
    },
    {
        "name": "hodgeguard_reset",
        "description": "Resets the Hodge curl manifold when starting a new user task.",
        "inputSchema": {"type": "object", "properties": {}},
    },
    {
        "name": "hg_bash",
        "description": "Execute a bash command securely through the HodgeGuard Firewall. Use this tool INSTEAD OF the default bash tool for all shell commands.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "command": {"type": "string", "description": "The shell command to execute"}
            },
            "required": ["command"]
        },
    }
]


def sha256_short(raw: str) -> str:
    if not raw:
        return ""
    return hashlib.sha256(raw.strip().encode("utf-8")).hexdigest()[:16]


def call_cloud_brain(endpoint: str, payload: dict) -> dict:
    req = urllib.request.Request(
        f"{API_URL}{endpoint}",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "X-HodgeGuard-Key": API_KEY,
            "User-Agent": "HodgeGuard-MCP/0.2.3",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=25.0) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
            return json.loads(raw) if raw.strip() else {"status": "OK", "halted": False}
    except urllib.error.HTTPError as e:
        raw = e.read().decode("utf-8", errors="replace")
        try:
            parsed = json.loads(raw)
            if isinstance(parsed, dict):
                return parsed
        except Exception:
            pass
        return {
            "status": f"HTTP_{e.code}",
            "halted": False,
            "recommendation": f"Cloud Brain returned HTTP {e.code}. Upgrade at {SHOP_URL}",
        }
    except Exception as exc:
        return {
            "status": "ERROR",
            "halted": False,
            "recommendation": f"Cloud Brain unreachable: {exc}",
        }


def handle_rpc(request: dict) -> Optional[dict]:
    req_id = request.get("id")
    method = request.get("method", "")
    params = request.get("params") or {}

    if method == "initialize":
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {
                "protocolVersion": "2024-11-05",
                "capabilities": {"tools": {}},
                "serverInfo": {"name": "hodgeguard-mcp", "version": "0.2.3"},
            },
        }
    if method == "notifications/initialized":
        return None
    if method == "tools/list":
        return {"jsonrpc": "2.0", "id": req_id, "result": {"tools": TOOLS}}
    if method == "tools/call":
        name = params.get("name")
        args = params.get("arguments") or {}

        if name == "hodgeguard_check_step":
            canonical_v = f"{str(args.get('tool_name', '')).lower()}::{args.get('target', '')}"
            cloud_resp = call_cloud_brain(
                "/v1/step",
                {
                    "vertex_hash": sha256_short(canonical_v),
                    "state_hash": sha256_short(str(args.get("state_fingerprint", ""))),
                    "verified_progress": bool(args.get("verified_progress", False)),
                },
            )
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "content": [{"type": "text", "text": json.dumps(cloud_resp, indent=2)}],
                    "isError": bool(cloud_resp.get("halted", False)),
                },
            }

        if name == "hodgeguard_reset":
            cloud_resp = call_cloud_brain("/v1/reset", {})
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {"content": [{"type": "text", "text": json.dumps(cloud_resp)}]},
            }

        if name == "hg_bash":
            command = args.get("command", "")
            target = command.strip().split()[0] if command.strip() else "empty_cmd"
            vertex_str = f"hg_bash::{target}"
            loop_detected = has_shell_loop_construct(command)
            state_input = f"{command}::LOOP_DETECTED" if loop_detected else command

            cloud_resp = call_cloud_brain(
                "/v1/step",
                {
                    "vertex_hash": sha256_short(vertex_str),
                    "state_hash": sha256_short(state_input),
                    "verified_progress": False,
                },
            )

            # Apply a penalty step on the manifold if a shell loop construct is embedded
            if loop_detected and not cloud_resp.get("halted"):
                cloud_resp = call_cloud_brain(
                    "/v1/step",
                    {
                        "vertex_hash": sha256_short(vertex_str),
                        "state_hash": sha256_short(state_input),
                        "verified_progress": False,
                    },
                )

            if cloud_resp.get("halted"):
                recommendation = cloud_resp.get("recommendation", "Livelock loop detected.")
                loop_note = " (Shell loop construct detected inside command.)" if loop_detected else ""
                return {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": {
                        "content": [
                            {
                                "type": "text",
                                "text": (
                                    f"🛑 HODGEGUARD BLOCKED: {recommendation}{loop_note}\n"
                                    "You are repeating the exact same command or hit a limit. Stop and change your approach."
                                ),
                            }
                        ],
                        "isError": True,
                    },
                }

            try:
                result = subprocess.run(
                    command,
                    shell=True,
                    capture_output=True,
                    text=True,
                    timeout=120,
                )
                output = ""
                if result.stdout:
                    output += f"{result.stdout}\n"
                if result.stderr:
                    output += f"STDERR:\n{result.stderr}\n"
                final_output = output.strip() if output.strip() else "Command executed successfully with no output."
            except subprocess.TimeoutExpired:
                final_output = "🛑 COMMAND TIMED OUT after 120 seconds."
            except Exception as e:
                final_output = f"🛑 EXECUTION ERROR: {str(e)}"

            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "content": [{"type": "text", "text": final_output}],
                    "isError": False,
                },
            }

    if req_id is not None:
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "error": {"code": -32601, "message": f"Method not found: {method}"},
        }
    return None


def main():
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            req = json.loads(line)
            if not isinstance(req, dict):
                raise ValueError("JSON-RPC message must be an object")
            resp = handle_rpc(req)
            if resp is not None:
                sys.stdout.write(json.dumps(resp) + "\n")
                sys.stdout.flush()
        except Exception as exc:
            sys.stdout.write(
                json.dumps(
                    {
                        "jsonrpc": "2.0",
                        "id": None,
                        "error": {"code": -32700, "message": str(exc)},
                    }
                )
                + "\n"
            )
            sys.stdout.flush()


if __name__ == "__main__":
    main()
