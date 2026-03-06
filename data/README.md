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
