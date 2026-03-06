"""
This file will contain the MILP formulation of the campaign selection problem,
including decision variables, objective function, and constraints.
"""

def build_model(data, budget, min_reach, risk_weight, channel_limits=None):
    """
    Build the optimization model.

    Parameters:
    data : pandas.DataFrame
        Campaign-level dataset.
    budget : float
        Total available marketing budget.
    min_reach : float
        Minimum required total reach.
    risk_weight : float
        Weight used to penalize campaign risk in the objective function.
    channel_limits : dict, optional
        Maximum number of campaigns allowed for each channel.

    Returns
  
    model : object
        Optimization model object (sonraki aşamada uygulanacak).
    """
    model = None
    return model
