from preprocess import load_campaign_data
from model import build_model


# Load dataset
data = load_campaign_data("data/marketing_campaign_dataset.csv")

# Use smaller sample for testing
data = data.sample(200)

# Build model
model, x = build_model(data, budget=500000, min_reach=100000)

# Solve model
model.solve()

print("Selected campaigns:")

for i in x:
    if x[i].value() == 1:
        print(i)
