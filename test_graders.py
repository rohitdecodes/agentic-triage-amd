"""
Test script to verify graders score correctly.
Tests both correct answers (should score high) and wrong answers (should score low).
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from server.graders.crash_grader import CrashGrader
from server.graders.cascade_grader import CascadeGrader
from server.graders.silent_degrade_grader import SilentDegradeGrader


def make_mock_state(actions: list, task_id: str = "test", step_count: int = 4):
    """Create a mock EpisodeState-like object for testing."""
    class MockAction(dict):
        def __init__(self, action_type, value):
            super().__init__(action_type=action_type, value=value)
            self.action_type = action_type
            self.value = value

    class MockState:
        def __init__(self):
            self.task_id = task_id
            self.step_count = step_count
            self.action_history = [MockAction(a[0], a[1]) for a in actions]
            self.episode_id = "test-episode"

    return MockState()


def run_test(grader, test_name: str, actions: list, expected_range: tuple, is_correct: bool = None):
    """Run a single grader test and report pass/fail.
    
    Args:
        is_correct: None = unknown, True = agent should get high score, False = agent should get low score
    """
    state = make_mock_state(actions)
    score = grader.score(state)
    min_expected, max_expected = expected_range
    passed = min_expected <= score <= max_expected
    
    # Status indicators
    if not passed:
        status = "❌ GRADER_BUG"
    elif is_correct is True:
        status = "✅ CORRECT"  # Agent got it right
    elif is_correct is False:
        status = "✅ PENALIZED"  # Agent got it wrong, grader correctly penalized
    else:
        status = "✅ VALID"  # Score in expected range
    
    print(f"\n{status} — {test_name}")
    print(f"  Score: {score:.4f} (expected {min_expected}–{max_expected})")
    if not passed:
        print(f"  ⚠️  GRADER BUG: score outside expected range!")
    return passed


print("=" * 60)
print("GRADER CORRECTNESS TESTS")
print("=" * 60)

results = []

# ============================================================
# CRASH GRADER TESTS
# ============================================================
print("\n--- CrashGrader (Task 1: Single Crash) ---")
crash = CrashGrader()

# Test 1: Perfect correct answer
results.append(run_test(crash, "Perfect correct answer", [
    ("classify_severity", "P1"),
    ("identify_root_cause", "payment-service"),
    ("remediate", "restart:payment-service"),
    ("resolve", "resolved"),
], (0.95, 1.0), is_correct=True))

# Test 2: Wrong root cause (the bug we're fixing)
results.append(run_test(crash, "WRONG root cause (user-db instead of payment-service)", [
    ("classify_severity", "P1"),
    ("identify_root_cause", "user-db"),        # WRONG
    ("remediate", "restart:payment-service"),
    ("resolve", "resolved"),
], (0.40, 0.65), is_correct=False))  # should NOT get 1.0

# Test 3: Wrong severity
results.append(run_test(crash, "Wrong severity (P2 instead of P1)", [
    ("classify_severity", "P2"),               # WRONG
    ("identify_root_cause", "payment-service"),
    ("remediate", "restart:payment-service"),
    ("resolve", "resolved"),
], (0.55, 0.75), is_correct=False))

# Test 4: Wrong remediation command
results.append(run_test(crash, "Wrong remediation (kill-query instead of restart)", [
    ("classify_severity", "P1"),
    ("identify_root_cause", "payment-service"),
    ("remediate", "kill-query:payment-service"),  # WRONG command
    ("resolve", "resolved"),
], (0.55, 0.75), is_correct=False))

# Test 5: Completely wrong answers
results.append(run_test(crash, "All wrong answers", [
    ("classify_severity", "P3"),               # WRONG
    ("identify_root_cause", "auth-service"),   # WRONG
    ("remediate", "restart:auth-service"),     # WRONG
    ("resolve", "resolved"),
], (0.0001, 0.15), is_correct=False))

# ============================================================
# CASCADE GRADER TESTS
# ============================================================
print("\n--- CascadeGrader (Task 2: Cascading Failure) ---")
cascade = CascadeGrader()

# Test 1: Perfect correct answer
results.append(run_test(cascade, "Perfect correct answer", [
    ("classify_severity", "P1"),
    ("identify_root_cause", "user-db"),
    ("remediate", "kill-query:user-db"),
    ("resolve", "resolved"),
], (0.90, 1.0), is_correct=True))

# Test 2: THE MAIN BUG — wrong root cause (payment-service)
results.append(run_test(cascade, "WRONG root cause (payment-service — the bug)", [
    ("classify_severity", "P1"),
    ("identify_root_cause", "payment-service"),  # WRONG — this is what was scoring 1.0
    ("remediate", "restart:payment-service"),    # WRONG
    ("resolve", "resolved"),
], (0.0001, 0.35), is_correct=False))  # should be LOW, not 1.0

# Test 3: Symptom as root cause (api-gateway)
results.append(run_test(cascade, "Identified symptom as root cause (api-gateway)", [
    ("classify_severity", "P1"),
    ("identify_root_cause", "api-gateway"),    # SYMPTOM not root cause
    ("remediate", "restart:api-gateway"),
    ("resolve", "resolved"),
], (0.0001, 0.25), is_correct=False))

# Test 4: Correct root cause, wrong remediation command
results.append(run_test(cascade, "Correct root cause, wrong remediation target", [
    ("classify_severity", "P1"),
    ("identify_root_cause", "user-db"),
    ("remediate", "restart:api-gateway"),      # WRONG target
    ("resolve", "resolved"),
], (0.45, 0.65), is_correct=False))

# ============================================================
# SILENT DEGRADE GRADER TESTS
# ============================================================
print("\n--- SilentDegradeGrader (Task 3: Silent Degradation) ---")
silent = SilentDegradeGrader()

# Test 1: Perfect correct answer
results.append(run_test(silent, "Perfect correct answer", [
    ("classify_severity", "P2"),               # P2 not P1!
    ("identify_root_cause", "payment-db"),
    ("remediate", "flush-cache:payment-db"),
    ("resolve", "resolved"),
], (0.90, 1.0), is_correct=True))

# Test 2: THE MAIN BUG — P1 severity (what was scoring 1.0)
results.append(run_test(silent, "WRONG severity P1 instead of P2 (the bug)", [
    ("classify_severity", "P1"),               # WRONG — was scoring 1.0 before fix
    ("identify_root_cause", "payment-service"),# WRONG
    ("remediate", "restart:payment-service"),  # WRONG
    ("resolve", "resolved"),
], (0.0001, 0.20), is_correct=False))  # should be very low

# Test 3: Correct severity but wrong service (payment-service vs payment-db)
results.append(run_test(silent, "Confused payment-db with payment-service", [
    ("classify_severity", "P2"),
    ("identify_root_cause", "payment-service"),  # WRONG — db vs service
    ("remediate", "restart:payment-service"),    # WRONG command + wrong service
    ("resolve", "resolved"),
], (0.0001, 0.30), is_correct=False))

# Test 4: Right root cause, wrong remediation (restart instead of flush-cache)
results.append(run_test(silent, "Right root cause, wrong command (restart instead of flush-cache)", [
    ("classify_severity", "P2"),
    ("identify_root_cause", "payment-db"),
    ("remediate", "restart:payment-db"),       # WRONG — should flush-cache or kill-query
    ("resolve", "resolved"),
], (0.50, 0.70), is_correct=False))

# ============================================================
# SUMMARY
# ============================================================
print("\n" + "=" * 60)
print("TEST SUMMARY")
print("=" * 60)
passed = sum(results)
total = len(results)
print(f"Passed: {passed}/{total}")
if passed == total:
    print("✅ All tests passed — graders are working correctly")
    sys.exit(0)
else:
    print(f"❌ {total - passed} tests failed — grader bugs still present")
    print("Fix the failing graders and re-run this script.")
    sys.exit(1)
