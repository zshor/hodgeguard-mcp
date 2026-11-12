#!/usr/bin/env python3
"""
PUBLIC OPEN-SOURCE MCP CLIENT: hodgeguard-mcp
Contains ZERO proprietary math.
- Auto-provisions a zero-friction anonymous trial key (250 free steps) per machine.
- Hashes tool names, targets, and state fingerprints locally via SHA-256 (100% Zero-Knowledge Privacy).
"""
import hashlib
import json
import os
import platform
import sys
import urllib.request
import urllib.error
import uuid
from typing import Optional

API_URL = os.environ.get("HODGEGUARD_API_URL", "https://hodgeguard-brain-api.fly.dev")


def get_default_anon_key() -> str:
    node_fingerprint = f"{platform.node()}-{uuid.getnode()}"
    digest = hashlib.sha256(node_fingerprint.encode("utf-8")).hexdigest()[:16]
    return f"hg_anon_{digest}"


API_KEY = os.environ.get("HODGEGUARD_API_KEY", get_default_anon_key())

TOOLS = [
    {
        "name": "hodgeguard_check_step",
        "description": (
            "Call before or after executing a shell/edit tool to verify the agent is not "
            "trapped in a non-convergent edit-test-fail livelock. Zero-knowledge SHA-256 privacy."
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
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=3.0) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        return json.loads(e.read().decode("utf-8"))
    except Exception as exc:
        return {"status": "ERROR", "halted": False, "recommendation": f"Cloud Brain unreachable: {exc}"}


def handle_rpc(request: dict) -> Optional[dict]:
    req_id = request.get("id")
    method = request.get("method", "")
    params = request.get("params", {})

    if method == "initialize":
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {
                "protocolVersion": "2024-11-05",
                "capabilities": {"tools": {}},
                "serverInfo": {"name": "hodgeguard-mcp", "version": "0.2.0"},
            },
        }
    elif method == "notifications/initialized":
        return None
    elif method == "tools/list":
        return {"jsonrpc": "2.0", "id": req_id, "result": {"tools": TOOLS}}
    elif method == "tools/call":
        name = params.get("name")
        args = params.get("arguments", {})
        if name == "hodgeguard_check_step":
            canonical_v = f"{args.get('tool_name', '').lower()}::{args.get('target', '')}"
            cloud_resp = call_cloud_brain("/v1/step", {
                "vertex_hash": sha256_short(canonical_v),
                "state_hash": sha256_short(args.get("state_fingerprint", "")),
                "verified_progress": bool(args.get("verified_progress", False)),
            })
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "content": [{"type": "text", "text": json.dumps(cloud_resp, indent=2)}],
                    "isError": bool(cloud_resp.get("halted", False)),
                },
            }
        elif name == "hodgeguard_reset":
            cloud_resp = call_cloud_brain("/v1/reset", {})
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {"content": [{"type": "text", "text": json.dumps(cloud_resp)}]},
            }
    if req_id is not None:
        return {"jsonrpc": "2.0", "id": req_id, "error": {"code": -32601, "message": f"Method not found: {method}"}}
    return None


def main():
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            req = json.loads(line)
            resp = handle_rpc(req)
            if resp is not None:
                sys.stdout.write(json.dumps(resp) + "\n")
                sys.stdout.flush()
        except Exception as exc:
            sys.stdout.write(json.dumps({"jsonrpc": "2.0", "id": None, "error": {"code": -32700, "message": str(exc)}}) + "\n")
            sys.stdout.flush()


if __name__ == "__main__":
    main()
