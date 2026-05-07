"""
Grader registry and scoring interface.
"""
from server.graders.crash_grader import CrashGrader
from server.graders.cascade_grader import CascadeGrader
from server.graders.silent_degrade_grader import SilentDegradeGrader
from server.models import EpisodeState


# Grader instances
_graders = {
    "single_crash": CrashGrader(),
    "cascading_failure": CascadeGrader(),
    "silent_degradation": SilentDegradeGrader(),
}


def score_episode(task_id: str, state: EpisodeState) -> dict:
    """
    Score a completed episode using the appropriate grader.
    
    Args:
        task_id: The task identifier (single_crash, cascading_failure, silent_degradation)
        state: The completed EpisodeState
        
    Returns:
        dict with 'score' (float) and 'breakdown' (dict)
    """
    if task_id not in _graders:
        raise ValueError(f"Unknown task: {task_id}. Must be one of {list(_graders.keys())}")
    
    grader = _graders[task_id]
    score = grader.score(state)
    breakdown = grader.get_breakdown()
    
    return {
        "task_id": task_id,
        "score": score,
        "breakdown": breakdown,
    }


def get_grader(task_id: str):
    """Get the grader instance for a task."""
    if task_id not in _graders:
        raise ValueError(f"Unknown task: {task_id}")
    return _graders[task_id]
