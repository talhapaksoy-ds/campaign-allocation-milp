# Data

This project uses a marketing campaign dataset containing campaign-level information.

The dataset includes attributes related to campaign performance and marketing channels. 
From this dataset, the parameters required by the optimization model will be derived.

Main fields used in the model:

- campaign_id
- channel
- cost
- roi
- risk
- reach

These variables will be used to construct the optimization inputs such as campaign cost, expected return, and audience reach.

If additional data is required for experiments, synthetic campaign records may be generated to test the model under different problem sizes.

# Dataset Information

This folder contains the dataset used in the marketing campaign optimization project.

Due to its large size, the dataset is stored as a compressed file:

marketing_campaign_dataset.zip

The dataset includes campaign-level information such as campaign type, marketing channel, acquisition cost, return on investment (ROI), and engagement metrics.

To run the preprocessing and optimization scripts, the dataset should be extracted from the zip file and placed in this folder as:

data/marketing_campaign_dataset.csv

The dataset is used to derive the parameters required for the optimization model, including campaign cost, expected return, audience reach, and marketing channel information.
