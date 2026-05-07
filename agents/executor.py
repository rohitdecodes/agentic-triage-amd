import json
import requests
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from amd_client import call_amd_llm


EXECUTOR_SYSTEM_PROMPT = """You are an SRE executing a live incident triage.
You have a strategy and you must take ONE action per step.

You must respond ONLY with a valid JSON object. No explanation, no markdown, no extra text.
JSON format:
{
  "action_type": "<one of the valid action types>",
  "value": "<appropriate value for the action type>",
  "confidence": <float 0.0 to 1.0>,
  "reasoning": "<one sentence max>"
}

Valid action_type values and their value formats:
  - classify_severity → value: "P1", "P2", or "P3"
  - identify_root_cause → value: service name e.g. "payment-service", "user-db"
  - escalate → value: team name e.g. "backend-team", "sre-team", "dba-team"
  - remediate → value: "command:service" e.g. "restart:payment-service", "kill-query:user-db", "flush-cache:payment-db"
  - request_more_logs → value: service name to get more logs from
  - resolve → value: "resolved"
  - ignore → value: "noise"

Rules:
  - Follow the strategy given to you
  - Do NOT repeat an action you already took
  - After remediating, always resolve
  - Never ignore a P1 incident
"""


def _format_step_prompt(observation: dict, strategy: dict, action_history: list, step: int) -> str:
    """Format the current state into a prompt for the executor."""
    logs = observation.get("logs", [])
    service_state = observation.get("service_state", [])
    reward = observation.get("reward", 0)

    log_text = "\n".join([
        f"[{log.get('level', 'INFO')}] {log.get('service', 'unknown')}: {log.get('message', '')}"
        for log in logs[-10:]  # last 10 logs
    ])

    service_text = "\n".join([
        f"- {svc.get('name', 'unknown')}: status={svc.get('status', 'unknown')}, "
        f"error_rate={svc.get('error_rate', 0):.1%}"
        for svc in service_state
    ])

    history_text = "\n".join([
        f"Step {i+1}: {a.get('action_type')}:{a.get('value')} (reward: {a.get('reward', '?')})"
        for i, a in enumerate(action_history)
    ]) or "No actions taken yet."

    return f"""=== CURRENT STEP: {step} ===

STRATEGY:
- Suspected severity: {strategy.get('suspected_severity')}
- Suspected root cause: {strategy.get('suspected_root_cause')}
- Confidence: {strategy.get('confidence')}

ACTIONS ALREADY TAKEN:
{history_text}

CURRENT LOGS:
{log_text}

CURRENT SERVICE HEALTH:
{service_text}

Last reward received: {reward}

What is your NEXT single action? Respond with JSON only:"""


def run_executor(
    strategy: dict,
    env_url: str = "http://localhost:7860",
    task_id: str = "single_crash",
    seed: int = 42
) -> dict:
    """
    Runs the full step loop for one episode.

    Args:
        strategy: output from run_planner()
        env_url: base URL of the FastAPI environment
        task_id: which task to run
        seed: episode seed for reproducibility

    Returns:
        result: dict with episode_id, task_id, actions, final_observation, total_steps
    """
    # Reset the environment
    reset_resp = requests.post(
        f"{env_url}/reset",
        json={"task_id": task_id, "seed": seed}
    )
    reset_resp.raise_for_status()
    observation = reset_resp.json()

    episode_id = observation.get("info", {}).get("episode_id", "unknown")
    max_steps = observation.get("incident_metadata", {}).get("max_steps", 10)

    print(f"\n[EXECUTOR] Starting episode {episode_id} — task={task_id}, max_steps={max_steps}")

    action_history = []
    done = False
    step = 0
    final_observation = observation

    while not done and step < max_steps:
        step += 1
        print(f"[EXECUTOR] Step {step}/{max_steps}...")

        # Ask LLM for next action
        prompt = _format_step_prompt(observation, strategy, action_history, step)
        response = call_amd_llm(
            prompt=prompt,
            system_prompt=EXECUTOR_SYSTEM_PROMPT,
            temperature=0.1
        )

        # Parse the action
        try:
            clean = response.strip().strip("```json").strip("```").strip()
            action = json.loads(clean)
        except json.JSONDecodeError:
            print(f"[EXECUTOR] Warning: Bad JSON on step {step}, using fallback action")
            action = {
                "action_type": "request_more_logs",
                "value": "system",
                "confidence": 0.5,
                "reasoning": "Fallback due to parse error"
            }

        print(f"[EXECUTOR] Action: {action.get('action_type')}:{action.get('value')} "
              f"(confidence={action.get('confidence', '?')})")

        # Send action to environment
        step_resp = requests.post(
            f"{env_url}/step",
            json={
                "action_type": action["action_type"],
                "value": action["value"],
                "confidence": action.get("confidence", 0.7),
                "reasoning": action.get("reasoning", "")
            }
        )
        step_resp.raise_for_status()
        observation = step_resp.json()

        reward = observation.get("reward", 0)
        done = observation.get("done", False)

        # Track action with its reward
        action["reward"] = reward
        action_history.append(action)

        print(f"[EXECUTOR] Reward: {reward:.3f} | Done: {done}")
        final_observation = observation

    print(f"[EXECUTOR] Episode complete. Steps used: {step}")

    return {
        "episode_id": episode_id,
        "task_id": task_id,
        "total_steps": step,
        "action_history": action_history,
        "final_observation": final_observation,
        "cumulative_score": sum(a.get("reward", 0) for a in action_history)
    }


if __name__ == "__main__":
    from agents.planner import run_planner
    import requests

    # First get initial observation
    reset = requests.post(
        "http://localhost:7860/reset",
        json={"task_id": "single_crash", "seed": 42}
    ).json()

    # Get strategy from planner
    strategy = run_planner(reset)

    # Run executor
    result = run_executor(strategy, task_id="single_crash", seed=42)
    print(f"\nEpisode result: {json.dumps(result, indent=2, default=str)}")