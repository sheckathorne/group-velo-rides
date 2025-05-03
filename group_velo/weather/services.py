from datetime import datetime, timedelta

import requests
from django.conf import settings


class WeatherService:
    def __init__(self):
        self.api_key = settings.WEATHER_API_KEY
        self.current_weather_url = settings.WEATHER_API_CURRENT_URL
        self.forecast_weather_url = settings.WEATHER_API_FORECAST_URL

    def get_weather_data(self, location=None, zipcode=None, forecast_date=None):
        """
        Fetch weather data for the given location and date from the external API

        Args:
            location: City or location name (optional if zipcode provided)
            zipcode: ZIP code for location (optional if location provided)
            forecast_date: Date to get forecast for (default: today)
        """
        try:
            # Determine if we need current weather or forecast
            today = datetime.now().date()
            forecast_date = forecast_date or today

            # Check if we need forecast or current weather
            days_ahead = (forecast_date - today).days

            if days_ahead == 0:
                return self._get_current_weather(location, zipcode)
            elif 1 <= days_ahead <= 7:  # Most free APIs limit forecasts to 7 days
                return self._get_forecast_weather(location, zipcode, days_ahead)
            else:
                raise ValueError(f"Cannot get forecast for {days_ahead} days ahead. Maximum is 7 days.")

        except requests.exceptions.RequestException as e:
            print(f"Error fetching weather data: {e}")
            raise

    def _get_current_weather(self, location=None, zipcode=None):
        """Get current weather data"""
        # Build the query parameters
        params = {"appid": self.api_key, "units": "metric"}

        # Add either location or zipcode parameter
        if zipcode:
            params["zip"] = zipcode
        elif location:
            params["q"] = location
        else:
            raise ValueError("Either location or zipcode must be provided")

        # Make the API request
        response = requests.get(self.current_weather_url, params=params)
        response.raise_for_status()

        data = response.json()

        # Extract the data we want to store
        weather_data = {
            "location": data["name"],  # Use the name returned by API
            "temperature": data["main"]["temp"],
            "humidity": data["main"]["humidity"],
            "wind_speed": data["wind"]["speed"],
            "description": data["weather"][0]["description"],
        }

        return weather_data

    def _get_forecast_weather(self, location=None, zipcode=None, days_ahead=1):
        """Get forecast weather data for a future date"""
        # Note: This implementation depends on your API provider
        # Here's a generic implementation for OpenWeatherMap's 5-day forecast

        # Build the query parameters
        params = {"appid": self.api_key, "units": "metric"}

        # Add either location or zipcode parameter
        if zipcode:
            params["zip"] = zipcode
        elif location:
            params["q"] = location
        else:
            raise ValueError("Either location or zipcode must be provided")

        # Make the API request
        response = requests.get(self.forecast_weather_url, params=params)
        response.raise_for_status()

        data = response.json()

        # Most APIs return forecast in 3-hour intervals
        # We need to find the forecast for the requested day
        target_date = datetime.now().date() + timedelta(days=days_ahead)

        # Find forecast entries for the target date (usually at noon)
        target_forecasts = []
        for forecast in data["list"]:
            forecast_dt = datetime.fromtimestamp(forecast["dt"]).date()
            if forecast_dt == target_date:
                target_forecasts.append(forecast)

        if not target_forecasts:
            raise ValueError(f"No forecast data available for {target_date}")

        # Use the forecast at midday (12:00) if available, otherwise use the first one
        midday_forecast = None
        for forecast in target_forecasts:
            forecast_hour = datetime.fromtimestamp(forecast["dt"]).hour
            if 11 <= forecast_hour <= 13:  # Around noon
                midday_forecast = forecast
                break

        selected_forecast = midday_forecast or target_forecasts[0]

        # Extract the data we want to store
        weather_data = {
            "location": data["city"]["name"],  # Use the name returned by API
            "temperature": selected_forecast["main"]["temp"],
            "humidity": selected_forecast["main"]["humidity"],
            "wind_speed": selected_forecast["wind"]["speed"],
            "description": selected_forecast["weather"][0]["description"],
        }

        return weather_data
