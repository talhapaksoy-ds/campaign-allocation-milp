# Week 8 MDP Notes

## Project Context

The original project solves a marketing campaign budget allocation problem as a Mixed Integer Linear Programming (MILP) model. The model selects a subset of marketing campaigns under budget, minimum reach, and channel capacity constraints while maximizing risk adjusted return.

For Week 8, the same problem is reinterpreted as a finite horizon Markov Decision Process (MDP). Instead of selecting all campaigns at once, the decision maker evaluates campaigns sequentially and decides whether to select or skip each campaign.

---

## Sequential Decision Interpretation

At each decision stage, one campaign is reviewed. The decision maker observes the current planning status and takes one action:

- select the current campaign, or
- skip the current campaign.

The decision affects the remaining budget, accumulated reach, and channel usage. Therefore, each action changes the feasibility of future decisions.

---

## State Space

A state at stage `t` is defined as:

```text
s_t = (t, b_t, r_t, n_1,t, n_2,t, ..., n_|K|,t)
```

where:

- `t` is the current campaign index or stage,
- `b_t` is the remaining budget,
- `r_t` is the accumulated reach,
- `n_k,t` is the number of selected campaigns from channel `k`,
- `K` is the set of marketing channels.

This state contains enough information to decide whether the next campaign can be selected feasibly.

---

## Action Space

At each state, the action is:

```text
a_t ∈ {0, 1}
```

where:

- `a_t = 1` means select campaign `t`,
- `a_t = 0` means skip campaign `t`.

The select action is feasible only if:

```text
Cost_t <= b_t
n_k(t),t + 1 <= L_k(t)
```

Skipping is always feasible.

---

## Transition Function

If the campaign is skipped:

```text
s_{t+1} = (t+1, b_t, r_t, n_1,t, ..., n_|K|,t)
```

If the campaign is selected:

```text
b_{t+1} = b_t - Cost_t
r_{t+1} = r_t + Reach_t
n_{k(t),t+1} = n_{k(t),t} + 1
```

All other channel counts remain unchanged.

---

## Reward Function

The immediate reward is based on the original MILP objective:

```text
R(s_t, a_t) = (ROI_t - lambda * Risk_t) * a_t
```

If the campaign is skipped, the immediate reward is zero.

A terminal penalty can be added if the final accumulated reach is below the required minimum reach.

---

## Policy

A policy is a rule that selects an action for every state:

```text
pi(s_t) = a_t
```

In this project, a policy decides whether the current campaign should be selected or skipped based on the remaining budget, accumulated reach, and channel usage.

---

## Bellman Recursion

The value function represents the best achievable future risk adjusted return from the current state onward:

```text
V_t(s_t) = max_{a_t in A(s_t)} [ (ROI_t - lambda * Risk_t) a_t + V_{t+1}(s_{t+1}) ]
```

The terminal value is:

```text
V_{T+1}(s_{T+1}) = 0    if accumulated reach >= minimum reach
V_{T+1}(s_{T+1}) = -M   otherwise
```

---

## MDP Type

The base formulation is:

- finite horizon,
- deterministic,
- fully observable,
- undiscounted.

A stochastic extension can be introduced by treating actual reach, ROI, or conversion rate as uncertain campaign outcomes.

---

## New Assumptions

The MDP interpretation introduces the following assumptions:

1. Campaigns are evaluated in a fixed sequence.
2. Campaign cost, ROI, reach, and risk are known before the action is selected.
3. The base model treats transitions as deterministic.
4. Minimum reach is handled through a terminal feasibility condition or terminal penalty.
5. Rewards are additive across selected campaigns.
