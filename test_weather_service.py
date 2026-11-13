
from weather_service import (
    get_current_weather,
    get_forecast,
    WeatherAPIError
)


def main():
    city = input("Enter a city name: ").strip()

    try:
        current = get_current_weather(city)

        print("\n--- CURRENT WEATHER ---")
        print(f"Location: {current['city']}, {current['country']}")
        print(f"Temperature: {current['temperature_c']:.1f} °C")
        print(f"Temperature: {current['temperature_f']:.1f} °F")
        print(f"Condition: {current['description']}")
        print(f"Humidity: {current['humidity']}%")
        print(f"Wind speed: {current['wind_speed']} m/s")

        forecast = get_forecast(city)

        print("\n--- FORECAST ---")
        for item in forecast[:6]:
            print(
                f"{item['datetime']} | "
                f"{item['temperature_c']:.1f} °C | "
                f"{item['description']}"
            )

        print(f"\nForecast entries received: {len(forecast)}")

    except WeatherAPIError as error:
        print(f"\nWeather Error: {error}")


if __name__ == "__main__":
    main()
