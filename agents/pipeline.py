import json
from typing import TypedDict, Optional
from langgraph.graph import StateGraph, END

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.planner import run_planner
from agents.executor import run_executor
from agents.summarizer import run_summarizer


# Define the shared state that flows through the graph
class TriageState(TypedDict):
    task_id: str
    seed: int
    env_url: str
    initial_observation: Optional[dict]
    strategy: Optional[dict]
    executor_result: Optional[dict]
    report: Optional[dict]
    error: Optional[str]


# Node 1: Planner
def planner_node(state: TriageState) -> TriageState:
    print(f"\n{'='*50}")
    print(f"[PIPELINE] Node 1: PLANNER — task={state['task_id']}")
    print(f"{'='*50}")
    try:
        strategy = run_planner(state["initial_observation"])
        return {**state, "strategy": strategy}
    except Exception as e:
        print(f"[PIPELINE] Planner error: {e}")
        return {**state, "error": str(e)}


# Node 2: Executor
def executor_node(state: TriageState) -> TriageState:
    print(f"\n{'='*50}")
    print(f"[PIPELINE] Node 2: EXECUTOR — task={state['task_id']}")
    print(f"{'='*50}")
    try:
        result = run_executor(
            strategy=state["strategy"],
            env_url=state["env_url"],
            task_id=state["task_id"],
            seed=state["seed"]
        )
        return {**state, "executor_result": result}
    except Exception as e:
        print(f"[PIPELINE] Executor error: {e}")
        return {**state, "error": str(e)}


# Node 3: Summarizer
def summarizer_node(state: TriageState) -> TriageState:
    print(f"\n{'='*50}")
    print(f"[PIPELINE] Node 3: SUMMARIZER — task={state['task_id']}")
    print(f"{'='*50}")
    try:
        report = run_summarizer(state["executor_result"])
        return {**state, "report": report}
    except Exception as e:
        print(f"[PIPELINE] Summarizer error: {e}")
        return {**state, "error": str(e)}


# Error check — routes to END if something went wrong
def should_continue(state: TriageState) -> str:
    if state.get("error"):
        print(f"[PIPELINE] Error detected, ending pipeline: {state['error']}")
        return "end"
    return "continue"


def build_pipeline() -> StateGraph:
    """Build and compile the LangGraph pipeline."""
    graph = StateGraph(TriageState)

    # Add nodes
    graph.add_node("planner", planner_node)
    graph.add_node("executor", executor_node)
    graph.add_node("summarizer", summarizer_node)

    # Set entry point
    graph.set_entry_point("planner")

    # Add edges with error checking
    graph.add_conditional_edges(
        "planner",
        should_continue,
        {"continue": "executor", "end": END}
    )
    graph.add_conditional_edges(
        "executor",
        should_continue,
        {"continue": "summarizer", "end": END}
    )
    graph.add_edge("summarizer", END)

    return graph.compile()


def run_pipeline(
    task_id: str,
    env_url: str = "http://localhost:7860",
    seed: int = 42
) -> dict:
    """
    Run the full triage pipeline for a single task.

    Returns the final state including the report and score.
    """
    import requests

    # Get initial observation from environment
    print(f"\n[PIPELINE] Resetting environment for task: {task_id}")
    reset_resp = requests.post(
        f"{env_url}/reset",
        json={"task_id": task_id, "seed": seed}
    )
    reset_resp.raise_for_status()
    initial_observation = reset_resp.json()

    # Set up initial state
    initial_state: TriageState = {
        "task_id": task_id,
        "seed": seed,
        "env_url": env_url,
        "initial_observation": initial_observation,
        "strategy": None,
        "executor_result": None,
        "report": None,
        "error": None
    }

    # Run the pipeline
    pipeline = build_pipeline()
    final_state = pipeline.invoke(initial_state)

    return final_state


if __name__ == "__main__":
    # Test the pipeline on single_crash
    result = run_pipeline(task_id="single_crash", seed=42)

    if result.get("report"):
        print("\n" + "="*50)
        print("FINAL REPORT:")
        print("="*50)
        print(json.dumps(result["report"], indent=2))
    elif result.get("error"):
        print(f"\nPipeline failed: {result['error']}")