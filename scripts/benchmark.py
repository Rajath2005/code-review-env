#!/usr/bin/env python3
"""
Multi-agent benchmark for code-review-env.

Evaluates 3 agents (weak/baseline/strong) across all 3 tasks
to demonstrate that the environment provides meaningful training signal.

Usage:
    python scripts/benchmark.py                    # Default: 10 episodes, seed 42
    python scripts/benchmark.py --num-episodes 5   # Run 5 episodes
    python scripts/benchmark.py --seed 99          # Use different seed
    python scripts/benchmark.py --json output.json # Save detailed results
"""

import argparse
import json
import random
import re
import sys
import os
from typing import Optional
from dataclasses import dataclass, asdict

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from server.environment import CodeReviewEnvironment, CodeReviewAction
from data.snippets import SNIPPETS


# ── Agent Definitions ─────────────────────────────────────────────────────────

class Agent:
    """Base class for benchmark agents."""
    
    def act(self, observation: dict) -> str:
        """Given an observation, return an action (response string)."""
        raise NotImplementedError
    
    @property
    def name(self) -> str:
        raise NotImplementedError


class WeakAgent(Agent):
    """Baseline: random/placeholder responses."""
    
    @property
    def name(self) -> str:
        return "Weak (Random)"
    
    def act(self, observation: dict) -> str:
        task = observation["task_name"]
        
        if task == "bug_identification":
            # Return common bug types at random
            return random.choice([
                "off-by-one error",
                "division by zero",
                "null pointer dereference",
                "infinite loop",
                "type error",
            ])
        elif task == "bug_fixing":
            # Return broken placeholder code
            return "def placeholder():\n    pass"
        else:  # full_review
            # Return minimal JSON
            return '{"bugs": [], "security_issues": [], "style_violations": []}'


class BaselineAgent(Agent):
    """Moderate: simple heuristic-based responses."""
    
    @property
    def name(self) -> str:
        return "Baseline (Heuristic)"
    
    def act(self, observation: dict) -> str:
        task = observation["task_name"]
        snippet = observation["code_snippet"]
        
        if task == "bug_identification":
            # Analyze code for common patterns
            if "range(len(" in snippet and "+ 1)" in snippet:
                return "off-by-one error"
            elif "/ " in snippet or "// " in snippet:
                return "division by zero"
            elif ".append" in snippet and "for " in snippet:
                return "mutating list while iterating"
            elif "None" in snippet and "[" in snippet:
                return "null pointer dereference"
            elif "while True" in snippet or "while 1" in snippet:
                return "infinite loop"
            else:
                return "logic error"
        
        elif task == "bug_fixing":
            # Attempt simple fixes based on pattern detection
            if "range(len(" in snippet and "+ 1)" in snippet:
                # off-by-one: remove + 1
                return snippet.replace("range(len(", "range(len(").replace("+ 1)", ")")
            elif "while True" in snippet:
                # infinite loop: try to add break
                lines = snippet.split("\n")
                for i, line in enumerate(lines):
                    if "while True" in line:
                        lines.insert(i + 2, "            break")
                        break
                return "\n".join(lines)
            else:
                # Return original (might pass some tests)
                return snippet
        
        else:  # full_review
            # Minimal review
            return json.dumps({
                "bugs": [{"line": 1, "severity": "high", "description": "Possible bug detected"}],
                "security_issues": [],
                "style_violations": [],
            })


class StrongAgent(Agent):
    """Strong: LLM-like responses (simulated with domain rules)."""
    
    @property
    def name(self) -> str:
        return "Strong (LLM-like)"
    
    def act(self, observation: dict) -> str:
        task = observation["task_name"]
        snippet = observation["code_snippet"]
        
        if task == "bug_identification":
            return self._identify_bug(snippet)
        elif task == "bug_fixing":
            return self._fix_code(snippet)
        else:  # full_review
            return self._full_review(snippet)
    
    def _identify_bug(self, snippet: str) -> str:
        """Extract likely bug from code analysis."""
        # Check snippet ID if available (simple pattern matching)
        snippet_lower = snippet.lower()
        
        patterns = {
            "off-by-one error": [r"range\(len\([^)]+\)\s*\+\s*1\)"],
            "division by zero": [r"/\s*", r"//\s*"],
            "infinite recursion": [r"def\s+\w+\(.*\):.*\1\("],
            "infinite loop": [r"while\s*(?:True|1)", r"while\s*1:"],
            "null pointer dereference": [r"\[.*?\]\s*\.", r"\..*?\[0\]"],
            "wrong initial value": [r"=\s*1\s*#.*total", r"sum\s*=\s*[^0]"],
            "command injection": [r"os\.system\(", r"subprocess\.call\("],
            "resource leak": [r"open\(", r"\.read\(\)"],
            "mutating list while iterating": [r"\.remove\(", r"\.pop\(.*for"],
            "type error": [r"str\(.*\)\s*\+\s*\d", r"\d\s*\+\s*str\("],
        }
        
        for bug_type, patterns_list in patterns.items():
            for pattern in patterns_list:
                if re.search(pattern, snippet):
                    return bug_type
        
        return "logic error"  # Fallback
    
    def _fix_code(self, snippet: str) -> str:
        """Attempt to fix common bugs."""
        result = snippet
        
        # Fix off-by-one
        result = re.sub(r"range\(len\(([^)]+)\)\s*\+\s*1\)", r"range(len(\1))", result)
        
        # Fix division by zero (add check)
        if re.search(r"(/|//)\s*[a-zA-Z_]", result):
            result = result.replace("return", "if denominator != 0: return")
        
        # Fix infinite recursion by limiting depth (simple heuristic)
        if re.search(r"def\s+\w+\([^)]*\):", result):
            result = re.sub(r"(\s+)([a-zA-Z_]\w*)\(", r"\1if depth < 100: \2(", result)
        
        return result
    
    def _full_review(self, snippet: str) -> str:
        """Generate structured review."""
        bugs = []
        security_issues = []
        style = []
        
        lines = snippet.split("\n")
        
        # Detect bugs
        if "range(len(" in snippet and "+ 1)" in snippet:
            bugs.append({"line": 3, "severity": "high", "description": "off-by-one error: range(len()+1) causes IndexError"})
        
        # Detect security issues
        if "os.system" in snippet or "subprocess" in snippet:
            security_issues.append({"line": 1, "severity": "high", "description": "potential command injection vulnerability"})
        
        if "eval(" in snippet:
            security_issues.append({"line": 1, "severity": "high", "description": "eval() is unsafe, use alternatives"})
        
        # Detect style issues
        if "for i in range(len(" in snippet:
            style.append({"line": 1, "severity": "low", "description": "use enumerate() instead of manual indexing"})
        
        if "while True:" in snippet:
            style.append({"line": 1, "severity": "low", "description": "consider using a clearer loop condition"})
        
        return json.dumps({
            "bugs": bugs,
            "security_issues": security_issues,
            "style_violations": style,
        })


class GoldAgent(Agent):
    """Oracle agent: always returns correct answer (proves graders work)."""
    
    @property
    def name(self) -> str:
        return "Gold (Oracle)"
    
    def act(self, observation: dict) -> str:
        task = observation["task_name"]
        # We need to find which snippet this is - look for matching code
        code = observation["code_snippet"]
        
        # Find the snippet by matching code
        matching_snippet = None
        for snippet in SNIPPETS:
            if snippet["code"] == code:
                matching_snippet = snippet
                break
        
        if not matching_snippet:
            return "unknown error"  # Fallback
        
        if task == "bug_identification":
            return matching_snippet["bug_type"]
        elif task == "bug_fixing":
            return matching_snippet["fixed_code"]
        else:  # full_review
            return json.dumps(matching_snippet["review"])


# ── Evaluation ────────────────────────────────────────────────────────────────

@dataclass
class EpisodeResult:
    """Result of one episode."""
    agent_name: str
    task_name: str
    snippet_id: int
    reward: float
    done: bool
    step_count: int


@dataclass
class AgentMetrics:
    """Summary metrics for one agent across all episodes."""
    agent_name: str
    num_episodes: int
    easy_avg: float
    medium_avg: float
    hard_avg: float
    overall_avg: float
    easy_completed: int
    medium_completed: int
    hard_completed: int


def run_episode(
    agent: Agent,
    env: CodeReviewEnvironment,
    task_name: str,
) -> EpisodeResult:
    """Run one episode with the given agent."""
    obs = env.reset(task_name=task_name)
    
    step_count = 0
    for step in range(5):  # max 5 steps
        step_count += 1
        
        try:
            # Convert Pydantic model to dict for agent
            obs_dict = {
                "code_snippet": obs.code_snippet,
                "task_name": obs.task_name,
                "instructions": obs.instructions,
                "feedback": obs.feedback,
                "reward": obs.reward,
                "done": obs.done,
            }
            action_str = agent.act(obs_dict)
            action = CodeReviewAction(response=action_str)
            obs = env.step(action)
        except Exception as e:
            # Agent error -> episode fails
            obs.reward = 0.0
            obs.done = True
            break
        
        if obs.done:
            break
    
    return EpisodeResult(
        agent_name=agent.name,
        task_name=task_name,
        snippet_id=env._state.snippet_id,
        reward=obs.reward,
        done=obs.done,
        step_count=step_count,
    )


def benchmark_agent(
    agent: Agent,
    num_episodes: int,
    seed: int,
) -> tuple[list[EpisodeResult], AgentMetrics]:
    """Benchmark a single agent across all tasks."""
    results = []
    
    # Run episodes with fixed seed
    random.seed(seed)
    
    for task in ["bug_identification", "bug_fixing", "full_review"]:
        env = CodeReviewEnvironment(seed=seed)
        
        for ep in range(num_episodes):
            result = run_episode(agent, env, task)
            results.append(result)
    
    # Compute metrics
    easy_rewards = [r.reward for r in results if r.task_name == "bug_identification"]
    medium_rewards = [r.reward for r in results if r.task_name == "bug_fixing"]
    hard_rewards = [r.reward for r in results if r.task_name == "full_review"]
    
    metrics = AgentMetrics(
        agent_name=agent.name,
        num_episodes=num_episodes,
        easy_avg=round(sum(easy_rewards) / len(easy_rewards), 3) if easy_rewards else 0.0,
        medium_avg=round(sum(medium_rewards) / len(medium_rewards), 3) if medium_rewards else 0.0,
        hard_avg=round(sum(hard_rewards) / len(hard_rewards), 3) if hard_rewards else 0.0,
        overall_avg=round(sum(easy_rewards + medium_rewards + hard_rewards) / len(results), 3) if results else 0.0,
        easy_completed=sum(1 for r in results if r.task_name == "bug_identification" and r.done),
        medium_completed=sum(1 for r in results if r.task_name == "bug_fixing" and r.done),
        hard_completed=sum(1 for r in results if r.task_name == "full_review" and r.done),
    )
    
    return results, metrics


def print_benchmark_table(all_metrics: list[AgentMetrics]) -> None:
    """Print results as formatted table."""
    print("\n" + "="*100)
    print("CODE REVIEW ENVIRONMENT — BENCHMARK RESULTS")
    print("="*100)
    
    print(f"\n{'Agent':<25} {'Easy':<12} {'Medium':<12} {'Hard':<12} {'Overall':<12}")
    print("-" * 100)
    
    for metrics in all_metrics:
        print(
            f"{metrics.agent_name:<25} "
            f"{metrics.easy_avg:<12.3f} "
            f"{metrics.medium_avg:<12.3f} "
            f"{metrics.hard_avg:<12.3f} "
            f"{metrics.overall_avg:<12.3f}"
        )
    
    print("\n" + "="*100)
    print("Task Completion Rates")
    print("="*100)
    
    print(f"\n{'Agent':<25} {'Easy':<15} {'Medium':<15} {'Hard':<15}")
    print("-" * 100)
    
    for metrics in all_metrics:
        print(
            f"{metrics.agent_name:<25} "
            f"{metrics.easy_completed}/{metrics.num_episodes:<13} "
            f"{metrics.medium_completed}/{metrics.num_episodes:<13} "
            f"{metrics.hard_completed}/{metrics.num_episodes:<13}"
        )
    
    print("\n" + "="*100 + "\n")


# ── CLI ───────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Benchmark code-review-env with multiple agents.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/benchmark.py                     # Run with defaults (seed=42, 10 episodes)
  python scripts/benchmark.py --num-episodes 5    # Run 5 episodes per task
  python scripts/benchmark.py --seed 99           # Use different seed
  python scripts/benchmark.py --json results.json # Save detailed results
        """
    )
    
    parser.add_argument(
        "--num-episodes",
        type=int,
        default=10,
        help="Number of episodes per task (default: 10)"
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for reproducibility (default: 42)"
    )
    parser.add_argument(
        "--json",
        dest="json_output",
        type=str,
        default=None,
        help="Save detailed results to JSON file"
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress table output"
    )
    
    args = parser.parse_args()
    
    # Define agents
    agents = [
        WeakAgent(),
        BaselineAgent(),
        StrongAgent(),
        GoldAgent(),  # Oracle: proves graders work correctly
    ]
    
    print(f"\n🚀 Starting benchmark with seed={args.seed}, episodes/task={args.num_episodes}\n")
    
    all_metrics = []
    all_results = []
    
    for agent in agents:
        print(f"📊 Benchmarking {agent.name}...")
        results, metrics = benchmark_agent(agent, args.num_episodes, args.seed)
        
        all_metrics.append(metrics)
        all_results.extend(results)
        
        print(f"   ✅ {agent.name}: {metrics.overall_avg:.3f} avg reward")
    
    # Print table
    if not args.quiet:
        print_benchmark_table(all_metrics)
    
    # Save JSON if requested
    if args.json_output:
        output = {
            "metadata": {
                "seed": args.seed,
                "num_episodes": args.num_episodes,
                "num_agents": len(agents),
            },
            "metrics": [asdict(m) for m in all_metrics],
            "episodes": [asdict(r) for r in all_results],
        }
        
        with open(args.json_output, "w") as f:
            json.dump(output, f, indent=2)
        
        print(f"💾 Results saved to {args.json_output}")
    
    # Exit with success
    print("✅ Benchmark complete!\n")


if __name__ == "__main__":
    main()
