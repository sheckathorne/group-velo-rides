from datetime import timedelta

from django.db import models
from django.utils import timezone


class WeatherForecastConditionBase(models.Model):
    condition_text = models.CharField("Condition", max_length=60)
    condition_icon_url = models.CharField("Icon URL", max_length=255)
    condition_code = models.IntegerField()
    chance_of_rain = models.IntegerField("Rain Chance", default=0)
    chance_of_snow = models.IntegerField("Snow Chance", default=0)

    @property
    def chance_of_precip(self):
        return max(self.chance_of_rain, self.chance_of_snow)

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

    maxtemp_c = models.FloatField()
    maxtemp_f = models.FloatField()
    mintemp_c = models.FloatField()
    mintemp_f = models.FloatField()
    maxwind_mph = models.FloatField()
    maxwind_kph = models.FloatField()
    description = models.CharField(max_length=200)

    @classmethod
    def is_fresh(cls, zip_code):
        """Check if forecast is less than 12 hours old"""
        try:
            forecast = cls.objects.filter(zip_code=zip_code).first()
            if forecast is None:
                return False

            if timezone.now() - forecast.last_fetched < timedelta(hours=12):
                return True
            else:
                forecast.delete()
                return False
        except cls.DoesNotExist:
            return False

    @classmethod
    def get_forecast(cls, zip_code):
        """Get forecast data if it exists"""
        try:
            if cls.is_fresh(zip_code):
                return cls.objects.filter(zip_code=zip_code)
            else:
                return None
        except cls.DoesNotExist:
            return None

    def __str__(self):
        date_str = self.forecast_date.strftime("%Y-%m-%d")
        return f"{self.zip_code} Weather - {date_str}"

    def to_dict(self):
        return {
            "id": self.pk,
            "zip_code": self.zip_code,
            "temperature": (self.mintemp_f, self.maxtemp_f),
            "forecast_date": self.forecast_date.strftime("%Y-%m-%d"),
            "last_fetched": self.last_fetched.strftime("%Y-%m-%d %H:%M:%S"),
            "createdatetime": self.createdatetime.strftime("%Y-%m-%d %H:%M:%S"),
        }

    @classmethod
    def get_cached_weather(cls, zip_code=None, max_age_hours=12):
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
        # forecast_date = timezone.now().date()

        # Build query based on available parameters
        query = cls.objects.filter(last_fetched__gte=cutoff_time, zip_code__in=zip_code)

        # Return most recently fetched result if it exists
        return query.order_by("-last_fetched").first()

    class Meta:
        constraints = [models.UniqueConstraint(fields=["zip_code", "forecast_date"], name="unique_zip_forecastdate")]


class WeatherForecastHour(WeatherForecastConditionBase):
    forecast = models.ForeignKey(WeatherForecastDay, on_delete=models.CASCADE)
    hour = models.SmallIntegerField(default=0)
    temperature_f = models.FloatField()
    temperature_c = models.FloatField()
    wind_mph = models.IntegerField()
    wind_kph = models.IntegerField()
    wind_direction = models.TextField("Wind Direction", max_length=3)
    wind_heading = models.IntegerField("Wind Heading")
    feelslike_c = models.FloatField()
    feelslike_f = models.FloatField()

    class Meta:
        constraints = [models.UniqueConstraint(fields=["forecast", "hour"], name="unique_forecast_time")]
        indexes = [
            # Index for faster querying of recent forecasts
            models.Index(fields=["hour"]),
        ]

    @classmethod
    def get_forecast_hour(cls, zip_code, forecast_date):
        """Get forecast data if it exists"""
        try:
            return cls.objects.filter(forecast__zip_code=zip_code, forecast__forecast_date=forecast_date)
        except cls.DoesNotExist:
            return None

    @property
    def chance_of_precip(self):
        return max(self.chance_of_rain, self.chance_of_snow)

    def __str__(self):
        date_str = f"{self.forecast.forecast_date.strftime('%Y-%m-%d')} {self.hour}"
        return f"{self.forecast.zip_code} Weather - {date_str}"
