import pandas as pd
from pathlib import Path
from sklearn.ensemble import RandomForestRegressor

# -----------------------------------
# 1. Load Bus Dataset
# -----------------------------------

BASE_DIR = Path(__file__).resolve().parent
data = pd.read_csv(BASE_DIR / "bus_data.csv")

# -----------------------------------
# 2. Input Features
# -----------------------------------

features = [
    "distance_km",
    "traffic_level",
    "weather",
    "previous_time_min"
]

X = data[features]

# Target: travel/arrival time in minutes
y = data["previous_time_min"]

# -----------------------------------
# 3. Create and Train ML Model
# -----------------------------------

model = RandomForestRegressor(
    n_estimators=200,
    random_state=42,
    max_depth=6
)

model.fit(X, y)


# -----------------------------------
# 4. Prediction Function
# -----------------------------------

def predict_arrival(
    distance,
    traffic,
    weather,
    previous_time
):

    input_data = pd.DataFrame(
        [[
            float(distance),
            float(traffic),
            float(weather),
            float(previous_time)
        ]],
        columns=features
    )

    prediction = model.predict(input_data)

    return round(float(prediction[0]), 2)


# -----------------------------------
# 5. Test Predictions
# -----------------------------------

if __name__ == "__main__":

    print("\n================================")
    print("   AI BUS ARRIVAL PREDICTION")
    print("================================\n")

    # Test 1
    result1 = predict_arrival(
        10,      # Distance
        2,       # Traffic
        1,       # Weather
        22       # Previous time
    )

    print("Test 1")
    print("Distance       : 10 km")
    print("Traffic Level  : 2")
    print("Weather        : 1")
    print("Previous Time  : 22 minutes")
    print("Predicted Time :", result1, "minutes")

    print("\n-------------------------------\n")

    # Test 2
    result2 = predict_arrival(
        20,
        3,
        2,
        42
    )

    print("Test 2")
    print("Distance       : 20 km")
    print("Traffic Level  : 3")
    print("Weather        : 2")
    print("Previous Time  : 42 minutes")
    print("Predicted Time :", result2, "minutes")

    print("\n================================")
    print("       MODEL TEST COMPLETE")
    print("================================")
