"""
Draft MDP representation for the Marketing Campaign Budget Allocation project.

This file is a Week 8 planning artifact. It does not replace the MILP model.
It provides a simple sequential interpretation where campaigns are reviewed
one by one and the action is either select or skip.
"""

from dataclasses import dataclass
from typing import Dict, List, Tuple


@dataclass(frozen=True)
class Campaign:
    campaign_id: str
    channel: str
    cost: float
    roi: float
    risk: float
    reach: float


@dataclass(frozen=True)
class MDPState:
    stage: int
    remaining_budget: float
    accumulated_reach: float
    channel_usage: Tuple[Tuple[str, int], ...]

    def usage_dict(self) -> Dict[str, int]:
        """Return channel usage as a dictionary."""
        return dict(self.channel_usage)


class CampaignAllocationMDP:
    """Finite horizon MDP draft for sequential campaign selection."""

    def __init__(
        self,
        campaigns: List[Campaign],
        initial_budget: float,
        min_reach: float,
        channel_caps: Dict[str, int],
        risk_penalty: float = 1.0,
        terminal_penalty: float = 1_000_000.0,
    ) -> None:
        self.campaigns = campaigns
        self.initial_budget = initial_budget
        self.min_reach = min_reach
        self.channel_caps = channel_caps
        self.risk_penalty = risk_penalty
        self.terminal_penalty = terminal_penalty
        self.horizon = len(campaigns)

    def initial_state(self) -> MDPState:
        usage = tuple(sorted((channel, 0) for channel in self.channel_caps))
        return MDPState(
            stage=0,
            remaining_budget=self.initial_budget,
            accumulated_reach=0.0,
            channel_usage=usage,
        )

    def feasible_actions(self, state: MDPState) -> List[int]:
        """
        Return feasible actions from the current state.

        0 = skip current campaign
        1 = select current campaign
        """
        if state.stage >= self.horizon:
            return []

        campaign = self.campaigns[state.stage]
        usage = state.usage_dict()

        can_select = (
            campaign.cost <= state.remaining_budget
            and usage.get(campaign.channel, 0) + 1 <= self.channel_caps[campaign.channel]
        )

        return [0, 1] if can_select else [0]

    def reward(self, state: MDPState, action: int) -> float:
        """Immediate risk-adjusted reward from taking an action."""
        if state.stage >= self.horizon or action == 0:
            return 0.0

        campaign = self.campaigns[state.stage]
        return campaign.roi - self.risk_penalty * campaign.risk

    def transition(self, state: MDPState, action: int) -> MDPState:
        """Deterministic transition after selecting or skipping a campaign."""
        if state.stage >= self.horizon:
            return state

        campaign = self.campaigns[state.stage]
        usage = state.usage_dict()

        next_budget = state.remaining_budget
        next_reach = state.accumulated_reach

        if action == 1:
            next_budget -= campaign.cost
            next_reach += campaign.reach
            usage[campaign.channel] = usage.get(campaign.channel, 0) + 1

        return MDPState(
            stage=state.stage + 1,
            remaining_budget=next_budget,
            accumulated_reach=next_reach,
            channel_usage=tuple(sorted(usage.items())),
        )

    def terminal_value(self, state: MDPState) -> float:
        """Terminal feasibility value based on the minimum reach requirement."""
        if state.accumulated_reach >= self.min_reach:
            return 0.0
        return -self.terminal_penalty
