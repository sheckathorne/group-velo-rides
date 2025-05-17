from datetime import datetime

import requests
from celery import shared_task
from django.conf import settings

from group_velo.weather.models import WeatherForecastDay, WeatherForecastHour


@shared_task(bind=True, max_retries=3)
def fetch_weather_for_zip(self, zip_code):
    """
    Celery task to fetch weather data for a zip code
    and update the database cache.
    """
    try:
        api_url = (
            f"{settings.WEATHER_API_BASE_URL}?key={settings.WEATHER_API_KEY}&days=3&q={zip_code}&alerts=no&aqi=no"
        )
        response = requests.get(api_url)

        if response.status_code == 200:
            forecast_data = response.json()
            forecast = forecast_data["forecast"]["forecastday"]

            # First delete any existing forecast for this zip code
            # This ensures we're replacing old data completely
            WeatherForecastDay.objects.filter(zip_code=zip_code).delete()

            weather_forcast_hours = []

            for fd in forecast:
                forecast_day = fd["day"]
                weather_forecast_day_object = WeatherForecastDay.objects.create(
                    zip_code=zip_code,
                    forecast_date=fd["date"],
                    maxtemp_c=forecast_day["maxtemp_c"],
                    maxtemp_f=forecast_day["maxtemp_f"],
                    mintemp_c=forecast_day["mintemp_c"],
                    mintemp_f=forecast_day["mintemp_f"],
                    maxwind_mph=forecast_day["maxwind_mph"],
                    maxwind_kph=forecast_day["maxwind_kph"],
                    chance_of_rain=forecast_day["daily_chance_of_rain"],
                    chance_of_snow=forecast_day["daily_chance_of_snow"],
                    condition_text=forecast_day["condition"]["text"],
                    condition_icon_url=forecast_day["condition"]["icon"],
                    condition_code=forecast_day["condition"]["code"],
                )

                for forecast_hour in fd["hour"]:
                    time_str = forecast_hour["time"]
                    dt_obj = datetime.strptime(time_str, "%Y-%m-%d %H:%M")
                    hour = dt_obj.hour
                    weather_forecast_hour_object = WeatherForecastHour.objects.create(
                        forecast=weather_forecast_day_object,
                        hour=hour,
                        temperature_f=forecast_hour["temp_f"],
                        temperature_c=forecast_hour["temp_c"],
                        wind_mph=forecast_hour["wind_mph"],
                        wind_kph=forecast_hour["wind_kph"],
                        wind_direction=forecast_hour["wind_dir"],
                        wind_heading=forecast_hour["wind_degree"],
                        feelslike_c=forecast_hour["feelslike_c"],
                        feelslike_f=forecast_hour["feelslike_f"],
                        chance_of_rain=forecast_hour["chance_of_rain"],
                        chance_of_snow=forecast_hour["chance_of_snow"],
                        condition_text=forecast_hour["condition"]["text"],
                        condition_icon_url=forecast_hour["condition"]["icon"],
                        condition_code=forecast_hour["condition"]["code"],
                    )

                    weather_forcast_hours.append(weather_forecast_hour_object)

            return {"success": True, "zip_code": zip_code}
        else:
            if 500 <= response.status_code < 600:
                raise self.retry(
                    exc=Exception(f"Server error {response.status_code}"), countdown=2**self.request.retries
                )

            return {
                "success": False,
                "zip_code": zip_code,
                "error": f"API returned status code {response.status_code}",
            }
    except self.MaxRetriesExceededError:
        return {"success": False, "zip_code": zip_code, "error": "Maximum retries exceeded"}
    except Exception as e:
        # For other errors, retry with exponential backoff
        try:
            raise self.retry(exc=e, countdown=2**self.request.retries)
        except self.MaxRetriesExceededError:
            return {"success": False, "zip_code": zip_code, "error": str(e)}
