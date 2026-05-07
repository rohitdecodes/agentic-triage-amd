import json
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from amd_client import call_amd_llm


SUMMARIZER_SYSTEM_PROMPT = """You are a technical writer producing a post-incident report for an SRE team.
You will receive a complete incident triage episode: the actions taken, rewards received, and final state.

You must respond ONLY with a valid JSON object. No explanation, no markdown, no extra text.
JSON format:
{
  "incident_title": "<short title>",
  "severity": "P1" | "P2" | "P3",
  "root_cause": "<identified service>",
  "timeline": [
    {"step": 1, "action": "<action taken>", "outcome": "<what happened>"}
  ],
  "resolution": "<what was done to fix it>",
  "score": <float>,
  "lessons_learned": "<1-2 sentences>",
  "escalated_to": "<team name or null>"
}
"""


def run_summarizer(executor_result: dict) -> dict:
    """
    Takes the executor result and generates a structured incident report.

    Args:
        executor_result: dict output from run_executor()

    Returns:
        report: dict with incident_title, severity, root_cause, timeline, etc.
    """
    task_id = executor_result.get("task_id", "unknown")
    action_history = executor_result.get("action_history", [])
    total_steps = executor_result.get("total_steps", 0)
    cumulative_score = executor_result.get("cumulative_score", 0)

    # Format action history for prompt
    actions_text = "\n".join([
        f"Step {i+1}: action={a.get('action_type')}, value={a.get('value')}, "
        f"reward={a.get('reward', 0):.3f}, reasoning={a.get('reasoning', 'N/A')}"
        for i, a in enumerate(action_history)
    ])

    prompt = f"""Generate a post-incident report for this completed triage episode.

=== EPISODE DETAILS ===
Task: {task_id}
Total steps used: {total_steps}
Cumulative score: {cumulative_score:.4f}

=== ACTIONS TAKEN ===
{actions_text}

Produce the incident report as JSON now:"""

    response = call_amd_llm(
        prompt=prompt,
        system_prompt=SUMMARIZER_SYSTEM_PROMPT,
        temperature=0.2
    )

    try:
        clean = response.strip().strip("```json").strip("```").strip()
        report = json.loads(clean)
    except json.JSONDecodeError:
        print(f"[SUMMARIZER] Warning: Could not parse report JSON. Raw: {response[:200]}")
        report = {
            "incident_title": f"Incident Triage — {task_id}",
            "severity": "P1",
            "root_cause": "unknown",
            "timeline": [],
            "resolution": "Episode completed",
            "score": cumulative_score,
            "lessons_learned": "Report generation failed — check LLM output.",
            "escalated_to": None
        }

    # Always inject the actual score from the environment
    report["score"] = cumulative_score
    report["task_id"] = task_id
    report["steps_used"] = total_steps

    print(f"[SUMMARIZER] Report generated: {report.get('incident_title')}")
    print(f"[SUMMARIZER] Score: {cumulative_score:.4f} | Root cause: {report.get('root_cause')}")

    return report


if __name__ == "__main__":
    # Test with a mock executor result
    mock_result = {
        "task_id": "single_crash",
        "total_steps": 4,
        "cumulative_score": 0.95,
        "action_history": [
            {"action_type": "classify_severity", "value": "P1", "reward": 0.30, "reasoning": "100% error rate"},
            {"action_type": "identify_root_cause", "value": "payment-service", "reward": 0.35, "reasoning": "FATAL logs"},
            {"action_type": "remediate", "value": "restart:payment-service", "reward": 0.25, "reasoning": "Standard restart"},
            {"action_type": "resolve", "value": "resolved", "reward": 0.10, "reasoning": "Done"},
        ],
        "final_observation": {}
    }

    report = run_summarizer(mock_result)
    print("\nFull report:")
    print(json.dumps(report, indent=2))