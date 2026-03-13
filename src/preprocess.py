import pandas as pd


def load_campaign_data(path):
    """
    Load and prepare campaign dataset
    """

    df = pd.read_csv(path)

    # Select relevant columns
    df_model = df[[
        "Campaign_ID",
        "Acquisition_Cost",
        "ROI",
        "Impressions",
        "Channel_Used"
    ]]

    # Rename columns for model
    df_model = df_model.rename(columns={
        "Acquisition_Cost": "cost",
        "ROI": "roi",
        "Impressions": "reach",
        "Channel_Used": "channel"
    })

    return df_model

