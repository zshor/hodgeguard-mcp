#!/usr/bin/env python3
"""
Local comparative benchmark harness for hodgeguard-mcp v0.3.0.
Compares No Guardrail, Exact-Match Blocker, Consecutive Error Counter,
and HodgeGuard's invariant target + manifold cycle logic across 6 scenarios.
"""

from collections import deque
import hashlib
import re

WRAPPER_TOKENS = {"env", "sudo", "command", "nohup", "time", "nice"}
PATH_OR_ENDPOINT_RE = re.compile(
    r"(?:https?://[^\s\"';&|]+|/[A-Za-z0-9_./-]+|localhost:\d+|127\.0\.0\.1:\d+)"
)
SHELL_LOOP_PATTERNS = [
    re.compile(r"\bfor\s+[a-zA-Z_][a-zA-Z0-9_]*\s+in\b", re.IGNORECASE),
    re.compile(r"\bwhile\s+", re.IGNORECASE),
    re.compile(r"\buntil\s+", re.IGNORECASE),
]


def normalize_whitespace(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "").strip())


def canonical_verb(command: str) -> str:
    tokens = normalize_whitespace(command).split()
    idx = 0
    while idx < len(tokens):
        tok = tokens[idx].strip("'\"").lower()
        if tok in WRAPPER_TOKENS:
            idx += 1
            continue
        if tok in {"bash", "sh", "zsh", "dash"} and idx + 1 < len(tokens) and tokens[idx + 1] == "-c":
            idx += 2
            continue
        return tok
    return "empty_cmd"


def has_shell_loop_construct(command: str) -> bool:
    if not command or not command.strip():
        return False
    if any(p.search(command) for p in SHELL_LOOP_PATTERNS):
        return True
    parts = [p.strip() for p in re.split(r"(?:&&|\|\||;)", command) if p.strip()]
    if len(parts) >= 3:
        cmds = [canonical_verb(p) for p in parts if canonical_verb(p)]
        for cmd in set(cmds):
            if cmds.count(cmd) >= 3:
                return True
    return False


def extract_invariant_signature(command: str) -> tuple[str, str]:
    norm_cmd = normalize_whitespace(command)
    verb = canonical_verb(norm_cmd)
    targets = PATH_OR_ENDPOINT_RE.findall(norm_cmd)
    cleaned_targets = [t.strip("'\"").rstrip("/") or "/" for t in targets]
    if cleaned_targets:
        primary_target = "|".join(dict.fromkeys(cleaned_targets[:2]))
        return f"target::{primary_target}", norm_cmd
    return f"verb::{verb}", norm_cmd


def sha256_short(raw: str) -> str:
    if not raw:
        return ""
    return hashlib.sha256(raw.strip().encode("utf-8")).hexdigest()[:16]


class LocalManifoldSim:
    def __init__(self, halt_threshold: float = 2.0):
        self.halt_threshold = halt_threshold
        self.trajectory: list[str] = []
        self.edge_weights: dict[tuple[str, str], int] = {}
        self.state_hash_counts: dict[str, int] = {}
        self.pair_counts: dict[tuple[str, str], int] = {}

    def reset(self) -> None:
        self.trajectory.clear()
        self.edge_weights.clear()
        self.state_hash_counts.clear()
        self.pair_counts.clear()

    def _cycle_circulation(self, v_prev: str, v_curr: str) -> tuple[float, str]:
        curl = 0.0
        label = "NONE"
        self_w = self.edge_weights.get((v_curr, v_curr), 0)
        if self_w >= 1:
            curl += 1.0 * self_w
            label = "SELF_LOOP"
        two_cycle = min(self.edge_weights.get((v_prev, v_curr), 0), self.edge_weights.get((v_curr, v_prev), 0))
        if two_cycle > 0:
            curl += 1.25 * two_cycle
            label = "2_CYCLE"
        if len(self.trajectory) >= 2:
            a, b, c = self.trajectory[-2], self.trajectory[-1], v_curr
            tri = min(
                self.edge_weights.get((a, b), 0),
                self.edge_weights.get((b, c), 0),
                self.edge_weights.get((c, a), 0),
            )
            if tri > 0:
                curl += 1.0 * tri
                if label == "NONE":
                    label = "3_CYCLE"
        return curl, label

    def step(self, vertex_hash: str, state_hash: str, verified_progress: bool) -> dict:
        if verified_progress:
            self.reset()
            return {"halted": False, "curl_energy": 0.0, "cycle_type": "GRADIENT_RESET"}

        v_key = vertex_hash or "__empty_vertex__"
        s_key = state_hash or ""
        pair_key = (v_key, s_key)

        state_repeat = 0.0
        if s_key:
            self.state_hash_counts[s_key] = self.state_hash_counts.get(s_key, 0) + 1
            if self.state_hash_counts[s_key] > 1:
                state_repeat = (self.state_hash_counts[s_key] - 1) * 1.5

        self.pair_counts[pair_key] = self.pair_counts.get(pair_key, 0) + 1
        harmonic = (self.pair_counts[pair_key] - 1) * 1.0 if self.pair_counts[pair_key] > 1 else 0.0

        curl_energy = state_repeat + harmonic
        cycle_type = "STATE_REPEAT" if state_repeat > 0 else ("HARMONIC_RETURN" if harmonic > 0 else "NONE")

        if self.trajectory:
            v_prev = self.trajectory[-1]
            self.edge_weights[(v_prev, v_key)] = self.edge_weights.get((v_prev, v_key), 0) + 1
            rot_curl, det_cycle = self._cycle_circulation(v_prev, v_key)
            curl_energy += rot_curl
            if det_cycle != "NONE":
                cycle_type = det_cycle

        self.trajectory.append(v_key)
        if len(self.trajectory) > 24:
            self.trajectory.pop(0)

        halted = curl_energy >= self.halt_threshold
        return {
            "halted": halted,
            "curl_energy": round(curl_energy, 3),
            "cycle_type": "LIVELOCK" if halted else cycle_type,
        }


def eval_hodgeguard(steps: list[dict]) -> int | None:
    tracker: deque[str] = deque(maxlen=8)
    sim = LocalManifoldSim()
    for idx, s in enumerate(steps, 1):
        if s.get("verified_progress"):
            tracker.clear()
            sim.step("", "", True)
            continue
        inv_target, norm_cmd = extract_invariant_signature(s["command"])
        v_str = f"hg_bash::{inv_target}"
        loop_det = has_shell_loop_construct(norm_cmd)
        tracker.append(v_str)
        w_hits = sum(1 for x in tracker if x == v_str)
        parts = [norm_cmd]
        if loop_det:
            parts.append("LOOP_DETECTED")
        if w_hits >= 3:
            parts.append(f"WINDOW_CYCLE_{w_hits}")
        res = sim.step(sha256_short(v_str), sha256_short("::".join(parts)), False)
        if (loop_det or w_hits >= 3) and not res["halted"]:
            res = sim.step(sha256_short(v_str), sha256_short("::".join(parts)), False)
        if res["halted"]:
            return idx
    return None


def eval_exact_match(steps: list[dict]) -> int | None:
    seen: set[str] = set()
    for idx, s in enumerate(steps, 1):
        if s.get("verified_progress"):
            continue
        cmd = normalize_whitespace(s["command"])
        if cmd in seen:
            return idx
        seen.add(cmd)
    return None


def eval_error_counter(steps: list[dict], limit: int = 3) -> int | None:
    streak = 0
    for idx, s in enumerate(steps, 1):
        if s.get("verified_progress"):
            streak = 0
            continue
        if s.get("failed", False):
            streak += 1
            if streak >= limit:
                return idx
        else:
            streak = 0
    return None


SCENARIOS = {
    "BM-01 Exact Retry Storm": [
        {"command": 'grep -n "MISSING" /etc/hosts; echo $?', "failed": True},
        {"command": 'grep -n "MISSING" /etc/hosts; echo $?', "failed": True},
        {"command": 'grep -n "MISSING" /etc/hosts; echo $?', "failed": True},
        {"command": 'grep -n "MISSING" /etc/hosts; echo $?', "failed": True},
    ],
    "BM-02 Syntax/Binary Evasion": [
        {"command": 'echo "bad" > /tmp/lint_target.txt', "failed": False},
        {"command": "bash /tmp/check_lint.sh", "failed": True},
        {"command": 'printf "bad2\\n" > /tmp/lint_target.txt', "failed": False},
        {"command": "sh /tmp/check_lint.sh", "failed": True},
        {"command": "cat << EOF > /tmp/lint_target.txt\nbad3\nEOF", "failed": False},
    ],
    "BM-03 Version Thrashing": [
        {"command": 'echo "v1" > /tmp/hg_proof.txt', "failed": False},
        {"command": 'echo "v2" > /tmp/hg_proof.txt', "failed": False},
        {"command": 'echo "v3" > /tmp/hg_proof.txt', "failed": False},
        {"command": 'echo "v4" > /tmp/hg_proof.txt', "failed": False},
    ],
    "BM-04 Parameter Drift": [
        {"command": "stat /tmp/nonexistent_svc_check", "failed": True},
        {"command": "ls -ld /tmp/nonexistent_svc_check", "failed": True},
        {"command": "file /tmp/nonexistent_svc_check", "failed": True},
        {"command": "wc -c /tmp/nonexistent_svc_check", "failed": True},
    ],
    "BM-05 3-Cycle / Alternating": [
        {"command": "curl -s http://localhost:9001/health", "failed": True},
        {"command": "curl -s http://localhost:9002/health", "failed": True},
        {"command": "curl -s http://localhost:9001/health", "failed": True},
        {"command": "curl -s http://localhost:9002/health", "failed": True},
        {"command": "curl -s http://localhost:9001/health", "failed": True},
    ],
    "BM-06 Progress Reset + Spin": [
        {"command": 'echo "READY_MARKER" > /tmp/hg_pass.txt && grep -q "READY_MARKER" /tmp/hg_pass.txt', "failed": False},
        {"verified_progress": True},
        {"command": 'grep -q "MISSING_MARKER" /tmp/hg_pass.txt', "failed": True},
        {"command": 'grep -q "MISSING_MARKER" /tmp/hg_pass.txt', "failed": True},
        {"command": 'grep -q "MISSING_MARKER" /tmp/hg_pass.txt', "failed": True},
    ],
}


def main() -> None:
    print(f"{'Scenario':28s} | {'HodgeGuard':10s} | {'ExactMatch':10s} | {'ErrCount3':9s}")
    print("-" * 66)
    for name, steps in SCENARIOS.items():
        hg = str(eval_hodgeguard(steps))
        ex = str(eval_exact_match(steps))
        er = str(eval_error_counter(steps))
        print(f"{name:28s} | {hg:10s} | {ex:10s} | {er:9s}")


if __name__ == "__main__":
    main()
