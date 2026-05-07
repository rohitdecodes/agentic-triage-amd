import json
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from amd_client import call_amd_llm


PLANNER_SYSTEM_PROMPT = """You are a senior Site Reliability Engineer (SRE) specializing in incident triage.
You will receive the initial state of a production incident: a list of logs and service health statuses.
Your job is to analyze the situation and produce a structured triage strategy.

You must respond ONLY with a valid JSON object. No explanation, no markdown, no extra text.
JSON format:
{
  "suspected_severity": "P1" | "P2" | "P3",
  "suspected_root_cause": "<service name>",
  "reasoning": "<1-2 sentence explanation>",
  "recommended_actions": ["<action_type>:<value>", ...],
  "confidence": "high" | "medium" | "low"
}

Action types available: classify_severity, identify_root_cause, escalate, remediate, request_more_logs, resolve, ignore
Action value examples:
  - classify_severity:P1
  - identify_root_cause:payment-service
  - escalate:backend-team
  - remediate:restart:payment-service
  - resolve:resolved
"""


def run_planner(observation: dict) -> dict:
    """
    Takes the initial observation from /reset and returns a triage strategy.

    Args:
        observation: dict from POST /reset response

    Returns:
        strategy: dict with suspected_severity, suspected_root_cause, recommended_actions, etc.
    """
    # Format the observation into a readable prompt
    logs = observation.get("logs", [])
    service_state = observation.get("service_state", [])
    incident_metadata = observation.get("incident_metadata", {})

    log_text = "\n".join([
        f"[{log.get('level', 'INFO')}] {log.get('service', 'unknown')}: {log.get('message', '')}"
        for log in logs[:20]  # first 20 logs max
    ])

    service_text = "\n".join([
        f"- {svc.get('name', 'unknown')}: status={svc.get('status', 'unknown')}, "
        f"error_rate={svc.get('error_rate', 0):.1%}, "
        f"latency_p99={svc.get('latency_p99_ms', 0)}ms"
        for svc in service_state
    ])

    prompt = f"""INCIDENT ALERT — Analyze and produce a triage strategy.

=== LOGS (most recent first) ===
{log_text}

=== SERVICE HEALTH ===
{service_text}

=== METADATA ===
Task: {incident_metadata.get('task_id', 'unknown')}
Step: 0 of {incident_metadata.get('max_steps', '?')}

Produce your triage strategy as JSON now:"""

    response = call_amd_llm(prompt=prompt, system_prompt=PLANNER_SYSTEM_PROMPT, temperature=0.1)

    # Parse JSON response
    try:
        # Strip any accidental markdown fences
        clean = response.strip().strip("```json").strip("```").strip()
        strategy = json.loads(clean)
    except json.JSONDecodeError:
        # Fallback strategy if LLM returns malformed JSON
        print(f"[PLANNER] Warning: Could not parse LLM response as JSON. Raw: {response[:200]}")
        strategy = {
            "suspected_severity": "P1",
            "suspected_root_cause": "unknown",
            "reasoning": "Could not parse planner response, defaulting to P1.",
            "recommended_actions": ["classify_severity:P1", "identify_root_cause:payment-service", "remediate:restart:payment-service", "resolve:resolved"],
            "confidence": "low"
        }

    print(f"[PLANNER] Strategy: severity={strategy.get('suspected_severity')}, "
          f"root_cause={strategy.get('suspected_root_cause')}, "
          f"confidence={strategy.get('confidence')}")
    return strategy


if __name__ == "__main__":
    # Quick test with a mock observation
    mock_obs = {
        "logs": [
            {"level": "FATAL", "service": "payment-service", "message": "NullPointerException in PaymentProcessor"},
            {"level": "ERROR", "service": "api-gateway", "message": "Upstream timeout: payment-service"},
            {"level": "ERROR", "service": "payment-service", "message": "Health check failed"},
        ],
        "service_state": [
            {"name": "payment-service", "status": "down", "error_rate": 1.0, "latency_p99_ms": 9999},
            {"name": "api-gateway", "status": "degraded", "error_rate": 0.8, "latency_p99_ms": 5000},
            {"name": "auth-service", "status": "up", "error_rate": 0.0, "latency_p99_ms": 120},
        ],
        "incident_metadata": {"task_id": "single_crash", "max_steps": 8}
    }
    strategy = run_planner(mock_obs)
    print("\nFull strategy:")
    print(json.dumps(strategy, indent=2))