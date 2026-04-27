"""
Draft policy evaluation utilities for future MDP experiments.

The current project is solved mainly as a MILP. This file provides simple
heuristic policies that can later be compared against the MILP solution.
"""

from typing import Callable

from mdp import CampaignAllocationMDP, MDPState


Policy = Callable[[CampaignAllocationMDP, MDPState], int]


def greedy_risk_adjusted_policy(mdp: CampaignAllocationMDP, state: MDPState) -> int:
    """
    Select the campaign if it is feasible and has positive risk-adjusted reward.
    Otherwise, skip it.
    """
    feasible = mdp.feasible_actions(state)
    if 1 not in feasible:
        return 0

    return 1 if mdp.reward(state, 1) > 0 else 0


def always_skip_policy(mdp: CampaignAllocationMDP, state: MDPState) -> int:
    """Baseline policy that skips every campaign."""
    return 0


def evaluate_policy(mdp: CampaignAllocationMDP, policy: Policy) -> float:
    """Evaluate a deterministic policy over one full finite horizon episode."""
    state = mdp.initial_state()
    total_reward = 0.0

    while state.stage < mdp.horizon:
        action = policy(mdp, state)
        if action not in mdp.feasible_actions(state):
            action = 0

        total_reward += mdp.reward(state, action)
        state = mdp.transition(state, action)

    total_reward += mdp.terminal_value(state)
    return total_reward
