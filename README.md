# Marketing Campaign Budget Allocation under Operational Constraints (MILP)

## Chosen Pathway
**Path B – Real Optimization Problem**

This project focuses on solving a real decision-making problem using an optimization model. The objective is to determine which marketing campaigns should be selected under limited budget and operational constraints.

---

## Problem Description

Companies often run multiple marketing campaigns across channels such as social media, search advertising, email marketing, and television. Each campaign requires a certain investment and produces different levels of expected return and audience reach. Because marketing budgets are limited, managers must decide which campaigns should be selected to achieve the best overall outcome.

This project develops an optimization model that allocates a limited marketing budget across a set of campaigns. The model selects the combination of campaigns that maximizes expected return while satisfying constraints such as budget limits, minimum reach requirements, and channel restrictions.

## Project Overview
This project aims to optimize the allocation of a limited marketing budget across multiple campaigns. Each campaign is characterized by cost, expected return (ROI), risk, reach, and channel type.

The objective is to select an optimal subset of campaigns that maximizes **risk-adjusted return** while satisfying:
- Budget constraints
- Minimum reach requirement
- Channel capacity limits

The problem is formulated as a **Mixed-Integer Linear Programming (MILP)** model and solved using the Gurobi optimization solver.

---

## Project Structure

src/
- main.py → runs the model and prints results  
- model.py → builds and solves the optimization model  
- data_generator.py → creates the test dataset  

outputs/
- test_output.txt → example solver output  

---

## Modeling Plan

The campaign selection problem will be modeled as a **Mixed Integer Linear Programming (MILP)** problem.

### Decision Variable
- x_i ∈ {0,1}  
- x_i = 1 if campaign i is selected, otherwise 0

### Objective
Maximize the risk-adjusted return of the selected campaigns:

max Σ(ROI_i * x_i) − λ Σ(Risk_i * x_i)

### Key Constraints

Budget constraint

Σ(Cost_i * x_i) ≤ B

Minimum reach constraint

Σ(Reach_i * x_i) ≥ R_min

Channel limit constraint

Σ(i ∈ C_k) x_i ≤ L_k

These constraints ensure that the selected campaign portfolio respects budget limits, achieves sufficient audience reach, and maintains a balanced distribution across marketing channels.

---

## Data

The project uses a marketing campaign dataset containing campaign-level information such as campaign type, marketing channel, cost, and performance indicators. These variables are used to derive the model parameters including campaign cost, expected return, and reach.

If necessary, additional synthetic campaign records may be generated to test the model under different experimental scenarios.

---

## Repository Structure

campaign-allocation-milp

data/  
    README.md
    marketing_campaign_dataset.csv  

src/  
    data.py  
    how_to_run.txt
    main.py  
    model.py
    test_output

README.md  
requirements.txt      

data/ contains the dataset used in the optimization model.  
src/ contains the optimization model and solver scripts.

