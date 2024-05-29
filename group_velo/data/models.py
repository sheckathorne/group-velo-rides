from django.db import models


class ZipCodeCoordinate(models.Model):
    zip_code = models.TextField("Zip Code", null=False, blank=False)
    lat = models.DecimalField(max_digits=8, decimal_places=5)
    long = models.DecimalField(max_digits=8, decimal_places=5)

    class Meta:
        indexes = [models.Index(fields=["zip_code"])]

    def __str__(self):
        return self.zip_code


class NavBarItem(models.Model):
    title = models.CharField("Title", max_length=50, null=False, blank=False)
    template_name = models.CharField("Template Name", max_length=50, null=False, blank=False)
    order = models.IntegerField("Sort Order", null=False, blank=False)
    active = models.BooleanField("Active", null=False, blank=False)

    def __str__(self):
        return self.title


def get_coords_of(zip_code):
    row = ZipCodeCoordinate.objects.filter(zip_code=zip_code).first()
    if row:
        return row.lat, row.long
    else:
        return 39.0473, -95.6752
