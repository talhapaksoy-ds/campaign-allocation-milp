
from __future__ import annotations

import math
import os
import random
import time
from dataclasses import dataclass
from typing import Dict, List, Tuple

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


RANDOM_SEED = 42

# Fixed project folder requested for the final DS502 project.
# Dataset path expected by this script:
# C:\\Users\\lenovo\\Desktop\\DS502-PROJECT\\data\\marketing_campaign_dataset_og.csv
# Output files are written to:
# C:\\Users\\lenovo\\Desktop\\DS502-PROJECT\\outputs
PROJECT_ROOT = r"C:\Users\lenovo\Desktop\DS502-PROJECT"

np.random.seed(RANDOM_SEED)
random.seed(RANDOM_SEED)


@dataclass(frozen=True)
class Scenario:
    run_id: int
    instance_size: int
    budget_level: str
    budget_pct: float
    lambda_risk: float
    reach_level: str
    reach_pct: float
    cap_type: str
    interaction_scenario: str


SCENARIOS: List[Scenario] = [
    Scenario(1, 50, "Low", 0.05, 0.00, "Relaxed", 0.03, "Equal", "No interaction"),
    Scenario(2, 50, "Medium", 0.10, 0.25, "Moderate", 0.05, "Equal", "Weak interaction"),
    Scenario(3, 100, "Low", 0.05, 0.50, "Moderate", 0.05, "Specific", "Weak interaction"),
    Scenario(4, 100, "Medium", 0.10, 1.00, "Strict", 0.08, "Specific", "Strong cannibalization"),
    Scenario(5, 250, "Medium", 0.10, 0.50, "Moderate", 0.05, "Equal", "Strong synergy"),
    Scenario(6, 250, "High", 0.20, 1.00, "Strict", 0.08, "Specific", "Strong cannibalization"),
    Scenario(7, 500, "Low", 0.05, 1.00, "Relaxed", 0.03, "Equal", "Strong cannibalization"),
    Scenario(8, 500, "Medium", 0.10, 2.00, "Moderate", 0.05, "Specific", "Strong synergy"),
    Scenario(9, 1000, "Medium", 0.10, 0.25, "Moderate", 0.05, "Equal", "Weak interaction"),
    Scenario(10, 1000, "High", 0.20, 2.00, "Strict", 0.08, "Specific", "Strong synergy"),
]


def root_dir() -> str:
    """Return the fixed local project directory."""
    return PROJECT_ROOT


def load_data(path: str) -> pd.DataFrame:
    df = pd.read_csv(path)
    df["Cost"] = (
        df["Acquisition_Cost"].astype(str)
        .str.replace("$", "", regex=False)
        .str.replace(",", "", regex=False)
        .str.strip()
        .astype(float)
    )
    df["Reach"] = df["Impressions"].astype(float)
    conv = df["Conversion_Rate"].astype(float)
    eng = df["Engagement_Score"].astype(float)
    conv_norm = (conv - conv.min()) / (conv.max() - conv.min())
    eng_norm = (eng - eng.min()) / (eng.max() - eng.min())
    df["Risk"] = 0.5 * (1 - conv_norm) + 0.5 * (1 - eng_norm)
    df["ROI"] = df["ROI"].astype(float)
    return df[["Campaign_ID", "Channel_Used", "Cost", "Reach", "ROI", "Risk"]].copy()


def sample_instance(df: pd.DataFrame, scenario: Scenario) -> pd.DataFrame:
    return df.sample(n=scenario.instance_size, random_state=RANDOM_SEED + scenario.run_id).reset_index(drop=True)


def channel_caps(instance: pd.DataFrame, scenario: Scenario) -> Dict[str, int]:
    channels = sorted(instance["Channel_Used"].unique().tolist())
    expected_selected = max(1, int(math.ceil(scenario.instance_size * scenario.budget_pct)))
    if scenario.cap_type == "Equal":
        cap = max(1, int(math.ceil(expected_selected / len(channels) * 1.5)))
        return {c: cap for c in channels}
    proportions = instance["Channel_Used"].value_counts(normalize=True).to_dict()
    return {c: max(1, int(math.ceil(expected_selected * proportions.get(c, 0) * 1.8))) for c in channels}


def theta_matrix(channels: List[str], scenario_name: str) -> np.ndarray:
    m = len(channels)
    theta = np.zeros((m, m), dtype=float)
    if scenario_name == "No interaction":
        return theta

    comp = {frozenset(["Email", "Google Ads"]), frozenset(["Google Ads", "Website"]),
            frozenset(["YouTube", "Instagram"]), frozenset(["Facebook", "Instagram"]),
            frozenset(["YouTube", "Website"]), frozenset(["Email", "Website"])}

    for i, a in enumerate(channels):
        for j, b in enumerate(channels):
            if scenario_name == "Weak interaction":
                theta[i, j] = -0.20 if a == b else (0.25 if frozenset([a, b]) in comp else -0.05)
            elif scenario_name == "Strong synergy":
                theta[i, j] = -0.10 if a == b else (0.80 if frozenset([a, b]) in comp else 0.15)
            elif scenario_name == "Strong cannibalization":
                theta[i, j] = -0.90 if a == b else (0.10 if frozenset([a, b]) in comp else -0.35)
            else:
                raise ValueError(f"Unknown interaction scenario: {scenario_name}")
    return theta


def encode_instance(instance: pd.DataFrame):
    channels = sorted(instance["Channel_Used"].unique().tolist())
    ch_to_idx = {c: i for i, c in enumerate(channels)}
    ch_idx = instance["Channel_Used"].map(ch_to_idx).to_numpy()
    return {
        "cost": instance["Cost"].to_numpy(float),
        "reach": instance["Reach"].to_numpy(float),
        "roi": instance["ROI"].to_numpy(float),
        "risk": instance["Risk"].to_numpy(float),
        "channels": channels,
        "ch_idx": ch_idx,
        "campaign_ids": instance["Campaign_ID"].to_numpy(),
    }


def interaction_from_counts(counts: np.ndarray, theta: np.ndarray) -> Tuple[float, float, float]:
    synergy = 0.0
    cannibal = 0.0
    m = len(counts)
    for i in range(m):
        if counts[i] > 1:
            val = theta[i, i] * counts[i] * (counts[i] - 1) / 2
            if val >= 0: synergy += val
            else: cannibal += -val
        for j in range(i + 1, m):
            if counts[i] and counts[j]:
                val = 0.5 * (theta[i, j] + theta[j, i]) * counts[i] * counts[j]
                if val >= 0: synergy += val
                else: cannibal += -val
    return synergy, cannibal, synergy - cannibal


def repair(x: np.ndarray, data: dict, budget: float, caps_arr: np.ndarray, lam: float) -> np.ndarray:
    x = x.copy().astype(np.int8)
    cost, roi, risk, ch_idx = data["cost"], data["roi"], data["risk"], data["ch_idx"]
    base_score = roi - lam * risk

    # repair channel caps
    while True:
        counts = np.bincount(ch_idx[x == 1], minlength=len(caps_arr))
        viol = np.where(counts > caps_arr)[0]
        if len(viol) == 0:
            break
        candidates = np.where((x == 1) & np.isin(ch_idx, viol))[0]
        drop = candidates[np.argmin(base_score[candidates])]
        x[drop] = 0

    # repair budget
    while float(np.dot(x, cost)) > budget and x.sum() > 0:
        selected = np.where(x == 1)[0]
        score_per_cost = base_score[selected] / cost[selected]
        drop = selected[np.argmin(score_per_cost)]
        x[drop] = 0

    return x


def evaluate(x: np.ndarray, data: dict, budget: float, min_reach: float, caps_arr: np.ndarray, lam: float, theta: np.ndarray) -> dict:
    cost = float(np.dot(x, data["cost"]))
    reach = float(np.dot(x, data["reach"]))
    selected = int(x.sum())
    counts = np.bincount(data["ch_idx"][x == 1], minlength=len(caps_arr))
    base_value = float(np.dot(x, data["roi"] - lam * data["risk"]))
    synergy, cannibal, net = interaction_from_counts(counts, theta)
    portfolio = base_value + net
    terminal_feasible = bool(cost <= budget + 1e-9 and reach >= min_reach - 1e-9 and np.all(counts <= caps_arr))
    objective = portfolio if terminal_feasible else portfolio - 3000.0
    avg_roi = float(np.dot(x, data["roi"]) / selected) if selected else 0.0
    avg_risk = float(np.dot(x, data["risk"]) / selected) if selected else 0.0
    channel_distribution = "; ".join([f"{ch}:{int(counts[i])}" for i, ch in enumerate(data["channels"])])
    return {
        "objective_value": objective,
        "portfolio_value_without_terminal_penalty": portfolio,
        "base_risk_adjusted_value": base_value,
        "total_synergy_value": synergy,
        "total_cannibalization_penalty": cannibal,
        "net_interaction_value": net,
        "total_selected_campaigns": selected,
        "total_acquisition_cost": cost,
        "budget_utilization": cost / budget if budget else 0.0,
        "total_reach": reach,
        "terminal_feasible": terminal_feasible,
        "average_roi": avg_roi,
        "average_risk": avg_risk,
        "channel_distribution": channel_distribution,
    }


def greedy(data: dict, budget: float, caps_arr: np.ndarray, lam: float, theta: np.ndarray, method: str, rng: np.random.Generator) -> np.ndarray:
    n = len(data["cost"])
    x = np.zeros(n, dtype=np.int8)
    remaining = budget
    counts = np.zeros(len(caps_arr), dtype=int)
    if method == "Greedy ROI":
        order = np.argsort(-data["roi"])
    elif method == "Greedy ROI per Cost":
        order = np.argsort(-(data["roi"] / data["cost"]))
    elif method == "Greedy Risk Adjusted":
        order = np.argsort(-(data["roi"] - lam * data["risk"]))
    elif method == "Random Feasible":
        order = rng.permutation(n)
    elif method == "Interaction Aware Greedy":
        remaining_set = set(range(n))
        while remaining_set:
            best_idx = None
            best_score = -1e18
            for idx in remaining_set:
                ch = data["ch_idx"][idx]
                if data["cost"][idx] <= remaining and counts[ch] + 1 <= caps_arr[ch]:
                    interaction = float(theta[ch, :] @ counts)
                    score = data["roi"][idx] - lam * data["risk"][idx] + interaction
                    if score > best_score:
                        best_score = score
                        best_idx = idx
            if best_idx is None or best_score <= 0:
                break
            ch = data["ch_idx"][best_idx]
            x[best_idx] = 1
            remaining -= data["cost"][best_idx]
            counts[ch] += 1
            remaining_set.remove(best_idx)
        return x
    else:
        raise ValueError(method)

    for idx in order:
        ch = data["ch_idx"][idx]
        if data["cost"][idx] <= remaining and counts[ch] + 1 <= caps_arr[ch]:
            x[idx] = 1
            remaining -= data["cost"][idx]
            counts[ch] += 1
    return x


def genetic_algorithm(data: dict, budget: float, min_reach: float, caps_arr: np.ndarray, lam: float, theta: np.ndarray, rng: np.random.Generator) -> np.ndarray:
    n = len(data["cost"])
    pop_size = 45
    generations = 55
    elite = 5
    tournament = 3
    mut_rate = min(0.04, max(1 / n, 0.003))

    seeds = []
    for method in ["Greedy ROI", "Greedy ROI per Cost", "Greedy Risk Adjusted", "Interaction Aware Greedy", "Random Feasible"]:
        seeds.append(greedy(data, budget, caps_arr, lam, theta, method, rng))

    population = []
    for s in seeds:
        population.append(s)
    p = min(0.25, max(0.03, budget / max(data["cost"].sum(), 1)))
    while len(population) < pop_size:
        x = (rng.random(n) < p).astype(np.int8)
        population.append(repair(x, data, budget, caps_arr, lam))
    population = np.array(population, dtype=np.int8)

    def fitness(ind):
        return evaluate(ind, data, budget, min_reach, caps_arr, lam, theta)["objective_value"]

    best = population[0].copy()
    best_score = fitness(best)

    for _ in range(generations):
        scores = np.array([fitness(ind) for ind in population])
        idx = int(np.argmax(scores))
        if scores[idx] > best_score:
            best_score = float(scores[idx])
            best = population[idx].copy()

        elites = np.argsort(scores)[-elite:]
        new_pop = [population[i].copy() for i in elites]

        while len(new_pop) < pop_size:
            cand1 = rng.choice(pop_size, size=tournament, replace=False)
            cand2 = rng.choice(pop_size, size=tournament, replace=False)
            p1 = population[cand1[np.argmax(scores[cand1])]]
            p2 = population[cand2[np.argmax(scores[cand2])]]
            mask = rng.random(n) < 0.5
            child = np.where(mask, p1, p2).astype(np.int8)
            muts = rng.random(n) < mut_rate
            child[muts] = 1 - child[muts]
            child = repair(child, data, budget, caps_arr, lam)
            new_pop.append(child)

        population = np.array(new_pop, dtype=np.int8)

    return best


def run():
    root = root_dir()
    data_path = os.path.join(root, "data", "marketing_campaign_dataset_og.csv")
    output_dir = os.path.join(root, "outputs")
    os.makedirs(output_dir, exist_ok=True)

    df = load_data(data_path)
    rows = []
    scenario_rows = []
    methods = ["Genetic Algorithm", "Interaction Aware Greedy", "Greedy ROI", "Greedy ROI per Cost", "Greedy Risk Adjusted", "Random Feasible"]

    for sc in SCENARIOS:
        inst = sample_instance(df, sc)
        data = encode_instance(inst)
        caps_dict = channel_caps(inst, sc)
        caps_arr = np.array([caps_dict[ch] for ch in data["channels"]], dtype=int)
        theta = theta_matrix(data["channels"], sc.interaction_scenario)
        budget = float(data["cost"].sum() * sc.budget_pct)
        min_reach = float(data["reach"].sum() * sc.reach_pct)
        scenario_rows.append({
            "run_id": sc.run_id, "instance_size": sc.instance_size, "budget_level": sc.budget_level,
            "budget_pct": sc.budget_pct, "budget": budget, "lambda_risk": sc.lambda_risk,
            "reach_level": sc.reach_level, "reach_pct": sc.reach_pct, "minimum_reach": min_reach,
            "cap_type": sc.cap_type, "channel_caps": "; ".join(f"{k}:{v}" for k, v in caps_dict.items()),
            "interaction_scenario": sc.interaction_scenario
        })
        for method in methods:
            rng = np.random.default_rng(RANDOM_SEED + 1000 * sc.run_id + len(method))
            start = time.perf_counter()
            if method == "Genetic Algorithm":
                x = genetic_algorithm(data, budget, min_reach, caps_arr, sc.lambda_risk, theta, rng)
            else:
                x = greedy(data, budget, caps_arr, sc.lambda_risk, theta, method, rng)
            runtime = time.perf_counter() - start
            metrics = evaluate(x, data, budget, min_reach, caps_arr, sc.lambda_risk, theta)
            rows.append({
                "run_id": sc.run_id, "method": method, "instance_size": sc.instance_size,
                "budget_level": sc.budget_level, "budget_pct": sc.budget_pct, "budget": budget,
                "lambda_risk": sc.lambda_risk, "reach_level": sc.reach_level,
                "minimum_reach": min_reach, "cap_type": sc.cap_type,
                "interaction_scenario": sc.interaction_scenario, "runtime_sec": runtime,
                "solver_status": "Completed", **metrics
            })

    results = pd.DataFrame(rows)
    scenarios = pd.DataFrame(scenario_rows)
    results.to_csv(os.path.join(output_dir, "ga_experiment_results_all_methods.csv"), index=False)
    scenarios.to_csv(os.path.join(output_dir, "ga_experiment_scenario_setup.csv"), index=False)

    summary = results.groupby("method").agg(
        avg_objective_value=("objective_value", "mean"),
        avg_portfolio_value=("portfolio_value_without_terminal_penalty", "mean"),
        avg_selected_campaigns=("total_selected_campaigns", "mean"),
        avg_budget_utilization=("budget_utilization", "mean"),
        avg_total_reach=("total_reach", "mean"),
        avg_net_interaction=("net_interaction_value", "mean"),
        avg_runtime_sec=("runtime_sec", "mean"),
        feasibility_rate=("terminal_feasible", "mean")
    ).reset_index().sort_values("avg_objective_value", ascending=False)
    summary.to_csv(os.path.join(output_dir, "ga_summary_by_method.csv"), index=False)

    selected = results[results["method"].isin(["Genetic Algorithm", "Interaction Aware Greedy", "Greedy ROI per Cost", "Random Feasible"])]
    selected.to_csv(os.path.join(output_dir, "ga_main_report_results_selected_methods.csv"), index=False)

    make_figures(results, output_dir)
    print("Genetic Algorithm experiments completed.")
    print(f"Outputs saved to: {output_dir}")
    print(summary.to_string(index=False))


def make_figures(results: pd.DataFrame, output_dir: str):
    selected_methods = ["Genetic Algorithm", "Interaction Aware Greedy", "Greedy ROI per Cost", "Random Feasible"]
    selected = results[results["method"].isin(selected_methods)]
    pivot = selected.pivot(index="run_id", columns="method", values="objective_value")
    ax = pivot.plot(kind="bar", figsize=(11, 6))
    ax.set_xlabel("Run")
    ax.set_ylabel("Objective Value")
    ax.set_title("Objective Value by Run and Method")
    ax.legend(title="Method", fontsize=8)
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "ga_figure_objective_value_by_run.png"), dpi=200)
    plt.close()

    runtime = results.groupby(["instance_size", "method"])["runtime_sec"].mean().reset_index()
    pivot = runtime.pivot(index="instance_size", columns="method", values="runtime_sec")
    ax = pivot.plot(kind="line", marker="o", figsize=(10, 6))
    ax.set_xlabel("Instance Size")
    ax.set_ylabel("Average Runtime (seconds)")
    ax.set_title("Runtime by Instance Size")
    ax.legend(title="Method", fontsize=8)
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "ga_figure_runtime_by_instance_size.png"), dpi=200)
    plt.close()

    feas = results.groupby("method")["terminal_feasible"].mean().sort_values(ascending=False)
    ax = feas.plot(kind="bar", figsize=(10, 6))
    ax.set_xlabel("Method")
    ax.set_ylabel("Terminal Feasibility Rate")
    ax.set_title("Terminal Feasibility Rate by Method")
    plt.xticks(rotation=30, ha="right")
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "ga_figure_feasibility_rate_by_method.png"), dpi=200)
    plt.close()

    inter = results[results["method"].isin(["Genetic Algorithm", "Interaction Aware Greedy", "Greedy ROI per Cost"])]
    pivot = inter.groupby(["interaction_scenario", "method"])["net_interaction_value"].mean().reset_index().pivot(
        index="interaction_scenario", columns="method", values="net_interaction_value"
    )
    ax = pivot.plot(kind="bar", figsize=(10, 6))
    ax.set_xlabel("Interaction Scenario")
    ax.set_ylabel("Average Net Interaction Value")
    ax.set_title("Net Interaction Value by Scenario")
    plt.xticks(rotation=25, ha="right")
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "ga_figure_net_interaction_by_scenario.png"), dpi=200)
    plt.close()

    counts = results.groupby("method")["total_selected_campaigns"].mean().sort_values(ascending=False)
    ax = counts.plot(kind="bar", figsize=(10, 6))
    ax.set_xlabel("Method")
    ax.set_ylabel("Average Selected Campaign Count")
    ax.set_title("Average Selected Campaign Count by Method")
    plt.xticks(rotation=30, ha="right")
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "ga_figure_selected_campaigns_by_method.png"), dpi=200)
    plt.close()


if __name__ == "__main__":
    run()
