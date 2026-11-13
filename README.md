# Weather Studio

A desktop weather application built with **Python and Tkinter** that retrieves current weather conditions and forecast data from the **OpenWeatherMap API**.

Weather Studio provides a clean graphical interface for checking weather by city name or Indian PIN code, viewing current conditions, and exploring upcoming forecast periods.

## Features

- **Location search:** Search by city/place name or six-digit Indian PIN code.
- **Current weather:** View temperature, feels-like temperature, humidity, wind speed, and weather conditions.
- **Weather icons:** Display weather-condition icons from OpenWeatherMap.
- **Forecast periods:** View the next six forecast entries supplied at three-hour intervals.
- **Five-day forecast:** View daily estimated temperature ranges based on the available three-hour forecast entries.
- **Temperature conversion:** Switch between Celsius and Fahrenheit.
- **Scrollable interface:** Navigate the dashboard using the scrollbar or mouse wheel.
- **Input and API error handling:** Show readable messages for empty input, invalid locations, network problems, and API errors.

> **Forecast note:** OpenWeatherMap's forecast endpoint provides forecast entries at three-hour intervals. The daily minimum and maximum shown by this application are estimates calculated from the available entries for each date; they are not guaranteed full-day observed minimum and maximum temperatures.

## Technology Stack

- Python
- Tkinter — desktop GUI
- Requests — HTTP requests to the weather API
- Pillow — weather icon image handling
- python-dotenv — local environment variable loading
- OpenWeatherMap API — current weather and forecast data

## Project Structure

```text
Weather-App/
├── main.py
├── weather_service.py
├── test_weather_service.py
├── requirements.txt
├── .gitignore
└── .env                  # Create this locally; do not commit it
```

## Requirements

- Python 3.10 or newer
- An OpenWeatherMap API key
- Internet connection

## Setup and Installation

### 1. Clone the repository

```bash
git clone https://github.com/YUREKAN1/Weather-App.git
cd Weather-App
```

### 2. Create and activate a virtual environment

**Windows PowerShell**

```powershell
python -m venv task4env
.\task4env\Scripts\Activate.ps1
```

### 3. Install dependencies

```powershell
python -m pip install -r requirements.txt
```

### 4. Configure the API key

Create a file named `.env` in the project root:

```env
OPENWEATHER_API_KEY=your_openweathermap_api_key
```

Replace the placeholder with your own API key. Do not share this file or commit it to Git. The repository's `.gitignore` excludes `.env`.

### 5. Run the application

```powershell
python main.py
```

Enter a city name (for example, `Chennai`) or a six-digit Indian PIN code (for example, `626101`) and select **Get Weather**.

## Running the Service Test

The project includes a weather-service test script:

```powershell
python test_weather_service.py
```

The script may make live API requests, so a valid API key and internet connection are required.

## API

Weather data is retrieved from [OpenWeatherMap](https://openweathermap.org/).

The application uses:
- Current Weather endpoint
- 5-day / 3-hour Forecast endpoint

See the [OpenWeatherMap API documentation](https://openweathermap.org/api) for details, account limits, and API-key activation.

## Security

- Keep your API key in the local `.env` file.
- Never commit `.env` or paste your API key into public issues, screenshots, or source files.
- If an API key is accidentally exposed, regenerate it through your OpenWeatherMap account.

## Author

**Yurekan M**

- GitHub: [@YUREKAN1](https://github.com/YUREKAN1)
