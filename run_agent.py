import json
import time
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from agents.pipeline import run_pipeline

ENV_URL = f"http://{os.environ.get('ENV_HOST', 'localhost')}:{os.environ.get('ENV_PORT', '7860')}"
SEED = 42

TASKS = [
    "single_crash",
    "cascading_failure",
    "silent_degradation"
]


def main():
    print("\n" + "="*60)
    print("  AgentTriage — AMD Developer Cloud Hackathon")
    print("  Multi-Agent SRE Incident Triage Pipeline")
    print("="*60)

    results = {}
    reports = {}

    for task_id in TASKS:
        print(f"\n{'='*60}")
        print(f"  RUNNING TASK: {task_id.upper()}")
        print(f"{'='*60}")

        start_time = time.time()

        try:
            final_state = run_pipeline(
                task_id=task_id,
                env_url=ENV_URL,
                seed=SEED
            )

            elapsed = time.time() - start_time

            if final_state.get("executor_result"):
                score = final_state["executor_result"]["cumulative_score"]
                steps = final_state["executor_result"]["total_steps"]
                results[task_id] = {
                    "score": round(score, 4),
                    "steps": steps,
                    "time_seconds": round(elapsed, 1),
                    "status": "completed"
                }
            else:
                results[task_id] = {
                    "score": 0.0,
                    "steps": 0,
                    "time_seconds": round(elapsed, 1),
                    "status": f"error: {final_state.get('error', 'unknown')}"
                }

            if final_state.get("report"):
                reports[task_id] = final_state["report"]

        except Exception as e:
            results[task_id] = {
                "score": 0.0,
                "steps": 0,
                "time_seconds": 0,
                "status": f"exception: {str(e)}"
            }
            print(f"[run_agent] Exception on {task_id}: {e}")

        # Small delay between tasks
        time.sleep(2)

    # Print final score table
    print("\n" + "="*60)
    print("  FINAL RESULTS")
    print("="*60)
    print(f"{'Task':<25} {'Score':>8} {'Steps':>7} {'Time':>8} {'Status'}")
    print("-"*60)

    total_score = 0
    for task_id, r in results.items():
        print(
            f"{task_id:<25} {r['score']:>8.4f} {r['steps']:>7} "
            f"{r['time_seconds']:>7.1f}s  {r['status']}"
        )
        total_score += r["score"]

    avg_score = total_score / len(TASKS)
    print("-"*60)
    print(f"{'AVERAGE':<25} {avg_score:>8.4f}")
    print("="*60)

    # Save results to file
    output = {
        "results": results,
        "average_score": round(avg_score, 4),
        "reports": reports
    }
    with open("results.json", "w") as f:
        json.dump(output, f, indent=2)

    print(f"\nResults saved to results.json")

    # Print one sample report
    if reports:
        first_task = list(reports.keys())[0]
        print(f"\nSample Report ({first_task}):")
        print(json.dumps(reports[first_task], indent=2))


if __name__ == "__main__":
    main()