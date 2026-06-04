# House Sale Price Prediction & Affordability Dashboard

## Project Overview

This project is an end-to-end data science application developed for the DS570 Final Project. It analyzes Turkish house sale listings, builds a predictive machine learning model for sale price estimation, and presents the results through an interactive Streamlit dashboard.

The project focuses on two connected questions:

1. Can house sale prices be predicted from listing-level property features such as city, district, neighborhood, area and room layout?
2. Can the model output be used to support a simple housing affordability analysis?

The project is designed as a reproducible data science application rather than a static notebook. It includes data processing, exploratory visualization, predictive modeling, model evaluation, an interactive dashboard, Git-based project organization and Docker containerization.

---

## Problem Statement

Housing prices are highly dependent on location and physical property characteristics. However, buyers often need more than raw listing prices. They need to understand whether a listed price is reasonable relative to similar listings and whether it is affordable under a chosen income scenario.

This project develops a dashboard that allows users to:

- Explore housing price patterns across cities, districts and neighborhoods.
- Compare sale prices by area and room layout.
- Predict the expected sale price of a property.
- Compare predicted prices with district-level medians.
- Evaluate affordability using a simple income-based purchase budget rule.

---

## Data Source

The project uses a processed Turkish house sale listings dataset.

Expected file location:

```text
data/processed/house_sales_cleaned_for_ds570.csv
```

The dataset contains the following main fields:

```text
seller_type
area_m2
room_layout
city
district
neighborhood
listing_date
price_try
```

Additional engineered fields are created during preprocessing:

```text
rooms
living_rooms
total_rooms
listing_month
listing_day
price_per_m2
```

The dataset is based on sale listings rather than completed transaction prices. Therefore, the target variable represents asking price rather than confirmed market transaction price.

---

## Target Variable

The machine learning target is:

```text
price_try
```

This represents the listed sale price in Turkish Lira.

---

## Methodology

The project follows a standard end-to-end data science workflow:

1. Data audit
2. Data cleaning
3. Feature engineering
4. Baseline model development
5. Machine learning model training
6. Model evaluation
7. Dashboard development
8. Docker containerization

---

## Data Processing

The preprocessing step performs the following operations:

- Standardizes column names.
- Parses room layout values such as `3+1` into numeric room variables.
- Converts listing dates into usable date fields.
- Creates `listing_month` and `listing_day` features.
- Calculates `price_per_m2` for exploratory analysis.
- Applies domain-based filtering to remove unrealistic property records.

Domain-based model candidate filters:

```text
20 <= area_m2 <= 500
500,000 <= price_try <= 50,000,000
room layout must be parseable
```

The project intentionally excludes `price_per_m2` from model inputs because it is calculated from the target variable and would create data leakage.

---

## Feature Engineering

The model uses the following input features:

```text
seller_type
room_layout
city
district
neighborhood
area_m2
rooms
living_rooms
total_rooms
listing_month
listing_day
```

Categorical features are encoded inside a scikit-learn pipeline. Numerical features are passed through the modeling pipeline without applying target-derived transformations.

---

## Models

Two models are used:

### Baseline Model

```text
City + district median price predictor
```

This baseline predicts the median training price for each city and district combination. It is a meaningful benchmark because location is one of the strongest determinants of housing prices.

### Machine Learning Model

```text
RandomForestRegressor with log-transformed target
```

The target is log-transformed during training to reduce the effect of the right-skewed housing price distribution.

---

## Model Evaluation

The model is evaluated using regression metrics:

```text
MAE
RMSE
R²
MAPE
```

Current model results:

| Model | MAE | RMSE | R² | MAPE |
|---|---:|---:|---:|---:|
| City + district median baseline | 1,343,255 TRY | 2,417,259 TRY | 0.2868 | 39.52% |
| Random Forest with log target | 949,546 TRY | 1,968,067 TRY | 0.5272 | 25.37% |

The Random Forest model reduces MAE by approximately 29.31% compared with the baseline.

---

## Dashboard Features

The Streamlit dashboard includes six main sections:

### 1. Overview

- Filtered listing count
- Median sale price
- Median price per square meter
- Median area
- District-level price comparison
- Sale price distribution

### 2. Exploratory Analysis

- Area vs sale price relationship
- Median price by room layout
- Monthly median price trend

### 3. Prediction Tool

Users can enter property characteristics and receive:

- Predicted sale price
- Predicted price per square meter
- District median comparison
- Affordability ratio

### 4. Model Performance

- Baseline vs ML model metrics
- Feature importance
- Actual vs predicted plot
- Residual distribution

### 5. Affordability Analysis

Users can enter annual household income and an affordability multiplier. The dashboard compares district median prices with the estimated affordable purchase budget.

### 6. Limitations

The dashboard explicitly describes data and modeling limitations.

---

## Repository Structure

```text
.
├── app/
│   └── streamlit_app.py
├── src/
│   ├── data/
│   │   └── preprocess.py
│   └── models/
│       ├── train.py
│       └── evaluate.py
├── data/
│   ├── raw/
│   └── processed/
│       └── house_sales_cleaned_for_ds570.csv
├── models/
│   └── .gitkeep
├── reports/
│   ├── DATA_AUDIT.md
│   ├── MODEL_REPORT.md
│   ├── DASHBOARD_REPORT.md
│   └── DOCKERIZATION_REPORT.md
├── Dockerfile
├── entrypoint.sh
├── .dockerignore
├── .gitignore
├── requirements.txt
├── Makefile
├── DOCKER_RUN_GUIDE.md
└── README.md
```

---

## How to Run Locally

Install dependencies:

```bash
pip install -r requirements.txt
```

Run the dashboard:

```bash
streamlit run app/streamlit_app.py
```

Then open:

```text
http://localhost:8501
```

If the model file is missing, the dashboard automatically runs the training script and generates the required artifacts.

---

## How to Run with Docker

Build the Docker image:

```bash
docker build -t ds570-house-price-dashboard .
```

Run the container:

```bash
docker run --rm -p 8501:8501 ds570-house-price-dashboard
```

Then open:

```text
http://localhost:8501
```

The container automatically checks for processed data and model artifacts. If the trained model is not available, it runs the training pipeline before starting the dashboard.

---

## Generated Artifacts

The following files are generated by the model training pipeline and are not required to be stored in Git:

```text
models/house_price_model.joblib
reports/metrics.json
reports/feature_importance.csv
reports/test_predictions.csv
```

Large model artifacts are excluded from version control using `.gitignore`.

---

## Reproducibility

The project is reproducible because:

- The code is organized into reusable modules.
- Dependencies are listed in `requirements.txt`.
- The model can be regenerated from the processed dataset.
- Docker builds the application environment from scratch.
- The dashboard can run without manually adding the trained model artifact.

---

## Limitations

- The dataset contains asking prices, not finalized transaction prices.
- The model does not currently include building age, floor level, heating type, elevator, parking or transportation proximity.
- The affordability analysis is a simplified scenario tool and does not include mortgage rates, down payments or household debt.
- The model is trained on national data and then filtered for Istanbul-oriented analysis, because the Istanbul subset alone is relatively small.
- The current model does not estimate uncertainty intervals.

---

## Future Work

Possible extensions include:

- Adding mortgage payment simulation.
- Adding interest rate and down payment assumptions.
- Incorporating neighborhood-level socioeconomic indicators.
- Adding geocoded map visualizations.
- Comparing Random Forest with gradient boosting models.
- Adding prediction intervals or quantile regression.
- Improving temporal modeling with more historical listing data.

---

## Project Status

```text
Data audit: complete
Preprocessing pipeline: complete
Baseline model: complete
ML model: complete
Dashboard MVP: complete
Dockerization: complete
Final documentation: complete
```
