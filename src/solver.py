from pathlib import Path
import pandas as pd
from model import build_model

def main():
    data_path = Path(__file__).resolve().parents[1] / "data" / "marketing_campaign_dataset.csv"

    data = pd.read_csv(data_path)

    budget = 100000
    min_reach = 50000
    risk_weight = 0.5
    channel_limits = {
        "Social Media": 3,
        "Search Engine": 3,
        "Email": 2,
        "TV": 2
    }

    model = build_model(
        data=data,
        budget=budget,
        min_reach=min_reach,
        risk_weight=risk_weight,
        channel_limits=channel_limits
    )

    print("Dataset loaded successfully.")
    print(f"Number of campaigns: {len(data)}")
    print("Model structure created (placeholder stage).")
    print("Optimization solution will be added in the next deliverable.")

if __name__ == "__main__":
    main()
