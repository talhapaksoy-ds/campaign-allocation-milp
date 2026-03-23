# main.py

from data_generator import get_test_instance
from model import solve_campaign_allocation


def main():
    data = get_test_instance()
    result = solve_campaign_allocation(data)

    print("=" * 55)
    print("MARKETING CAMPAIGN BUDGET ALLOCATION - TEST RUN")
    print("=" * 55)

    print(f"Solver Status   : {result['status']}")

    if result["objective_value"] is not None:
        print(f"Objective Value : {result['objective_value']:.2f}")
        print(f"Selected Items  : {', '.join(result['selected_campaigns'])}")
        print(f"Total Cost      : {result['total_cost']}")
        print(f"Total Reach     : {result['total_reach']}")

        print("\nChannel Usage:")
        for ch, count in result["channel_usage"].items():
            print(f"  - {ch}: {count}")

        print("\nInterpretation:")
        print(
            "The model selected the campaign portfolio that maximizes "
            "risk-adjusted return while satisfying the budget, minimum "
            "reach, and channel limit constraints."
        )
    else:
        print("No feasible optimal solution was returned.")
        print(
            "Check whether the instance is infeasible, the solver license "
            "is unavailable, or another solver issue occurred."
        )

    print("=" * 55)


if __name__ == "__main__":
    main()
