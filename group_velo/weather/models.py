from datetime import timedelta

from django.db import models
from django.utils import timezone


class WeatherForecastConditionBase(models.Model):
    condition_text = models.TextField("Condition", max_length=20)
    condition_icon_url = models.TextField("Icon URL", max_length=255)
    condition_code = models.IntegerField()

    class Meta:
        abstract = True


class WeatherForecastDay(WeatherForecastConditionBase):
    # When the data was fetched from the API
    last_fetched = models.DateTimeField(default=timezone.now)
    # The date this forecast is for (if forecast data)
    forecast_date = models.DateField(default=timezone.now, db_index=True)
    # Zipcode for more precise location tracking
    zip_code = models.CharField(max_length=10, blank=True, null=True, db_index=True)
    # When was this record created in our DB
    createdatetime = models.DateTimeField(default=timezone.now)

    location = models.CharField(max_length=100, db_index=True)
    maxtemp_c = models.FloatField()
    maxtemp_f = models.FloatField()
    mintemp_c = models.FloatField()
    mintemp_f = models.FloatField()
    description = models.CharField(max_length=200)

    class Meta:
        # Unique constraint to prevent duplicate forecasts for the same location/date
        unique_together = ("zip_code", "forecast_date")
        indexes = [
            # Index for faster querying of recent forecasts
            models.Index(fields=["last_fetched"]),
        ]

    def __str__(self):
        date_str = self.forecast_date.strftime("%Y-%m-%d")
        return f"{self.zip_code} Weather - {date_str}"

    def to_dict(self):
        return {
            "id": self.id,
            "zip_code": self.zip_code,
            "temperature": (self.mintemp_f, self.maxtemp_f),
            "forecast_date": self.forecast_date.strftime("%Y-%m-%d"),
            "last_fetched": self.last_fetched.strftime("%Y-%m-%d %H:%M:%S"),
            "createdatetime": self.createdatetime.strftime("%Y-%m-%d %H:%M:%S"),
        }

    @classmethod
    def get_cached_weather(cls, zipcode=None, forecast_date=None, max_age_hours=12):
        """
        Retrieve cached weather data if it exists and is recent enough

        Args:
            location: City or location name
            zipcode: Optional zipcode for more precise lookup
            forecast_date: Date to get forecast for (defaults to today)
            max_age_hours: Maximum age of cached data in hours

        Returns:
            WeatherData object if valid cache exists, None otherwise
        """
        cutoff_time = timezone.now() - timedelta(hours=max_age_hours)
        forecast_date = forecast_date or timezone.now().date()

        # Build query based on available parameters
        query = cls.objects.filter(last_fetched__gte=cutoff_time, forecast_date=forecast_date)

        if zipcode:
            query = query.filter(zipcode=zipcode)

        # Return most recently fetched result if it exists
        return query.order_by("-last_fetched").first()


class WeatherForecastHour(WeatherForecastConditionBase):
    forecast = models.ForeignKey(WeatherForecastDay, on_delete=models.CASCADE)
    time = models.DateTimeField(default=timezone.now)
    teperature_f = models.FloatField()
    teperature_c = models.FloatField()
    wind_mph = models.IntegerField()
    wind_kph = models.IntegerField()
    wind_direction = models.TextField("Wind Direction", max_length=3)
    wind_heading = models.IntegerField("Wind Heading")
    feelslike_c = models.FloatField()
    feelslike_f = models.FloatField()

    class Meta:
        # Unique constraint to prevent duplicate forecasts for the same location/date
        unique_together = ("forecast", "time")
        indexes = [
            # Index for faster querying of recent forecasts
            models.Index(fields=["time"]),
        ]

    def __str__(self):
        date_str = f"{self.forecast.date.strftime('%Y-%m-%d')} {self.forecast.time.strftime('%H:%mm')}"
        return f"{self.forecast.zip_code} Weather - {date_str}"
