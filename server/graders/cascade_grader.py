"""
Grader for Task 2 — Cascading Failure (Medium)

Scoring breakdown:
  Correct severity (P1)                    → +0.20
  Correct root cause (user-db)             → +0.35
  Correct remediation (kill-query/restart) → +0.25
  Ordering bonus (no symptom fix first)    → +0.10
  Speed bonus (resolved ≤ 8 steps)         → +0.10
  ─────────────────────────────────────────────────
  Maximum possible score                   →  1.00

Penalties:
  Identified symptom as root cause         →  0.00 (no credit)
  Remediated symptom service first         → -0.10 (ordering penalty)
  Never resolved                           → -0.10
"""
from __future__ import annotations
from server.models import EpisodeState
from server.graders.base_grader import BaseGrader


class CascadeGrader(BaseGrader):
    """Official grader for Task 2 — Cascading Failure."""

    CORRECT_SEVERITY = "P1"
    CORRECT_ROOT_CAUSE = "user-db"
    CORRECT_REMEDIATION_PREFIXES = {"kill-query", "restart"}
    CORRECT_REMEDIATION_SERVICE = "user-db"
    SYMPTOM_SERVICES = {"api-gateway", "auth-service"}  # wrong answers
    MAX_STEPS = 12
    SPEED_THRESHOLD = 8

    def score(self, state: EpisodeState) -> float:
        """
        Score the completed Task 2 episode with STRICT validation.
        CRITICAL: user-db is root cause. api-gateway and auth-service are SYMPTOMS.
        Identifying symptoms as root cause gets PENALIZED.
        """
        score = 0.0
        breakdown = {}

        # --- SEVERITY CHECK ---
        severity_value = self._get_first_value(state, "classify_severity")
        if severity_value == "P1":
            score += 0.20
            breakdown["severity"] = "+0.20 (correct: P1)"
        else:
            breakdown["severity"] = f"0.00 (wrong: got '{severity_value}', expected 'P1')"

        # --- ROOT CAUSE CHECK ---
        # STRICT: must be user-db exactly.
        # api-gateway and auth-service are SYMPTOMS, not root cause.
        # Identifying symptoms as root cause gets PENALTY.
        root_cause_value = self._get_first_value(state, "identify_root_cause")
        symptom_services = {"api-gateway", "auth-service", "api_gateway", "auth_service"}

        if root_cause_value == "user-db":
            score += 0.35
            breakdown["root_cause"] = "+0.35 (correct: user-db)"
        elif root_cause_value in symptom_services:
            # Explicitly penalize symptom-as-root-cause
            score -= 0.10
            breakdown["root_cause"] = f"-0.10 (identified SYMPTOM as root cause: '{root_cause_value}')"
        else:
            breakdown["root_cause"] = f"0.00 (wrong: got '{root_cause_value}', expected 'user-db')"

        # --- ORDERING CHECK ---
        # Bonus for NOT remediating symptoms before identifying real root cause.
        # Check if agent tried to remediate api-gateway or auth-service first.
        all_remediations = self._get_actions_of_type(state, "remediate")
        symptom_remediated_first = False
        for action in all_remediations:
            val = action.get("value", "")
            if any(sym in val for sym in ["api-gateway", "auth-service"]):
                symptom_remediated_first = True
                break

        if not symptom_remediated_first:
            score += 0.10
            breakdown["ordering"] = "+0.10 (did not remediate symptoms first)"
        else:
            score -= 0.10
            breakdown["ordering"] = "-0.10 (remediated symptom service before root cause)"

        # --- REMEDIATION CHECK ---
        # Must target user-db with kill-query or restart
        remediation_value = self._get_first_value(state, "remediate")
        correct_remediation = (
            remediation_value and
            "user-db" in remediation_value and
            (remediation_value.startswith("kill-query:") or
             remediation_value.startswith("restart:"))
        )
        if correct_remediation:
            score += 0.25
            breakdown["remediation"] = f"+0.25 (correct: {remediation_value})"
        else:
            breakdown["remediation"] = f"0.00 (wrong: got '{remediation_value}', expected 'kill-query:user-db' or 'restart:user-db')"

        # --- SPEED BONUS ---
        steps_used = self._steps_used(state)
        resolved = self._episode_resolved(state)
        if resolved and steps_used <= 8 and score > 0.59:
            score += 0.10
            breakdown["speed"] = f"+0.10 (resolved in {steps_used} steps <= 8)"
        else:
            breakdown["speed"] = f"0.00 (steps={steps_used}, resolved={resolved})"

        # --- UNRESOLVED PENALTY ---
        if not resolved:
            score -= 0.10
            breakdown["penalty"] = "-0.10 (episode not resolved)"

        print(f"[CASCADE_GRADER] Score breakdown: {breakdown}")
        self._breakdown = breakdown
        return self._clamp(score)

    def get_breakdown(self) -> dict:
        """Return scoring breakdown from last score() call."""
        return getattr(self, "_breakdown", {})
