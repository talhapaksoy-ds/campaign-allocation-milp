# model.py

import gurobipy as gp
from gurobipy import GRB


def solve_campaign_allocation(data):
    campaigns = data["campaigns"]
    budget = data["budget"]
    min_reach = data["min_reach"]
    risk_penalty = data["risk_penalty"]
    channel_caps = data["channel_caps"]

    campaign_ids = [c["id"] for c in campaigns]

    cost = {c["id"]: c["cost"] for c in campaigns}
    roi = {c["id"]: c["roi"] for c in campaigns}
    risk = {c["id"]: c["risk"] for c in campaigns}
    reach = {c["id"]: c["reach"] for c in campaigns}
    channel = {c["id"]: c["channel"] for c in campaigns}

    model = gp.Model("marketing_campaign_budget_allocation")

    # Optional: suppress verbose solver output
    model.Params.OutputFlag = 0

    # Decision variables: x[i] = 1 if campaign i is selected, 0 otherwise
    x = model.addVars(campaign_ids, vtype=GRB.BINARY, name="x")

    # Objective: maximize risk-adjusted return
    model.setObjective(
        gp.quicksum((roi[i] - risk_penalty * risk[i]) * x[i] for i in campaign_ids),
        GRB.MAXIMIZE
    )

    # Budget constraint
    model.addConstr(
        gp.quicksum(cost[i] * x[i] for i in campaign_ids) <= budget,
        name="budget_constraint"
    )

    # Minimum reach constraint
    model.addConstr(
        gp.quicksum(reach[i] * x[i] for i in campaign_ids) >= min_reach,
        name="minimum_reach_constraint"
    )

    # Channel capacity constraints
    for ch, cap in channel_caps.items():
        model.addConstr(
            gp.quicksum(x[i] for i in campaign_ids if channel[i] == ch) <= cap,
            name=f"channel_cap_{ch}"
        )

    model.optimize()

    result = {
        "status_code": model.Status,
        "status": _get_status_text(model.Status),
        "objective_value": None,
        "selected_campaigns": [],
        "total_cost": None,
        "total_reach": None,
        "channel_usage": {},
    }

    if model.Status == GRB.OPTIMAL:
        selected = [i for i in campaign_ids if x[i].X > 0.5]

        total_cost = sum(cost[i] for i in selected)
        total_reach = sum(reach[i] for i in selected)

        channel_usage = {}
        for ch in channel_caps:
            channel_usage[ch] = sum(1 for i in selected if channel[i] == ch)

        result.update({
            "objective_value": model.ObjVal,
            "selected_campaigns": selected,
            "total_cost": total_cost,
            "total_reach": total_reach,
            "channel_usage": channel_usage,
        })

    return result


def _get_status_text(status_code):
    if status_code == GRB.OPTIMAL:
        return "Optimal"
    if status_code == GRB.INFEASIBLE:
        return "Infeasible"
    if status_code == GRB.TIME_LIMIT:
        return "Time limit"
    if status_code == GRB.UNBOUNDED:
        return "Unbounded"
    if status_code == GRB.INF_OR_UNBD:
        return "Infeasible or Unbounded"
    return f"Other status ({status_code})"
