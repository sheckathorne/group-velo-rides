from datetime import timedelta

from celery import shared_task
from django.db import transaction
from django.utils import timezone

from group_velo.events.models import EventOccurence
from group_velo.weather.models import WeatherForecastDay
from group_velo.weather.services import WeatherService


@shared_task
def fetch_weather_data(location, zip_code=None):
    """
    Celery task to fetch weather data and store it in the database

    Args:
        location: City or location name
        zipcode: Optional zipcode for more precise location
        forecast_date: Date to get forecast for (defaults to today)
        force_refresh: If True, bypass cache and force API call
    """
    try:
        forecast_date = timezone.now().date()

        # Check if we have recent cached data for this location/date
        cached_data = WeatherForecastDay.get_cached_weather(zip_code=zip_code)
        if cached_data:
            print(f"Using cached weather data for {zip_code} on {forecast_date}")
            return cached_data.to_dict()

        # If we're here, we need fresh data
        print(f"Fetching fresh weather data for {zip_code} on {forecast_date}")
        weather_service = WeatherService()
        weather_data = weather_service.get_weather_data(zip_code, forecast_date)

        # Check if we already have a record for this location/date to update
        existing_record = WeatherForecastDay.objects.filter(forecast_date=forecast_date)

        if zip_code:
            existing_record = existing_record.filter(zipcode=zip_code)
        elif location:
            existing_record = existing_record.filter(location__iexact=location)

        existing_record = existing_record.first()

        if existing_record:
            # Update existing record
            existing_record.temperature = weather_data["temperature"]
            existing_record.humidity = weather_data["humidity"]
            existing_record.wind_speed = weather_data["wind_speed"]
            existing_record.description = weather_data["description"]
            existing_record.last_fetched = timezone.now()
            existing_record.save()
            weather_record = existing_record
        else:
            # Create new record
            weather_record = WeatherForecastDay.objects.create(
                location=weather_data["location"],
                zip_code=zip_code,
                temperature=weather_data["temperature"],
                humidity=weather_data["humidity"],
                wind_speed=weather_data["wind_speed"],
                description=weather_data["description"],
                forecast_date=forecast_date,
                last_fetched=timezone.now(),
            )

        # Return the saved data
        return weather_record.to_dict()

    except Exception as e:
        # Return error info
        return {"error": str(e)}


@shared_task
def process_upcoming_events_weather():
    """
    Process all upcoming events for the next 3 days and fetch their weather forecasts
    """
    today = timezone.now().date()
    three_days_later = today + timedelta(days=3)

    # Get all events in the next 3 days
    upcoming_events = EventOccurence.objects.filter(event_date__gte=today, event_date__lt=three_days_later).order_by(
        "event_date"
    )

    # Extract unique zip codes by date
    unique_zipcodes_by_date = {}
    for event in upcoming_events:
        if event.ride_date not in unique_zipcodes_by_date:
            unique_zipcodes_by_date[event.ride_date] = set()
        unique_zipcodes_by_date[event.ride_date].add(event.ride_date)

    # Process each unique zipcode for each date
    results = []
    for event_date, zipcodes in unique_zipcodes_by_date.items():
        for zipcode in zipcodes:
            # Fetch or use cached weather data for each zipcode/date combo
            task_result = fetch_weather_data.apply_async(
                kwargs={
                    "location": None,  # We're using zipcode-based lookup
                    "zipcode": zipcode,
                    "forecast_date": event_date.isoformat(),
                    "force_refresh": False,  # Use cache if available
                }
            )
            # Get the result
            weather_data_dict = task_result.get()
            if "error" not in weather_data_dict:
                # Find the actual weather data record
                weather_record = WeatherForecastDay.objects.get(id=weather_data_dict["id"])

                # Update all events with this zipcode and date
                with transaction.atomic():
                    events_to_update = EventOccurence.objects.filter(
                        zipcode=zipcode,
                        event_date=event_date,
                        weather_data__isnull=True,  # Only update events without weather data
                    )
                    for event in events_to_update:
                        event.weather_data = weather_record
                        event.save(update_fields=["weather_data"])

                results.append(
                    {
                        "date": event_date.isoformat(),
                        "zipcode": zipcode,
                        "weather_id": weather_record.id,
                        "updated_events": events_to_update.count(),
                    }
                )
            else:
                results.append(
                    {"date": event_date.isoformat(), "zipcode": zipcode, "error": weather_data_dict["error"]}
                )

    return results


@shared_task
def refresh_event_weather(event_id):
    """
    Refresh weather data for a specific event
    """
    try:
        event = EventOccurence.objects.get(id=event_id)

        # Fetch fresh weather data
        task_result = fetch_weather_data.apply_async(
            kwargs={
                "location": event.location,
                "zip_code": event.zip_code,
                "forecast_date": event.event_date.isoformat(),
                "force_refresh": True,  # Force refresh
            }
        )

        weather_data_dict = task_result.get()
        if "error" not in weather_data_dict:
            # Link the weather data to the event
            weather_record = WeatherForecastDay.objects.get(id=weather_data_dict["id"])
            event.weather_data = weather_record
            event.save(update_fields=["weather_data"])

            return {"success": True, "event_id": event.id, "weather_id": weather_record.id}
        else:
            return {"success": False, "event_id": event.id, "error": weather_data_dict["error"]}

    except EventOccurence.DoesNotExist:
        return {"success": False, "error": f"Event with ID {event_id} not found"}
    except Exception as e:
        return {"success": False, "error": str(e)}
