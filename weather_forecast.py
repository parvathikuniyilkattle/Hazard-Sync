
import requests
import pandas as pd

def get_rainfall_forecast():

    url = "https://api.open-meteo.com/v1/forecast"

    params = {
        "latitude": 11.87,
        "longitude": 75.37,
        "daily": [
            "precipitation_sum",
            "precipitation_probability_max"
        ],
        "forecast_days": 7,
        "timezone": "Asia/Kolkata"
    }

    try:
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()

        data = response.json()
        daily = data["daily"]

        forecast = pd.DataFrame({
            "Date": daily["time"],
            "Rainfall_mm": daily["precipitation_sum"],
            "Rain_Probability_Percent":
                daily["precipitation_probability_max"]
        })

        return forecast

    except requests.RequestException as error:
        print("Weather API error:", error)
        return None

if __name__ == "__main__":

    forecast = get_rainfall_forecast()

    if forecast is not None:
        print("\nKANNUR 7-DAY RAINFALL FORECAST")
        print("=" * 45)
        print(forecast.to_string(index=False))

        forecast.to_csv(
            "kannur_7day_forecast.csv",
            index=False
        )

        print("\nForecast saved successfully!")
