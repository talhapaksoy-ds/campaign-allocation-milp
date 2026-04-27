"""
Draft dynamic programming recursion for the Week 8 MDP interpretation.

This file demonstrates how the Bellman recursion could be implemented for
small campaign instances. It is intended as a draft extension, not as the main
solver for the project.
"""

from functools import lru_cache
from typing import Dict, List, Tuple

from mdp import Campaign, CampaignAllocationMDP, MDPState


def bellman_value(mdp: CampaignAllocationMDP, state: MDPState) -> float:
    """Compute the optimal value from a state using recursive DP."""

    @lru_cache(maxsize=None)
    def value_cached(
        stage: int,
        remaining_budget: float,
        accumulated_reach: float,
        channel_usage: Tuple[Tuple[str, int], ...],
    ) -> float:
        current_state = MDPState(
            stage=stage,
            remaining_budget=remaining_budget,
            accumulated_reach=accumulated_reach,
            channel_usage=channel_usage,
        )

        if current_state.stage >= mdp.horizon:
            return mdp.terminal_value(current_state)

        best_value = float("-inf")
        for action in mdp.feasible_actions(current_state):
            next_state = mdp.transition(current_state, action)
            candidate_value = mdp.reward(current_state, action) + value_cached(
                next_state.stage,
                next_state.remaining_budget,
                next_state.accumulated_reach,
                next_state.channel_usage,
            )
            best_value = max(best_value, candidate_value)

        return best_value

    return value_cached(
        state.stage,
        state.remaining_budget,
        state.accumulated_reach,
        state.channel_usage,
    )


def small_example() -> None:
    """Run a very small example for checking the MDP logic."""
    campaigns: List[Campaign] = [
        Campaign("C1", "Social", cost=60, roi=20, risk=4, reach=80),
        Campaign("C2", "Social", cost=50, roi=18, risk=2, reach=70),
    ]

    mdp = CampaignAllocationMDP(
        campaigns=campaigns,
        initial_budget=100,
        min_reach=120,
        channel_caps={"Social": 1},
        risk_penalty=1.0,
    )

    initial_state = mdp.initial_state()
    optimal_value = bellman_value(mdp, initial_state)
    print(f"Optimal value from initial state: {optimal_value}")


if __name__ == "__main__":
    small_example()
