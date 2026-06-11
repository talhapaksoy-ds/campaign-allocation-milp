"""
Marketing Campaign Budget Allocation Experiment Script

Final project version:
- 20 experimental runs with two replicates of the same scenario structure
- Genetic Algorithm as the main heuristic method
- Greedy ROI per Cost as the representative greedy baseline
- Linearized MILP benchmark solved with Gurobi

Expected input file:
    data/marketing_campaign_dataset.csv

Main outputs:
    outputs/ga_milp_20run_results.csv
    outputs/ga_milp_20run_scenario_setup.csv
    outputs/ga_vs_milp_20run_comparison.csv
    outputs/ga_milp_20run_method_summary.csv
    outputs/figures/figure_objective_ga_milp_greedy_20runs.png
    outputs/figures/figure_runtime_ga_milp_greedy_20runs.png
    outputs/figures/figure_ga_pct_of_milp_optimal_runs.png
    outputs/figures/figure_milp_model_size_20runs.png
"""

from __future__ import annotations

import math
import random
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Tuple, Optional

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

try:
    import gurobipy as gp
    from gurobipy import GRB
except ImportError:
    gp = None
    GRB = None


RANDOM_SEED = 42
TERMINAL_PENALTY = 3000.0


@dataclass(frozen=True)
class Scenario:
    run_id: int
    base_run_id: int
    replicate: int
    instance_size: int
    budget_level: str
    budget_pct: float
    lambda_risk: float
    reach_level: str
    reach_pct: float
    cap_type: str
    interaction_scenario: str


BASE_SCENARIOS = [
    (1, 50, "Low", 0.05, 0.00, "Relaxed", 0.03, "Equal", "No interaction"),
    (2, 50, "Medium", 0.10, 0.25, "Moderate", 0.05, "Equal", "Weak interaction"),
    (3, 100, "Low", 0.05, 0.50, "Moderate", 0.05, "Specific", "Weak interaction"),
    (4, 100, "Medium", 0.10, 1.00, "Strict", 0.08, "Specific", "Strong cannibalization"),
    (5, 250, "Medium", 0.10, 0.50, "Moderate", 0.05, "Equal", "Strong synergy"),
    (6, 250, "High", 0.20, 1.00, "Strict", 0.08, "Specific", "Strong cannibalization"),
    (7, 500, "Low", 0.05, 1.00, "Relaxed", 0.03, "Equal", "Strong cannibalization"),
    (8, 500, "Medium", 0.10, 2.00, "Moderate", 0.05, "Specific", "Strong synergy"),
    (9, 1000, "Medium", 0.10, 0.25, "Moderate", 0.05, "Equal", "Weak interaction"),
    (10, 1000, "High", 0.20, 2.00, "Strict", 0.08, "Specific", "Strong synergy"),
]


def build_scenarios() -> List[Scenario]:
    """Build the final 20 run replicated scenario design."""
    scenarios: List[Scenario] = []

    for replicate in [1, 2]:
        for base_run_id, size, budget_level, budget_pct, lam, reach_level, reach_pct, cap_type, interaction in BASE_SCENARIOS:
            run_id = base_run_id if replicate == 1 else base_run_id + 10
            scenarios.append(
                Scenario(
                    run_id=run_id,
                    base_run_id=base_run_id,
                    replicate=replicate,
                    instance_size=size,
                    budget_level=budget_level,
                    budget_pct=budget_pct,
                    lambda_risk=lam,
                    reach_level=reach_level,
                    reach_pct=reach_pct,
                    cap_type=cap_type,
                    interaction_scenario=interaction,
                )
            )

    return scenarios


def load_data(data_path: str | Path) -> pd.DataFrame:
    """Load and preprocess the campaign dataset."""
    data_path = Path(data_path)

    if not data_path.exists():
        raise FileNotFoundError(
            f"Dataset not found at {data_path}. "
            "Place the dataset under data/marketing_campaign_dataset.csv or update DATA_PATH."
        )

    df = pd.read_csv(data_path)

    required_cols = [
        "Campaign_ID",
        "Channel_Used",
        "Acquisition_Cost",
        "Impressions",
        "Conversion_Rate",
        "Engagement_Score",
        "ROI",
    ]
    missing = [col for col in required_cols if col not in df.columns]

    if missing:
        raise ValueError(f"Missing required columns: {missing}")

    df["Cost"] = (
        df["Acquisition_Cost"]
        .astype(str)
        .str.replace("$", "", regex=False)
        .str.replace(",", "", regex=False)
        .str.strip()
        .astype(float)
    )

    df["Reach"] = df["Impressions"].astype(float)
    df["ROI"] = df["ROI"].astype(float)

    conversion = df["Conversion_Rate"].astype(float)
    engagement = df["Engagement_Score"].astype(float)

    conv_range = conversion.max() - conversion.min()
    eng_range = engagement.max() - engagement.min()

    conv_norm = (conversion - conversion.min()) / conv_range if conv_range != 0 else pd.Series(0.0, index=df.index)
    eng_norm = (engagement - engagement.min()) / eng_range if eng_range != 0 else pd.Series(0.0, index=df.index)

    df["Risk"] = 0.5 * (1.0 - conv_norm) + 0.5 * (1.0 - eng_norm)

    return df[["Campaign_ID", "Channel_Used", "Cost", "Reach", "ROI", "Risk"]].copy()


def sample_instance(df: pd.DataFrame, scenario: Scenario) -> pd.DataFrame:
    """Sample one campaign instance for a scenario."""
    return (
        df.sample(n=scenario.instance_size, random_state=RANDOM_SEED + scenario.run_id)
        .reset_index(drop=True)
        .copy()
    )


def get_channel_caps(instance: pd.DataFrame, scenario: Scenario) -> Dict[str, int]:
    """Create equal or channel specific capacity limits."""
    channels = sorted(instance["Channel_Used"].unique().tolist())
    expected_selected = max(1, int(math.ceil(scenario.instance_size * scenario.budget_pct)))

    if scenario.cap_type == "Equal":
        equal_cap = max(1, int(math.ceil(expected_selected / len(channels) * 1.5)))
        return {channel: equal_cap for channel in channels}

    proportions = instance["Channel_Used"].value_counts(normalize=True).to_dict()
    return {
        channel: max(1, int(math.ceil(expected_selected * proportions.get(channel, 0.0) * 1.8)))
        for channel in channels
    }


def build_theta_matrix(channels: List[str], interaction_scenario: str) -> np.ndarray:
    """Create the channel interaction coefficient matrix."""
    m = len(channels)
    theta = np.zeros((m, m), dtype=float)

    if interaction_scenario == "No interaction":
        return theta

    complementary_pairs = {
        frozenset(["Email", "Google Ads"]),
        frozenset(["Google Ads", "Website"]),
        frozenset(["YouTube", "Instagram"]),
        frozenset(["Facebook", "Instagram"]),
        frozenset(["YouTube", "Website"]),
        frozenset(["Email", "Website"]),
    }

    for i, channel_i in enumerate(channels):
        for j, channel_j in enumerate(channels):
            is_same_channel = channel_i == channel_j
            is_complementary = frozenset([channel_i, channel_j]) in complementary_pairs

            if interaction_scenario == "Weak interaction":
                theta[i, j] = -0.20 if is_same_channel else (0.25 if is_complementary else -0.05)
            elif interaction_scenario == "Strong synergy":
                theta[i, j] = -0.10 if is_same_channel else (0.80 if is_complementary else 0.15)
            elif interaction_scenario == "Strong cannibalization":
                theta[i, j] = -0.90 if is_same_channel else (0.10 if is_complementary else -0.35)
            else:
                raise ValueError(f"Unknown interaction scenario: {interaction_scenario}")

    return theta


def encode_instance(instance: pd.DataFrame) -> Dict[str, object]:
    """Convert a sampled instance into numpy arrays."""
    channels = sorted(instance["Channel_Used"].unique().tolist())
    channel_to_index = {channel: idx for idx, channel in enumerate(channels)}

    return {
        "campaign_ids": instance["Campaign_ID"].to_numpy(),
        "channels": channels,
        "channel_index": instance["Channel_Used"].map(channel_to_index).to_numpy(dtype=int),
        "cost": instance["Cost"].to_numpy(dtype=float),
        "reach": instance["Reach"].to_numpy(dtype=float),
        "roi": instance["ROI"].to_numpy(dtype=float),
        "risk": instance["Risk"].to_numpy(dtype=float),
    }


def interaction_from_counts(counts: np.ndarray, theta: np.ndarray) -> Tuple[float, float, float]:
    """Calculate synergy, cannibalization, and net interaction from selected channel counts."""
    synergy = 0.0
    cannibalization = 0.0
    m = len(counts)

    for i in range(m):
        if counts[i] > 1:
            value = theta[i, i] * counts[i] * (counts[i] - 1) / 2.0
            if value >= 0:
                synergy += value
            else:
                cannibalization += -value

        for j in range(i + 1, m):
            if counts[i] > 0 and counts[j] > 0:
                theta_avg = 0.5 * (theta[i, j] + theta[j, i])
                value = theta_avg * counts[i] * counts[j]
                if value >= 0:
                    synergy += value
                else:
                    cannibalization += -value

    return synergy, cannibalization, synergy - cannibalization


def evaluate_solution(
    x: np.ndarray,
    data: Dict[str, object],
    budget: float,
    minimum_reach: float,
    caps_array: np.ndarray,
    lambda_risk: float,
    theta: np.ndarray,
) -> Dict[str, object]:
    """Evaluate a complete campaign portfolio."""
    x = np.asarray(x, dtype=np.int8)

    cost = float(np.dot(x, data["cost"]))
    reach = float(np.dot(x, data["reach"]))
    selected = int(x.sum())

    counts = np.bincount(data["channel_index"][x == 1], minlength=len(caps_array))

    base_value = float(np.dot(x, data["roi"] - lambda_risk * data["risk"]))
    synergy, cannibalization, net_interaction = interaction_from_counts(counts, theta)

    portfolio_value = base_value + net_interaction

    terminal_feasible = bool(
        cost <= budget + 1e-9
        and reach >= minimum_reach - 1e-9
        and np.all(counts <= caps_array)
    )

    objective_value = portfolio_value if terminal_feasible else portfolio_value - TERMINAL_PENALTY

    average_roi = float(np.dot(x, data["roi"]) / selected) if selected > 0 else 0.0
    average_risk = float(np.dot(x, data["risk"]) / selected) if selected > 0 else 0.0

    channel_distribution = "; ".join(
        f"{channel}:{int(counts[idx])}" for idx, channel in enumerate(data["channels"])
    )

    return {
        "objective_value": objective_value,
        "portfolio_value_without_terminal_penalty": portfolio_value,
        "base_risk_adjusted_value": base_value,
        "total_synergy_value": synergy,
        "total_cannibalization_penalty": cannibalization,
        "net_interaction_value": net_interaction,
        "total_selected_campaigns": selected,
        "total_acquisition_cost": cost,
        "budget_utilization": cost / budget if budget > 0 else 0.0,
        "total_reach": reach,
        "terminal_feasible": terminal_feasible,
        "average_roi": average_roi,
        "average_risk": average_risk,
        "channel_distribution": channel_distribution,
    }


def repair_solution(
    x: np.ndarray,
    data: Dict[str, object],
    budget: float,
    caps_array: np.ndarray,
    lambda_risk: float,
) -> np.ndarray:
    """Repair budget and channel capacity violations."""
    x = x.copy().astype(np.int8)
    base_score = data["roi"] - lambda_risk * data["risk"]

    while True:
        counts = np.bincount(data["channel_index"][x == 1], minlength=len(caps_array))
        violated_channels = np.where(counts > caps_array)[0]

        if len(violated_channels) == 0:
            break

        candidates = np.where((x == 1) & np.isin(data["channel_index"], violated_channels))[0]
        worst_candidate = candidates[np.argmin(base_score[candidates])]
        x[worst_candidate] = 0

    while float(np.dot(x, data["cost"])) > budget and x.sum() > 0:
        selected = np.where(x == 1)[0]
        score_per_cost = base_score[selected] / data["cost"][selected]
        worst_selected = selected[np.argmin(score_per_cost)]
        x[worst_selected] = 0

    return x


def greedy_solution(
    data: Dict[str, object],
    budget: float,
    caps_array: np.ndarray,
    lambda_risk: float,
    theta: np.ndarray,
    method: str,
    rng: np.random.Generator,
) -> np.ndarray:
    """Create a greedy or random feasible portfolio."""
    n = len(data["cost"])
    x = np.zeros(n, dtype=np.int8)
    remaining_budget = budget
    counts = np.zeros(len(caps_array), dtype=int)

    if method == "Greedy ROI":
        order = np.argsort(-data["roi"])
    elif method == "Greedy ROI per Cost":
        order = np.argsort(-(data["roi"] / data["cost"]))
    elif method == "Greedy Risk Adjusted":
        order = np.argsort(-(data["roi"] - lambda_risk * data["risk"]))
    elif method == "Random Feasible":
        order = rng.permutation(n)
    elif method == "Interaction Aware Greedy":
        remaining_set = set(range(n))

        while remaining_set:
            best_idx: Optional[int] = None
            best_score = -1e18

            for idx in remaining_set:
                channel = data["channel_index"][idx]
                if data["cost"][idx] <= remaining_budget and counts[channel] + 1 <= caps_array[channel]:
                    interaction_score = float(theta[channel, :] @ counts)
                    score = data["roi"][idx] - lambda_risk * data["risk"][idx] + interaction_score

                    if score > best_score:
                        best_score = score
                        best_idx = idx

            if best_idx is None or best_score <= 0:
                break

            channel = data["channel_index"][best_idx]
            x[best_idx] = 1
            remaining_budget -= data["cost"][best_idx]
            counts[channel] += 1
            remaining_set.remove(best_idx)

        return x
    else:
        raise ValueError(f"Unknown greedy method: {method}")

    for idx in order:
        channel = data["channel_index"][idx]

        if data["cost"][idx] <= remaining_budget and counts[channel] + 1 <= caps_array[channel]:
            x[idx] = 1
            remaining_budget -= data["cost"][idx]
            counts[channel] += 1

    return x


def genetic_algorithm(
    data: Dict[str, object],
    budget: float,
    minimum_reach: float,
    caps_array: np.ndarray,
    lambda_risk: float,
    theta: np.ndarray,
    rng: np.random.Generator,
) -> np.ndarray:
    """Run the Genetic Algorithm."""
    n = len(data["cost"])

    pop_size = 45
    generations = 55
    elite_size = 5
    tournament_size = 3
    mutation_rate = min(0.04, max(1.0 / n, 0.003))

    seed_methods = [
        "Greedy ROI",
        "Greedy ROI per Cost",
        "Greedy Risk Adjusted",
        "Interaction Aware Greedy",
        "Random Feasible",
    ]

    population = [
        greedy_solution(data, budget, caps_array, lambda_risk, theta, method, rng)
        for method in seed_methods
    ]

    initial_selection_probability = min(0.25, max(0.03, budget / max(float(data["cost"].sum()), 1.0)))

    while len(population) < pop_size:
        random_x = (rng.random(n) < initial_selection_probability).astype(np.int8)
        repaired_x = repair_solution(random_x, data, budget, caps_array, lambda_risk)
        population.append(repaired_x)

    population = np.array(population, dtype=np.int8)

    def fitness(individual: np.ndarray) -> float:
        return float(
            evaluate_solution(
                individual,
                data,
                budget,
                minimum_reach,
                caps_array,
                lambda_risk,
                theta,
            )["objective_value"]
        )

    scores = np.array([fitness(individual) for individual in population])
    best_idx = int(np.argmax(scores))
    best_solution = population[best_idx].copy()
    best_score = float(scores[best_idx])

    for _ in range(generations):
        scores = np.array([fitness(individual) for individual in population])

        current_best_idx = int(np.argmax(scores))
        if float(scores[current_best_idx]) > best_score:
            best_solution = population[current_best_idx].copy()
            best_score = float(scores[current_best_idx])

        elite_indices = np.argsort(scores)[-elite_size:]
        new_population = [population[idx].copy() for idx in elite_indices]

        while len(new_population) < pop_size:
            parent_1_candidates = rng.choice(pop_size, size=tournament_size, replace=False)
            parent_2_candidates = rng.choice(pop_size, size=tournament_size, replace=False)

            parent_1 = population[parent_1_candidates[np.argmax(scores[parent_1_candidates])]]
            parent_2 = population[parent_2_candidates[np.argmax(scores[parent_2_candidates])]]

            crossover_mask = rng.random(n) < 0.5
            child = np.where(crossover_mask, parent_1, parent_2).astype(np.int8)

            mutation_mask = rng.random(n) < mutation_rate
            child[mutation_mask] = 1 - child[mutation_mask]

            child = repair_solution(child, data, budget, caps_array, lambda_risk)
            new_population.append(child)

        population = np.array(new_population, dtype=np.int8)

    return best_solution


def solve_milp_gurobi(
    data: Dict[str, object],
    budget: float,
    minimum_reach: float,
    caps_array: np.ndarray,
    lambda_risk: float,
    theta: np.ndarray,
    time_limit: float,
    mip_gap: float = 1e-4,
) -> Tuple[Optional[np.ndarray], Dict[str, object]]:
    """
    Solve the linearized MILP benchmark with Gurobi.

    The interaction term is linearized with:
    - delta[k, q]: channel k has exactly q selected campaigns
    - w[a, b, q, r]: channel a has q selected campaigns and channel b has r selected campaigns
    """
    if gp is None:
        raise ImportError(
            "gurobipy is not installed. Install it with 'pip install gurobipy' "
            "and make sure Gurobi Optimizer has a valid license."
        )

    n = len(data["cost"])
    m = len(caps_array)
    caps = caps_array.astype(int).tolist()

    model = gp.Model("campaign_allocation_linearized_milp")
    model.Params.OutputFlag = 0
    model.Params.TimeLimit = time_limit
    model.Params.MIPGap = mip_gap

    x = model.addVars(n, vtype=GRB.BINARY, name="x")

    delta = {}
    for k in range(m):
        for q in range(caps[k] + 1):
            delta[k, q] = model.addVar(vtype=GRB.BINARY, name=f"delta_{k}_{q}")

    w = {}
    for a in range(m):
        for b in range(a + 1, m):
            for q in range(caps[a] + 1):
                for r in range(caps[b] + 1):
                    w[a, b, q, r] = model.addVar(vtype=GRB.BINARY, name=f"w_{a}_{b}_{q}_{r}")

    model.update()

    model.addConstr(
        gp.quicksum(data["cost"][i] * x[i] for i in range(n)) <= budget,
        name="budget_constraint",
    )

    model.addConstr(
        gp.quicksum(data["reach"][i] * x[i] for i in range(n)) >= minimum_reach,
        name="minimum_reach_constraint",
    )

    for k in range(m):
        indices_in_channel = [i for i in range(n) if data["channel_index"][i] == k]

        model.addConstr(
            gp.quicksum(x[i] for i in indices_in_channel)
            == gp.quicksum(q * delta[k, q] for q in range(caps[k] + 1)),
            name=f"channel_count_consistency_{k}",
        )

        model.addConstr(
            gp.quicksum(delta[k, q] for q in range(caps[k] + 1)) == 1,
            name=f"one_count_level_{k}",
        )

        model.addConstr(
            gp.quicksum(x[i] for i in indices_in_channel) <= caps[k],
            name=f"channel_capacity_{k}",
        )

    for a in range(m):
        for b in range(a + 1, m):
            for q in range(caps[a] + 1):
                model.addConstr(
                    gp.quicksum(w[a, b, q, r] for r in range(caps[b] + 1)) == delta[a, q],
                    name=f"coupling_a_{a}_{b}_{q}",
                )

            for r in range(caps[b] + 1):
                model.addConstr(
                    gp.quicksum(w[a, b, q, r] for q in range(caps[a] + 1)) == delta[b, r],
                    name=f"coupling_b_{a}_{b}_{r}",
                )

    base_objective = gp.quicksum(
        (data["roi"][i] - lambda_risk * data["risk"][i]) * x[i]
        for i in range(n)
    )

    same_channel_interaction = gp.quicksum(
        theta[k, k] * q * (q - 1) / 2.0 * delta[k, q]
        for k in range(m)
        for q in range(caps[k] + 1)
    )

    cross_channel_interaction = gp.quicksum(
        0.5 * (theta[a, b] + theta[b, a]) * q * r * w[a, b, q, r]
        for a in range(m)
        for b in range(a + 1, m)
        for q in range(caps[a] + 1)
        for r in range(caps[b] + 1)
    )

    model.setObjective(base_objective + same_channel_interaction + cross_channel_interaction, GRB.MAXIMIZE)
    model.optimize()

    status_map = {
        GRB.OPTIMAL: "Optimal",
        GRB.TIME_LIMIT: "Time limit",
        GRB.INFEASIBLE: "Infeasible",
        GRB.UNBOUNDED: "Unbounded",
        GRB.INF_OR_UNBD: "Infeasible or unbounded",
        GRB.INTERRUPTED: "Interrupted",
    }

    status = status_map.get(model.Status, f"Status {model.Status}")

    info = {
        "solver_status": status,
        "milp_time_limit_sec": time_limit,
        "mip_gap": model.MIPGap if model.SolCount > 0 else np.nan,
        "mip_bound": model.ObjBound if model.SolCount > 0 else np.nan,
        "mip_node_count": model.NodeCount,
        "milp_num_vars": model.NumVars,
        "milp_num_constraints": model.NumConstrs,
        "milp_objective_bound": model.ObjBound if model.SolCount > 0 else np.nan,
    }

    if model.SolCount == 0:
        return None, info

    solution = np.array([1 if x[i].X >= 0.5 else 0 for i in range(n)], dtype=np.int8)
    return solution, info


def run_experiments(data_path: str | Path, output_dir: str | Path) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Run all 20 experiments and save result files."""
    output_dir = Path(output_dir)
    figures_dir = output_dir / "figures"
    output_dir.mkdir(parents=True, exist_ok=True)
    figures_dir.mkdir(parents=True, exist_ok=True)

    np.random.seed(RANDOM_SEED)
    random.seed(RANDOM_SEED)

    full_data = load_data(data_path)

    result_rows = []
    scenario_rows = []

    for scenario in build_scenarios():
        print(f"Running scenario {scenario.run_id}/20...")

        instance = sample_instance(full_data, scenario)
        data = encode_instance(instance)

        caps_dict = get_channel_caps(instance, scenario)
        caps_array = np.array([caps_dict[channel] for channel in data["channels"]], dtype=int)

        theta = build_theta_matrix(data["channels"], scenario.interaction_scenario)

        budget = float(np.sum(data["cost"]) * scenario.budget_pct)
        minimum_reach = float(np.sum(data["reach"]) * scenario.reach_pct)

        scenario_rows.append(
            {
                "run_id": scenario.run_id,
                "base_run_id": scenario.base_run_id,
                "replicate": scenario.replicate,
                "instance_size": scenario.instance_size,
                "budget_level": scenario.budget_level,
                "budget_pct": scenario.budget_pct,
                "budget": budget,
                "lambda_risk": scenario.lambda_risk,
                "reach_level": scenario.reach_level,
                "reach_pct": scenario.reach_pct,
                "minimum_reach": minimum_reach,
                "cap_type": scenario.cap_type,
                "channel_caps": "; ".join(f"{key}:{value}" for key, value in caps_dict.items()),
                "interaction_scenario": scenario.interaction_scenario,
            }
        )

        methods = ["Genetic Algorithm", "Greedy ROI per Cost", "MILP Linearized"]

        for method in methods:
            rng = np.random.default_rng(RANDOM_SEED + 1000 * scenario.run_id + len(method))
            start_time = time.perf_counter()

            extra_info = {}

            if method == "Genetic Algorithm":
                x = genetic_algorithm(
                    data,
                    budget,
                    minimum_reach,
                    caps_array,
                    scenario.lambda_risk,
                    theta,
                    rng,
                )
                extra_info["solver_status"] = "Completed"

            elif method == "Greedy ROI per Cost":
                x = greedy_solution(
                    data,
                    budget,
                    caps_array,
                    scenario.lambda_risk,
                    theta,
                    method,
                    rng,
                )
                extra_info["solver_status"] = "Completed"

            elif method == "MILP Linearized":
                time_limit = 10.0 if scenario.instance_size <= 250 else 20.0
                x, extra_info = solve_milp_gurobi(
                    data,
                    budget,
                    minimum_reach,
                    caps_array,
                    scenario.lambda_risk,
                    theta,
                    time_limit=time_limit,
                )

            else:
                raise ValueError(f"Unknown method: {method}")

            runtime_sec = time.perf_counter() - start_time

            if x is None:
                metrics = {
                    "objective_value": np.nan,
                    "portfolio_value_without_terminal_penalty": np.nan,
                    "base_risk_adjusted_value": np.nan,
                    "total_synergy_value": np.nan,
                    "total_cannibalization_penalty": np.nan,
                    "net_interaction_value": np.nan,
                    "total_selected_campaigns": np.nan,
                    "total_acquisition_cost": np.nan,
                    "budget_utilization": np.nan,
                    "total_reach": np.nan,
                    "terminal_feasible": False,
                    "average_roi": np.nan,
                    "average_risk": np.nan,
                    "channel_distribution": "",
                }
            else:
                metrics = evaluate_solution(
                    x,
                    data,
                    budget,
                    minimum_reach,
                    caps_array,
                    scenario.lambda_risk,
                    theta,
                )

            result_rows.append(
                {
                    "run_id": scenario.run_id,
                    "base_run_id": scenario.base_run_id,
                    "replicate": scenario.replicate,
                    "method": method,
                    "runtime_sec": runtime_sec,
                    "instance_size": scenario.instance_size,
                    "budget_level": scenario.budget_level,
                    "budget_pct": scenario.budget_pct,
                    "budget": budget,
                    "lambda_risk": scenario.lambda_risk,
                    "reach_level": scenario.reach_level,
                    "reach_pct": scenario.reach_pct,
                    "minimum_reach": minimum_reach,
                    "cap_type": scenario.cap_type,
                    "interaction_scenario": scenario.interaction_scenario,
                    **extra_info,
                    **metrics,
                }
            )

    results = pd.DataFrame(result_rows)
    scenarios = pd.DataFrame(scenario_rows)

    results_path = output_dir / "ga_milp_20run_results.csv"
    scenarios_path = output_dir / "ga_milp_20run_scenario_setup.csv"
    summary_path = output_dir / "ga_milp_20run_method_summary.csv"
    comparison_path = output_dir / "ga_vs_milp_20run_comparison.csv"

    results.to_csv(results_path, index=False)
    scenarios.to_csv(scenarios_path, index=False)

    summary = (
        results.groupby("method")
        .agg(
            avg_objective=("objective_value", "mean"),
            median_objective=("objective_value", "median"),
            avg_runtime_sec=("runtime_sec", "mean"),
            feasibility_rate=("terminal_feasible", "mean"),
            avg_selected_campaigns=("total_selected_campaigns", "mean"),
            avg_budget_utilization=("budget_utilization", "mean"),
            avg_reach=("total_reach", "mean"),
            avg_net_interaction=("net_interaction_value", "mean"),
        )
        .reset_index()
        .sort_values("avg_objective", ascending=False)
    )

    summary.to_csv(summary_path, index=False)

    comparison = build_ga_milp_comparison(results)
    comparison.to_csv(comparison_path, index=False)

    create_figures(results, comparison, figures_dir)

    print("\nExperiment completed.")
    print(f"Results saved to: {output_dir}")

    return results, scenarios, summary


def build_ga_milp_comparison(results: pd.DataFrame) -> pd.DataFrame:
    """Create a run level comparison between GA, MILP, and Greedy ROI per Cost."""
    pivot = results.pivot_table(
        index=[
            "run_id",
            "base_run_id",
            "replicate",
            "instance_size",
            "budget_level",
            "budget_pct",
            "lambda_risk",
            "reach_level",
            "reach_pct",
            "cap_type",
            "interaction_scenario",
        ],
        columns="method",
        values="objective_value",
        aggfunc="first",
    ).reset_index()

    pivot.columns.name = None

    if "Genetic Algorithm" in pivot.columns and "MILP Linearized" in pivot.columns:
        pivot["ga_pct_of_milp"] = 100.0 * pivot["Genetic Algorithm"] / pivot["MILP Linearized"]

    status = (
        results[results["method"] == "MILP Linearized"][
            [
                "run_id",
                "solver_status",
                "runtime_sec",
                "mip_gap",
                "mip_bound",
                "mip_node_count",
                "milp_num_vars",
                "milp_num_constraints",
                "milp_time_limit_sec",
            ]
        ]
        .rename(
            columns={
                "solver_status": "milp_status",
                "runtime_sec": "milp_runtime_sec",
            }
        )
    )

    return pivot.merge(status, on="run_id", how="left")


def create_figures(results: pd.DataFrame, comparison: pd.DataFrame, figures_dir: Path) -> None:
    """Create the main experiment figures."""
    method_order = ["MILP Linearized", "Genetic Algorithm", "Greedy ROI per Cost"]

    objective_pivot = results.pivot_table(
        index="run_id",
        columns="method",
        values="objective_value",
        aggfunc="first",
    )

    plt.figure(figsize=(11, 6))
    for method in method_order:
        if method in objective_pivot.columns:
            plt.plot(objective_pivot.index, objective_pivot[method], marker="o", label=method)
    plt.xlabel("Run")
    plt.ylabel("Objective Value")
    plt.title("Objective Value Across 20 Runs")
    plt.legend()
    plt.tight_layout()
    plt.savefig(figures_dir / "figure_objective_ga_milp_greedy_20runs.png", dpi=300)
    plt.close()

    runtime_summary = (
        results.groupby(["instance_size", "method"])["runtime_sec"]
        .mean()
        .reset_index()
    )

    plt.figure(figsize=(11, 6))
    for method in method_order:
        subset = runtime_summary[runtime_summary["method"] == method]
        if not subset.empty:
            plt.plot(subset["instance_size"], subset["runtime_sec"], marker="o", label=method)
    plt.xlabel("Instance Size")
    plt.ylabel("Average Runtime Seconds")
    plt.title("Runtime by Instance Size")
    plt.legend()
    plt.tight_layout()
    plt.savefig(figures_dir / "figure_runtime_ga_milp_greedy_20runs.png", dpi=300)
    plt.close()

    if "ga_pct_of_milp" in comparison.columns:
        plt.figure(figsize=(11, 6))
        plt.bar(comparison["run_id"], comparison["ga_pct_of_milp"])
        plt.axhline(100, linestyle="--", linewidth=1)
        plt.xlabel("Run")
        plt.ylabel("GA Percentage of MILP Objective")
        plt.title("GA Objective as Percentage of MILP Benchmark")
        plt.tight_layout()
        plt.savefig(figures_dir / "figure_ga_pct_of_milp_optimal_runs.png", dpi=300)
        plt.close()

    milp_rows = results[results["method"] == "MILP Linearized"].copy()
    if not milp_rows.empty and "milp_num_vars" in milp_rows.columns:
        plt.figure(figsize=(11, 6))
        plt.plot(milp_rows["run_id"], milp_rows["milp_num_vars"], marker="o", label="Variables")
        plt.plot(milp_rows["run_id"], milp_rows["milp_num_constraints"], marker="o", label="Constraints")
        plt.xlabel("Run")
        plt.ylabel("Count")
        plt.title("MILP Model Size Across 20 Runs")
        plt.legend()
        plt.tight_layout()
        plt.savefig(figures_dir / "figure_milp_model_size_20runs.png", dpi=300)
        plt.close()


if __name__ == "__main__":
    DATA_PATH = Path("data") / "marketing_campaign_dataset.csv"
    OUTPUT_DIR = Path("outputs")

    run_experiments(DATA_PATH, OUTPUT_DIR)
