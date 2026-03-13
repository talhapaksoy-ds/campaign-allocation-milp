import pulp


def build_model(data, budget, min_reach):
    """
    Build MILP optimization model
    """

    model = pulp.LpProblem("Marketing_Campaign_Selection", pulp.LpMaximize)

    campaigns = data.index

    # Decision variables
    x = pulp.LpVariable.dicts("x", campaigns, cat="Binary")

    # Objective function
    model += pulp.lpSum(data.loc[i, "roi"] * x[i] for i in campaigns)

    # Budget constraint
    model += pulp.lpSum(data.loc[i, "cost"] * x[i] for i in campaigns) <= budget

    # Reach constraint
    model += pulp.lpSum(data.loc[i, "reach"] * x[i] for i in campaigns) >= min_reach

    return model, x
