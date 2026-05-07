"""
Grader for Task 3 — Silent Degradation (Hard)

Scoring breakdown:
  Correct severity (P2)                    → +0.30
  Correct root cause (payment-db)          → +0.35
  Correct remediation (flush-cache/query)  → +0.25
  Speed bonus (resolved ≤ 10 steps)        → +0.10
  ─────────────────────────────────────────────────
  Maximum possible score                   →  1.00

CRITICAL TRAPS:
  - Severity is P2 (no crash), not P1
  - root_cause is payment-db (database), NOT payment-service (app)
  - Remediation is flush-cache/kill-query, NOT restart

Penalties:
  P1 overcall (no crash = not critical)    → -0.15
  payment-service confusion                → -0.10
  Wrong remediation command                → -0.10
  Never resolved                           → -0.10
"""
from __future__ import annotations
from server.models import EpisodeState
from server.graders.base_grader import BaseGrader


class SilentDegradeGrader(BaseGrader):
    """Official grader for Task 3 — Silent Degradation."""

    CORRECT_SEVERITY = "P2"
    CORRECT_ROOT_CAUSE = "payment-db"
    CORRECT_REMEDIATION_COMMANDS = {"flush-cache", "kill-query"}
    CORRECT_REMEDIATION_SERVICE = "payment-db"
    MAX_STEPS = 15
    SPEED_THRESHOLD = 10

    def score(self, state: EpisodeState) -> float:
        """
        Score the completed Task 3 episode with STRICT validation.
        
        Key trap: severity is P2, NOT P1.
        Agents that auto-classify everything as P1 get penalized here.
        Root cause is payment-db — not payment-service.
        """
        score = 0.0
        breakdown = {}

        # --- SEVERITY CHECK ---
        # CRITICAL TRAP: must be P2, not P1.
        # P1 means the agent didn't read the logs carefully.
        # No crashes, no complete failures = P2.
        severity_value = self._get_first_value(state, "classify_severity")
        if severity_value == "P2":
            score += 0.30
            breakdown["severity"] = "+0.30 (correct: P2)"
        elif severity_value == "P1":
            # Explicit penalty for P1 overcall on a degradation scenario
            score -= 0.15
            breakdown["severity"] = "-0.15 (overcalled P1 — this is degradation, not crash)"
        else:
            breakdown["severity"] = f"0.00 (wrong: got '{severity_value}', expected 'P2')"

        # --- ROOT CAUSE CHECK ---
        # Must be payment-db (the database), NOT payment-service (the app).
        # These are different services — confusing them = wrong.
        root_cause_value = self._get_first_value(state, "identify_root_cause")
        if root_cause_value == "payment-db":
            score += 0.35
            breakdown["root_cause"] = "+0.35 (correct: payment-db)"
        elif root_cause_value == "payment-service":
            # Common confusion — penalize explicitly
            score -= 0.10
            breakdown["root_cause"] = "-0.10 (confused payment-db with payment-service)"
        else:
            breakdown["root_cause"] = f"0.00 (wrong: got '{root_cause_value}', expected 'payment-db')"

        # --- REMEDIATION CHECK ---
        # flush-cache or kill-query targeting payment-db
        # restart is WRONG here — not a crash, don't restart
        remediation_value = self._get_first_value(state, "remediate")
        correct_commands = ["flush-cache:", "kill-query:"]
        correct_remediation = (
            remediation_value and
            "payment-db" in remediation_value and
            any(remediation_value.startswith(cmd) for cmd in correct_commands)
        )
        wrong_command = (
            remediation_value and
            remediation_value.startswith("restart:") and
            "payment-db" in remediation_value
        )

        if correct_remediation:
            score += 0.25
            breakdown["remediation"] = f"+0.25 (correct: {remediation_value})"
        elif wrong_command:
            # Restarting for a degradation is wrong — should flush-cache or kill-query
            score -= 0.10
            breakdown["remediation"] = f"-0.10 (wrong command type: '{remediation_value}' — use flush-cache or kill-query)"
        else:
            breakdown["remediation"] = f"0.00 (wrong: got '{remediation_value}')"

        # --- SPEED BONUS ---
        steps_used = self._steps_used(state)
        resolved = self._episode_resolved(state)
        if resolved and steps_used <= 10 and score > 0.79:
            score += 0.10
            breakdown["speed"] = f"+0.10 (resolved in {steps_used} steps <= 10)"
        else:
            breakdown["speed"] = f"0.00 (steps={steps_used}, resolved={resolved})"

        # --- UNRESOLVED PENALTY ---
        if not resolved:
            score -= 0.10
            breakdown["penalty"] = "-0.10 (episode not resolved)"

        print(f"[SILENT_DEGRADE_GRADER] Score breakdown: {breakdown}")
        self._breakdown = breakdown
        return self._clamp(score)

    def get_breakdown(self) -> dict:
        """Return scoring breakdown from last score() call."""
        return getattr(self, "_breakdown", {})
