import os
import re
import requests
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("OPENWEATHER_API_KEY")

CURRENT_WEATHER_URL = "https://api.openweathermap.org/data/2.5/weather"
FORECAST_URL = "https://api.openweathermap.org/data/2.5/forecast"


class WeatherAPIError(Exception):
    """Readable error raised for weather API failures."""


def _location_params(location):
    """
    Build OpenWeatherMap location parameters.

    Six-digit Indian PIN codes are sent as postal codes with country IN.
    Other inputs are treated as city/place names.
    """
    value = str(location).strip()

    if re.fullmatch(r"\d{6}", value):
        return {"zip": f"{value},IN"}

    return {"q": value}


def _make_request(url, params):
    if not API_KEY:
        raise WeatherAPIError(
            "API key is missing. Check that OPENWEATHER_API_KEY is set in .env."
        )

    request_params = dict(params)
    request_params["appid"] = API_KEY

    try:
        response = requests.get(url, params=request_params, timeout=10)

        if response.status_code == 401:
            raise WeatherAPIError(
                "The API key is invalid or has not been activated yet."
            )
        if response.status_code == 404:
            raise WeatherAPIError(
                "Location not found. Check the city name or Indian PIN code."
            )

        response.raise_for_status()
        try:
            return response.json()
        except ValueError as error:
            raise WeatherAPIError(
                "The weather service returned an unreadable response."
            ) from error

    except WeatherAPIError:
        raise
    except requests.exceptions.Timeout as error:
        raise WeatherAPIError(
            "The request timed out. Please try again."
        ) from error
    except requests.exceptions.ConnectionError as error:
        raise WeatherAPIError(
            "Network connection failed. Check your internet connection."
        ) from error
    except requests.exceptions.HTTPError as error:
        raise WeatherAPIError(
            "The weather service returned an HTTP error."
        ) from error
    except requests.exceptions.RequestException as error:
        raise WeatherAPIError(
            "Unable to connect to the weather service."
        ) from error


def get_current_weather(location):
    """Fetch current conditions by city name or six-digit Indian PIN code."""
    if not isinstance(location, str) or not location.strip():
        raise WeatherAPIError("Please enter a city name or PIN code.")

    params = _location_params(location)
    params["units"] = "metric"
    data = _make_request(CURRENT_WEATHER_URL, params)

    try:
        main = data["main"]
        weather = data["weather"][0]
        wind = data.get("wind", {})

        temp_c = float(main["temp"])
        feels_like_c = float(main["feels_like"])

        return {
            "city": data["name"],
            "country": data["sys"]["country"],
            "temperature_c": temp_c,
            "temperature_f": (temp_c * 9 / 5) + 32,
            "feels_like_c": feels_like_c,
            "feels_like_f": (feels_like_c * 9 / 5) + 32,
            "humidity": main["humidity"],
            "description": weather["description"].title(),
            "icon": weather["icon"],
            "wind_speed": float(wind.get("speed", 0))
        }
    except (KeyError, IndexError, TypeError, ValueError) as error:
        raise WeatherAPIError(
            "The current-weather response was missing expected data."
        ) from error


def get_forecast(location):
    """Fetch the 5-day forecast at 3-hour intervals by city or Indian PIN code."""
    if not isinstance(location, str) or not location.strip():
        raise WeatherAPIError("Please enter a city name or PIN code.")

    params = _location_params(location)
    params["units"] = "metric"
    data = _make_request(FORECAST_URL, params)

    forecast_items = []
    try:
        for item in data.get("list", []):
            main = item["main"]
            weather = item["weather"][0]
            temp_c = float(main["temp"])

            forecast_items.append({
                "datetime": item["dt_txt"],
                "temperature_c": temp_c,
                "temperature_f": (temp_c * 9 / 5) + 32,
                "humidity": main["humidity"],
                "description": weather["description"].title(),
                "icon": weather["icon"],
                "wind_speed": float(item.get("wind", {}).get("speed", 0))
            })
    except (KeyError, IndexError, TypeError, ValueError) as error:
        raise WeatherAPIError(
            "The forecast response was missing expected data."
        ) from error

    if not forecast_items:
        raise WeatherAPIError("No forecast information is available.")

    return forecast_items
