
import pandas as pd
import numpy as np

from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error

# 1. Load historical rainfall data
df = pd.read_csv("kannur_nasa_power_rainfall_2000_2020.csv")

df["Date"] = pd.to_datetime(df["Date"])
df = df.sort_values("Date").reset_index(drop=True)

# 2. Create rainfall history features
lag_days = [1, 2, 3, 4, 5, 6, 7, 14, 30, 365]

for i in lag_days:
    df[f"Rainfall_lag_{i}"] = df["Rainfall_mm"].shift(i)

# 3. Calculate previous rainfall averages
for window in [7, 14, 30]:
    df[f"Rainfall_rolling_mean_{window}"] = (
        df["Rainfall_mm"].shift(1).rolling(window).mean()
    )

# 4. Add seasonal features
df["Day_of_year"] = df["Date"].dt.day_of_year

df["Season_sin"] = np.sin(
    2 * np.pi * df["Day_of_year"] / 365.25
)

df["Season_cos"] = np.cos(
    2 * np.pi * df["Day_of_year"] / 365.25
)

# 5. Remove incomplete records
df = df.dropna().reset_index(drop=True)

# 6. Select features and target
lag_features = [
    f"Rainfall_lag_{i}" for i in lag_days
]

rolling_features = [
    f"Rainfall_rolling_mean_{i}" for i in [7, 14, 30]
]

seasonal_features = ["Season_sin", "Season_cos"]

X = df[lag_features + rolling_features + seasonal_features]
y = df["Rainfall_mm"]

# 7. Chronological train-test split
split = int(len(df) * 0.8)

X_train = X.iloc[:split]
X_test = X.iloc[split:]

y_train = y.iloc[:split]
y_test = y.iloc[split:]

# 8. Train Random Forest model
model = RandomForestRegressor(
    n_estimators=200,
    random_state=42,
    n_jobs=-1
)

model.fit(X_train, y_train)

# 9. Generate predictions
predictions = model.predict(X_test)

# 10. Evaluate Random Forest model
model_mae = mean_absolute_error(y_test, predictions)

model_rmse = np.sqrt(
    mean_squared_error(y_test, predictions)
)

# 11. Compare baseline models on the same test records
print("\nBASELINE MODEL COMPARISON")
print("=" * 40)

for lag in [1, 365]:

    baseline_predictions = X_test[f"Rainfall_lag_{lag}"]

    baseline_mae = mean_absolute_error(
        y_test, baseline_predictions
    )

    baseline_rmse = np.sqrt(
        mean_squared_error(y_test, baseline_predictions)
    )

    label = "Previous-day" if lag == 1 else "Previous-year"

    print(f"\n{label} Baseline")
    print("MAE:", round(baseline_mae, 3), "mm")
    print("RMSE:", round(baseline_rmse, 3), "mm")

# 12. Display Random Forest results
print("\nRANDOM FOREST MODEL")
print("=" * 40)

print("Training records:", len(X_train))
print("Testing records:", len(X_test))

print("MAE:", round(model_mae, 3), "mm")
print("RMSE:", round(model_rmse, 3), "mm")

print("\nModel training and evaluation completed!")
