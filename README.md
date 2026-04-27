# Marketing Campaign Budget Allocation under Operational Constraints (MILP)

## Chosen Pathway

Path B – Real Optimization Problem

This project focuses on solving a real decision-making problem using an optimization model. The objective is to determine which marketing campaigns should be selected under limited budget and operational constraints.

---

## Problem Description

Companies often run multiple marketing campaigns across channels such as social media, search advertising, email marketing, and television. Each campaign requires a certain investment and produces different levels of expected return and audience reach. Because marketing budgets are limited, managers must decide which campaigns should be selected to achieve the best overall outcome.

This project develops an optimization model that allocates a limited marketing budget across a set of campaigns. The model selects the combination of campaigns that maximizes expected return while satisfying constraints such as budget limits, minimum reach requirements, and channel restrictions.

## Project Overview

This project aims to optimize the allocation of a limited marketing budget across multiple campaigns. Each campaign is characterized by cost, expected return (ROI), risk, reach, and channel type.

The objective is to select an optimal subset of campaigns that maximizes risk-adjusted return while satisfying:

- Budget constraints
- Minimum reach requirement
- Channel capacity limits

The problem is formulated as a Mixed-Integer Linear Programming (MILP) model and solved using the Gurobi optimization solver.

---

## Week 8 Update: MDP Interpretation

For Week 8, the original static MILP model is reinterpreted as a finite horizon Markov Decision Process (MDP). Instead of selecting all campaigns at once, the campaign allocation problem is viewed as a sequential decision process where campaigns are evaluated one by one.

At each stage, the decision maker observes the current system state and decides whether to select or skip the current campaign. The state includes:

- current campaign index,
- remaining budget,
- accumulated reach,
- channel usage counts.

The action is binary:

- `1` = select the current campaign,
- `0` = skip the current campaign.

The transition updates the remaining budget, accumulated reach, and channel usage after each decision. The immediate reward is defined as the campaign's risk-adjusted return:

```text
reward = ROI - lambda * Risk
```

The MDP is modeled as deterministic, fully observable, finite horizon, and undiscounted in the base formulation. A future stochastic extension can model uncertain campaign reach, ROI, or conversion rate.

The detailed MDP formulation is provided in:

```text
mdp_notes.md
reports/Deliverable5.pdf
```

---

## Week 8/9 Planned Experiments

The next computational stage will test how the optimization model behaves under different operational scenarios. The planned experiments include:

### Parameters to Vary

- Instance size: 50, 100, 250, 500, and 1000 campaigns
- Budget level: low, medium, and high budget scenarios
- Risk penalty parameter: lambda values such as 0, 0.25, 0.50, 1.00, and 2.00
- Minimum reach requirement: relaxed, moderate, and strict reach targets
- Channel capacity limits: equal channel caps and channel-specific caps

### Performance Measures

The following outputs will be reported:

- objective value,
- total selected campaign count,
- total acquisition cost,
- total reach,
- selected channel distribution,
- average ROI of selected campaigns,
- average risk of selected campaigns,
- runtime,
- solver status,
- feasibility rate across scenarios.

### Baseline Comparisons

The MILP solution will be compared against simple heuristic baselines:

1. Greedy ROI baseline
2. Greedy risk-adjusted ROI baseline
3. Low-cost campaign selection baseline

These baselines will help evaluate whether the optimization model provides better portfolio decisions than simple ranking-based selection rules.

---

## New Assumptions Introduced by the MDP Reformulation

The MDP interpretation introduces several additional assumptions:

1. Campaigns are evaluated in a fixed sequence.
2. At each stage, the decision maker knows the current campaign's cost, ROI, reach, risk, and channel.
3. Remaining budget, accumulated reach, and channel usage are fully observable.
4. In the base MDP, transitions are deterministic.
5. Minimum reach is evaluated at the terminal stage through a feasibility condition or penalty.
6. Campaign rewards are additive and do not include interaction effects between campaigns.

---

## Project Structure

```text
campaign-allocation-milp/
│
├── data/
│   └── marketing_campaign_dataset.csv
│
├── reports/
│   └── Deliverable5.pdf
│
├── src/
│   ├── main.py
│   ├── model.py
│   ├── data_generator.py
│   ├── mdp.py
│   ├── dp.py
│   └── policy_evaluation.py
│
├── mdp_notes.md
├── README.md
└── requirements.txt
```

---

## Modeling Plan

The campaign selection problem is modeled as a Mixed Integer Linear Programming (MILP) problem.

### Decision Variable

```text
x_i ∈ {0,1}
```

where:

```text
x_i = 1 if campaign i is selected, otherwise 0
```

### Objective

Maximize the risk-adjusted return of the selected campaigns:

```text
max Σ(ROI_i * x_i) − λ Σ(Risk_i * x_i)
```

### Key Constraints

Budget constraint:

```text
Σ(Cost_i * x_i) ≤ B
```

Minimum reach constraint:

```text
Σ(Reach_i * x_i) ≥ R_min
```

Channel limit constraint:

```text
Σ(i ∈ C_k) x_i ≤ L_k
```

These constraints ensure that the selected campaign portfolio respects budget limits, achieves sufficient audience reach, and maintains a balanced distribution across marketing channels.

---

## Data

The project uses a marketing campaign dataset containing campaign-level information such as campaign type, marketing channel, cost, and performance indicators. These variables are used to derive the model parameters including campaign cost, expected return, risk, and reach.

If necessary, additional synthetic campaign records may be generated to test the model under different experimental scenarios.

---

## How to Run

Install the required packages:

```bash
pip install -r requirements.txt
```

Run the current optimization model:

```bash
python src/main.py
```

Review the Week 8 MDP formulation:

```bash
cat mdp_notes.md
```

Optional draft files for future MDP and dynamic programming extensions are located in `src/mdp.py`, `src/dp.py`, and `src/policy_evaluation.py`.
