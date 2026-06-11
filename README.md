# Marketing Campaign Budget Allocation under Budget, Risk, Reach, and Channel Interaction Constraints

## Chosen Pathway

Path B – Real Optimization Problem

This project focuses on solving a real marketing decision problem using optimization and heuristic search methods. The objective is to select a subset of marketing campaigns under limited budget, minimum reach, channel capacity, risk, and channel interaction constraints.

The final model combines a Genetic Algorithm, a Greedy ROI per Cost baseline, and a Linearized MILP benchmark solved with Gurobi.

---

## Problem Description

Companies often run many marketing campaigns across channels such as email, search advertising, social media, websites, and video platforms. Each campaign has a cost, expected return, reach contribution, risk level, and channel type.

The campaign selection problem is not only about choosing the campaigns with the highest ROI. A campaign may be costly, may fail to contribute enough reach, may increase risk, may exceed channel capacity, or may overlap with other selected campaigns. Therefore, campaign allocation is treated as a portfolio optimization problem.

This project develops a campaign budget allocation model that selects a feasible campaign portfolio while maximizing risk adjusted portfolio value. The model also includes channel based synergy and cannibalization effects to represent how selected campaigns interact with one another.

---

## Project Overview

The objective is to select the best subset of campaigns that maximizes total portfolio value while satisfying:

* budget constraint,
* minimum reach requirement,
* channel capacity limits,
* risk penalty,
* channel interaction effects.

The model uses binary campaign selection decisions:

```text
x_i = 1 if campaign i is selected
x_i = 0 otherwise
```

The final objective combines three components:

```text
portfolio value = risk adjusted campaign value + synergy value - cannibalization penalty
```

The project compares three main methods:

1. Linearized MILP benchmark
2. Genetic Algorithm
3. Greedy ROI per Cost baseline

Several additional greedy and random baseline methods were also implemented as supporting checks, but Greedy ROI per Cost is used as the main representative baseline because it was the strongest simple ranking method.

---

## Dataset

The project uses a marketing campaign dataset containing 200,000 campaign records. The dataset includes campaign level information such as cost, channel, impressions, conversion rate, engagement score, and performance indicators.

The full dataset is sampled into smaller experimental instances to make the optimization study computationally manageable. The tested instance sizes are:

```text
50, 100, 250, 500, and 1000 campaigns
```

The following variables are used in the model:

* Acquisition_Cost is used as campaign cost.
* Impressions is used as the reach proxy.
* Channel_Used is used as the campaign channel.
* ROI is used as the expected return measure.
* Risk is constructed as a proxy using normalized conversion rate and engagement score.

The risk proxy is defined so that campaigns with lower conversion rate and lower engagement score are treated as riskier.

---

## Mathematical Model

The campaign selection problem is formulated as a constrained binary portfolio optimization problem.

### Decision Variable

```text
x_i ∈ {0,1}
```

where:

```text
x_i = 1 if campaign i is selected
x_i = 0 otherwise
```

### Base Objective

The base campaign value is defined as:

```text
ROI_i - λ Risk_i
```

where `λ` controls the importance of risk in the objective.

### Final Objective

The final portfolio objective includes risk adjusted return and channel interaction effects:

```text
maximize risk adjusted return + synergy value - cannibalization penalty
```

### Key Constraints

Budget constraint:

```text
Σ Cost_i x_i ≤ B
```

Minimum reach constraint:

```text
Σ Reach_i x_i ≥ R_min
```

Channel capacity constraint:

```text
Σ x_i ≤ L_k for each channel k
```

These constraints ensure that the selected campaign portfolio respects budget limits, reaches enough audience, and avoids over selecting campaigns from the same channel.

---

## MDP Interpretation

The campaign allocation problem is also interpreted as a finite horizon Markov Decision Process.

Instead of selecting all campaigns at once, the decision maker evaluates campaigns sequentially. At each stage, the decision maker chooses whether to select or skip the current campaign.

The state includes:

* current campaign index,
* remaining budget,
* accumulated reach,
* channel usage counts.

The action is binary:

```text
1 = select the current campaign
0 = skip the current campaign
```

The transition updates the remaining budget, accumulated reach, and channel usage counts. The reward combines the campaign's risk adjusted value with channel based interaction effects.

This interpretation connects the portfolio selection problem to a sequential decision structure.

---

## Genetic Algorithm

A Genetic Algorithm is used as the main heuristic solution method.

Each chromosome is a binary vector:

```text
[x_1, x_2, ..., x_n]
```

Each gene represents whether a campaign is selected or not.

The Genetic Algorithm uses:

* binary chromosome encoding,
* population based search,
* tournament selection,
* uniform crossover,
* random mutation,
* elitism,
* repair function for budget and channel feasibility,
* fixed random seeds for reproducibility.

The repair function removes campaigns when crossover or mutation creates a solution that violates budget or channel capacity constraints.

The Genetic Algorithm is useful because the number of possible campaign portfolios grows exponentially with instance size.

---

## Linearized MILP Benchmark

A Linearized MILP benchmark is implemented to evaluate the quality of the Genetic Algorithm solutions.

The original channel interaction structure includes nonlinear count based terms. To solve the problem as a MILP, the nonlinear interaction terms are linearized using:

* channel count indicator variables,
* auxiliary coupling variables,
* linear count consistency constraints.

The MILP benchmark uses the same budget, reach, channel capacity, risk adjusted return, and channel interaction structure as the Genetic Algorithm.

Gurobi is used to solve the Linearized MILP model. When Gurobi reaches certified optimality, the MILP result is used as an optimal benchmark. When the solver reaches the time limit, the MILP result is interpreted as the best feasible incumbent found within the time limit.

---

## Experimental Design

The computational study uses 20 experimental runs. The design covers:

* five instance size levels,
* different budget levels,
* different risk penalty values,
* relaxed, moderate, and strict reach requirements,
* equal and specific channel capacity settings,
* no interaction, weak interaction, strong synergy, and strong cannibalization scenarios.

Runs 1 to 10 and Runs 11 to 20 follow the same scenario structure, but they use different sampled campaign subsets. This replicated design helps evaluate whether the results are consistent across different samples under the same scenario settings.

The instance sizes tested are:

```text
50, 100, 250, 500, and 1000 campaigns
```

A MILP time limit of 10 seconds is used for instances up to 250 campaigns, and 20 seconds is used for larger instances.

---

## Main Results

Across the 20 experimental runs:

* Linearized MILP achieved the highest average objective value: `2232.68`
* Genetic Algorithm achieved an average objective value of: `2108.96`
* Greedy ROI per Cost achieved an average objective value of: `1981.20`

The Linearized MILP benchmark reached certified optimality in 18 out of 20 runs. In these 18 certified optimal runs, the Genetic Algorithm achieved on average `98.56%` of the MILP optimum and matched the optimum exactly in 5 runs.

The Genetic Algorithm matched or outperformed Greedy ROI per Cost in all 20 runs.

The largest strong synergy scenarios were the most difficult cases for the MILP solver. Run 10 and Run 20 reached the MILP time limit, so their MILP values should be interpreted as incumbent solutions rather than certified optima.

---

## Output Files

The experiment script exports the following result files:

```text
ga_milp_20run_results.csv
ga_milp_20run_scenario_setup.csv
ga_vs_milp_20run_comparison.csv
ga_milp_20run_method_summary.csv
```

It also generates figures for objective values, runtime comparison, GA percentage of MILP benchmark, and MILP model size.

---

## Project Structure

```text
campaign-allocation-optimization/
│
├── data/
│   └── marketing_campaign_dataset.csv
│
├── outputs/
│   ├── ga_milp_20run_results.csv
│   ├── ga_milp_20run_scenario_setup.csv
│   ├── ga_vs_milp_20run_comparison.csv
│   ├── ga_milp_20run_method_summary.csv
│   └── figures/
│
├── reports/
│   └── Final_Report_Marketing_Campaign_Budget_Allocation.docx
│
├── run_ga_milp_20run_experiments.py
├── master_code_experiments.py
├── README.md
└── requirements.txt
```

---

## Requirements

To run this project, install the required Python packages:

```bash
pip install -r requirements.txt
```

The project requires:

```text
pandas
numpy
matplotlib
gurobipy
```

The Linearized MILP benchmark also requires Gurobi Optimizer with a valid license.

---

## How to Run

Install dependencies:

```bash
pip install -r requirements.txt
```

Run the main experiment script:

```bash
python run_ga_milp_20run_experiments.py
```

The script runs the 20 experimental scenarios, solves the Genetic Algorithm, Greedy ROI per Cost baseline, and Linearized MILP benchmark, then exports result tables and figures.

---

## Notes on Gurobi

The `gurobipy` package provides the Python interface for Gurobi. However, Gurobi Optimizer must also be installed and licensed separately.

To verify that Gurobi is correctly installed, run:

```bash
python -c "import gurobipy as gp; print(gp.gurobi.version())"
```

---

## Limitations

This project has several limitations:

* Interaction coefficients are scenario based rather than estimated from historical campaign interaction data.
* Risk is represented by a proxy using conversion and engagement metrics.
* The model uses binary campaign selection, while real firms may allocate partial budgets.
* The experiments use sampled instances instead of solving the full 200,000 record dataset directly.
* The Linearized MILP model becomes more computationally demanding in large strong synergy scenarios.
* ROI, cost, reach, and risk values are assumed to be known before optimization.

---

## Future Work

Future work can extend this project by:

* estimating channel interaction coefficients from historical campaign performance,
* adding stochastic reach, ROI, and conversion outcomes,
* allowing partial budget allocation,
* testing reinforcement learning or approximate dynamic programming methods,
* using hybrid Genetic Algorithm and MILP approaches,
* improving scalability with parallel Genetic Algorithm implementations,
* applying normalized or capped interaction functions for large instances.
