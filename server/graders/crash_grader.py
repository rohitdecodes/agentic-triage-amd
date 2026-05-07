"""
Grader for Task 1 — Single Service Crash (Easy)

Scoring breakdown:
  Correct severity (P1)                    → +0.30
  Correct root cause (payment-service)     → +0.35
  Correct remediation (restart:payment-*) → +0.25
  Speed bonus (resolved ≤ 5 steps)         → +0.10
  ─────────────────────────────────────────────────
  Maximum possible score                   →  1.00

Penalties:
  Ignored P1 incident                      → -0.30 (from base)
  Wrong root cause identified              →  0.00 (no credit)
  Never resolved                           → -0.10
"""
from __future__ import annotations
from server.models import EpisodeState
from server.graders.base_grader import BaseGrader


class CrashGrader(BaseGrader):
    """Official grader for Task 1 — Single Service Crash."""

    # Ground truth constants
    CORRECT_SEVERITY = "P1"
    CORRECT_ROOT_CAUSE = "payment-service"
    CORRECT_REMEDIATION_PREFIX = "restart"
    CORRECT_REMEDIATION_SERVICE = "payment-service"
    MAX_STEPS = 8
    SPEED_THRESHOLD = 5  # must resolve within this many steps for speed bonus

    def score(self, state: EpisodeState) -> float:
        """
        Score the completed Task 1 episode with STRICT validation.
        Deterministic — same action history always produces same score.
        No partial credits — wrong answers get zero.
        """
        score = 0.0
        breakdown = {}

        # --- SEVERITY CHECK ---
        # Must be exactly P1. P2 or P3 gets zero (no partial credit).
        severity_value = self._get_first_value(state, "classify_severity")
        if severity_value == "P1":
            score += 0.30
            breakdown["severity"] = "+0.30 (correct: P1)"
        else:
            breakdown["severity"] = f"0.00 (wrong: got '{severity_value}', expected 'P1')"

        # --- ROOT CAUSE CHECK ---
        # Must be exactly payment-service. Any other service gets zero.
        root_cause_value = self._get_first_value(state, "identify_root_cause")
        if root_cause_value == "payment-service":
            score += 0.35
            breakdown["root_cause"] = "+0.35 (correct: payment-service)"
        else:
            breakdown["root_cause"] = f"0.00 (wrong: got '{root_cause_value}', expected 'payment-service')"

        # --- REMEDIATION CHECK ---
        # Must contain restart AND target payment-service specifically.
        # restart:payment-service → correct
        # restart:auth-service → wrong
        # kill-query:payment-service → wrong (wrong command type)
        remediation_value = self._get_first_value(state, "remediate")
        if (remediation_value and
            remediation_value.startswith("restart:") and
            "payment-service" in remediation_value):
            score += 0.25
            breakdown["remediation"] = f"+0.25 (correct: {remediation_value})"
        else:
            breakdown["remediation"] = f"0.00 (wrong: got '{remediation_value}', expected 'restart:payment-service')"

        # --- SPEED BONUS ---
        # Only awarded if ALL above are correct AND resolved within threshold
        steps_used = self._steps_used(state)
        resolved = self._episode_resolved(state)
        if resolved and steps_used <= 5 and score > 0.89:
            score += 0.10
            breakdown["speed"] = f"+0.10 (resolved in {steps_used} steps <= 5)"
        else:
            breakdown["speed"] = f"0.00 (steps={steps_used}, resolved={resolved})"

        # --- UNRESOLVED PENALTY ---
        if not resolved:
            score -= 0.10
            breakdown["penalty"] = "-0.10 (episode not resolved)"

        print(f"[CRASH_GRADER] Score breakdown: {breakdown}")
        self._breakdown = breakdown
        return self._clamp(score)

    def get_breakdown(self) -> dict:
        """Return scoring breakdown from last score() call."""
        return getattr(self, "_breakdown", {})
