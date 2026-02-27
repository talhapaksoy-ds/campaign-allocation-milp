# Marketing Campaign Budget Allocation under Operational Constraints (MILP)

## Problem Overview
Companies must allocate a limited marketing budget across a set of candidate campaigns. Each campaign has a cost, an expected return (ROI), a risk score, an expected reach, and a channel label (e.g., Social, Search, TV, Email). The goal is to select an optimal portfolio of campaigns that maximizes risk-adjusted return while satisfying realistic operational constraints.

## Draft Mathematical Model
**Index**
- i = 1..n campaigns
- k channels

**Parameters**
- Cost_i: investment cost of campaign i
- ROI_i: expected return coefficient of campaign i
- Risk_i: risk score of campaign i
- Reach_i: expected reach of campaign i
- B: total available budget
- C_k: set of campaigns in channel k
- L_k: maximum number of campaigns allowed in channel k
- R_min: minimum total reach requirement
- λ (lambda): risk penalty parameter

**Decision variable**
- x_i ∈ {0,1}: 1 if campaign i is selected, 0 otherwise

**Objective (risk-adjusted)**
max  Σ(ROI_i * x_i)  -  λ Σ(Risk_i * x_i)

**Constraints**
- Budget:      Σ(Cost_i * x_i) ≤ B
- Channel cap: Σ_{i∈C_k} x_i ≤ L_k   for all k
- Reach:       Σ(Reach_i * x_i) ≥ R_min
- Binary:      x_i ∈ {0,1}

## Expected Method
This project will use **Mixed Integer Linear Programming (MILP)** due to binary selection decisions with linear objective and constraints. The model will be implemented in Python and solved using a MILP solver (Gurobi or PuLP).

## Data Plan
A synthetic dataset generator will be used to create realistic campaign attributes:
- n campaigns (e.g., 30/50/80)
- costs in a plausible range (e.g., 10k–200k)
- ROI coefficients and risk scores with controllable distributions
- channel labels with configurable proportions
- reach values to support a minimum reach constraint

If real data is later obtained, it can replace the synthetic generator without changing the model.

## Repository Structure
- `data/`: dataset files or links, and synthetic generator
- `src/`: model, solver, and experiment scripts
- `results/`: tables/plots/logs produced by experiments
